# feedback_ui/widgets/feedback_text_edit.py
import os
import sys
import re
from typing import Optional, Any # For type hinting parent

from PySide6.QtWidgets import QTextEdit, QWidget, QHBoxLayout, QApplication
from PySide6.QtCore import Qt, QTimer, QEvent, QMimeData, QPoint
from PySide6.QtGui import (
    QFont, QKeyEvent, QTextCursor, QPalette, QColor, QPixmap, QImage,
    QTextCharFormat
)

# Forward declaration for type hinting to avoid circular import
# This is a common pattern when dealing with tightly coupled classes
# that will be in different modules.
# FeedbackUI 类型的前向声明，以避免循环导入。
# 这是处理将位于不同模块中的紧密耦合类时的常见模式。
FeedbackUI = "FeedbackUI"


class FeedbackTextEdit(QTextEdit):
    """
    Custom QTextEdit for feedback input, handling text, image pasting/dropping,
    and file reference management.

    用于反馈输入的自定义 QTextEdit，处理文本、图像粘贴/拖放以及文件引用管理。
    """
    # Define signals if you want to decouple further, e.g.:
    # image_pasted = Signal(QPixmap)
    # file_dropped = Signal(str, str) # file_path, file_name
    # submit_triggered = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        document = self.document()
        document.setDefaultStyleSheet("") # Ensure no default rich text styles
        self.setAutoFormatting(QTextEdit.AutoFormattingFlag.AutoNone)
        self.setPlainText("") # Start with empty plain text
        
        font = QFont("Segoe UI", 13)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        # font.setHintingPreference(QFont.HintingPreference.PreferFullHinting) # Not in PySide6 QFont
        font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 101.5)
        font.setWordSpacing(1.0)
        self.setFont(font)
        
        self._file_reference_cache = {
            'text': '',
            'references': [],  # List of display_name strings
            'positions': {}  # Dict of display_name: (start_pos, end_pos)
        }
        self._cache_valid = False
        self._last_cursor_pos = 0
        
        self.setCursorWidth(2)
        self.setAcceptDrops(True)
        self.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Timer to ensure cursor visibility after certain key events
        # 用于在某些按键事件后确保光标可见性的计时器
        self._key_repeat_timer = QTimer(self)
        self._key_repeat_timer.setSingleShot(True)
        self._key_repeat_timer.setInterval(10) # ms
        self._key_repeat_timer.timeout.connect(self._ensure_cursor_visible_slot) # Renamed slot
        
        self._is_key_repeating = False

        # Container for image previews shown at the bottom of the text edit
        # 用于在文本编辑器底部显示图像预览的容器
        self.images_container = QWidget(self)
        self.images_layout = QHBoxLayout(self.images_container)
        self.images_layout.setContentsMargins(10, 10, 10, 10)
        self.images_layout.setSpacing(10)
        self.images_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.images_container.setVisible(False)
        
        # Set placeholder text color using QPalette
        # 使用 QPalette 设置占位符文本颜色
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#777777"))
        self.setPalette(palette)
            
    def resizeEvent(self, event: QEvent): # QResizeEvent
        super().resizeEvent(event)
        container_height = 60 # Height of the images container
        # Position images_container at the bottom
        self.images_container.setGeometry(0, self.height() - container_height, self.width(), container_height)
        
        if self.images_container.isVisible():
            self.setViewportMargins(0, 0, 0, container_height)
        else:
            self.setViewportMargins(0, 0, 0, 0)
            
    def showEvent(self, event: QEvent): # QShowEvent
        super().showEvent(event)
        # Ensure correct geometry for images_container on show
        container_height = 60
        self.images_container.setGeometry(0, self.height() - container_height, self.width(), container_height)
        if self.images_container.isVisible():
            self.setViewportMargins(0, 0, 0, container_height)
        
        QTimer.singleShot(10, self.ensureCursorVisible) # Ensure cursor is visible on show

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        self._is_key_repeating = event.isAutoRepeat()
            
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Home, Qt.Key.Key_End):
            super().keyPressEvent(event)
            self._last_cursor_pos = self.textCursor().position()
            self._schedule_ensure_cursor_visible()
            return
            
        cursor_pos = self.textCursor().position()
        self._last_cursor_pos = cursor_pos
            
        parent_feedback_ui = self._find_feedback_ui_parent()

        if key == Qt.Key.Key_Backspace:
            if parent_feedback_ui and parent_feedback_ui.dropped_file_references and self._is_cursor_near_file_reference(cursor_pos, is_backspace=True):
                if self._handle_file_reference_deletion_action(is_backspace=True):
                    self._invalidate_reference_cache()
                    self._schedule_ensure_cursor_visible()
                    return
            # Standard backspace behavior
            cursor = self.textCursor()
            if not cursor.hasSelection():
                cursor.deletePreviousChar()
            else:
                cursor.removeSelectedText()
            self._invalidate_reference_cache()
            self._schedule_ensure_cursor_visible()
            return
            
        elif key == Qt.Key.Key_Delete:
            if parent_feedback_ui and parent_feedback_ui.dropped_file_references and self._is_cursor_near_file_reference(cursor_pos, is_backspace=False):
                if self._handle_file_reference_deletion_action(is_backspace=False):
                    self._invalidate_reference_cache()
                    self._schedule_ensure_cursor_visible()
                    return
            # Standard delete behavior
            cursor = self.textCursor()
            if not cursor.hasSelection():
                cursor.deleteChar()
            else:
                cursor.removeSelectedText()
            self._invalidate_reference_cache()
            self._schedule_ensure_cursor_visible()
            return
            
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier: # Shift + Enter for newline
                super().keyPressEvent(event)
                self._invalidate_reference_cache()
                self._schedule_ensure_cursor_visible()
            elif event.modifiers() == Qt.KeyboardModifier.ControlModifier or event.modifiers() == Qt.KeyboardModifier.NoModifier:
                # Ctrl + Enter or Enter to submit
                if parent_feedback_ui and hasattr(parent_feedback_ui, '_submit_feedback'):
                    parent_feedback_ui._submit_feedback() # Consider emitting a signal instead
            else: # Other modifiers + Enter (e.g., Alt+Enter), treat as newline
                super().keyPressEvent(event)
                self._invalidate_reference_cache()
                self._schedule_ensure_cursor_visible()
            return # Event handled

        elif key == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier: # Ctrl + V for paste
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                if parent_feedback_ui and hasattr(parent_feedback_ui, 'handle_paste_image'):
                    if parent_feedback_ui.handle_paste_image(): # Parent handles image paste
                        return # Paste handled by parent
            
            super().keyPressEvent(event) # Default paste for text etc.
            self._invalidate_reference_cache()
            self._schedule_ensure_cursor_visible()
            return # Event handled

        else: # Default key press handling
            super().keyPressEvent(event)
            self._invalidate_reference_cache()
            self._schedule_ensure_cursor_visible()
            
    def keyReleaseEvent(self, event: QKeyEvent):
        self._is_key_repeating = False
        super().keyReleaseEvent(event)
        
    def _schedule_ensure_cursor_visible(self):
        """Schedules a call to ensure the cursor is visible."""
        self._key_repeat_timer.start()
        
    def _ensure_cursor_visible_slot(self):
        """Slot connected to the timer to make the cursor visible."""
        self.ensureCursorVisible()
        self.viewport().update() # Force viewport update
        
    def mousePressEvent(self, event: QEvent): # QMouseEvent
        self._key_repeat_timer.stop() # Stop timer on mouse press
        self._is_key_repeating = False
        super().mousePressEvent(event)
        self._last_cursor_pos = self.textCursor().position()
        
    def mouseReleaseEvent(self, event: QEvent): # QMouseEvent
        super().mouseReleaseEvent(event)
        self.ensureCursorVisible() # Ensure visibility after mouse release
        
    def _find_feedback_ui_parent(self) -> Optional[Any]: # Should be Optional[FeedbackUI]
        """
        Finds the FeedbackUI instance in the parent hierarchy.
        This creates a tight coupling. Consider using signals/slots for decoupling.

        在父级层次结构中查找 FeedbackUI 实例。
        这会产生紧密耦合。考虑使用信号/槽进行解耦。
        """
        parent = self.parent()
        while parent:
            # Check class name due to forward declaration of FeedbackUI
            if parent.__class__.__name__ == "FeedbackUI":
                return parent
            parent = parent.parent()
        return None
        
    def _invalidate_reference_cache(self):
        """Marks the file reference cache as invalid."""
        self._cache_valid = False
        
    def _update_file_reference_cache_if_needed(self):
        """Updates the file reference cache from the current text content if it's invalid."""
        if self._cache_valid:
            return
            
        parent_feedback_ui = self._find_feedback_ui_parent()
        if not parent_feedback_ui or not parent_feedback_ui.dropped_file_references:
            self._file_reference_cache['text'] = self.toPlainText()
            self._file_reference_cache['references'] = []
            self._file_reference_cache['positions'] = {}
            self._cache_valid = True
            return
            
        current_text = self.toPlainText()
        # Only update if text has actually changed
        if current_text == self._file_reference_cache['text']:
            self._cache_valid = True
            return
            
        self._file_reference_cache['text'] = current_text
        self._file_reference_cache['references'] = []
        self._file_reference_cache['positions'] = {}
        
        # Rebuild cache based on current text and parent's references
        for display_name in parent_feedback_ui.dropped_file_references.keys():
            start_pos = 0
            while True:
                pos = current_text.find(display_name, start_pos)
                if pos == -1:
                    break
                # Store display name and its start/end positions
                self._file_reference_cache['references'].append(display_name)
                self._file_reference_cache['positions'][display_name] = (pos, pos + len(display_name))
                start_pos = pos + len(display_name)
        self._cache_valid = True
        
    def _is_cursor_near_file_reference(self, cursor_pos: int, is_backspace: bool = True) -> bool:
        """Checks if the cursor is at the start/end of a known file reference."""
        self._update_file_reference_cache_if_needed()
        for _display_name, (start, end) in self._file_reference_cache['positions'].items():
            if is_backspace and cursor_pos == end: # Cursor at the end of reference for backspace
                return True
            elif not is_backspace and cursor_pos == start: # Cursor at the start of reference for delete
                return True
        return False

    def _handle_file_reference_deletion_action(self, is_backspace: bool = True) -> bool:
        """Handles the deletion of a file reference when Backspace or Delete is pressed."""
        parent_feedback_ui = self._find_feedback_ui_parent()
        if not parent_feedback_ui or not parent_feedback_ui.dropped_file_references:
            return False
            
        self._update_file_reference_cache_if_needed()
        cursor = self.textCursor()
        if cursor.hasSelection(): # Don't interfere with selection deletion
            return False
            
        cursor_pos = cursor.position()
        
        # Iterate over a copy of items if modifying the underlying dict
        for display_name, (start, end) in list(self._file_reference_cache['positions'].items()):
            should_delete = False
            if is_backspace and cursor_pos == end:
                should_delete = True
            elif not is_backspace and cursor_pos == start:
                should_delete = True
            
            if should_delete:
                # Select the display_name text and remove it
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                
                # Remove from parent's tracking and internal cache
                if display_name in parent_feedback_ui.dropped_file_references:
                    del parent_feedback_ui.dropped_file_references[display_name]
                if display_name in self._file_reference_cache['positions']:
                    del self._file_reference_cache['positions'][display_name]
                if display_name in self._file_reference_cache['references']:
                    self._file_reference_cache['references'].remove(display_name)
                
                self._invalidate_reference_cache() # Mark cache as invalid for next update
                return True # Deletion handled
        return False

    def insertFromMimeData(self, source: QMimeData):
        """Handles insertion of content from MIME data (e.g., paste)."""
        parent_feedback_ui = self._find_feedback_ui_parent()
        handled = False

        if source.hasImage() and parent_feedback_ui:
            image = QImage(source.imageData()) # source.imageData() returns QVariant -> QImage
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull() and hasattr(parent_feedback_ui, 'add_image_preview'):
                    parent_feedback_ui.add_image_preview(pixmap)
                    handled = True
        
        # Always try to paste text if available, even if image was handled (or not)
        if source.hasText():
            text_to_insert = source.text().strip() # Strip to avoid pasting only newlines
            if text_to_insert: # Only insert if there's actual text
                 self.insertPlainText(text_to_insert)
            # Mark as handled if text was present, even if empty after strip
            # This prevents super().insertFromMimeData if only whitespace was pasted
            handled = True 
        
        if not handled: # If neither image nor text was handled by custom logic
            super().insertFromMimeData(source)
        
        self._invalidate_reference_cache()

    def show_images_container(self, visible: bool):
        """Shows or hides the image preview container at the bottom."""
        self.images_container.setVisible(visible)
        container_height = 60 if visible else 0
        self.setViewportMargins(0, 0, 0, container_height)
        self.viewport().update()
        
    def dragEnterEvent(self, event: QEvent): # QDragEnterEvent
        mime_data = event.mimeData()
        if mime_data.hasUrls() or mime_data.hasText() or mime_data.hasImage(): # Simplified
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event: QEvent): # QDragMoveEvent
        # Same conditions as dragEnterEvent generally
        if event.mimeData().hasUrls() or event.mimeData().hasText() or event.mimeData.hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QEvent): # QDropEvent
        mime_data = event.mimeData()
        parent_feedback_ui = self._find_feedback_ui_parent()
            
        if not parent_feedback_ui:
            event.ignore()
            return
            
        # Ensure dropped_file_references exists on parent
        if not hasattr(parent_feedback_ui, 'dropped_file_references'):
            parent_feedback_ui.dropped_file_references = {} # Initialize if missing
            
        dropped_content = False
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if not urls and mime_data.hasText(): # Some OS might wrap file paths in text for drag
                dropped_content = self._process_text_drop_as_file(event, mime_data, parent_feedback_ui)
            else:
                for url in urls:
                    if url.isLocalFile():
                        file_path = url.toLocalFile()
                        file_name = os.path.basename(file_path)
                        
                        # Try to add as image first
                        if os.path.isfile(file_path) and \
                           os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                            try:
                                pixmap = QPixmap(file_path)
                                if not pixmap.isNull() and pixmap.width() > 0:
                                    if hasattr(parent_feedback_ui, 'add_image_preview'):
                                        parent_feedback_ui.add_image_preview(pixmap)
                                    dropped_content = True
                                    continue # Next URL if this was an image
                            except Exception as e:
                                print(f"ERROR: FeedbackTextEdit dropEvent - Loading image failed: {file_path}, {e}", file=sys.stderr)
                        
                        # If not an image or image loading failed, add as file reference
                        if not dropped_content or not os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                             self._insert_file_reference_text(parent_feedback_ui, file_path, file_name)
                             dropped_content = True
                if dropped_content:
                    event.acceptProposedAction()
        
        elif mime_data.hasImage() and not dropped_content: # If not already handled by URL processing
             image = QImage(mime_data.imageData())
             if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                if not pixmap.isNull() and hasattr(parent_feedback_ui, 'add_image_preview'):
                    parent_feedback_ui.add_image_preview(pixmap)
                    dropped_content = True
                    event.acceptProposedAction()

        elif mime_data.hasText() and not dropped_content:
            if self._process_text_drop_as_file(event, mime_data, parent_feedback_ui):
                dropped_content = True
            else: # Fallback to inserting plain text if not a file path
                self.insertPlainText(mime_data.text())
                dropped_content = True
                event.acceptProposedAction()
        
        if not dropped_content:
            super().dropEvent(event) # Default handling if no custom logic applied
            return
            
        # If any content was dropped and action accepted
        if event.isAccepted():
            self._invalidate_reference_cache()
            QTimer.singleShot(100, lambda: self._focus_after_content_drop(event.position().toPoint()))


    def _process_text_drop_as_file(self, event: QEvent, mime_data: QMimeData, parent_feedback_ui: Any) -> bool:
        """
        Attempts to interpret dropped text as one or more file paths.
        Returns True if text was successfully processed as file(s), False otherwise.

        尝试将拖放的文本解释为一个或多个文件路径。
        如果文本成功处理为文件，则返回 True，否则返回 False。
        """
        text = mime_data.text()
        potential_paths = []

        # Check for typical file URI scheme
        if text.startswith("file:///"):
            try:
                from urllib.parse import unquote
                # Remove scheme and decode, handle OS-specific path adjustments
                path_str = unquote(text.replace("file:///", ""))
                if sys.platform.startswith("win") and len(path_str) > 1 and path_str[1] != ':': # e.g. /D:/path
                    path_str = path_str[1:] if path_str.startswith('/') else path_str
                potential_paths.append(path_str)
            except Exception as e:
                print(f"ERROR: FeedbackTextEdit _process_text_drop - Parsing file URI failed: {e}", file=sys.stderr)
        else:
            # Check for Windows-style absolute paths (e.g., C:\...)
            # Or treat lines as potential paths if they exist
            lines = text.splitlines()
            for line in lines:
                line = line.strip()
                if not line: continue
                # Simple check for Windows path or if path exists (more generic)
                if (re.match(r'^[a-zA-Z]:[/\\].+', line) and os.path.exists(line)) or \
                   (not re.match(r'^[a-zA-Z]:[/\\].+', line) and os.path.exists(line)): # Unix-like or relative paths that exist
                    potential_paths.append(line.replace('\\', os.sep)) # Normalize separators
        
        processed_any_file = False
        for path_str in potential_paths:
            if os.path.exists(path_str):
                file_name = os.path.basename(path_str)
                # Try to add as image first
                is_image_file = os.path.isfile(path_str) and \
                                os.path.splitext(path_str)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
                
                image_added = False
                if is_image_file:
                    try:
                        pixmap = QPixmap(path_str)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            if hasattr(parent_feedback_ui, 'add_image_preview'):
                                parent_feedback_ui.add_image_preview(pixmap)
                            image_added = True
                            processed_any_file = True
                    except Exception as e:
                         print(f"ERROR: FeedbackTextEdit _process_text_drop - Loading image from text path failed: {path_str}, {e}", file=sys.stderr)
                
                # If not an image or image loading failed, add as file reference
                if not image_added:
                    self._insert_file_reference_text(parent_feedback_ui, path_str, file_name)
                    processed_any_file = True
        
        if processed_any_file:
            event.acceptProposedAction()
            return True
        return False
    
    def _insert_file_reference_text(self, parent_feedback_ui: Any, file_path: str, file_name: str):
        """Inserts a styled file reference placeholder into the text edit."""
        display_name = f"@{file_name}"
        counter = 1
        original_display_name = display_name
        # Ensure unique display name if multiple files with same name are dropped
        while display_name in parent_feedback_ui.dropped_file_references:
            display_name = f"{original_display_name}({counter})" # Note: Original was f"... ({counter})"
            counter += 1
        
        parent_feedback_ui.dropped_file_references[display_name] = file_path
        
        try:
            cursor = self.textCursor()
            current_format = cursor.charFormat() # Save current format to restore later
            
            # Style for the file reference
            ref_format = QTextCharFormat()
            ref_format.setForeground(QColor("#1a73e8")) # Blue color
            ref_format.setFontWeight(QFont.Weight.Bold)
            # ref_format.setAnchor(True) # Could make it an anchor if handling clicks
            # ref_format.setAnchorHref(f"file:///{file_path}")

            cursor.clearSelection() # Ensure no text is replaced
            cursor.insertText(" ", current_format) # Add a space before if cursor is not at start or after newline
            cursor.insertText(display_name, ref_format)
            cursor.insertText(" ", current_format) # Add a space after
            
            self.setTextCursor(cursor) # Move cursor to end of inserted text
            self.update() # Ensure UI update
            self._invalidate_reference_cache()
            # QTimer.singleShot(100, lambda: self._ensure_focus_after_insert(cursor)) # Not strictly needed if _focus_after_content_drop is called
        except Exception as e:
            print(f"ERROR: FeedbackTextEdit _insert_file_reference - Text insertion failed: {e}", file=sys.stderr)
            
    def _ensure_focus_after_insert(self, cursor: QTextCursor): # Keep for specific focus needs
        """Ensures the text edit has focus and the cursor is visible after insertion."""
        window = self.window()
        if window:
            window.activateWindow()
            window.raise_()
            
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.FocusPolicy.MouseFocusReason) # Or OtherFocusReason
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _focus_after_content_drop(self, drop_pos: QPoint):
        """Sets focus and attempts to position cursor near the drop position."""
        window = self.window()
        if window:
            window.activateWindow()
            window.raise_()
        
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.FocusPolicy.MouseFocusReason)
        
        try:
            # Attempt to set cursor position based on where the drop occurred
            # QDropEvent.position() returns QPointF, cursorForPosition expects QPoint
            cursor_at_drop = self.cursorForPosition(drop_pos)
            self.setTextCursor(cursor_at_drop)
        except Exception: # Fallback if cursorForPosition fails
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
        
        self.ensureCursorVisible()

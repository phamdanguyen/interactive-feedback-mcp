# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by pawa (https://github.com/pawaovo) with ideas from https://github.com/noopstudios/interactive-feedback-mcp
import os
import sys
import json
import argparse
import base64
from typing import Optional, TypedDict, List, Dict, Any, Union, Tuple
# from io import BytesIO # BytesIO 似乎未在优化后的代码中使用
# import time # time 模块似乎未在优化后的代码中使用
# import traceback # traceback 模块似乎未在优化后的代码中使用
# from datetime import datetime # datetime 模块似乎未在优化后的代码中使用
# import functools # functools 模块似乎未在优化后的代码中使用
import re
import webbrowser

# pyperclip 模块的导入保留，以防万一有隐藏的依赖或未来使用
try:
    import pyperclip
except ImportError:
    print("警告: 无法导入pyperclip模块，部分剪贴板功能可能无法正常工作", file=sys.stderr)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame, QSizePolicy, QScrollArea, QToolTip, QDialog, QListWidget,
    QMessageBox, QListWidgetItem, QComboBox, QGridLayout, QSpacerItem, QLayout, # QComboBox, QGridLayout, QSpacerItem, QLayout 似乎未在优化后的代码中使用
    QDialogButtonBox, QFileDialog
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QTimer, QSettings, QEvent, QSize, 
    QByteArray, QBuffer, QIODevice, QMimeData, QPoint, QRect, QRectF # QStringListModel, QPoint, QRect, QRectF 似乎未在优化后的代码中使用
)
from PySide6.QtGui import (
    QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QPixmap, QCursor, 
    QPainter, QClipboard, QImage, QFont, QKeySequence, QShortcut, QDrag, QPen, QAction, QFontMetrics, QTextCharFormat # QKeySequence, QShortcut, QDrag, QPen, QAction 似乎未在优化后的代码中使用
)

# --- 常量定义 ---
APP_NAME = "InteractiveFeedbackMCP"
SETTINGS_GROUP_MAIN = "MainWindow_General"
SETTINGS_GROUP_CANNED_RESPONSES = "CannedResponses"
SETTINGS_KEY_GEOMETRY = "geometry"
SETTINGS_KEY_WINDOW_STATE = "windowState"
SETTINGS_KEY_WINDOW_PINNED = "windowPinned"
SETTINGS_KEY_PHRASES = "phrases"
SETTINGS_KEY_SHOW_SHORTCUT_ICONS = "showShortcutIcons"
SETTINGS_KEY_NUMBER_ICONS_VISIBLE = "numberIconsVisible"

MAX_IMAGE_WIDTH = 512
MAX_IMAGE_HEIGHT = 512
MAX_IMAGE_BYTES = 1048576

# --- 类型定义 ---
class ContentItem(TypedDict):
    type: str
    text: Optional[str]
    data: Optional[str]
    mimeType: Optional[str]

class FeedbackResult(TypedDict):
    content: List[ContentItem]

# --- 自定义控件 ---
class ClickableLabel(QLabel):
    clicked = Signal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # 样式已移至全局 QSS 或通过 get_dark_mode_palette 和 app.setStyleSheet 应用
        # self.setStyleSheet("""...""") # 示例移除
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self._cursor_filter = CursorOverrideFilter(self)
        self.installEventFilter(self._cursor_filter)
    
    def mouseMoveEvent(self, event):
        QApplication.restoreOverrideCursor()
        QApplication.setOverrideCursor(Qt.PointingHandCursor)
        super().mouseMoveEvent(event)
    
    def enterEvent(self, event):
        QApplication.setOverrideCursor(Qt.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class CursorOverrideFilter(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Enter, QEvent.HoverEnter, QEvent.HoverMove, 
                           QEvent.MouseMove, QEvent.MouseButtonPress, 
                           QEvent.MouseButtonRelease):
            obj.setCursor(Qt.ArrowCursor)
            return False
        return False

class FeedbackTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(False)
        document = self.document()
        document.setDefaultStyleSheet("")
        self.setAutoFormatting(QTextEdit.AutoNone)
        self.setPlainText("")
        
        font = QFont("Segoe UI", 13)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setHintingPreference(QFont.PreferFullHinting)
        # font.setWeight(QFont.Normal) # QFont.Normal 是默认值
        font.setLetterSpacing(QFont.PercentageSpacing, 101.5)
        font.setWordSpacing(1.0)
        self.setFont(font)
        
        self._file_reference_cache = {
            'text': '',
            'references': [],
            'positions': {}
        }
        self._cache_valid = False
        self._last_cursor_pos = 0
        
        self.setCursorWidth(2)
        self.setAcceptDrops(True)
        self.viewport().setCursor(Qt.IBeamCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        
        self._key_repeat_timer = QTimer(self)
        self._key_repeat_timer.setSingleShot(True)
        self._key_repeat_timer.setInterval(10)
        self._key_repeat_timer.timeout.connect(self._ensure_cursor_visible)
        
        self._is_key_repeating = False
        # self._current_repeat_key = None # _current_repeat_key 似乎未在逻辑中使用

        self.images_container = QWidget(self)
        self.images_layout = QHBoxLayout(self.images_container)
        self.images_layout.setContentsMargins(10, 10, 10, 10)
        self.images_layout.setSpacing(10)
        self.images_layout.setAlignment(Qt.AlignLeft)
        
        # 样式已移至全局 QSS
        # self.images_container.setStyleSheet("""...""")
        # self.setStyleSheet("""...""")
        
        self.images_container.setVisible(False)
        
        palette = self.palette()
        palette.setColor(QPalette.PlaceholderText, QColor("#777777"))
        self.setPalette(palette)
        
        self.setAcceptDrops(True)
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        container_height = 60
        self.images_container.setGeometry(0, self.height() - container_height, self.width(), container_height)
        
        if self.images_container.isVisible():
            self.setViewportMargins(0, 0, 0, container_height)
        else:
            self.setViewportMargins(0, 0, 0, 0)
            
    def showEvent(self, event):
        super().showEvent(event)
        container_height = 60
        self.images_container.setGeometry(0, self.height() - container_height, self.width(), container_height)
        
        if self.images_container.isVisible():
            self.setViewportMargins(0, 0, 0, container_height)
        
        # 优化初始光标显示
        QTimer.singleShot(10, self.ensureCursorVisible)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        
        if event.isAutoRepeat():
            self._is_key_repeating = True
            # self._current_repeat_key = key # 未使用
        else:
            self._is_key_repeating = False
            # self._current_repeat_key = None # 未使用
            
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End):
            super().keyPressEvent(event)
            self._last_cursor_pos = self.textCursor().position()
            self._schedule_ensure_cursor_visible()
            return
            
        cursor_pos = self.textCursor().position()
        self._last_cursor_pos = cursor_pos
            
        parent = self._find_parent() # 提前获取，避免多次调用

        if key == Qt.Key_Backspace:
            if parent and parent.dropped_file_references and self._near_file_reference(cursor_pos, is_backspace=True):
                if self._handle_file_reference_deletion(is_backspace=True):
                    self._invalidate_cache()
                    self._schedule_ensure_cursor_visible()
                    return
            
            cursor = self.textCursor()
            if not cursor.hasSelection():
                cursor.deletePreviousChar()
            else:
                cursor.removeSelectedText()
            
            self._invalidate_cache()
            self._schedule_ensure_cursor_visible()
            return
            
        elif key == Qt.Key_Delete:
            if parent and parent.dropped_file_references and self._near_file_reference(cursor_pos, is_backspace=False):
                if self._handle_file_reference_deletion(is_backspace=False):
                    self._invalidate_cache()
                    self._schedule_ensure_cursor_visible()
                    return
            
            cursor = self.textCursor()
            if not cursor.hasSelection():
                cursor.deleteChar()
            else:
                cursor.removeSelectedText()
            
            self._invalidate_cache()
            self._schedule_ensure_cursor_visible()
            return
            
        elif key == Qt.Key_Return:
            if event.modifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event)
                self._invalidate_cache()
                self._schedule_ensure_cursor_visible()
            elif event.modifiers() == Qt.ControlModifier or event.modifiers() == Qt.NoModifier:
                if parent:
                    parent._submit_feedback()
            else:
                super().keyPressEvent(event)
                self._invalidate_cache()
                self._schedule_ensure_cursor_visible()
        elif key == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                if parent:
                    if parent.handle_paste_image():
                        return
            
            super().keyPressEvent(event)
            self._invalidate_cache()
            self._schedule_ensure_cursor_visible()
        else:
            super().keyPressEvent(event)
            self._invalidate_cache()
            self._schedule_ensure_cursor_visible()
            
    def keyReleaseEvent(self, event):
        self._is_key_repeating = False
        # self._current_repeat_key = None # 未使用
        super().keyReleaseEvent(event)
        
    def _schedule_ensure_cursor_visible(self):
        self._key_repeat_timer.start()
        
    def _ensure_cursor_visible(self):
        # cursor = self.textCursor() # 未使用
        self.ensureCursorVisible()
        self.viewport().update()
        
    def mousePressEvent(self, event):
        self._key_repeat_timer.stop()
        self._is_key_repeating = False
        # self._current_repeat_key = None # 未使用
        super().mousePressEvent(event)
        self._last_cursor_pos = self.textCursor().position()
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.ensureCursorVisible()
        
    def _find_parent(self):
        parent = self.parent()
        while parent and not isinstance(parent, FeedbackUI):
            parent = parent.parent()
        return parent
        
    def _invalidate_cache(self):
        self._cache_valid = False
        
    def _update_reference_cache(self):
        if self._cache_valid:
            return
            
        parent = self._find_parent()
        if not parent or not parent.dropped_file_references:
            self._cache_valid = True
            return
            
        text = self.toPlainText()
        if text == self._file_reference_cache['text']:
            self._cache_valid = True
            return
            
        self._file_reference_cache['text'] = text
        self._file_reference_cache['references'] = []
        self._file_reference_cache['positions'] = {}
        
        for display_name in parent.dropped_file_references:
            start_pos = 0
            while True:
                pos = text.find(display_name, start_pos)
                if pos == -1:
                    break
                self._file_reference_cache['references'].append(display_name)
                self._file_reference_cache['positions'][display_name] = (pos, pos + len(display_name))
                start_pos = pos + len(display_name)
        self._cache_valid = True
        
    def _near_file_reference(self, cursor_pos, is_backspace=True):
        self._update_reference_cache()
        for _display_name, (start, end) in self._file_reference_cache['positions'].items(): # _display_name 未使用
            if is_backspace and cursor_pos == end:
                return True
            elif not is_backspace and cursor_pos == start:
                return True
        return False

    def _handle_file_reference_deletion(self, is_backspace=True):
        parent_window = self._find_parent()
        if not parent_window or not parent_window.dropped_file_references:
            return False
            
        self._update_reference_cache()
        cursor = self.textCursor()
        if cursor.hasSelection():
            return False
            
        cursor_pos = cursor.position()
        
        if is_backspace:
            for display_name, (start, end) in self._file_reference_cache['positions'].items():
                if cursor_pos == end:
                    cursor.setPosition(start)
                    cursor.setPosition(end, QTextCursor.KeepAnchor)
                    cursor.removeSelectedText()
                    if display_name in parent_window.dropped_file_references:
                        del parent_window.dropped_file_references[display_name]
                    self._invalidate_cache()
                    return True
        else:
            for display_name, (start, end) in self._file_reference_cache['positions'].items():
                if cursor_pos == start:
                    cursor.setPosition(end, QTextCursor.KeepAnchor) # 应该是 setPosition(start), setPosition(end, KeepAnchor)
                    cursor.removeSelectedText()
                    if display_name in parent_window.dropped_file_references:
                        del parent_window.dropped_file_references[display_name]
                    self._invalidate_cache()
                    return True
        return False

    def insertFromMimeData(self, source):
        handled = False
        if source.hasImage():
            parent = self._find_parent()
            if parent:
                image = source.imageData()
                if image and not image.isNull():
                    pixmap = QPixmap.fromImage(QImage(image))
                    if not pixmap.isNull():
                        parent.add_image_preview(pixmap)
                        handled = True
        
        if source.hasText():
            text = source.text().strip()
            if text:
                self.insertPlainText(text)
                handled = True
        
        if not handled:
            super().insertFromMimeData(source)

    def show_images_container(self, visible):
        self.images_container.setVisible(visible)
        container_height = 60 if visible else 0
        self.setViewportMargins(0, 0, 0, container_height)
        self.viewport().update()
        
    def dragEnterEvent(self, event):
        mime_data = event.mimeData()
        if mime_data.hasUrls() or mime_data.hasText() or mime_data.hasHtml() or mime_data.hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasText() or event.mimeData.hasHtml() or event.mimeData.hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        mime_data = event.mimeData()
        parent_window = self._find_parent()
            
        if not parent_window:
            event.ignore()
            return
            
        if not hasattr(parent_window, 'dropped_file_references'):
            parent_window.dropped_file_references = {}
            
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if len(urls) == 0 and mime_data.hasText():
                return self._process_text_drop(event, mime_data, parent_window)
            
            for url in urls:
                # url_str = url.toString() # 未使用
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_name = os.path.basename(file_path)
                    
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        try:
                            pixmap = QPixmap(file_path)
                            if not pixmap.isNull() and pixmap.width() > 0:
                                parent_window.add_image_preview(pixmap)
                                continue
                        except Exception as e:
                            print(f"ERROR: dropEvent - 加载图片出错: {e}", file=sys.stderr)
                    
                    self._insert_file_reference(parent_window, file_path, file_name)
        
        elif mime_data.hasText():
            return self._process_text_drop(event, mime_data, parent_window)
        else:
            super().dropEvent(event)
            return
            
        event.acceptProposedAction()
        QTimer.singleShot(100, lambda: self._focus_after_drop(event.pos()))
    
    def _process_text_drop(self, event, mime_data, parent_window):
        text = mime_data.text()
        
        if text.startswith("file:///"):
            try:
                from urllib.parse import unquote
                clean_path = unquote(text.replace("file:///", ""))
                if sys.platform.startswith("win"):
                    if not clean_path.startswith("C:") and len(clean_path) > 1: # 假设驱动器号后跟冒号
                        # 修正Windows路径，例如 "D/path" -> "D:/path"
                        if clean_path[1] != ':':
                           clean_path = clean_path[0] + ":" + clean_path[1:]


                if os.path.exists(clean_path):
                    file_name = os.path.basename(clean_path)
                    if os.path.isfile(clean_path) and os.path.splitext(clean_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        try:
                            pixmap = QPixmap(clean_path)
                            if not pixmap.isNull() and pixmap.width() > 0:
                                parent_window.add_image_preview(pixmap)
                                event.acceptProposedAction()
                                QTimer.singleShot(100, lambda: parent_window._set_text_focus())
                                return True
                        except Exception as e:
                            print(f"ERROR: _process_text_drop - 加载图片失败: {e}", file=sys.stderr)
                    
                    self._insert_file_reference(parent_window, clean_path, file_name)
                    event.acceptProposedAction()
                    return True
            except Exception as e:
                print(f"ERROR: _process_text_drop - 解析文件URL失败: {e}", file=sys.stderr)
        
        windows_path_pattern = re.compile(r'^[a-zA-Z]:[/\\].+')
        if windows_path_pattern.match(text):
            path = text.replace('\\', os.sep) # 使用 os.sep 保证跨平台
            if os.path.exists(path):
                file_name = os.path.basename(path)
                if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                    try:
                        pixmap = QPixmap(path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            parent_window.add_image_preview(pixmap)
                            event.acceptProposedAction()
                            QTimer.singleShot(100, lambda: parent_window._set_text_focus())
                            return True
                    except Exception as e:
                        print(f"ERROR: _process_text_drop - 加载Windows路径图片失败: {e}", file=sys.stderr)
                
                self._insert_file_reference(parent_window, path, file_name)
                event.acceptProposedAction()
                return True
        
        possible_paths = text.split('\n')
        for path_str in possible_paths: # 重命名变量避免与 os.path 冲突
            path_str = path_str.strip()
            if path_str and os.path.exists(path_str):
                file_name = os.path.basename(path_str)
                if os.path.isfile(path_str) and os.path.splitext(path_str)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                    try:
                        pixmap = QPixmap(path_str)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            parent_window.add_image_preview(pixmap)
                            event.acceptProposedAction()
                            QTimer.singleShot(100, lambda: parent_window._set_text_focus())
                            return True
                    except Exception as e:
                        print(f"ERROR: _process_text_drop - 从文本路径加载图片失败: {e}", file=sys.stderr)
                
                self._insert_file_reference(parent_window, path_str, file_name)
                event.acceptProposedAction()
                return True
        
        if text.startswith("http://") or text.startswith("https://"):
            self.insertPlainText(text)
            event.acceptProposedAction()
            return True
                
        self.insertPlainText(text)
        event.acceptProposedAction()
        QTimer.singleShot(100, lambda: self._focus_after_drop(event.pos()))
        return True
    
    def _insert_file_reference(self, parent_window, file_path, file_name):
        display_name = f"@{file_name}"
        counter = 1
        original_display_name = display_name
        while display_name in parent_window.dropped_file_references:
            display_name = f"{original_display_name} ({counter})"
            counter += 1
        
        parent_window.dropped_file_references[display_name] = file_path
        
        try:
            cursor = self.textCursor()
            current_format = cursor.charFormat()
            
            blue_format = QTextCharFormat()
            blue_format.setForeground(QColor("#1a73e8"))
            blue_format.setFontWeight(QFont.Bold)
            # blue_format.setFontUnderline(False) # 默认就是 False
            
            cursor.clearSelection()
            cursor.setCharFormat(blue_format)
            cursor.insertText(display_name)
            cursor.setCharFormat(current_format)
            cursor.insertText(" ")
            
            self.update()
            QTimer.singleShot(100, lambda: self._ensure_focus(cursor))
        except Exception as e:
            print(f"ERROR: _insert_file_reference - 插入文本出错: {e}", file=sys.stderr)
            
    def _ensure_focus(self, cursor):
        window = self.window()
        if window:
            window.activateWindow()
            window.raise_()
            
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.MouseFocusReason)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _focus_after_drop(self, pos):
        window = self.window()
        if window:
            window.activateWindow()
            window.raise_()
        
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.MouseFocusReason)
        
        try:
            # PySide6 中 QPointF 直接传递给 QCursorForPosition
            cursor_pos_obj = self.cursorForPosition(pos if isinstance(pos, QPoint) else QPoint(int(pos.x()), int(pos.y())))
            self.setTextCursor(cursor_pos_obj)
        except Exception:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        
        self.ensureCursorVisible()

class ImagePreviewWidget(QWidget):
    image_deleted = Signal(int)
    
    def __init__(self, image_pixmap, image_id, parent=None):
        super().__init__(parent)
        self.image_pixmap = image_pixmap
        self.image_id = image_id
        self.original_pixmap = image_pixmap
        self.is_hovering = False
        # self.hover_color = False # hover_color 似乎未在逻辑中使用

        self.setFixedSize(48, 48)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        thumbnail = image_pixmap.scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.original_thumbnail = thumbnail
        self.red_thumbnail = self._create_red_thumbnail(thumbnail)
        self.thumbnail_label.setPixmap(thumbnail)
        layout.addWidget(self.thumbnail_label)
        
        # 样式已移至全局 QSS
        # self.setStyleSheet("""...""")
        
        self.setToolTip("悬停查看大图，点击图标删除图片")
        self.setMouseTracking(True)
    
    def _create_red_thumbnail(self, pixmap):
        if pixmap.isNull():
            return pixmap
            
        red_pixmap = QPixmap(pixmap.size())
        red_pixmap.fill(Qt.transparent)
        
        painter = QPainter(red_pixmap)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        painter.fillRect(red_pixmap.rect(), QColor(255, 100, 100, 160))
        painter.end()
        return red_pixmap
    
    def enterEvent(self, event):
        self.is_hovering = True
        # self.hover_color = True # 未使用
        self.thumbnail_label.setPixmap(self.red_thumbnail)
        self._show_full_image()
        return super().enterEvent(event) # 确保事件继续传递
    
    def leaveEvent(self, event):
        self.is_hovering = False
        # self.hover_color = False # 未使用
        self.thumbnail_label.setPixmap(self.original_thumbnail)
        QToolTip.hideText()
        if hasattr(self, 'preview_window') and self.preview_window:
            self.preview_window.close()
        return super().leaveEvent(event) # 确保事件继续传递
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._delete_image()
            return # 事件已处理
        return super().mousePressEvent(event)
        
    def _show_full_image(self):
        if self.is_hovering and not self.original_pixmap.isNull():
            max_width = 400
            max_height = 300
            
            preview_pixmap = self.original_pixmap
            if preview_pixmap.width() > max_width or preview_pixmap.height() > max_height:
                preview_pixmap = preview_pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # preview_label = QLabel() # 未使用
            # preview_label.setPixmap(preview_pixmap)
            # preview_label.setStyleSheet("background-color: #333; padding: 5px; border: 1px solid #666;")
            
            cursor_pos = QCursor.pos()
            QToolTip.showText(
                cursor_pos,
                f"<div style='background-color: #333; padding: 10px; border: 1px solid #666;'>"
                f"<div style='color: white; margin-bottom: 5px;'>图片预览 ({self.original_pixmap.width()}x{self.original_pixmap.height()})</div>"
                f"</div>",
                self
            )
            
            self.preview_window = QMainWindow(self) # QMainWindow 作为预览窗口可能过重，但遵循原设计
            self.preview_window.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
            self.preview_window.setAttribute(Qt.WA_DeleteOnClose)
            self.preview_window.setAttribute(Qt.WA_TranslucentBackground)
            
            preview_widget = QWidget()
            preview_layout = QVBoxLayout(preview_widget)
            preview_layout.setContentsMargins(10, 10, 10, 10)
            
            preview_image_label = QLabel()
            preview_image_label.setPixmap(preview_pixmap)
            preview_image_label.setAlignment(Qt.AlignCenter)
            preview_image_label.setStyleSheet("background-color: #333; padding: 5px; border: 1px solid #666; border-radius: 4px;")
            preview_layout.addWidget(preview_image_label)
            
            info_label = QLabel(f"尺寸: {self.original_pixmap.width()} x {self.original_pixmap.height()} 像素")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: white; background-color: #333; padding: 5px;")
            preview_layout.addWidget(info_label)
            
            self.preview_window.setCentralWidget(preview_widget)
            self.preview_window.resize(preview_pixmap.width() + 30, preview_pixmap.height() + 70)
            
            preview_window_x = cursor_pos.x() + 20
            preview_window_y = cursor_pos.y() + 20
            
            screen_geo = QApplication.primaryScreen().geometry() # 使用 screen_geo 避免重复调用
            if preview_window_x + self.preview_window.width() > screen_geo.width():
                preview_window_x = screen_geo.width() - self.preview_window.width()
            if preview_window_y + self.preview_window.height() > screen_geo.height():
                preview_window_y = screen_geo.height() - self.preview_window.height()
                
            self.preview_window.move(preview_window_x, preview_window_y)
            self.preview_window.show()
    
    def _delete_image(self):
        self.image_deleted.emit(self.image_id)
        self.deleteLater()

# 将 AtIconLabel 移至模块级别或 FeedbackUI 类的静态成员（此处移至模块级别）
class AtIconLabel(QLabel):
    clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(28, 28)
        self.setStyleSheet("background-color: transparent;") # 确保背景透明
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setPen(QColor("#cccccc"))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        painter.setFont(font)
        rect = self.rect()
        adjusted_rect = QRect(rect.x(), rect.y() - 2, rect.width(), rect.height())
        painter.drawText(adjusted_rect, Qt.AlignCenter, "@")
        painter.end()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class FeedbackUI(QMainWindow):
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None):
        super().__init__()
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.result = None
        self.image_pixmap = None
        self.next_image_id = 0
        self.image_widgets = {}
        self.canned_responses = []
        self.dropped_file_references = {}
        self.disable_auto_minimize = False
        self.window_pinned = False
        
        self.setWindowTitle("Interactive Feedback MCP")
        self.setMinimumWidth(1000)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "images", "feedback.png")
        
        try:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                images_dir = os.path.join(script_dir, "images")
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir, exist_ok=True)
        except Exception as e:
            print(f"警告: 无法加载图标文件: {e}", file=sys.stderr)
        
        self.setWindowFlags(Qt.Window)
        
        self.settings = QSettings(APP_NAME, APP_NAME)
        
        self.resize(1000, 750)
        self.setMinimumHeight(700)
        
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 1000) // 2, (screen.height() - 750) // 2)
        
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        geometry = self.settings.value(SETTINGS_KEY_GEOMETRY)
        if geometry:
            self.restoreGeometry(geometry)
            if self.width() < 1000:
                self.setMinimumWidth(1000) # 确保最小宽度
                self.resize(1000, self.height())
        state = self.settings.value(SETTINGS_KEY_WINDOW_STATE)
        if state:
            self.restoreState(state)
            
        self.window_pinned = self.settings.value(SETTINGS_KEY_WINDOW_PINNED, False, type=bool)
        self.settings.endGroup()

        self._load_canned_responses()

        self.show_shortcut_icons = self.settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_SHOW_SHORTCUT_ICONS}", True, type=bool)
        self.number_icons_visible = self.settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_NUMBER_ICONS_VISIBLE}", True, type=bool)
        
        self._create_ui()
        self._update_number_icons()
        
        if hasattr(self, 'shortcuts_container'): # 检查属性是否存在
            self.shortcuts_container.setVisible(self.show_shortcut_icons)
            if hasattr(self, 'number_icons_container'): # 检查属性是否存在
                self.number_icons_container.setVisible(self.number_icons_visible and self.show_shortcut_icons)
        
        if self.window_pinned:
            QTimer.singleShot(100, self._apply_window_pin_state)

    def _load_canned_responses(self):
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        responses = self.settings.value(SETTINGS_KEY_PHRASES, [])
        self.settings.endGroup()
        
        if responses is None:
            self.canned_responses = []
        elif isinstance(responses, str):
            self.canned_responses = [responses] if responses else [] # 处理空字符串情况
        else:
            try:
                self.canned_responses = [str(r) for r in responses if str(r).strip()] # 确保是字符串且非空
            except TypeError: # 处理 responses 不可迭代的情况
                self.canned_responses = []


    def _update_number_icons(self):
        if not hasattr(self, 'shortcut_number_icons') or not self.shortcut_number_icons:
            return
            
        for i, icon in enumerate(self.shortcut_number_icons):
            display_index = i + 1
            if i < len(self.canned_responses):
                canned_response = self.canned_responses[i]
                tooltip_text = canned_response if len(canned_response) <= 50 else canned_response[:47] + "..."
                icon.setToolTip(tooltip_text)
                icon.setStyleSheet(f"""
                    QLabel#number_icon_{display_index} {{
                        color: #777777 !important;
                        background-color: rgba(60, 60, 60, 0.5);
                        border-radius: 14px;
                        font-size: 14px;
                        font-weight: bold;
                    }}
                    QLabel#number_icon_{display_index}:hover {{
                        color: #aaaaaa !important;
                        background-color: rgba(85, 85, 85, 0.6);
                    }}
                """)
                icon.setCursor(Qt.PointingHandCursor)
                icon.setVisible(True)
            else:
                icon.setVisible(False)

    def _create_ui(self):
        central_widget = QWidget()
        central_widget.setMinimumWidth(1000)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(20)
        
        self.feedback_group = QGroupBox()
        # self.feedback_group.setTitle("") # 已在QSS中设置或默认
        # self.feedback_group.setStyleSheet("""...""") # 样式应在全局QSS中处理
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setContentsMargins(15, 5, 15, 15)
        feedback_layout.setSpacing(5) # 调整间距以适应快捷图标容器
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded) # 默认值
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        # scroll_area.setStyleSheet("""...""") # 样式应在全局QSS中处理
        scroll_area.setMaximumHeight(250)
        
        description_container = QWidget()
        description_layout = QVBoxLayout(description_container)
        description_layout.setContentsMargins(15, 5, 15, 15)
        # description_container.setStyleSheet("background: transparent;") # 样式应在全局QSS中处理
        
        self.description_label = ClickableLabel(self.prompt)
        self.description_label.setWordWrap(True)
        # self.description_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # 已在 ClickableLabel 中处理或默认
        # self.description_label.setStyleSheet("""...""") # 样式应在全局QSS中处理
        description_layout.addWidget(self.description_label)
        
        self.image_usage_label = ClickableLabel("如果图片反馈异常，建议切换cluade3.5")
        self.image_usage_label.setWordWrap(True)
        # self.image_usage_label.setStyleSheet("""...""") # 样式应在全局QSS中处理
        self.image_usage_label.setVisible(False)
        description_layout.addWidget(self.image_usage_label)
        
        self.paste_optimization_label = ClickableLabel("新功能: 已优化粘贴后的发送逻辑，图片和文本会一次性完整发送到Cursor。使用Ctrl+V粘贴内容。")
        self.paste_optimization_label.setWordWrap(True)
        # self.paste_optimization_label.setStyleSheet("""...""") # 样式应在全局QSS中处理
        self.paste_optimization_label.setVisible(False)
        description_layout.addWidget(self.paste_optimization_label)
        
        self.status_label = ClickableLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignLeft)
        # self.status_label.setStyleSheet("""...""") # 样式应在全局QSS中处理
        self.status_label.setVisible(False)
        description_layout.addWidget(self.status_label)

        scroll_area.setWidget(description_container)
        feedback_layout.addWidget(scroll_area)

        self.option_checkboxes = []
        self.option_labels = []
        
        options_frame = QFrame()
        options_frame.setMinimumWidth(950)
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(2, 0, 2, 0)
        options_layout.setSpacing(0)

        if self.predefined_options: # 简化条件检查
            for option_text in self.predefined_options:
                # option_row_layout = QHBoxLayout() # 未使用
                # option_row_layout.setContentsMargins(0, 0, 0, 0)
                # option_row_layout.setSpacing(8)
                
                checkbox = QCheckBox()
                checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                self.option_checkboxes.append(checkbox)
                
                option_container = QFrame()
                option_container.setObjectName("optionContainer")
                # option_container.setStyleSheet("""...""") # 样式应在全局QSS中处理
                
                container_layout = QHBoxLayout(option_container)
                container_layout.setContentsMargins(8, 2, 8, 2)
                container_layout.setSpacing(8)
                container_layout.addWidget(checkbox)
                
                label = ClickableLabel(option_text)
                label.setWordWrap(True)
                # label.setStyleSheet("""...""") # 样式应在全局QSS中处理
                self.option_labels.append(label)
                
                container_layout.addWidget(label)
                container_layout.setStretchFactor(checkbox, 0)
                container_layout.setStretchFactor(label, 1)
                options_layout.addWidget(option_container)
        
        feedback_layout.addWidget(options_frame)
            
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        # separator.setStyleSheet("background-color: rgba(85, 85, 85, 0.2);") # 样式应在全局QSS中处理
        feedback_layout.addWidget(separator)

        self.shortcuts_container = QWidget()
        self.shortcuts_container.setFixedHeight(30)
        # self.shortcuts_container.setStyleSheet("background-color: transparent;") # 样式应在全局QSS中处理
        shortcuts_container_layout = QHBoxLayout(self.shortcuts_container) # 重复设置布局，可移除
        shortcuts_container_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_container_layout.setSpacing(0)
        
        # 使用模块级别的 AtIconLabel
        self.at_icon = AtIconLabel(self.shortcuts_container)
        self.at_icon.move(12, 1)
        self.at_icon.clicked.connect(self._toggle_number_icons_visibility)

        self.number_icons_container = QWidget(self.shortcuts_container)
        self.number_icons_container.setGeometry(38, 0, 902, 30)
        number_icons_layout = QHBoxLayout(self.number_icons_container)
        number_icons_layout.setContentsMargins(0, 1, 0, 1)
        number_icons_layout.setSpacing(1)

        self.shortcut_number_icons = []
        for i in range(1, 11):
            icon_container = QWidget()
            icon_container.setFixedSize(28, 28)
            
            number_label = QLabel(str(i), icon_container)
            number_label.setGeometry(0, 0, 28, 28)
            number_label.setAlignment(Qt.AlignCenter)
            number_label.setObjectName(f"number_icon_{i}")
            # number_label.setStyleSheet(f"""...""") # 样式在 _update_number_icons 中设置
            number_label.setCursor(Qt.PointingHandCursor)
            number_label.setToolTip(f"常用语 {i}")
            number_label.installEventFilter(self)
            number_label.setProperty("shortcut_index", i - 1)
            
            number_icons_layout.addWidget(icon_container)
            self.shortcut_number_icons.append(number_label)
        
        feedback_layout.addWidget(self.shortcuts_container)

        number_icons_visible = self.settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_NUMBER_ICONS_VISIBLE}", True, type=bool)
        if hasattr(self, 'number_icons_container'): # 检查属性
            self.number_icons_container.setVisible(number_icons_visible)

        text_input_container = QWidget()
        text_input_container.setMinimumWidth(950)
        text_input_layout = QVBoxLayout(text_input_container)
        text_input_layout.setContentsMargins(0, 1, 0, 10)
        text_input_layout.setSpacing(15)
        
        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.setMinimumWidth(950)
        self.feedback_text.setMinimumHeight(250)
        self.feedback_text.setPlaceholderText("在此输入反馈内容 (纯文本格式，按Enter发送，Shift+Enter换行，Ctrl+V粘贴图片)")
        self.feedback_text.textChanged.connect(self._update_submit_button_text)
        
        # buttons_container = QWidget() # 未使用
        # buttons_layout = QVBoxLayout(buttons_container)
        # buttons_layout.setContentsMargins(0, 10, 0, 0)
        # buttons_layout.setSpacing(10)
        
        secondary_buttons_layout = QHBoxLayout()
        secondary_buttons_layout.setContentsMargins(5, 0, 5, 0)
        secondary_buttons_layout.setSpacing(15)
        secondary_buttons_layout.setAlignment(Qt.AlignLeft)
        
        self.bottom_canned_responses_button = QPushButton("常用语")
        self.bottom_canned_responses_button.setObjectName("secondary_button")
        self.bottom_canned_responses_button.setToolTip("选择或管理常用反馈短语")
        self.bottom_canned_responses_button.clicked.connect(self._show_canned_responses)
        secondary_buttons_layout.addWidget(self.bottom_canned_responses_button)
        
        self.pin_window_button = QPushButton("固定窗口")
        self.pin_window_button.setObjectName("secondary_button")
        self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
        self.pin_window_button.clicked.connect(self._toggle_pin_window)
        secondary_buttons_layout.addWidget(self.pin_window_button)
        
        # buttons_layout.addLayout(secondary_buttons_layout) # 未使用 buttons_layout
        
        submit_button_layout_container = QHBoxLayout() # 重命名避免与内部的 submit_button_layout 混淆
        submit_button_layout_container.setContentsMargins(5, 0, 5, 0)
        
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.submit_button.setMinimumHeight(60)
        self.submit_button.clicked.connect(self._submit_feedback)
        
        submit_button_layout_container.addWidget(self.submit_button)
        # buttons_layout.addLayout(submit_button_layout_container) # 未使用 buttons_layout
        
        text_input_layout.addWidget(self.feedback_text, 1)
        
        secondary_buttons_container = QWidget()
        secondary_buttons_container_layout = QHBoxLayout(secondary_buttons_container)
        secondary_buttons_container_layout.setContentsMargins(5, 0, 5, 0)
        secondary_buttons_container_layout.setSpacing(15)
        secondary_buttons_container_layout.setAlignment(Qt.AlignLeft)
        # 重复创建 bottom_canned_responses_button 和 pin_window_button，应使用已创建的实例
        secondary_buttons_container_layout.addWidget(self.bottom_canned_responses_button)
        secondary_buttons_container_layout.addWidget(self.pin_window_button)
        
        text_input_layout.addWidget(secondary_buttons_container)
        
        submit_button_container = QWidget()
        # submit_button_layout = QHBoxLayout(submit_button_container) # 变量名冲突，改为 submit_btn_layout
        submit_btn_layout = QHBoxLayout(submit_button_container)
        submit_btn_layout.setContentsMargins(5, 5, 5, 0)
        submit_btn_layout.addWidget(self.submit_button) # 使用已创建的 submit_button
        text_input_layout.addWidget(submit_button_container)
        
        feedback_layout.addWidget(text_input_container)
        main_layout.addWidget(self.feedback_group)
        
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setContentsMargins(0, 0, 0, 0)
        github_layout.setAlignment(Qt.AlignCenter)
        
        github_label = QLabel()
        github_label.setText("<a href='#' style='color: #aaaaaa; text-decoration: none;'>GitHub</a>")
        github_label.setOpenExternalLinks(False)
        github_label.setToolTip("访问项目GitHub仓库")
        github_label.setCursor(Qt.PointingHandCursor)
        github_label.linkActivated.connect(self._open_github_repo)
        # github_label.setStyleSheet("""...""") # 样式应在全局QSS中处理
        github_layout.addWidget(github_label)
        main_layout.addWidget(github_container)
        
        self._update_submit_button_text()

    def _set_text_focus(self):
        if hasattr(self, 'feedback_text') and self.feedback_text is not None:
            self.activateWindow()
            self.raise_()
            self.feedback_text.activateWindow()
            self.feedback_text.raise_()
            self.feedback_text.setFocus(Qt.MouseFocusReason)
            cursor = self.feedback_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.feedback_text.setTextCursor(cursor)
            self.feedback_text.ensureCursorVisible()

    def get_image_content_data(self, image_id=None) -> Optional[Dict[str, Any]]:
        pixmap_to_save = None 
        if self.image_widgets:
            if image_id is not None and image_id in self.image_widgets:
                pixmap_to_save = self.image_widgets[image_id].original_pixmap
            elif self.image_widgets: 
                last_id = max(self.image_widgets.keys()) # 确保 self.image_widgets 非空
                pixmap_to_save = self.image_widgets[last_id].original_pixmap
        
        if pixmap_to_save is None or pixmap_to_save.isNull():
            return None
            
        original_width = pixmap_to_save.width()
        original_height = pixmap_to_save.height()
        
        if original_width > MAX_IMAGE_WIDTH or original_height > MAX_IMAGE_HEIGHT:
            pixmap_to_save = pixmap_to_save.scaled(MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        save_format = "JPEG"
        mime_type = "image/jpeg"
        saved_successfully = False
        quality = 80 # 初始压缩质量
        
        # 尝试以不同质量保存，直到满足大小限制
        # 首先尝试默认质量
        if buffer.open(QIODevice.WriteOnly):
            if pixmap_to_save.save(buffer, save_format, quality):
                saved_successfully = True
            buffer.close()
        
        if not saved_successfully or byte_array.size() > MAX_IMAGE_BYTES:
            # 如果不成功或仍然太大，则降低质量重试
            quality_levels = [70, 60, 50, 40] 
            saved_successfully = False # 重置标志
            for lower_quality in quality_levels:
                byte_array.clear() # 清空 byte_array 以便重新写入
                buffer = QBuffer(byte_array) # 为新的尝试重新创建 buffer
                if buffer.open(QIODevice.WriteOnly):
                    if pixmap_to_save.save(buffer, save_format, lower_quality):
                        saved_successfully = True
                        buffer.close()
                        if byte_array.size() <= MAX_IMAGE_BYTES:
                            quality = lower_quality # 更新使用的质量
                            break # 已满足大小要求
                    else:
                        buffer.close() # 即使保存失败也要关闭 buffer
                if saved_successfully and byte_array.size() <= MAX_IMAGE_BYTES: # 双重检查
                    break
        
        if not saved_successfully or byte_array.isEmpty(): # 检查 byte_array 是否为空
            QMessageBox.critical(self, "图像处理错误", "无法将图像保存为 JPEG 格式。")
            return None
            
        if byte_array.size() > MAX_IMAGE_BYTES:
            QMessageBox.critical(self, "图像过大", 
                              f"图像大小 ({byte_array.size() // 1024} KB) 超过了限制 ({MAX_IMAGE_BYTES // 1024} KB)。\n"
                              "请使用更小的图像或进一步压缩。")
            return None
            
        image_data_bytes = byte_array.data() # 获取字节数据
        if not image_data_bytes: # 确保字节数据非空
             QMessageBox.critical(self, "图像处理错误", "无法获取图像数据。")
             return None
        
        try:
            base64_encoded_data = base64.b64encode(image_data_bytes).decode('utf-8')
            metadata = {
                "width": pixmap_to_save.width(),
                "height": pixmap_to_save.height(),
                "format": save_format.lower(), 
                "size": byte_array.size()
            }
            image_data_dict = {
                "type": "image",
                "data": base64_encoded_data,
                "mimeType": mime_type
            }
            return {"image_data": image_data_dict, "metadata": metadata}
        except Exception as e:
            QMessageBox.critical(self, "图像处理错误", f"图像数据编码失败: {e}")
            return None
    
    def get_all_images_content_data(self) -> List[Dict[str, Any]]:
        result = []
        for image_id in list(self.image_widgets.keys()): # 使用 list() 避免在迭代时修改字典
            processed_data = self.get_image_content_data(image_id)
            if processed_data:
                metadata = processed_data["metadata"]
                image_data_dict = processed_data["image_data"]
                metadata_item = {"type": "text", "text": json.dumps(metadata)}
                image_item = image_data_dict
                result.append({"metadata_item": metadata_item, "image_item": image_item})
        return result

    def _submit_feedback(self):
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []
        
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    option_text = self.predefined_options[i].strip()
                    option_text = re.sub(r'^\d+\.\s*', '', option_text)
                    selected_options.append(option_text)
        
        combined_text = ""
        if selected_options and feedback_text:
            combined_text = f"{'; '.join(selected_options)}\n{feedback_text}"
        elif selected_options:
            combined_text = f"{'; '.join(selected_options)}"
        else: # 只有 feedback_text 或者都为空
            combined_text = feedback_text # 如果 feedback_text 也为空，则 combined_text 为空字符串
        
        content_list = []
        if combined_text: # 仅当 combined_text 非空时添加
            content_list.append({"type": "text", "text": combined_text})

        if self.dropped_file_references:
            final_text_content = self.feedback_text.toPlainText() # 获取最终文本以检查引用
            for display_name, file_path in self.dropped_file_references.items():
                if display_name in final_text_content: # 确保引用仍在文本中
                    content_list.append({
                        "type": "file_reference",
                        "display_name": display_name,
                        "path": file_path
                    })
        
        all_images_data = self.get_all_images_content_data()
        if all_images_data:
            for image_set in all_images_data:
                if "image_item" in image_set and image_set["image_item"]:
                    content_list.append(image_set["image_item"])
        
        # 即使 content_list 为空，也应该设置 self.result 并关闭
        self.result = FeedbackResult(content=content_list if content_list else [])
        self.close()


    def closeEvent(self, event):
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_GEOMETRY, self.saveGeometry())
        self.settings.setValue(SETTINGS_KEY_WINDOW_STATE, self.saveState())
        self.settings.setValue(SETTINGS_KEY_WINDOW_PINNED, self.window_pinned)
        self.settings.endGroup()
        self.dropped_file_references.clear()
        super().closeEvent(event)
        
    def _apply_window_pin_state(self):
        current_geometry = self.geometry() # 保存当前几何信息
        if self.window_pinned:
            self.pin_window_button.setObjectName("pin_window_active")
            self.pin_window_button.setText("取消固定")
            self.pin_window_button.setToolTip("点击取消固定窗口")
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        else:
            self.pin_window_button.setObjectName("secondary_button")
            self.pin_window_button.setText("固定窗口")
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
            self.setWindowFlags(Qt.Window)
        
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        QTimer.singleShot(10, lambda: self._restore_window_state(current_geometry)) # 延迟恢复
        
        self.settings.beginGroup(SETTINGS_GROUP_MAIN) # 保存状态
        self.settings.setValue(SETTINGS_KEY_WINDOW_PINNED, self.window_pinned)
        self.settings.endGroup()


    def run(self) -> FeedbackResult:
        self.show()
        QTimer.singleShot(100, self._enforce_window_size)
        QTimer.singleShot(200, self._set_text_focus)
        QApplication.instance().exec()

        if not self.result:
            return FeedbackResult(content=[])
        return self.result
        
    def _enforce_window_size(self):
        needs_resize = False
        if self.width() < 1000:
            needs_resize = True
        if self.height() < 750: # 之前是 750
            needs_resize = True
            
        if needs_resize:
            self.resize(1000, 750) # 确保高度一致
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - 1000) // 2, (screen.height() - 750) // 2)

    def event(self, event):
        if event.type() == QEvent.WindowDeactivate:
            if self.window_pinned:
                return super().event(event)
            if self.isVisible() and not self.isMinimized() and not self.disable_auto_minimize:
                QTimer.singleShot(100, self.showMinimized)
        return super().event(event)
        
    def handle_paste_image(self):
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        handled_content = False
        
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                self.add_image_preview(pixmap)
                handled_content = True
        
        if mime_data.hasText():
            text = mime_data.text().strip()
            if text:
                cursor = self.feedback_text.textCursor()
                if self.feedback_text.toPlainText().strip() == "" or cursor.hasSelection():
                    self.feedback_text.setPlainText(text)
                else:
                    self.feedback_text.insertPlainText(text)
                handled_content = True
        
        if mime_data.hasUrls() and not handled_content: # 应该是 not handled_image
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            self.add_image_preview(pixmap)
                            handled_content = True
                            break 
        
        self._update_submit_button_text()
        return handled_content
    
    def add_image_preview(self, pixmap):
        if pixmap and not pixmap.isNull():
            image_id = self.next_image_id
            self.next_image_id += 1
            image_widget = ImagePreviewWidget(pixmap, image_id, self)
            image_widget.image_deleted.connect(self.remove_image)
            self.feedback_text.images_layout.addWidget(image_widget)
            self.image_widgets[image_id] = image_widget
            self.feedback_text.show_images_container(True)
            self.image_pixmap = pixmap # 更新 self.image_pixmap
            if hasattr(self, 'image_usage_label'):
                self.image_usage_label.setVisible(True)
            self._update_submit_button_text()
            QTimer.singleShot(100, self._set_text_focus)
            return image_id
        return None
    
    def remove_image(self, image_id):
        if image_id in self.image_widgets:
            widget = self.image_widgets.pop(image_id)
            self.feedback_text.images_layout.removeWidget(widget)
            widget.deleteLater()
            
            if not self.image_widgets:
                self.feedback_text.show_images_container(False)
                self.image_pixmap = None
                if hasattr(self, 'image_usage_label'):
                    self.image_usage_label.setVisible(False)
            else:
                # 更新 self.image_pixmap 指向最后一个图像
                if self.image_widgets: # 确保字典非空
                    last_id = max(self.image_widgets.keys())
                    self.image_pixmap = self.image_widgets[last_id].original_pixmap
                else: # 如果清空后字典为空
                    self.image_pixmap = None

            self._update_submit_button_text()
    
    def clear_all_images(self):
        image_ids = list(self.image_widgets.keys())
        for image_id in image_ids:
            self.remove_image(image_id)
        # self.image_pixmap = None # remove_image 中已处理
        # self.feedback_text.show_images_container(False) # remove_image 中已处理
        # if hasattr(self, 'image_usage_label'): # remove_image 中已处理
        #     self.image_usage_label.setVisible(False)
        # self._update_submit_button_text() # remove_image 中已处理
    
    def _update_submit_button_text(self):
        has_text = bool(self.feedback_text.toPlainText().strip())
        has_images = bool(self.image_widgets)
        
        if has_text and has_images:
            self.submit_button.setText(f"发送图片反馈 ({len(self.image_widgets)} 张)")
            self.submit_button.setToolTip("点击后将自动关闭窗口并激活Cursor对话框")
        elif has_images:
            self.submit_button.setText(f"发送 {len(self.image_widgets)} 张图片")
            self.submit_button.setToolTip("点击后将自动关闭窗口并激活Cursor对话框")
        elif has_text:
            self.submit_button.setText("提交反馈")
            self.submit_button.setToolTip("")
        else:
            self.submit_button.setText("提交")
            self.submit_button.setToolTip("")
        
        self.submit_button.setObjectName("submit_button") # 确保始终应用正确的样式
        self.submit_button.style().unpolish(self.submit_button)
        self.submit_button.style().polish(self.submit_button)

    def _show_canned_responses(self):
        self.disable_auto_minimize = True
        try:
            settings = QSettings(APP_NAME, APP_NAME) # 使用常量
            settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES) # 使用常量
            responses = settings.value(SETTINGS_KEY_PHRASES, []) # 使用常量
            settings.endGroup()
            
            # 确保 responses 是列表
            if responses is None: responses = []
            elif not isinstance(responses, list):
                responses = [str(responses)] if responses else []


            dialog = SelectCannedResponseDialog(responses, self)
            dialog.setWindowModality(Qt.ApplicationModal) # 确保模态
            # result = dialog.exec() # exec() 返回 QDialog.Accepted 或 QDialog.Rejected
            dialog.exec() # 只执行，不关心返回值，因为状态通过 settings 保存

            self._load_canned_responses()
            show_icons_enabled = settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_SHOW_SHORTCUT_ICONS}", True, type=bool)
            self._update_shortcut_icons_visibility(show_icons_enabled)
            self._update_number_icons()
            
            if show_icons_enabled and hasattr(self, 'number_icons_container'):
                number_icons_visible = settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_NUMBER_ICONS_VISIBLE}", True, type=bool)
                if hasattr(self, 'number_icons_container'): # 再次检查以防万一
                    self.number_icons_container.setVisible(number_icons_visible)
        finally:
            self.disable_auto_minimize = False

    def _add_images_from_clipboard(self): # 此方法似乎未被 FeedbackUI 类中的任何其他方法调用
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        added_images = 0
        
        if mime_data.hasImage():
            pixmap = QPixmap(clipboard.pixmap()) # 直接使用 clipboard.pixmap()
            if not pixmap.isNull() and pixmap.width() > 0:
                self.add_image_preview(pixmap) # 使用 add_image_preview
                added_images += 1
        
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            self.add_image_preview(pixmap) # 使用 add_image_preview
                            added_images += 1
        
        # self._update_submit_button_text() # add_image_preview 中已调用
        
        if added_images > 0:
            self.status_label.setText(f"成功添加了 {added_images} 张图片")
            self.status_label.setStyleSheet("color: green;")
            if self.image_usage_label: self.image_usage_label.setVisible(True)
        else:
            self.status_label.setText("剪贴板中没有找到有效图片")
            self.status_label.setStyleSheet("color: #ff6f00;")
        
        self.status_label.setVisible(True)
        QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))
        return added_images
        
    # def _remove_image(self, widget): # 这个方法签名与 ImagePreviewWidget 发出的信号不匹配，应为 remove_image(self, image_id)
        # 此方法已被 remove_image(self, image_id) 替代

    def _toggle_pin_window(self):
        current_geometry = self.geometry()
        self.window_pinned = not self.window_pinned
        
        if self.window_pinned:
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            self.pin_window_button.setText("取消固定")
            self.pin_window_button.setToolTip("点击取消固定窗口")
            self.pin_window_button.setObjectName("pin_window_active")
        else:
            self.setWindowFlags(Qt.Window)
            self.pin_window_button.setText("固定窗口")
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
            self.pin_window_button.setObjectName("secondary_button")
        
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        QTimer.singleShot(10, lambda: self._restore_window_state(current_geometry))
        
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_WINDOW_PINNED, self.window_pinned)
        self.settings.endGroup()
        
    def _open_github_repo(self):
        webbrowser.open("https://github.com/pawaovo/interactive-feedback-mcp")

    def _restore_window_state(self, geometry):
        self.setGeometry(geometry)
        self.show() # 确保在设置标志后调用 show
        self.raise_()
        self.activateWindow()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            if hasattr(watched, 'property') and watched.property("shortcut_index") is not None:
                shortcut_index = watched.property("shortcut_index")
                self._handle_number_icon_click(shortcut_index)
                return True
        return super().eventFilter(watched, event)
    
    def _handle_number_icon_click(self, index):
        if 0 <= index < len(self.canned_responses):
            text = self.canned_responses[index]
            if not text or not isinstance(text, str): return # 检查文本有效性
            
            # icon = self.shortcut_number_icons[index] # 未使用
            # display_index = index + 1 # 未使用
            
            if hasattr(self, 'feedback_text'):
                cursor = self.feedback_text.textCursor()
                cursor.insertText(text)
                self.feedback_text.setTextCursor(cursor) # 确保光标位置更新
                self.feedback_text.setFocus()

    def _update_shortcut_icons_visibility(self, visible=None):
        if visible is None:
            visible = self.settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_SHOW_SHORTCUT_ICONS}", True, type=bool)
        
        self.show_shortcut_icons = visible
        if hasattr(self, 'shortcuts_container'):
            self.shortcuts_container.setVisible(visible)
            if visible and hasattr(self, 'number_icons_container'):
                saved_number_icons_visible = self.settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_NUMBER_ICONS_VISIBLE}", True, type=bool)
                self.number_icons_container.setVisible(saved_number_icons_visible)
            self._update_number_icons()

    def _toggle_number_icons_visibility(self):
        if hasattr(self, 'number_icons_container') and self.number_icons_container:
            current_visibility = self.number_icons_container.isVisible()
            new_visibility = not current_visibility
            self.number_icons_container.setVisible(new_visibility)
            self.settings.setValue(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_NUMBER_ICONS_VISIBLE}", new_visibility) # 使用常量
            if new_visibility:
                self._update_number_icons()

class ManageCannedResponsesDialog(QDialog):
    def __init__(self, parent=None): # parent 应该传递给 super
        super().__init__(parent)
        self.setWindowTitle("管理常用语")
        self.resize(500, 500)
        self.setMinimumSize(400, 400)
        self.setWindowModality(Qt.ApplicationModal)
        # self.setModal(True) # setWindowModality(Qt.ApplicationModal) 已包含此行为
        
        self.settings = QSettings(APP_NAME, APP_NAME)
        self._create_ui()
        self._load_canned_responses()
    
    def _create_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)
        
        description_label = QLabel("管理您的常用反馈短语。点击列表项进行编辑，编辑完成后点击\"更新\"按钮。")
        description_label.setWordWrap(True)
        description_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(description_label)
        
        self.responses_list = QListWidget()
        self.responses_list.setAlternatingRowColors(True)
        # self.responses_list.setSelectionMode(QListWidget.SingleSelection) # 默认值
        self.responses_list.itemClicked.connect(self._on_item_selected)
        main_layout.addWidget(self.responses_list)
        
        edit_group = QGroupBox("编辑常用语")
        edit_layout = QVBoxLayout(edit_group)
        edit_layout.setContentsMargins(12, 15, 12, 15)
        edit_layout.setSpacing(12)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语或编辑选中的项目")
        edit_layout.addWidget(self.input_field)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self._add_response)
        self.add_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.add_button)
        
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self._update_response)
        self.update_button.setEnabled(False)
        self.update_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.update_button)
        
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self._delete_response)
        self.delete_button.setEnabled(False)
        self.delete_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.delete_button)
        
        self.clear_button = QPushButton("清空全部")
        self.clear_button.clicked.connect(self._clear_responses)
        self.clear_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.clear_button)
        
        edit_layout.addLayout(buttons_layout)
        main_layout.addWidget(edit_group)
        
        button_dialog_layout = QHBoxLayout() # 重命名避免与上面 buttons_layout 冲突
        button_dialog_layout.setSpacing(10)
        button_dialog_layout.addStretch(1)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept) # 通常 accept 用于确认，reject/close 用于取消
        self.close_button.setObjectName("secondary_button")
        button_dialog_layout.addWidget(self.close_button)
        main_layout.addLayout(button_dialog_layout)
        
        # 样式应在全局QSS中处理
        # self.setStyleSheet("""...""")
    
    def _load_canned_responses(self):
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        responses = self.settings.value(SETTINGS_KEY_PHRASES, [])
        self.settings.endGroup()
        
        if responses: # 确保 responses 是可迭代的列表
            self.responses_list.clear()
            for response in responses:
                if isinstance(response, str) and response.strip(): # 确保是字符串且非空
                    self.responses_list.addItem(response)
    
    def _save_canned_responses(self): # 方法名应为 _save_responses 或 _save_canned_responses
        responses = []
        for i in range(self.responses_list.count()):
            responses.append(self.responses_list.item(i).text())
        
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        self.settings.setValue(SETTINGS_KEY_PHRASES, responses)
        self.settings.endGroup()
        self.settings.sync() # 确保更改立即写入
    
    def _on_item_selected(self, item):
        if item:
            self.input_field.setText(item.text())
            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else: # 如果没有选中项（例如列表为空时）
            self.input_field.clear() # 清空输入框
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)
    
    def _add_response(self):
        text = self.input_field.text().strip()
        if text:
            # 检查重复使用 findItems
            # exists = False
            # for i in range(self.responses_list.count()):
            #     # item_widget 相关的检查不适用于 QListWidgetItem.text()
            #     if self.responses_list.item(i).text() == text:
            #         exists = True
            #         break
            
            # 使用更简洁的方式检查重复
            items = self.responses_list.findItems(text, Qt.MatchExactly)
            if items: # 如果找到匹配项
                QMessageBox.warning(self, "重复项", "此常用语已存在，请输入不同的内容。")
                return
                
            self.responses_list.addItem(text) # 直接添加文本项
            self._save_canned_responses() # 使用正确的方法名
            self.input_field.clear()
            QToolTip.showText(QCursor.pos(), "成功添加常用语", self, QRect(), 2000)
    
    def _update_response(self):
        current_item = self.responses_list.currentItem()
        if current_item:
            text = self.input_field.text().strip()
            if text:
                # 检查重复（排除自身）
                for i in range(self.responses_list.count()):
                    item = self.responses_list.item(i)
                    if item != current_item and item.text() == text:
                        QMessageBox.warning(self, "重复项", "此常用语已存在，请输入不同的内容。")
                        return
                
                current_item.setText(text)
                self._save_canned_responses()
                self.input_field.clear()
                self.update_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                self.responses_list.clearSelection() # 清除选择
    
    def _delete_response(self):
        current_row = self.responses_list.currentRow()
        if current_row >= 0:
            reply = QMessageBox.question(self, "确认删除", "确定要删除此常用语吗？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.responses_list.takeItem(current_row)
                self._save_canned_responses()
                self.input_field.clear()
                self.update_button.setEnabled(False)
                self.delete_button.setEnabled(False)
    
    def _clear_responses(self):
        if self.responses_list.count() > 0:
            reply = QMessageBox.question(self, "确认清空", "确定要清空所有常用语吗？此操作不可撤销。", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.responses_list.clear()
                self._save_canned_responses()
                self.input_field.clear()
                self.update_button.setEnabled(False)
                self.delete_button.setEnabled(False)
    
    def get_all_responses(self): # 此方法似乎未被调用
        responses = []
        for i in range(self.responses_list.count()):
            responses.append(self.responses_list.item(i).text())
        return responses

class SelectCannedResponseDialog(QDialog):
    def __init__(self, responses, parent=None):
        super().__init__(parent)
        self.setWindowTitle("常用语管理")
        self.resize(500, 450)
        self.setMinimumSize(450, 400)
        self.setWindowModality(Qt.ApplicationModal)
        
        self.parent_window = parent
        self.selected_response = None
        self.responses = responses if responses else []
        self.settings = QSettings(APP_NAME, APP_NAME)
        self._create_ui()
        self._load_responses()
    
    def _create_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(18, 18, 18, 18)
        
        top_layout = QHBoxLayout()
        title = QLabel("常用语列表")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;") # 内联样式可考虑移至全局
        top_layout.addWidget(title)
        top_layout.addStretch(1)
        
        self.show_shortcut_icons_checkbox = QCheckBox("常用语图标")
        # self.show_shortcut_icons_checkbox.setStyleSheet("""...""") # 样式应在全局QSS中处理
        top_layout.addWidget(self.show_shortcut_icons_checkbox)
        layout.addLayout(top_layout)
        
        hint = QLabel("双击插入文本，点击删除按钮移除项目")
        hint.setStyleSheet("font-size: 9pt; color: #aaaaaa;") # 内联样式可考虑移至全局
        layout.addWidget(hint)
        
        show_icons_enabled = self.settings.value(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_SHOW_SHORTCUT_ICONS}", True, type=bool)
        self.show_shortcut_icons_checkbox.setChecked(show_icons_enabled)
        layout.addSpacing(5)
        
        self.list_widget = DraggableListWidget() # DraggableListWidget 已有样式设置
        self.list_widget.setAlternatingRowColors(True)
        # self.list_widget.setSelectionMode(QListWidget.SingleSelection) # DraggableListWidget 中已设置
        self.list_widget.setProperty("NoAutoSelect", True)
        self.list_widget.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.item_double_clicked.connect(self._insert_text_to_parent)
        self.list_widget.drag_completed.connect(self._save_responses)
        # self.list_widget.setStyleSheet("""...""") # DraggableListWidget 中已有样式设置
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setToolTip("拖拽项目可以调整顺序")
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.list_widget, 1)
        
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语")
        self.input_field.returnPressed.connect(self._add_response)
        # self.input_field.setStyleSheet("""...""") # 样式应在全局QSS中处理
        input_layout.addWidget(self.input_field)
        
        self.add_button = QPushButton("保存")
        self.add_button.clicked.connect(self._add_response)
        self.add_button.setObjectName("secondary_button")
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)
        
        # self.setStyleSheet("""...""") # 对话框本身的样式应在全局QSS中处理
    
    def _load_responses(self):
        self.list_widget.clear()
        for response in self.responses: # self.responses 已在 __init__ 中确保是列表
            if isinstance(response, str) and response.strip(): # 再次确保是字符串且非空
                self._add_item_to_list(response)
        self.list_widget.clearSelection()
        self.list_widget.setCurrentItem(None)
        # current_stylesheet = self.list_widget.styleSheet() # 移除重复的样式设置
        # self.list_widget.setStyleSheet(current_stylesheet + """...""")
    
    def _add_item_to_list(self, text):
        item = QListWidgetItem()
        # self.list_widget.addItem(item) # DraggableListWidget 的 addItem 行为可能不同，此处应直接用 item

        widget = QWidget()
        layout_item = QHBoxLayout(widget) # 重命名变量
        layout_item.setContentsMargins(6, 3, 6, 3)
        layout_item.setSpacing(8)

        label = QLabel(text)
        label.setStyleSheet("color: white; font-size: 11pt; text-overflow: ellipsis;")
        label.setWordWrap(False)
        label.setMaximumWidth(350)
        label.setAttribute(Qt.WA_TranslucentBackground)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout_item.addWidget(label, 1)

        delete_btn = QPushButton("")
        delete_btn.setFixedSize(40, 25)
        # delete_btn.setStyleSheet("""...""") # 样式应在全局QSS中处理
        delete_btn.setObjectName("delete_canned_item_button") # 为按钮设置特定对象名以便QSS选择
        delete_btn.setToolTip("删除此常用语")
        delete_btn.clicked.connect(lambda: self._delete_response(text)) # 使用 lambda 捕获 text
        layout_item.addWidget(delete_btn)

        # 在DraggableListWidget中，我们通常直接添加QListWidgetItem，然后设置其widget
        self.list_widget.addItem(item) # 先添加 item
        self.list_widget.setItemWidget(item, widget) # 再设置 widget

        font_metrics = QFontMetrics(label.font())
        single_line_height = font_metrics.height()
        button_height = delete_btn.sizeHint().height()
        item_height = max(single_line_height + 10, button_height + 10)
        # item.setSizeHint(QSize(self.list_widget.viewport().width() - 10, item_height)) # 宽度由布局管理
        item.setSizeHint(QSize(0, item_height)) # 高度固定，宽度自适应
    
    def _add_response(self):
        text = self.input_field.text().strip()
        if not text: return
            
        # 检查重复
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel) # 更可靠地查找 QLabel
                if label and label.text() == text:
                    QMessageBox.warning(self, "重复项", "此常用语已存在")
                    return
        
        self._add_item_to_list(text)
        if text not in self.responses: # 避免重复添加内部数据
             self.responses.append(text)
        self._save_responses()
        self.input_field.clear()
    
    def _delete_response(self, text_to_delete): # 参数名清晰
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel) # 更可靠地查找 QLabel
                if label and label.text() == text_to_delete:
                    self.list_widget.takeItem(i)
                    if text_to_delete in self.responses: # 从内部数据中移除
                        self.responses.remove(text_to_delete)
                    self._save_responses()
                    return # 找到并删除后即可返回
    
    def _on_item_double_clicked(self, item): # item 是 QListWidgetItem
        widget = self.list_widget.itemWidget(item)
        if widget:
            label = widget.findChild(QLabel) # 更可靠地查找 QLabel
            if label:
                text = label.text()
                if self.parent_window and hasattr(self.parent_window, 'feedback_text'):
                    feedback_text_edit = self.parent_window.feedback_text # 清晰的变量名
                    feedback_text_edit.insertPlainText(text)
                    QTimer.singleShot(10, lambda: self._set_parent_focus(feedback_text_edit)) # 使用清晰的变量名
                    self.selected_response = text
                    self.accept()
    
    def _save_responses(self):
        # 从UI重新构建responses列表以保证顺序
        current_ui_responses = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel) # 更可靠地查找 QLabel
                if label:
                    current_ui_responses.append(label.text())
        self.responses = current_ui_responses # 更新内部数据以匹配UI

        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        self.settings.setValue(SETTINGS_KEY_PHRASES, self.responses) # 保存匹配UI的responses
        self.settings.endGroup()
        self.settings.sync()
    
    def closeEvent(self, event):
        self._save_responses()
        show_icons_enabled = self.show_shortcut_icons_checkbox.isChecked()
        self.settings.setValue(f"{SETTINGS_GROUP_CANNED_RESPONSES}/{SETTINGS_KEY_SHOW_SHORTCUT_ICONS}", show_icons_enabled)
        super().closeEvent(event)
    
    def get_selected_response(self): # 此方法似乎未被调用
        return self.selected_response

    def _insert_text_to_parent(self, text):
        if text and self.parent_window and hasattr(self.parent_window, 'feedback_text'):
            feedback_text_edit = self.parent_window.feedback_text # 清晰的变量名
            feedback_text_edit.insertPlainText(text)
            QTimer.singleShot(10, lambda: self._set_parent_focus(feedback_text_edit)) # 使用清晰的变量名
            self.selected_response = text
            self.accept()
            
    def _set_parent_focus(self, text_edit):
        if text_edit:
            text_edit.setFocus()
            cursor = text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            text_edit.setTextCursor(cursor)

class DraggableListWidget(QListWidget):
    drag_completed = Signal()
    item_double_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.drag_start_position = None # mousePressEvent 中初始化
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        # self.setDefaultDropAction(Qt.MoveAction) # 默认即是 MoveAction
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAlternatingRowColors(True)
        self.setCurrentRow(-1) # 避免默认选中第一项
        self.setIconSize(QSize(32, 32))
        # self.setStyleSheet("""...""") # 样式应在全局QSS中处理
        
    def showEvent(self, event):
        super().showEvent(event)
        self.clearSelection()
        self.setCurrentItem(None) # 确保没有当前项
    
    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            item_widget = self.itemWidget(item)
            if item_widget:
                text_label = item_widget.findChild(QLabel) # 更可靠地查找 QLabel
                if text_label:
                    self.item_double_clicked.emit(text_label.text())
                    return # 事件已处理
        super().mouseDoubleClickEvent(event) # 如果未处理，则调用基类
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
            # self.drag_item = self.itemAt(event.pos()) # drag_item 未在后续使用
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        # 简化拖拽触发逻辑，依赖Qt内部的startDragDistance
        # if (event.buttons() & Qt.LeftButton) and hasattr(self, 'drag_start_position') and self.drag_start_position:
        #     distance = (event.pos() - self.drag_start_position).manhattanLength()
        #     if distance >= QApplication.startDragDistance():
        #         # if hasattr(self, 'drag_item') and self.drag_item: # drag_item 未定义
        #         #     self.drag_item.setSelected(True) # Qt 会自动处理选中项的拖拽
        #         pass # 交给Qt处理
        super().mouseMoveEvent(event)
    
    def dropEvent(self, event):
        super().dropEvent(event)
        QTimer.singleShot(0, self.clearSelection) # 使用 0ms 延迟确保在事件循环中执行
        self.drag_completed.emit()

# --- 主函数和辅助函数 ---
def get_dark_mode_palette(app: QApplication):
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    darkPalette = app.palette() # 获取当前应用的调色板以修改
    
    darkPalette.setColor(QPalette.Window, QColor(30, 30, 30))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(45, 45, 45))
    darkPalette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(45, 45, 45))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(40, 40, 40))
    darkPalette.setColor(QPalette.Shadow, QColor(25, 25, 25))
    darkPalette.setColor(QPalette.Button, QColor(60, 60, 60))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, QColor(240, 240, 240))
    darkPalette.setColor(QPalette.Link, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.Highlight, QColor(70, 70, 70))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    
    # 返回调色板，由调用者设置
    # app.setStyleSheet("""...""") # 全局样式表应在 feedback_ui 中应用
    return darkPalette

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    app = QApplication.instance() or QApplication(sys.argv) # 确保 sys.argv 传递
    
    # 应用调色板和全局样式表
    app.setPalette(get_dark_mode_palette(app)) # 先设置调色板
    app.setStyle("Fusion") # Fusion 风格通常与自定义QSS配合良好
    
    # 全局 QSS (示例，具体内容根据需要调整)
    # 将之前分散的 QSS 规则整合到这里
    GLOBAL_QSS = """
        /* 全局字体设置 */
        * {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QWidget { font-size: 10pt; }

        /* ... (从 get_dark_mode_palette 和其他地方整合的样式) ... */

        QGroupBox {
            border: 1px solid #555;
            border-radius: 6px;
            margin-top: 12px; /* 为标题留出空间 */
            padding-top: 12px; /* 确保内容在标题下方 */
            background-color: transparent; /* 与 FeedbackUI._create_ui 中一致 */
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 8px;
            color: #aaa; /* 确保标题颜色 */
            font-weight: bold;
        }
        QLabel { color: white; padding: 2px; font-size: 11pt; }
        ClickableLabel { /* 针对 ClickableLabel 的特定样式 */
            color: #ffffff;
            selection-background-color: #2374E1;
            selection-color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            padding: 2px;
        }
        /* ... 其他控件的样式 ... */
        QPushButton {
            background-color: #3C3C3C; color: white; border: none;
            border-radius: 6px; padding: 8px 16px; font-weight: bold;
            font-size: 11pt; min-width: 120px; min-height: 36px;
        }
        QPushButton:hover { background-color: #444444; }
        QPushButton:pressed { background-color: #333333; }
        QPushButton:disabled { background-color: #555; color: #999; }

        QPushButton#submit_button { /* ... submit_button 样式 ... */
            background-color: #252525; color: white; border: 2px solid #3A3A3A;
            padding: 12px 20px; font-weight: bold; font-size: 13pt;
            border-radius: 15px; min-height: 60px;
            /* box-shadow 不被 Qt QSS 直接支持，考虑用其他方式实现或移除 */
        }
        QPushButton#submit_button:hover { background-color: #303030; border: 2px solid #454545; }
        QPushButton#submit_button:pressed { background-color: #202020; border: 2px solid #353535; }

        QPushButton#secondary_button, QPushButton#delete_canned_item_button { /* 合并相似按钮 */
            background-color: transparent; color: white; border: 1px solid #454545;
            font-size: 10pt; padding: 5px 10px; min-height: 32px;
            min-width: 100px; /* 统一最小宽度 */ max-height: 32px;
        }
        QPushButton#secondary_button:hover, QPushButton#delete_canned_item_button:hover {
            background-color: rgba(64, 64, 64, 0.3); border: 1px solid #555555;
        }
        QPushButton#secondary_button:pressed, QPushButton#delete_canned_item_button:pressed {
            background-color: rgba(48, 48, 48, 0.4);
        }
        QPushButton#delete_canned_item_button { /* 特化删除按钮 */
            background-color: #d32f2f; min-width: 40px; /* 之前设定的 */
        }
        QPushButton#delete_canned_item_button:hover { background-color: #f44336; }
        QPushButton#delete_canned_item_button:pressed { background-color: #b71c1c; }


        QPushButton#pin_window_active {
            background-color: rgba(80, 80, 80, 0.5); color: white; border: 1px solid #606060;
            font-size: 10pt; padding: 5px 10px; min-height: 32px;
            min-width: 120px; max-height: 32px;
        }
        QPushButton#pin_window_active:hover { background-color: rgba(85, 85, 85, 0.6); border: 1px solid #676767; }
        QPushButton#pin_window_active:pressed { background-color: rgba(69, 69, 69, 0.6); }

        QTextEdit, FeedbackTextEdit { /* 同时为 QTextEdit 和 FeedbackTextEdit 设置样式 */
            background-color: #272727; color: #ffffff; font-size: 13pt;
            font-family: 'Segoe UI', 'Microsoft YaHei UI', Arial, sans-serif;
            font-weight: 400; /* line-height, letter-spacing, word-spacing 不被QSS直接支持 */
            border: 2px solid #3A3A3A; border-radius: 10px; padding: 12px;
            selection-background-color: #505050; selection-color: white;
            min-height: 250px;
        }
        QTextEdit:hover, FeedbackTextEdit:hover { border: 2px solid #454545; background-color: #272727; }
        QTextEdit:focus, FeedbackTextEdit:focus { border: 2px solid #505050; }
        /* QTextEdit[placeholderText] { color: #999; }  QPalette 用于占位符文本 */

        QCheckBox { color: #b8b8b8; spacing: 8px; font-size: 11pt; min-height: 28px; padding: 1px; }
        QCheckBox::indicator {
            width: 22px; height: 22px; border: 1px solid #444444;
            border-radius: 4px; background-color: transparent;
        }
        QCheckBox::indicator:checked {
            background-color: #4D4D4D; border: 2px solid #555555;
            /* transform 不被QSS支持 */
            image: none; /* 确保SVG背景图生效 */
            background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='#ffffff' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
            background-position: center; background-repeat: no-repeat;
        }
        QCheckBox::indicator:hover:!checked { border: 1px solid #666666; background-color: #333333; }
        QCheckBox::indicator:checked:hover { background-color: #555555; border-color: #666666; }
        /* QCheckBox::indicator:checked + QLabel { color: white; } QSS中难以实现兄弟选择器 */

        QFrame[frameShape="4"] /* HLine */ {
            color: #555555; max-height: 1px; margin: 10px 0;
            background-color: #555555; border: none;
        }
        QScrollArea { background-color: transparent; border: none; }
        QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
        QScrollBar::handle:vertical { background: rgba(85,85,85,0.3); min-height: 20px; border-radius: 4px; }
        QScrollBar::handle:vertical:hover { background: rgba(119,119,119,0.4); }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

        /* FeedbackTextEdit 内部图片容器 */
        FeedbackTextEdit > QWidget { /* 直接子控件QWidget */
            background-color: #4a4a4a;
            border-top: 1px solid #555555;
            border-radius: 0 0 10px 10px;
            padding: 8px;
        }
        /* ImagePreviewWidget 样式 */
        ImagePreviewWidget {
            background-color: rgba(51, 51, 51, 200);
            border: 1px solid #555;
            border-radius: 4px;
            margin: 2px;
        }
        ImagePreviewWidget:hover { border: 1px solid #2a82da; }

        /* Canned Response Dialogs 样式 */
        ManageCannedResponsesDialog QListWidget, SelectCannedResponseDialog QListWidget, DraggableListWidget {
            font-size: 11pt; padding: 5px; background-color: #2D2D2D;
            border: 1px solid #3A3A3A; border-radius: 4px; color: white;
        }
        ManageCannedResponsesDialog QListWidget::item, SelectCannedResponseDialog QListWidget::item, DraggableListWidget::item {
            border-bottom: 1px solid #3A3A3A; padding: 6px; margin: 1px;
        }
        ManageCannedResponsesDialog QListWidget::item:hover, SelectCannedResponseDialog QListWidget::item:hover, DraggableListWidget::item:hover {
            background-color: transparent;
        }
        ManageCannedResponsesDialog QListWidget::item:selected, SelectCannedResponseDialog QListWidget::item:selected, DraggableListWidget::item:selected {
            background-color: transparent; border: none;
        }
        ManageCannedResponsesDialog QListWidget::item:focus, SelectCannedResponseDialog QListWidget::item:focus, DraggableListWidget::item:focus {
            background-color: transparent; border: none;
        }
        ManageCannedResponsesDialog QLineEdit, SelectCannedResponseDialog QLineEdit {
            font-size: 11pt; padding: 8px; /* height: 20px; 已由padding控制 */
            background-color: #333333; color: white; border: 1px solid #444; border-radius: 4px;
        }
        ManageCannedResponsesDialog QPushButton, SelectCannedResponseDialog QPushButton {
             /* 继承通用按钮样式，或按需特化 */
        }
        ManageCannedResponsesDialog QLabel, SelectCannedResponseDialog QLabel { /* Dialog 内的 Label */
            font-size: 10pt; color: #aaa;
        }
        SelectCannedResponseDialog QLabel[text="常用语列表"] { /* 特定标题 */
             font-size: 14pt; font-weight: bold; color: white;
        }
         SelectCannedResponseDialog QLabel[text="双击插入文本，点击删除按钮移除项目"] {
             font-size: 9pt; color: #aaaaaa;
        }
        SelectCannedResponseDialog QCheckBox { /* Dialog 内的 CheckBox */
            font-size: 11pt; color: #ffffff; spacing: 8px;
        }
        SelectCannedResponseDialog QCheckBox::indicator {
            width: 18px; height: 18px; border: 1px solid #555555;
            border-radius: 3px; background-color: #333333;
        }
        SelectCannedResponseDialog QCheckBox::indicator:checked {
            background-color: #555555; border: 1px solid #666666;
        }
        /* DraggableListWidget 特有项目内 QLabel */
        DraggableListWidget QLabel {
             color: white; font-size: 11pt; text-overflow: ellipsis;
        }
    """
    app.setStyleSheet(GLOBAL_QSS) # 应用全局样式
    app.setQuitOnLastWindowClosed(True)
    
    if predefined_options is None:
        predefined_options = []
    
    ui = FeedbackUI(prompt, predefined_options)
    result = ui.run()

    if output_file and result:
        # 确保目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir): # 检查 output_dir 是否为空
            os.makedirs(output_dir)
        
        try: # 添加try-except块以处理文件写入错误
            with open(output_file, "w", encoding='utf-8') as f: # 指定编码
                json.dump(result, f, ensure_ascii=False, indent=2) # 美化输出并确保中文正确显示
            # return None # 如果写入文件，则不返回结果给调用者（原逻辑）
        except IOError as e:
            print(f"ERROR: 无法写入输出文件 {output_file}: {e}", file=sys.stderr)
            # 根据需求，这里可以决定是否仍然返回 result，或者返回 None/抛出异常
            # return result # 或者返回 None，取决于错误处理策略
    
    return result # 即使写入文件，也返回结果，以便主程序打印


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the feedback UI")
    parser.add_argument("--prompt", default="I implemented the changes you requested.", help="The prompt to show to the user")
    parser.add_argument("--predefined-options", default="", help="Pipe-separated list of predefined options (|||)")
    parser.add_argument("--output-file", help="Path to save the feedback result as JSON")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with more verbose output") # debug 参数未使用
    parser.add_argument("--full-ui", action="store_true", default=False, help="显示完整UI界面，包含所有功能")
    args = parser.parse_args()
    
    # debug_mode = args.debug # 未使用
    
    if args.predefined_options:
        predefined_options = [opt for opt in args.predefined_options.split("|||") if opt.strip()] # 确保选项非空
    else:
        if args.full_ui:
            predefined_options = ["示例选项1", "示例选项2", "示例选项3"]
        else:
            predefined_options = []
    
    result = feedback_ui(args.prompt, predefined_options, args.output_file)
    if result and not args.output_file: # 仅当未指定输出文件时打印到控制台
        pretty_result = json.dumps(result, indent=2, ensure_ascii=False)
        print(f"\n反馈结果:\n{pretty_result}")
        
    sys.exit(0)

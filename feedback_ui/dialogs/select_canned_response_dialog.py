# feedback_ui/dialogs/select_canned_response_dialog.py
from typing import List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidgetItem, QWidget, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QSize, QObject
from PySide6.QtGui import QFontMetrics, QTextCursor

from ..utils.settings_manager import SettingsManager # Relative import
from .draggable_list_widget import DraggableListWidget # Import the custom list widget

# Forward declaration for type hinting parent window
# FeedbackUI 类型的前向声明
FeedbackUI = "FeedbackUI" 

class SelectCannedResponseDialog(QDialog):
    """
    Dialog for selecting a canned response, managing the list (add/delete/reorder),
    and inserting the selected response into the parent's text edit.

    用于选择常用回复、管理列表（添加/删除/重新排序）并将所选回复插入父窗口文本编辑器的对话框。
    """
    def __init__(self, responses: list[str], parent_window: QObject): # parent_window is FeedbackUI
        super().__init__(parent_window) # Set parent for modality and context
        self.setWindowTitle("常用语管理 (Manage Canned Responses)")
        self.resize(500, 450)
        self.setMinimumSize(450, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.parent_feedback_ui = parent_window # Store reference to the main UI
        self.initial_responses = responses[:] # Store a copy of initial responses
        self.settings_manager = SettingsManager(self)
        
        self._create_ui()
        self._load_responses_to_list_widget(self.initial_responses)

    def _create_ui(self):
        """Creates the UI elements for the dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(18, 18, 18, 18)
        
        top_layout = QHBoxLayout()
        title_label = QLabel("常用语列表 (Canned Responses List)")
        title_label.setObjectName("DialogTitleLabel") # For QSS styling
        # title_label.setStyleSheet("font-size: 14pt; font-weight: bold;") # Style via QSS
        top_layout.addWidget(title_label)
        top_layout.addStretch(1)
        
        self.show_shortcut_icons_checkbox = QCheckBox("显示快捷图标 (Show Shortcut Icons)")
        # self.show_shortcut_icons_checkbox.setStyleSheet(...) # Style via QSS
        current_show_icons_pref = self.settings_manager.get_show_shortcut_icons()
        self.show_shortcut_icons_checkbox.setChecked(current_show_icons_pref)
        self.show_shortcut_icons_checkbox.toggled.connect(self._save_show_icons_preference)
        top_layout.addWidget(self.show_shortcut_icons_checkbox)
        layout.addLayout(top_layout)
        
        hint_label = QLabel("双击插入文本，点击删除按钮移除，拖拽调整顺序。\n(Double-click to insert, click delete button, drag to reorder.)")
        hint_label.setObjectName("DialogHintLabel")
        # hint_label.setStyleSheet("font-size: 9pt; color: #aaaaaa;") # Style via QSS
        layout.addWidget(hint_label)
        layout.addSpacing(5)
        
        self.responses_list_widget = DraggableListWidget(self)
        self.responses_list_widget.item_double_clicked.connect(self._on_list_item_double_clicked)
        self.responses_list_widget.drag_completed.connect(self._save_responses_from_list_widget)
        layout.addWidget(self.responses_list_widget, 1) # Give list widget stretch factor
        
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语 (Enter new canned response)")
        self.input_field.returnPressed.connect(self._add_new_response_from_input)
        input_layout.addWidget(self.input_field)
        
        self.add_button = QPushButton("保存 (Save)") # Or "Add"
        self.add_button.clicked.connect(self._add_new_response_from_input)
        self.add_button.setObjectName("secondary_button")
        input_layout.addWidget(self.add_button)
        layout.addLayout(input_layout)

        # OK/Close button (optional, as double-click also closes)
        close_button = QPushButton("关闭 (Close)")
        close_button.setObjectName("secondary_button")
        close_button.clicked.connect(self.accept) # Accept will save and close
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

    def _load_responses_to_list_widget(self, responses: List[str]):
        """Populates the list widget with given responses."""
        self.responses_list_widget.clear()
        for response_text in responses:
            if isinstance(response_text, str) and response_text.strip():
                self._add_item_to_gui_list(response_text)
        self.responses_list_widget.setCurrentRow(-1) # No selection
    
    def _add_item_to_gui_list(self, text: str):
        """Adds a single response item (with custom widget) to the DraggableListWidget."""
        item = QListWidgetItem() # Create the item itself
        
        # Create a custom widget for the item
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(6, 3, 6, 3)
        item_layout.setSpacing(8)

        text_label = QLabel(text)
        # text_label.setStyleSheet("color: white; font-size: 11pt;") # Style via global QSS
        text_label.setWordWrap(False) # Ensure it doesn't wrap to keep item height consistent
        text_label.setMaximumWidth(350) # Prevent very long text from expanding too much
        # text_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction) # Non-selectable
        item_layout.addWidget(text_label, 1) # Label takes available space

        delete_button = QPushButton("删 (Del)") # Short text for delete
        delete_button.setFixedSize(40, 25) # Make delete button compact
        delete_button.setObjectName("delete_canned_item_button") # For specific styling via QSS
        delete_button.setToolTip("删除此常用语 (Delete this canned response)")
        # Use lambda to pass the item (or its text) to the delete function
        delete_button.clicked.connect(lambda checked=False, item_to_delete=item: self._delete_response_item(item_to_delete))
        item_layout.addWidget(delete_button)

        item_widget.setLayout(item_layout) # Set layout on the custom widget
        
        # Calculate item height based on content
        font_metrics = QFontMetrics(text_label.font())
        text_height = font_metrics.height()
        button_height = delete_button.sizeHint().height()
        item_height = max(text_height, button_height) + item_layout.contentsMargins().top() + item_layout.contentsMargins().bottom() + 6 # Add some padding

        item.setSizeHint(QSize(0, item_height)) # Width will be managed by list, set height

        self.responses_list_widget.addItem(item) # Add the QListWidgetItem
        self.responses_list_widget.setItemWidget(item, item_widget) # Set custom widget for the item
    
    def _add_new_response_from_input(self):
        """Adds a new response from the input field to the list and settings."""
        text_to_add = self.input_field.text().strip()
        if not text_to_add:
            QMessageBox.warning(self, "输入无效 (Invalid Input)", "常用语不能为空。(Canned response cannot be empty.)")
            return
            
        # Check for duplicates in the current list items
        for i in range(self.responses_list_widget.count()):
            item = self.responses_list_widget.item(i)
            widget = self.responses_list_widget.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel)
                if label and label.text() == text_to_add:
                    QMessageBox.warning(self, "重复项 (Duplicate Item)", "此常用语已存在。(This canned response already exists.)")
                    return
        
        self._add_item_to_gui_list(text_to_add)
        self._save_responses_from_list_widget() # Save immediately
        self.input_field.clear()
    
    def _delete_response_item(self, item_to_delete: QListWidgetItem):
        """Deletes the specified response item from the list and settings."""
        row = self.responses_list_widget.row(item_to_delete)
        if row >= 0:
            self.responses_list_widget.takeItem(row) # Remove from GUI list
            self._save_responses_from_list_widget() # Update settings
            
    def _on_list_item_double_clicked(self, text_of_item: str):
        """Handles double-click on a list item to insert text into parent."""
        if text_of_item and self.parent_feedback_ui and hasattr(self.parent_feedback_ui, 'feedback_text'):
            # Access the feedback_text QTextEdit widget on the parent FeedbackUI
            feedback_text_widget = self.parent_feedback_ui.feedback_text
            if feedback_text_widget:
                feedback_text_widget.insertPlainText(text_of_item)
                # Optionally, set focus back to the text edit and move cursor
                feedback_text_widget.setFocus()
                cursor = feedback_text_widget.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                feedback_text_widget.setTextCursor(cursor)
            
            # self.selected_response = text_of_item # Not strictly needed if action is direct
            self.accept() # Close the dialog after insertion

    def _save_responses_from_list_widget(self):
        """Saves the current order and content of responses from the list widget to settings."""
        current_responses_in_list = []
        for i in range(self.responses_list_widget.count()):
            item = self.responses_list_widget.item(i)
            widget = self.responses_list_widget.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel)
                if label:
                    current_responses_in_list.append(label.text())
        self.settings_manager.set_canned_responses(current_responses_in_list)

    def _save_show_icons_preference(self, checked: bool):
        """Saves the preference for showing shortcut icons."""
        self.settings_manager.set_show_shortcut_icons(checked)
        # Notify parent window to update its UI if necessary
        if self.parent_feedback_ui and hasattr(self.parent_feedback_ui, '_update_shortcut_icons_visibility'):
            self.parent_feedback_ui._update_shortcut_icons_visibility(checked)


    # Override accept and reject to ensure current list state is saved
    def accept(self):
        self._save_responses_from_list_widget()
        super().accept()
    
    def reject(self):
        self._save_responses_from_list_widget() # Also save if rejected (e.g., Esc pressed)
        super().reject()


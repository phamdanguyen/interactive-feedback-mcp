# feedback_ui/dialogs/select_canned_response_dialog.py

from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtGui import QFontMetrics, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid  # 替换sip

from ..utils.settings_manager import SettingsManager  # Relative import
from ..utils.tooltip_formatter import TooltipFormatter  # Import tooltip formatter
from .draggable_list_widget import DraggableListWidget  # Import the custom list widget

# Forward declaration for type hinting parent window
# FeedbackUI 类型的前向声明
FeedbackUI = "FeedbackUI"


class SelectCannedResponseDialog(QDialog):
    """
    Dialog for selecting a canned response, managing the list (add/delete/reorder),
    and inserting the selected response into the parent's text edit.

    用于选择常用回复、管理列表（添加/删除/重新排序）并将所选回复插入父窗口文本编辑器的对话框。
    """

    def __init__(
        self, responses: list[str], parent_window: QObject
    ):  # parent_window is FeedbackUI
        super().__init__(parent_window)  # Set parent for modality and context
        self.setWindowTitle(self.tr("常用语管理"))
        self.resize(500, 500)  # 增加高度
        self.setMinimumSize(450, 450)  # 增加最小高度
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.parent_feedback_ui = parent_window  # Store reference to the main UI
        self.initial_responses = responses[:]  # Store a copy of initial responses
        self.settings_manager = SettingsManager(self)

        # 双语文本映射
        self.texts = {
            "title": {"zh_CN": "常用语管理", "en_US": "Manage Canned Responses"},
            "list_title": {"zh_CN": "常用语列表", "en_US": "Canned Responses List"},
            "hint": {
                "zh_CN": "双击插入文本，点击删除按钮移除，拖拽调整顺序。",
                "en_US": "Double-click to insert, click delete button, drag to reorder.",
            },
            "input_label": {
                "zh_CN": "输入新的常用语:",
                "en_US": "Enter new canned response:",
            },
            "input_placeholder": {
                "zh_CN": "输入新的常用语",
                "en_US": "Enter new canned response",
            },
            "save_button": {"zh_CN": "保存", "en_US": "Save"},
            "close_button": {"zh_CN": "关闭", "en_US": "Close"},
            "delete_button": {"zh_CN": "删除", "en_US": "Delete"},
            "delete_tooltip": {
                "zh_CN": "删除此常用语",
                "en_US": "Delete this canned response",
            },
            "invalid_input": {"zh_CN": "输入无效", "en_US": "Invalid Input"},
            "empty_input_message": {
                "zh_CN": "常用语不能为空。",
                "en_US": "Canned response cannot be empty.",
            },
            "duplicate_title": {"zh_CN": "重复项", "en_US": "Duplicate Item"},
            "duplicate_message": {
                "zh_CN": "此常用语已存在。",
                "en_US": "This canned response already exists.",
            },
        }

        self._create_ui()
        self._load_responses_to_list_widget(self.initial_responses)

        # 初始更新文本
        self._update_texts()

    def _create_ui(self):
        """Creates the UI elements for the dialog."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(18, 18, 18, 18)

        # 移除标题和提示标签，简化界面

        self.responses_list_widget = DraggableListWidget(self)
        self.responses_list_widget.item_double_clicked.connect(
            self._on_list_item_double_clicked
        )
        self.responses_list_widget.drag_completed.connect(
            self._save_responses_from_list_widget
        )

        # 设置列表的最小高度，确保能显示更多项目
        self.responses_list_widget.setMinimumHeight(250)  # 增加列表高度

        layout.addWidget(
            self.responses_list_widget, 1
        )  # Give list widget stretch factor

        # 输入框单独一行，移除标签
        self.input_field = QLineEdit()
        # 稍后设置占位符文本
        self.input_field.returnPressed.connect(self._add_new_response_from_input)
        layout.addWidget(self.input_field)

        # 底部按钮区域 - 左侧保存，右侧关闭
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # 保存按钮（左侧）
        self.add_button = QPushButton("")  # 稍后设置文本
        self.add_button.clicked.connect(self._add_new_response_from_input)
        self.add_button.setObjectName("secondary_button")
        button_layout.addWidget(self.add_button)

        # 弹性空间
        button_layout.addStretch()

        # 关闭按钮（右侧）
        close_button = QPushButton("")  # 稍后设置文本
        close_button.setObjectName("secondary_button")
        close_button.clicked.connect(self.accept)  # Accept will save and close
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        self.close_button = close_button

    def _load_responses_to_list_widget(self, responses: list[str]):
        """Populates the list widget with given responses."""
        self.responses_list_widget.clear()
        for response_text in responses:
            if isinstance(response_text, str) and response_text.strip():
                self._add_item_to_gui_list(response_text)
        self.responses_list_widget.setCurrentRow(-1)  # No selection

    def _add_item_to_gui_list(self, text: str):
        """Adds a single response item (with custom widget) to the DraggableListWidget."""
        item = QListWidgetItem()  # Create the item itself

        # Create a custom widget for the item
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(6, 3, 6, 3)
        item_layout.setSpacing(8)

        text_label = QLabel(text)
        text_label.setWordWrap(
            False
        )  # Ensure it doesn't wrap to keep item height consistent
        text_label.setMaximumWidth(
            350
        )  # Prevent very long text from expanding too much
        # 为文本标签设置工具提示，显示完整的常用语文本内容
        TooltipFormatter.set_tooltip_for_widget(text_label, text)
        item_layout.addWidget(text_label, 1)  # Label takes available space

        current_language = self.settings_manager.get_current_language()
        delete_button = QPushButton(self.texts["delete_button"][current_language])
        delete_button.setFixedSize(40, 25)  # Make delete button compact
        delete_button.setObjectName(
            "delete_canned_item_button"
        )  # For specific styling via QSS
        delete_button.setToolTip(self.texts["delete_tooltip"][current_language])
        # Use lambda to pass the item (or its text) to the delete function
        delete_button.clicked.connect(
            lambda _, item_to_delete=item: self._delete_response_item(item_to_delete)
        )
        item_layout.addWidget(delete_button)

        item_widget.setLayout(item_layout)  # Set layout on the custom widget

        # Calculate item height based on content
        font_metrics = QFontMetrics(text_label.font())
        text_height = font_metrics.height()
        button_height = delete_button.sizeHint().height()
        item_height = (
            max(text_height, button_height)
            + item_layout.contentsMargins().top()
            + item_layout.contentsMargins().bottom()
            + 6
        )  # Add some padding

        item.setSizeHint(
            QSize(0, item_height)
        )  # Width will be managed by list, set height

        self.responses_list_widget.addItem(item)  # Add the QListWidgetItem
        self.responses_list_widget.setItemWidget(
            item, item_widget
        )  # Set custom widget for the item

        # 保存按钮引用以便语言切换时更新
        if not hasattr(self, "delete_buttons"):
            self.delete_buttons = []
        self.delete_buttons.append(delete_button)

    def _add_new_response_from_input(self):
        """Adds a new response from the input field to the list and settings."""
        # 立即获取输入文本
        text_to_add = self.input_field.text().strip()

        # 如果输入为空，静默返回，不显示警告
        if not text_to_add:
            return

        current_language = self.settings_manager.get_current_language()

        # Check for duplicates in the current list items
        for i in range(self.responses_list_widget.count()):
            item = self.responses_list_widget.item(i)
            widget = self.responses_list_widget.itemWidget(item)
            if widget:
                label = widget.findChild(QLabel)
                if label and label.text() == text_to_add:
                    QMessageBox.warning(
                        self,
                        self.texts["duplicate_title"][current_language],
                        self.texts["duplicate_message"][current_language],
                    )
                    return

        self._add_item_to_gui_list(text_to_add)
        self._save_responses_from_list_widget()  # Save immediately
        self.input_field.clear()

    def _delete_response_item(self, item_to_delete: QListWidgetItem):
        """Deletes the specified response item from the list and settings."""
        row = self.responses_list_widget.row(item_to_delete)
        if row >= 0:
            self.responses_list_widget.takeItem(row)  # Remove from GUI list
            self._save_responses_from_list_widget()  # Update settings

    def _on_list_item_double_clicked(self, text_of_item: str):
        """Handles double-click on a list item to insert text into parent."""
        if (
            text_of_item
            and self.parent_feedback_ui
            and hasattr(self.parent_feedback_ui, "text_input")
        ):
            # 隐藏任何现有的预览窗口
            if hasattr(self.parent_feedback_ui, "_hide_canned_responses_preview"):
                self.parent_feedback_ui._hide_canned_responses_preview()

            # Access the text_input QTextEdit widget on the parent FeedbackUI
            feedback_text_widget = self.parent_feedback_ui.text_input
            if feedback_text_widget:
                feedback_text_widget.insertPlainText(text_of_item)
                # Optionally, set focus back to the text edit and move cursor
                feedback_text_widget.setFocus()
                cursor = feedback_text_widget.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                feedback_text_widget.setTextCursor(cursor)

            # self.selected_response = text_of_item # Not strictly needed if action is direct
            self.accept()  # Close the dialog after insertion

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

    # Override accept and reject to ensure current list state is saved
    def accept(self):
        self._save_responses_from_list_widget()
        super().accept()

    def reject(self):
        self._save_responses_from_list_widget()  # Also save if rejected (e.g., Esc pressed)
        super().reject()

    def changeEvent(self, event: QEvent):
        """处理语言变化事件"""
        if event.type() == QEvent.Type.LanguageChange:
            self._update_texts()
        super().changeEvent(event)

    def _update_texts(self):
        """根据当前语言设置更新所有文本"""
        current_language = self.settings_manager.get_current_language()

        # 更新窗口标题
        self.setWindowTitle(self.texts["title"][current_language])

        # 由于移除了标题和提示标签，直接更新输入框占位符
        if hasattr(self, "input_field"):
            self.input_field.setPlaceholderText(
                self.texts["input_placeholder"][current_language]
            )

        # 更新按钮文本
        if hasattr(self, "add_button"):
            self.add_button.setText(self.texts["save_button"][current_language])

        if hasattr(self, "close_button"):
            self.close_button.setText(self.texts["close_button"][current_language])

        # 更新删除按钮
        if hasattr(self, "delete_buttons"):
            for button in self.delete_buttons:
                if button and isValid(button):
                    button.setText(self.texts["delete_button"][current_language])
                    button.setToolTip(self.texts["delete_tooltip"][current_language])

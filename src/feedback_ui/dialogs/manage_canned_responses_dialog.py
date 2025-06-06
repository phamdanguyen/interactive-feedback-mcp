# feedback_ui/dialogs/manage_canned_responses_dialog.py
from PySide6.QtCore import QEvent, QObject, Qt  # Added QObject and QEvent
from PySide6.QtGui import QCursor, QRect  # Added QRect, QCursor
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QToolTip,
    QVBoxLayout,
)

from ..utils.settings_manager import SettingsManager  # Relative import


class ManageCannedResponsesDialog(QDialog):
    """
    Dialog for managing a list of canned text responses.
    Allows adding, updating, deleting, and clearing responses.

    用于管理常用文本回复列表的对话框。
    允许添加、更新、删除和清空回复。
    """

    def __init__(self, parent: QObject = None):  # parent should be QWidget for dialogs
        super().__init__(parent)
        self.setWindowTitle(self.tr("管理常用语"))
        self.resize(500, 500)
        self.setMinimumSize(400, 400)
        self.setWindowModality(
            Qt.WindowModality.ApplicationModal
        )  # Ensures it blocks parent window

        self.settings_manager = SettingsManager(self)  # Can be passed or instantiated

        self._create_ui()
        self._load_responses_from_settings()

    def _create_ui(self):
        """Creates the UI elements for the dialog."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        description_label = QLabel()
        description_label.setText(
            self.tr(
                "管理您的常用反馈短语。点击列表项进行编辑，编辑完成后点击更新按钮。"
            )
        )
        description_label.setWordWrap(True)
        description_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        main_layout.addWidget(description_label)

        self.responses_list_widget = QListWidget()
        self.responses_list_widget.setAlternatingRowColors(True)
        self.responses_list_widget.itemClicked.connect(self._on_list_item_selected)
        main_layout.addWidget(self.responses_list_widget)

        # --- Edit Group ---
        edit_group = QGroupBox(self.tr("编辑常用语"))
        edit_layout = QVBoxLayout(edit_group)
        edit_layout.setContentsMargins(12, 15, 12, 15)
        edit_layout.setSpacing(12)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(self.tr("输入新的常用语或编辑选中的项目"))
        self.input_field.returnPressed.connect(
            self._add_or_update_response
        )  # Add/Update on Enter
        edit_layout.addWidget(self.input_field)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        self.add_button = QPushButton(self.tr("添加"))
        self.add_button.clicked.connect(self._add_new_response)
        self.add_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.add_button)

        self.update_button = QPushButton(self.tr("更新"))
        self.update_button.clicked.connect(self._update_selected_response)
        self.update_button.setEnabled(False)  # Disabled until an item is selected
        self.update_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.update_button)

        self.delete_button = QPushButton(self.tr("删除"))
        self.delete_button.clicked.connect(self._delete_selected_response)
        self.delete_button.setEnabled(False)  # Disabled until an item is selected
        self.delete_button.setObjectName(
            "secondary_button"
        )  # Could have a more destructive style
        buttons_layout.addWidget(self.delete_button)

        self.clear_all_button = QPushButton(self.tr("清空全部"))
        self.clear_all_button.clicked.connect(self._clear_all_responses)
        self.clear_all_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.clear_all_button)

        edit_layout.addLayout(buttons_layout)
        main_layout.addWidget(edit_group)

        # --- Dialog Buttons ---
        dialog_buttons_layout = QHBoxLayout()
        dialog_buttons_layout.addStretch(1)  # Push button to the right

        self.close_dialog_button = QPushButton(self.tr("关闭"))
        self.close_dialog_button.clicked.connect(
            self.accept
        )  # accept() closes dialog and signals acceptance
        self.close_dialog_button.setObjectName("secondary_button")
        dialog_buttons_layout.addWidget(self.close_dialog_button)
        main_layout.addLayout(dialog_buttons_layout)

    def _load_responses_from_settings(self):
        """Loads canned responses from settings and populates the list widget."""
        responses = self.settings_manager.get_canned_responses()
        self.responses_list_widget.clear()
        if responses:
            for response_text in responses:
                self.responses_list_widget.addItem(response_text)
        self._update_button_states()

    def _save_responses_to_settings(self):
        """Saves the current list of responses to settings."""
        responses = []
        for i in range(self.responses_list_widget.count()):
            item = self.responses_list_widget.item(i)
            if item:  # Should always be an item
                responses.append(item.text())
        self.settings_manager.set_canned_responses(responses)

    def _on_list_item_selected(self, item):  # item is QListWidgetItem
        """Handles selection of an item in the list."""
        if item:
            self.input_field.setText(item.text())
        else:  # Should not happen with itemClicked if list is not empty
            self.input_field.clear()
        self._update_button_states()

    def _add_or_update_response(self):
        """Adds a new response or updates the selected one when Enter is pressed in input field."""
        if self.responses_list_widget.currentItem() and self.update_button.isEnabled():
            self._update_selected_response()
        else:
            self._add_new_response()

    def _add_new_response(self):
        """Adds a new response from the input field to the list."""
        text = self.input_field.text().strip()
        if not text:
            QMessageBox.warning(self, self.tr("输入无效"), self.tr("常用语不能为空。"))
            return

        # Check for duplicates
        items = self.responses_list_widget.findItems(text, Qt.MatchFlag.MatchExactly)
        if items:
            QMessageBox.warning(self, self.tr("重复项"), self.tr("此常用语已存在。"))
            return

        self.responses_list_widget.addItem(text)
        self._save_responses_to_settings()
        self.input_field.clear()
        self.responses_list_widget.setCurrentRow(
            self.responses_list_widget.count() - 1
        )  # Select new item
        self._update_button_states()
        QToolTip.showText(QCursor.pos(), self.tr("成功添加常用语"), self, QRect(), 2000)

    def _update_selected_response(self):
        """Updates the currently selected response with text from the input field."""
        current_item = self.responses_list_widget.currentItem()
        if not current_item:
            return  # Should not happen if update_button is enabled

        new_text = self.input_field.text().strip()
        if not new_text:
            QMessageBox.warning(self, self.tr("输入无效"), self.tr("常用语不能为空。"))
            return

        # Check for duplicates (excluding the current item itself)
        for i in range(self.responses_list_widget.count()):
            item = self.responses_list_widget.item(i)
            if item != current_item and item.text() == new_text:
                QMessageBox.warning(
                    self, self.tr("重复项"), self.tr("此常用语已存在。")
                )
                return

        current_item.setText(new_text)
        self._save_responses_to_settings()
        # self.input_field.clear() # Keep text for further editing if desired
        # self.responses_list_widget.clearSelection() # Keep item selected
        self._update_button_states()  # Update button state might be needed if text becomes empty

    def _delete_selected_response(self):
        """Deletes the currently selected response from the list."""
        current_row = (
            self.responses_list_widget.currentRow()
        )  # More reliable than currentItem sometimes
        if current_row >= 0:
            reply = QMessageBox.question(
                self,
                self.tr("确认删除"),
                self.tr("确定要删除此常用语吗？"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,  # Default button
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.responses_list_widget.takeItem(current_row)  # Remove item
                self._save_responses_to_settings()
                self.input_field.clear()
                self._update_button_states()

    def _clear_all_responses(self):
        """Clears all responses from the list after confirmation."""
        if self.responses_list_widget.count() > 0:
            reply = QMessageBox.question(
                self,
                self.tr("确认清空"),
                self.tr("确定要清空所有常用语吗？此操作不可撤销。"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.responses_list_widget.clear()
                self._save_responses_to_settings()
                self.input_field.clear()
                self._update_button_states()

    def _update_button_states(self):
        """Updates the enabled state of edit/delete buttons based on selection."""
        has_selection = self.responses_list_widget.currentItem() is not None
        self.update_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.clear_all_button.setEnabled(self.responses_list_widget.count() > 0)

    # Override accept to ensure settings are saved if dialog is closed via "Close" button
    def accept(self):
        self._save_responses_to_settings()  # Ensure saving before closing
        super().accept()

    # Override reject for Esc key or window close button (if not explicitly handled)
    def reject(self):
        self._save_responses_to_settings()  # Also save on reject
        super().reject()

    def changeEvent(self, event: QEvent):
        """处理语言变化事件"""
        if event.type() == QEvent.Type.LanguageChange:
            self.retranslateUi()
        super().changeEvent(event)

    def retranslateUi(self):
        """更新界面上的所有文本"""
        self.setWindowTitle(self.tr("管理常用语"))

        # 更新描述标签
        description_label = self.findChild(QLabel)
        if description_label:
            description_label.setText(
                self.tr(
                    "管理您的常用反馈短语。点击列表项进行编辑，编辑完成后点击更新按钮。"
                )
            )

        # 更新分组框标题
        edit_group = None
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                edit_group = widget
                break

        if edit_group:
            edit_group.setTitle(self.tr("编辑常用语"))

            # 更新输入框
            input_field = edit_group.findChild(QLineEdit)
            if input_field:
                input_field.setPlaceholderText(
                    self.tr("输入新的常用语或编辑选中的项目")
                )

            # 更新按钮
            buttons = edit_group.findChildren(QPushButton)
            for button in buttons:
                if button.objectName() == "add_button" or "添加" in button.text():
                    button.setText(self.tr("添加"))
                elif button.objectName() == "update_button" or "更新" in button.text():
                    button.setText(self.tr("更新"))
                elif button.objectName() == "delete_button" or "删除" in button.text():
                    button.setText(self.tr("删除"))
                elif (
                    button.objectName() == "clear_all_button" or "清空" in button.text()
                ):
                    button.setText(self.tr("清空全部"))

        # 更新关闭按钮
        close_button = self.findChild(QPushButton, "close_dialog_button")
        if close_button:
            close_button.setText(self.tr("关闭"))

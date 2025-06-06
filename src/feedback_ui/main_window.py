# feedback_ui/main_window.py
import os
import sys
import json
import re # 正则表达式 (Regular expressions)
import webbrowser # 打开网页链接 (For opening web links)
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QGroupBox, QFrame, QSizePolicy,
    QScrollArea, QMessageBox, QAbstractSlider, QLineEdit
)
from PySide6.QtCore import Qt, QTimer, QEvent, QObject, QEventLoop
from PySide6.QtGui import QIcon, QTextCursor, QPixmap, QPalette, QColor

# --- 从子模块导入 (Imports from submodules) ---
from .utils.constants import FeedbackResult, ContentItem
from .utils.settings_manager import SettingsManager
from .utils.image_processor import get_image_items_from_widgets
from .utils.ui_helpers import set_selection_colors

from .widgets.clickable_label import ClickableLabel, AtIconLabel
from .widgets.selectable_label import SelectableLabel
from .widgets.feedback_text_edit import FeedbackTextEdit
from .widgets.image_preview import ImagePreviewWidget

from .dialogs.select_canned_response_dialog import SelectCannedResponseDialog
from .dialogs.settings_dialog import SettingsDialog

class FeedbackUI(QMainWindow):
    """
    Main window for the Interactive Feedback MCP application.
    交互式反馈MCP应用程序的主窗口。
    """
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.output_result = FeedbackResult(content=[])  # 初始化为空结果 (Initialize with empty result)

        # --- 内部状态 (Internal State) ---
        self.image_widgets: Dict[int, ImagePreviewWidget] = {} # image_id: widget
        self.option_checkboxes: List[QCheckBox] = [] # Initialize here to prevent AttributeError
        self.next_image_id = 0
        self.canned_responses: List[str] = []
        self.dropped_file_references: Dict[str, str] = {} # display_name: file_path
        self.disable_auto_minimize = False
        self.window_pinned = False

        # 按钮文本的双语映射
        self.button_texts = {
            "submit_button": {
                "zh_CN": "提交",
                "en_US": "Submit"
            },
            "canned_responses_button": {
                "zh_CN": "常用语",
                "en_US": "Canned Responses"
            },
            "pin_window_button": {
                "zh_CN": "固定窗口",
                "en_US": "Pin Window"
            },
            "settings_button": {
                "zh_CN": "设置",
                "en_US": "Settings"
            }
        }
        
        # 工具提示的双语映射
        self.tooltip_texts = {
            "canned_responses_button": {
                "zh_CN": "选择或管理常用语",
                "en_US": "Select or manage canned responses"
            },
            "settings_button": {
                "zh_CN": "打开设置面板",
                "en_US": "Open settings panel"
            }
        }

        self.settings_manager = SettingsManager(self)

        self._setup_window()
        self._load_settings()
        
        self._create_ui_layout()
        self._connect_signals()

        self._update_number_icons_display()
        self._update_shortcut_icons_visibility_state(self.show_shortcut_icons)
        self._apply_pin_state_on_load()
        
        # 初始化时更新界面文本显示
        self._update_displayed_texts()
        
        # 为主窗口安装事件过滤器，以实现点击背景聚焦输入框的功能
        self.installEventFilter(self)

    def _setup_window(self):
        """Sets up basic window properties like title, icon, size."""
        self.setWindowTitle("交互式反馈 MCP (Interactive Feedback MCP)")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        self.setWindowFlags(Qt.WindowType.Window)

        icon_path = os.path.join(os.path.dirname(__file__), "images", "feedback.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "feedback.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 图标文件未找到于 '{icon_path}'。", file=sys.stderr)

    def _load_settings(self):
        """从设置中加载保存的窗口状态和几何形状"""
        
        # 加载窗口几何形状（位置和大小）
        # 设置默认大小和位置
        default_width, default_height = 1000, 750
        
        # 尝试获取保存的窗口大小
        saved_size = self.settings_manager.get_main_window_size()
        if saved_size:
            width, height = saved_size
            self.resize(width, height)
        else:
            self.resize(default_width, default_height)
        
        # 获取屏幕大小
        screen = QApplication.primaryScreen().geometry()
        screen_width, screen_height = screen.width(), screen.height()
        
        # 尝试获取保存的窗口位置
        saved_position = self.settings_manager.get_main_window_position()
        if saved_position:
            x, y = saved_position
            # 检查位置是否有效（在屏幕范围内）
            if (0 <= x < screen_width - 100 and 0 <= y < screen_height - 100):
                self.move(x, y)
            else:
                # 位置无效，使用默认居中位置
                default_x = (screen_width - self.width()) // 2
                default_y = (screen_height - self.height()) // 2
                self.move(default_x, default_y)
        else:
            # 没有保存的位置，使用默认居中位置
            default_x = (screen_width - self.width()) // 2
            default_y = (screen_height - self.height()) // 2
            self.move(default_x, default_y)
        
        # 恢复窗口状态
        state = self.settings_manager.get_main_window_state()
        if state: self.restoreState(state)
            
        self.window_pinned = self.settings_manager.get_main_window_pinned()
        self._load_canned_responses_from_settings()
        self.show_shortcut_icons = self.settings_manager.get_show_shortcut_icons()
        self.number_icons_visible = self.settings_manager.get_number_icons_visible()

        # 加载字体大小设置
        self.update_font_sizes()

    def _create_ui_layout(self):
        """Creates the main UI layout and populates it with widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(15)

        self.feedback_group = QGroupBox()
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setContentsMargins(15, 5, 15, 15)
        feedback_layout.setSpacing(10)

        self._create_description_area(feedback_layout)

        if self.predefined_options:
            self._create_options_checkboxes(feedback_layout)
            
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        feedback_layout.addWidget(separator)

        self._create_shortcut_icons_panel(feedback_layout)
        self._create_input_submission_area(feedback_layout)
        
        main_layout.addWidget(self.feedback_group)
        
        self._setup_bottom_bar(main_layout)

        # The submit button now lives here, spanning the full width
        current_language = self.settings_manager.get_current_language()
        self.submit_button = QPushButton(self.button_texts["submit_button"][current_language])
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(50)
        main_layout.addWidget(self.submit_button)
        
        self._create_github_link_area(main_layout)
        
        self._update_submit_button_text_status()

    def _create_description_area(self, parent_layout: QVBoxLayout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(200)

        desc_widget_container = QWidget()
        desc_layout = QVBoxLayout(desc_widget_container)
        desc_layout.setContentsMargins(15, 5, 15, 15)
        
        self.description_label = SelectableLabel(self.prompt, self)
        self.description_label.setProperty("class", "prompt-label")
        self.description_label.setWordWrap(True)
        desc_layout.addWidget(self.description_label)
        
        self.image_usage_label = SelectableLabel("如果图片反馈异常，建议切换Claude 3.5 Sonnet模型。", self)
        self.image_usage_label.setWordWrap(True)
        self.image_usage_label.setVisible(False)
        desc_layout.addWidget(self.image_usage_label)
        
        self.status_label = SelectableLabel("", self)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setVisible(False)
        desc_layout.addWidget(self.status_label)

        scroll_area.setWidget(desc_widget_container)
        parent_layout.addWidget(scroll_area)

    def _create_options_checkboxes(self, parent_layout: QVBoxLayout):
        self.option_checkboxes: List[QCheckBox] = []
        options_frame = QFrame()
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(0,0,0,0)
        options_layout.setSpacing(2)

        for i, option_text in enumerate(self.predefined_options):
            # 创建一个水平容器用于放置复选框和可选择的标签
            option_container = QWidget()
            option_container_layout = QHBoxLayout(option_container)
            option_container_layout.setContentsMargins(0, 0, 0, 0)
            option_container_layout.setSpacing(5)
            
            # 创建无文本的复选框
            checkbox = QCheckBox("", self)
            checkbox.setObjectName(f"optionCheckbox_{i}")
            
            # 创建可选择文本的标签
            label = SelectableLabel(option_text, self)
            label.setProperty("class", "option-label")
            label.setWordWrap(True)
            
            # 连接标签的点击信号到复选框的切换方法
            label.clicked.connect(checkbox.toggle)
            
            # 将复选框和标签添加到水平容器
            option_container_layout.addWidget(checkbox)
            option_container_layout.addWidget(label, 1)  # 标签使用剩余的空间
            
            # 将复选框添加到列表，保持与原有逻辑兼容
            self.option_checkboxes.append(checkbox)
            
            # 将整个容器添加到选项布局
            options_layout.addWidget(option_container)
        
        parent_layout.addWidget(options_frame)

    def _create_shortcut_icons_panel(self, parent_layout: QVBoxLayout):
        self.shortcuts_container = QWidget(self)
        shortcuts_container_layout = QHBoxLayout(self.shortcuts_container)
        shortcuts_container_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_container_layout.setSpacing(5)

        self.at_icon = AtIconLabel(self.shortcuts_container)
        shortcuts_container_layout.addWidget(self.at_icon)
        
        self.number_icons_container = QWidget(self.shortcuts_container)
        number_icons_layout = QHBoxLayout(self.number_icons_container)
        number_icons_layout.setContentsMargins(0,0,0,0)
        number_icons_layout.setSpacing(5)
        
        self.shortcut_number_icons: List[ClickableLabel] = []
        for i in range(10):
            number_label = ClickableLabel(str(i+1), self.number_icons_container)
            number_label.setFixedSize(22, 22)
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setObjectName("shortcut_number_icon")
            number_icons_layout.addWidget(number_label)
            self.shortcut_number_icons.append(number_label)
            
        number_icons_layout.addStretch(1)
        shortcuts_container_layout.addWidget(self.number_icons_container, 1)
        parent_layout.addWidget(self.shortcuts_container)

    def _create_input_submission_area(self, parent_layout: QVBoxLayout):
        self.text_input = FeedbackTextEdit(self)
        self.text_input.setPlaceholderText("在此输入反馈...")
        # QTextEdit should expand vertically, so we give it a stretch factor
        parent_layout.addWidget(self.text_input, 1)

    def _setup_bottom_bar(self, parent_layout: QVBoxLayout):
        """Creates the bottom bar with canned responses, pin, and settings buttons."""
        bottom_bar_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar_widget)
        bottom_layout.setContentsMargins(0, 5, 0, 5)
        bottom_layout.setSpacing(10)

        current_language = self.settings_manager.get_current_language()

        # 使用语言相关的文本
        self.canned_responses_button = QPushButton(self.button_texts["canned_responses_button"][current_language])
        self.canned_responses_button.setObjectName("secondary_button")
        self.canned_responses_button.setToolTip(self.tooltip_texts["canned_responses_button"][current_language])
        bottom_layout.addWidget(self.canned_responses_button)

        self.pin_window_button = QPushButton(self.button_texts["pin_window_button"][current_language])
        self.pin_window_button.setCheckable(True)
        self.pin_window_button.setObjectName("secondary_button")
        bottom_layout.addWidget(self.pin_window_button)

        # --- Settings Button (设置按钮) ---
        self.settings_button = QPushButton(self.button_texts["settings_button"][current_language])
        self.settings_button.setObjectName("secondary_button")
        self.settings_button.setToolTip(self.tooltip_texts["settings_button"][current_language])
        bottom_layout.addWidget(self.settings_button)

        bottom_layout.addStretch() # Pushes buttons to the left

        parent_layout.addWidget(bottom_bar_widget)

    def _create_github_link_area(self, parent_layout: QVBoxLayout):
        """Creates the GitHub link at the bottom."""
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setContentsMargins(0, 10, 0, 0)
        
        github_label = QLabel("<a href='https://github.com/lucas-710/interactive-feedback-mcp'>Project GitHub</a>")
        github_label.setOpenExternalLinks(True)
        # 启用文本选择功能
        github_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        
        # 设置选择文本时的高亮颜色为灰色
        set_selection_colors(github_label)
        
        github_layout.addStretch()
        github_layout.addWidget(github_label)
        github_layout.addStretch()
        parent_layout.addWidget(github_container)

    def _connect_signals(self):
        self.at_icon.clicked.connect(self._toggle_number_icons_visibility_action)
        self.text_input.textChanged.connect(self._update_submit_button_text_status)
        self.canned_responses_button.clicked.connect(self._show_canned_responses_dialog)
        self.pin_window_button.toggled.connect(self._toggle_pin_window_action)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.submit_button.clicked.connect(self._prepare_and_submit_feedback)
        
        for i, icon in enumerate(self.shortcut_number_icons):
            icon.clicked.connect(lambda i=i: self._handle_number_icon_click_action(i))

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate:
            if not self.window_pinned and self.isVisible() and not self.isMinimized() and not self.disable_auto_minimize:
                QTimer.singleShot(100, self.showMinimized)
        return super().event(event)

    def closeEvent(self, event: QEvent):
        # 保存窗口几何和状态
        self.settings_manager.set_main_window_geometry(self.saveGeometry())
        self.settings_manager.set_main_window_state(self.saveState())
        self.settings_manager.set_main_window_pinned(self.window_pinned)
        
        # 单独保存窗口大小
        self.settings_manager.set_main_window_size(self.width(), self.height())
        
        # 保存窗口位置
        self.settings_manager.set_main_window_position(self.x(), self.y())
        
        # 确保在用户直接关闭窗口时也返回空结果
        # 此处不需要检查 self.output_result 是否已设置，因为在 __init__ 中已初始化为空结果
        # 如果没有显式通过 _prepare_and_submit_feedback 设置结果，则保持初始的空结果
        
        super().closeEvent(event)

    def _load_canned_responses_from_settings(self):
        self.canned_responses = self.settings_manager.get_canned_responses()

    def _update_number_icons_display(self):
        for i, icon in enumerate(self.shortcut_number_icons):
            if i < len(self.canned_responses):
                icon.setToolTip(self.canned_responses[i])
                icon.setVisible(True)
            else:
                icon.setVisible(False)

    def _update_shortcut_icons_visibility_state(self, visible: Optional[bool] = None):
        if visible is None:
            visible = self.settings_manager.get_show_shortcut_icons()
        self.number_icons_container.setVisible(visible)

    def _toggle_number_icons_visibility_action(self):
        new_visibility = not self.number_icons_container.isVisible()
        self.settings_manager.set_number_icons_visible(new_visibility)
        self.number_icons_container.setVisible(new_visibility)

    def _handle_number_icon_click_action(self, index: int):
        if 0 <= index < len(self.canned_responses):
            text_to_insert = self.canned_responses[index]
            if text_to_insert and isinstance(text_to_insert, str):
                self.text_input.insertPlainText(text_to_insert)
                self.text_input.setFocus()

    def _update_submit_button_text_status(self):
        has_text = bool(self.text_input.toPlainText().strip())
        has_images = bool(self.image_widgets)
        
        has_options_selected = any(cb.isChecked() for cb in self.option_checkboxes)
        
        # 修改：按钮应始终可点击，即使没有内容，以支持提交空反馈
        # self.submit_button.setEnabled(has_text or has_images or has_options_selected)
        self.submit_button.setEnabled(True)

    def _show_canned_responses_dialog(self):
        self.disable_auto_minimize = True
        dialog = SelectCannedResponseDialog(self.canned_responses, self)
        dialog.exec()
        self.disable_auto_minimize = False
        # After the dialog closes, settings are updated internally by the dialog.
        # We just need to reload them here.
        self._load_canned_responses_from_settings()
        self._update_number_icons_display()
    
    def open_settings_dialog(self):
        """Opens the settings dialog."""
        self.disable_auto_minimize = True
        dialog = SettingsDialog(self)
        dialog.exec()
        self.disable_auto_minimize = False

    def _apply_pin_state_on_load(self):
        # 从设置中加载固定窗口状态，但不改变按钮样式
        self.pin_window_button.setChecked(self.window_pinned)
        
        # 只应用窗口标志，不改变按钮样式
        if self.window_pinned:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            # 设置提示文本
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)")
            self.pin_window_button.setObjectName("pin_window_active")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.pin_window_button.setToolTip("")
            # 确保按钮初始状态样式与其他按钮一致
            self.pin_window_button.setObjectName("secondary_button")
            
        # 只应用样式到固定窗口按钮，避免影响其他按钮
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        self.pin_window_button.update()

    def _toggle_pin_window_action(self):
        # 获取按钮当前的勾选状态
        self.window_pinned = self.pin_window_button.isChecked()
        self.settings_manager.set_main_window_pinned(self.window_pinned)
        
        # 设置窗口标志
        if self.window_pinned:
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            # 只有当按钮被激活时才改变样式
            self.pin_window_button.setObjectName("pin_window_active")
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            # 恢复为普通按钮样式
            self.pin_window_button.setObjectName("secondary_button")
            self.pin_window_button.setToolTip("")
            
        # 只应用样式变化到固定窗口按钮，避免影响其他按钮
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        self.pin_window_button.update()
        
        # 重新显示窗口（因为改变了窗口标志）
        self.show()

    def add_image_preview(self, pixmap: QPixmap) -> Optional[int]:
        if pixmap and not pixmap.isNull():
            image_id = self.next_image_id
            self.next_image_id += 1
            
            image_widget = ImagePreviewWidget(pixmap, image_id, self.text_input.images_container)
            image_widget.image_deleted.connect(self._remove_image_widget)
            
            self.text_input.images_layout.addWidget(image_widget)
            self.image_widgets[image_id] = image_widget
            
            self.text_input.show_images_container(True)
            self.image_usage_label.setVisible(True)
            self._update_submit_button_text_status()
            return image_id
        return None
    
    def _remove_image_widget(self, image_id: int):
        if image_id in self.image_widgets:
            widget_to_remove = self.image_widgets.pop(image_id)
            self.text_input.images_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
            
            if not self.image_widgets:
                self.text_input.show_images_container(False)
                self.image_usage_label.setVisible(False)
            self._update_submit_button_text_status()

    def _prepare_and_submit_feedback(self):
        final_content_list: List[ContentItem] = []
        feedback_plain_text = self.text_input.toPlainText().strip()
        
        # 获取选中的选项
        selected_options = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked() and i < len(self.predefined_options):
                # 使用预定义选项列表中的文本
                selected_options.append(self.predefined_options[i])
        
        combined_text_parts = []
        if selected_options: combined_text_parts.append("; ".join(selected_options))
        if feedback_plain_text: combined_text_parts.append(feedback_plain_text)
        
        final_text = "\n".join(combined_text_parts).strip()
        # 允许提交空内容，即使 final_text 为空
        if final_text:
            final_content_list.append({"type": "text", "text": final_text})

        image_items = get_image_items_from_widgets(self.image_widgets)
        final_content_list.extend(image_items)
        
        # 处理文件引用（恢复之前移除的代码）
        current_text_content_for_refs = self.text_input.toPlainText()
        file_references = {k: v for k, v in self.dropped_file_references.items() if k in current_text_content_for_refs}
        
        # 不管 final_content_list 是否为空，都设置结果并关闭窗口
        self.output_result = FeedbackResult(content=final_content_list)
        
        # 保存窗口几何和状态信息，确保即使通过提交反馈关闭窗口时也能保存这些信息
        self.settings_manager.set_main_window_geometry(self.saveGeometry())
        self.settings_manager.set_main_window_state(self.saveState())
        
        # 单独保存窗口大小
        self.settings_manager.set_main_window_size(self.width(), self.height())
        
        # 保存窗口位置
        self.settings_manager.set_main_window_position(self.x(), self.y())
        
        self.close()

    def run_ui_and_get_result(self) -> FeedbackResult:
        self.show()
        self.activateWindow()
        self.text_input.setFocus()
        
        app_instance = QApplication.instance()
        if app_instance:
            app_instance.exec()
            
        # 直接返回 self.output_result，它在 __init__ 中已初始化为空结果
        # 如果用户有提交内容，它已在 _prepare_and_submit_feedback 中被更新
        return self.output_result

    def _set_initial_focus(self):
        """Sets initial focus to the feedback text edit."""
        if hasattr(self, 'text_input') and self.text_input:
            self.text_input.setFocus(Qt.FocusReason.OtherFocusReason)
            cursor = self.text_input.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_input.setTextCursor(cursor)
            self.text_input.ensureCursorVisible()

    def _enforce_min_window_size(self):
        pass

    def _clear_all_image_previews(self):
        pass

    def changeEvent(self, event: QEvent):
        """处理语言变化事件，更新界面文本"""
        if event.type() == QEvent.Type.LanguageChange:
            print("FeedbackUI: 接收到语言变化事件，更新UI文本")
            # 更新所有文本
            self._update_displayed_texts()
        super().changeEvent(event)

    def _update_displayed_texts(self):
        """根据当前语言设置更新显示的文本内容"""
        current_lang = self.settings_manager.get_current_language()
        
        # 更新提示文字
        if self.description_label:
            self.description_label.setText(self._filter_text_by_language(self.prompt, current_lang))
        
        # 更新选项复选框的关联标签
        for i, checkbox in enumerate(self.option_checkboxes):
            if i < len(self.predefined_options):
                # 找到复选框所在的容器
                option_container = checkbox.parent()
                if option_container:
                    # 找到容器中的SelectableLabel
                    for child in option_container.children():
                        if isinstance(child, SelectableLabel):
                            # 更新标签文本
                            child.setText(self._filter_text_by_language(self.predefined_options[i], current_lang))
                            break
                
        # 更新按钮文本
        self._update_button_texts(current_lang)
    
    def _update_button_texts(self, language_code):
        """根据当前语言更新所有按钮的文本"""
        # 更新提交按钮
        if hasattr(self, 'submit_button') and self.submit_button:
            self.submit_button.setText(self.button_texts["submit_button"].get(language_code, "提交"))
            
        # 更新底部按钮
        if hasattr(self, 'canned_responses_button') and self.canned_responses_button:
            self.canned_responses_button.setText(self.button_texts["canned_responses_button"].get(language_code, "常用语"))
            self.canned_responses_button.setToolTip(self.tooltip_texts["canned_responses_button"].get(language_code, "选择或管理常用语"))
            
        if hasattr(self, 'pin_window_button') and self.pin_window_button:
            # 保存当前按钮的样式类名
            current_object_name = self.pin_window_button.objectName()
            self.pin_window_button.setText(self.button_texts["pin_window_button"].get(language_code, "固定窗口"))
            # 单独刷新固定窗口按钮的样式，避免影响其他按钮
            self.pin_window_button.style().unpolish(self.pin_window_button)
            self.pin_window_button.style().polish(self.pin_window_button)
            self.pin_window_button.update()
            
        if hasattr(self, 'settings_button') and self.settings_button:
            self.settings_button.setText(self.button_texts["settings_button"].get(language_code, "设置"))
            self.settings_button.setToolTip(self.tooltip_texts["settings_button"].get(language_code, "打开设置面板"))
            
        # 单独为提交按钮、常用语按钮和设置按钮刷新样式
        for btn in [self.submit_button, self.canned_responses_button, self.settings_button]:
            if btn:
                btn.style().unpolish(btn)
                btn.style().polish(btn)
                btn.update()
                
    def _filter_text_by_language(self, text: str, lang_code: str) -> str:
        """
        从双语文本中提取指定语言的部分
        支持的格式:
        - "中文 (English)" 或 "中文（English）"
        - "中文 - English" 或类似分隔符
        """
        if not text or not isinstance(text, str):
            return text
        
        # 如果是中文模式
        if lang_code == "zh_CN":
            # 格式1：标准括号格式 "中文 (English)" 或 "中文（English）"
            match = re.match(r'^(.*?)[\s]*[\(（].*?[\)）](\s*|$)', text)
            if match:
                return match.group(1).strip()
                
            # 格式2：中英文之间有破折号或其他分隔符 "中文 - English"
            match = re.match(r'^(.*?)[\s]*[-—–][\s]*[A-Za-z].*?$', text)
            if match:
                return match.group(1).strip()
                
            # 如果都不匹配，可能是纯中文，直接返回
            return text
        
        # 如果是英文模式
        elif lang_code == "en_US":
            # 格式1：标准括号格式，提取括号内的英文
            match = re.search(r'[\(（](.*?)[\)）]', text)
            if match:
                return match.group(1).strip()
                
            # 格式2：中英文之间有破折号或其他分隔符 "中文 - English"
            match = re.search(r'[-—–][\s]*(.*?)$', text)
            if match and re.search(r'[A-Za-z]', match.group(1)):
                return match.group(1).strip()
                
            # 如果上述格式都不匹配，检查是否包含英文单词
            if re.search(r'[A-Za-z]{2,}', text):  # 至少包含2个连续英文字母
                return text
                
            # 可能是纯中文，那就返回原文本
            return text
        
        # 默认返回原文本
        return text

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        事件过滤器，用于实现无论点击窗口哪个区域，都自动保持文本输入框的活跃状态。
        Event filter to keep the text input active regardless of where the user clicks.
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            # 对于任何鼠标点击，都激活输入框
            # For any mouse click, activate the text input
            
            # 如果文本输入框当前没有焦点，则设置焦点并移动光标到末尾
            if not self.text_input.hasFocus():
                self.text_input.setFocus()
                cursor = self.text_input.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.text_input.setTextCursor(cursor)
            
            # 重要：不消耗事件，让它继续传递，确保被点击的控件（如按钮）能正常响应
            # Important: Don't consume the event, let it pass through to ensure clicked controls (like buttons) respond normally
        
        # 将事件传递给父类处理，保持所有控件的原有功能
        return super().eventFilter(obj, event)

    def update_font_sizes(self):
        """
        通过重新应用当前主题来更新UI中的字体大小。
        style_manager会处理动态字体大小的注入。
        """
        app = QApplication.instance()
        if app:
            from .utils.style_manager import apply_theme
            current_theme = self.settings_manager.get_current_theme()
            apply_theme(app, current_theme)


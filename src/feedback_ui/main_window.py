# feedback_ui/main_window.py
import os
import re  # 正则表达式 (Regular expressions)
import sys

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .dialogs.select_canned_response_dialog import SelectCannedResponseDialog
from .dialogs.settings_dialog import SettingsDialog

# --- 从子模块导入 (Imports from submodules) ---
from .utils.constants import (
    ContentItem,
    FeedbackResult,
    LAYOUT_HORIZONTAL,
    LAYOUT_VERTICAL,
    MIN_LEFT_AREA_WIDTH,
    MIN_LOWER_AREA_HEIGHT,
    MIN_RIGHT_AREA_WIDTH,
    MIN_UPPER_AREA_HEIGHT,
)
from .utils.image_processor import get_image_items_from_widgets
from .utils.settings_manager import SettingsManager
from .utils.ui_helpers import set_selection_colors

from .widgets.feedback_text_edit import FeedbackTextEdit
from .widgets.image_preview import ImagePreviewWidget
from .widgets.selectable_label import SelectableLabel


class FeedbackUI(QMainWindow):
    """
    Main window for the Interactive Feedback MCP application.
    交互式反馈MCP应用程序的主窗口。
    """

    def __init__(
        self,
        prompt: str,
        predefined_options: list[str] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.output_result = FeedbackResult(
            content=[]
        )  # 初始化为空结果 (Initialize with empty result)

        # --- 内部状态 (Internal State) ---
        self.image_widgets: dict[int, ImagePreviewWidget] = {}  # image_id: widget
        self.option_checkboxes: list[QCheckBox] = (
            []
        )  # Initialize here to prevent AttributeError
        self.next_image_id = 0
        self.canned_responses: list[str] = []
        self.dropped_file_references: dict[str, str] = {}  # display_name: file_path
        self.disable_auto_minimize = False
        self.window_pinned = False

        # 按钮文本的双语映射
        self.button_texts = {
            "submit_button": {"zh_CN": "提交", "en_US": "Submit"},
            "canned_responses_button": {"zh_CN": "常用语", "en_US": "Canned Responses"},
            "pin_window_button": {"zh_CN": "固定窗口", "en_US": "Pin Window"},
            "settings_button": {"zh_CN": "设置", "en_US": "Settings"},
        }

        # 工具提示的双语映射
        self.tooltip_texts = {
            "canned_responses_button": {
                "zh_CN": "选择或管理常用语",
                "en_US": "Select or manage canned responses",
            },
            "settings_button": {
                "zh_CN": "打开设置面板",
                "en_US": "Open settings panel",
            },
        }

        self.settings_manager = SettingsManager(self)

        self._setup_window()
        self._load_settings()

        self._create_ui_layout()
        self._connect_signals()

        self._apply_pin_state_on_load()

        # 延迟设置分割器样式，确保在窗口显示后应用
        QTimer.singleShot(100, self._ensure_splitter_visibility)

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
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "images", "feedback.png"
            )
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
            if 0 <= x < screen_width - 100 and 0 <= y < screen_height - 100:
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
        if state:
            self.restoreState(state)

        self.window_pinned = self.settings_manager.get_main_window_pinned()
        self._load_canned_responses_from_settings()

        # 加载字体大小设置
        self.update_font_sizes()

    def _create_ui_layout(self):
        """根据设置创建对应的UI布局"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 获取布局方向设置
        layout_direction = self.settings_manager.get_layout_direction()

        if layout_direction == LAYOUT_HORIZONTAL:
            self._create_horizontal_layout(central_widget)
        else:
            self._create_vertical_layout(central_widget)

    def _create_vertical_layout(self, central_widget: QWidget):
        """创建上下布局（当前布局）"""
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(15)

        # 创建垂直分割器
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)

        # 上部区域和下部区域
        self.upper_area = self._create_upper_area()
        self.lower_area = self._create_lower_area()

        self.main_splitter.addWidget(self.upper_area)
        self.main_splitter.addWidget(self.lower_area)

        self._setup_vertical_splitter_properties()
        main_layout.addWidget(self.main_splitter)

        # 强制设置分割器样式
        self._force_splitter_style()

        # 底部按钮和GitHub链接
        self._setup_bottom_bar(main_layout)
        self._create_submit_button(main_layout)
        self._create_github_link_area(main_layout)

        self._update_submit_button_text_status()

    def _create_horizontal_layout(self, central_widget: QWidget):
        """创建左右布局（混合布局）"""
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(15)

        # 创建上部分割区域
        upper_splitter_area = self._create_upper_splitter_area()
        main_layout.addWidget(upper_splitter_area, 1)  # 占据主要空间

        # 创建底部按钮区域（横跨全宽）
        self._setup_bottom_bar(main_layout)
        self._create_submit_button(main_layout)
        self._create_github_link_area(main_layout)

        self._update_submit_button_text_status()

    def _create_submit_button(self, parent_layout: QVBoxLayout):
        """创建提交按钮"""
        current_language = self.settings_manager.get_current_language()
        self.submit_button = QPushButton(
            self.button_texts["submit_button"][current_language]
        )
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(42)
        parent_layout.addWidget(self.submit_button)

    def _recreate_layout(self):
        """重新创建布局（用于布局方向切换）"""
        # 保存当前的文本内容和选项状态
        current_text = ""
        selected_options = []

        if hasattr(self, "text_input") and self.text_input:
            current_text = self.text_input.toPlainText()

        if hasattr(self, "option_checkboxes"):
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked() and i < len(self.predefined_options):
                    selected_options.append(i)

        # 重新创建UI布局
        self._create_ui_layout()

        # 恢复文本内容和选项状态
        if current_text and hasattr(self, "text_input"):
            self.text_input.setPlainText(current_text)

        if selected_options and hasattr(self, "option_checkboxes"):
            for i in selected_options:
                if i < len(self.option_checkboxes):
                    self.option_checkboxes[i].setChecked(True)

        # 重新连接信号
        self._connect_signals()

        # 应用主题和字体设置
        self.update_font_sizes()

        # 设置焦点
        self._set_initial_focus()

    def _create_upper_splitter_area(self) -> QWidget:
        """创建上部分割区域（左右布局专用）"""
        splitter_container = QWidget()
        splitter_layout = QVBoxLayout(splitter_container)
        splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建水平分割器
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("mainSplitter")
        self.main_splitter.setChildrenCollapsible(False)

        # 左侧：提示文字区域
        self.left_area = self._create_left_area()
        self.main_splitter.addWidget(self.left_area)

        # 右侧：选项+输入框区域
        self.right_area = self._create_right_area()
        self.main_splitter.addWidget(self.right_area)

        self._setup_horizontal_splitter_properties()
        splitter_layout.addWidget(self.main_splitter)

        # 强制设置分割器样式
        self._force_splitter_style()

        return splitter_container

    def _create_left_area(self) -> QWidget:
        """创建左侧区域（提示文字 + 选项）"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(10)

        # 添加提示文字区域，在左右布局中给予更多空间
        self._create_description_area(left_layout)

        # 在左右布局中，将选项区域添加到左侧
        if self.predefined_options:
            self._create_options_checkboxes(left_layout)

        return left_widget

    def _create_right_area(self) -> QWidget:
        """创建右侧区域（仅输入框）"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(10)

        # 在左右布局中，右侧只包含输入框区域
        # 选项区域已移动到左侧
        self._create_input_submission_area(right_layout)

        return right_widget

    def _create_upper_area(self) -> QWidget:
        """创建上部区域容器（提示文字 + 选项）"""
        upper_widget = QWidget()
        upper_layout = QVBoxLayout(upper_widget)
        upper_layout.setContentsMargins(15, 5, 15, 15)
        upper_layout.setSpacing(10)

        # 添加现有的描述区域
        self._create_description_area(upper_layout)

        # 添加选项复选框（如果有）
        if self.predefined_options:
            self._create_options_checkboxes(upper_layout)

        return upper_widget

    def _create_lower_area(self) -> QWidget:
        """创建下部区域容器（输入框）"""
        lower_widget = QWidget()
        lower_layout = QVBoxLayout(lower_widget)
        lower_layout.setContentsMargins(15, 5, 15, 15)
        lower_layout.setSpacing(10)

        # 添加输入提交区域
        self._create_input_submission_area(lower_layout)

        return lower_widget

    def _setup_vertical_splitter_properties(self):
        """配置垂直分割器属性"""
        self.main_splitter.setHandleWidth(6)
        self.upper_area.setMinimumHeight(MIN_UPPER_AREA_HEIGHT)
        self.lower_area.setMinimumHeight(MIN_LOWER_AREA_HEIGHT)

        saved_sizes = self.settings_manager.get_splitter_sizes()
        self.main_splitter.setSizes(saved_sizes)

        self.main_splitter.splitterMoved.connect(self._on_vertical_splitter_moved)
        self._setup_splitter_double_click()

    def _setup_horizontal_splitter_properties(self):
        """配置水平分割器属性"""
        self.main_splitter.setHandleWidth(6)
        self.left_area.setMinimumWidth(MIN_LEFT_AREA_WIDTH)
        self.right_area.setMinimumWidth(MIN_RIGHT_AREA_WIDTH)

        saved_sizes = self.settings_manager.get_horizontal_splitter_sizes()
        self.main_splitter.setSizes(saved_sizes)

        self.main_splitter.splitterMoved.connect(self._on_horizontal_splitter_moved)
        self._setup_splitter_double_click()

    def _force_splitter_style(self):
        """强制设置分割器样式，确保可见性"""
        # 获取当前主题的按钮悬停颜色，保持UI风格一致
        current_theme = self.settings_manager.get_current_theme()
        is_dark = current_theme == "dark"

        if is_dark:
            # 深色主题：使用与按钮悬停相同的颜色
            base_color = "#444444"
            hover_color = "#555555"
            pressed_color = "#333333"
        else:
            # 浅色主题：使用与按钮悬停相同的颜色
            base_color = "#cccccc"
            hover_color = "#dddddd"
            pressed_color = "#bbbbbb"

        # 精致的分割线样式：细线，与UI风格一致
        splitter_style = f"""
        QSplitter::handle:vertical {{
            background-color: {base_color} !important;
            border: none !important;
            border-radius: 2px;
            height: 6px !important;
            min-height: 6px !important;
            max-height: 6px !important;
            margin: 2px 4px;
        }}
        QSplitter::handle:vertical:hover {{
            background-color: {hover_color} !important;
        }}
        QSplitter::handle:vertical:pressed {{
            background-color: {pressed_color} !important;
        }}
        QSplitter::handle:horizontal {{
            width: 6px !important;
            min-width: 6px !important;
            max-width: 6px !important;
            background-color: {base_color} !important;
            border: none !important;
            border-radius: 2px;
            margin: 4px 2px;
        }}
        QSplitter::handle:horizontal:hover {{
            background-color: {hover_color} !important;
        }}
        QSplitter::handle:horizontal:pressed {{
            background-color: {pressed_color} !important;
        }}
        """
        self.main_splitter.setStyleSheet(splitter_style)

        # 设置精致的手柄宽度
        self.main_splitter.setHandleWidth(6)

        # 确保分割器手柄可见
        layout_direction = self.settings_manager.get_layout_direction()
        for i in range(self.main_splitter.count() - 1):
            handle = self.main_splitter.handle(i + 1)
            if handle:
                handle.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

                # 根据布局方向设置不同的尺寸属性
                if layout_direction == LAYOUT_HORIZONTAL:
                    # 水平分割器（左右布局）：设置宽度
                    handle.setMinimumWidth(6)
                    handle.setMaximumWidth(6)
                    # 设置与主题一致的背景色，保持与横向分割线相同的margin比例
                    handle.setStyleSheet(
                        f"background-color: {base_color}; border: none; border-radius: 2px; margin: 2px 0px;"
                    )
                else:
                    # 垂直分割器（上下布局）：设置高度
                    handle.setMinimumHeight(6)
                    handle.setMaximumHeight(6)
                    # 设置与主题一致的背景色
                    handle.setStyleSheet(
                        f"background-color: {base_color}; border: none; border-radius: 2px; margin: 2px 4px;"
                    )

    def _ensure_splitter_visibility(self):
        """确保分割器在窗口显示后可见"""
        if hasattr(self, "main_splitter"):
            # 重新应用样式
            self._force_splitter_style()

            # 强制刷新分割器
            self.main_splitter.update()

    def _setup_splitter_double_click(self):
        """设置分割器双击重置功能"""
        # 获取分割器手柄并设置双击事件
        handle = self.main_splitter.handle(1)
        if handle:
            handle.mouseDoubleClickEvent = self._reset_splitter_to_default

    def _reset_splitter_to_default(self, event):
        """双击分割器手柄时重置为默认比例"""
        layout_direction = self.settings_manager.get_layout_direction()

        if layout_direction == LAYOUT_HORIZONTAL:
            from .utils.constants import DEFAULT_HORIZONTAL_SPLITTER_RATIO

            self.main_splitter.setSizes(DEFAULT_HORIZONTAL_SPLITTER_RATIO)
            self._on_horizontal_splitter_moved(0, 0)
        else:
            from .utils.constants import DEFAULT_SPLITTER_RATIO

            self.main_splitter.setSizes(DEFAULT_SPLITTER_RATIO)
            self._on_vertical_splitter_moved(0, 0)

    def _on_vertical_splitter_moved(self, pos: int, index: int):
        """垂直分割器移动时保存状态"""
        sizes = self.main_splitter.sizes()
        self.settings_manager.set_splitter_sizes(sizes)
        self.settings_manager.set_splitter_state(self.main_splitter.saveState())

    def _on_horizontal_splitter_moved(self, pos: int, index: int):
        """水平分割器移动时保存状态"""
        sizes = self.main_splitter.sizes()
        self.settings_manager.set_horizontal_splitter_sizes(sizes)
        self.settings_manager.set_horizontal_splitter_state(
            self.main_splitter.saveState()
        )

    def _create_description_area(self, parent_layout: QVBoxLayout):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 在左右布局模式下不限制高度，让其充分利用可用空间
        # 修复：在上下布局中也移除高度限制，允许描述区域随分割器拖拽正常扩展
        layout_direction = self.settings_manager.get_layout_direction()
        if layout_direction == LAYOUT_HORIZONTAL:
            # 左右布局：不限制高度，让其充分利用可用空间
            pass
        else:
            # 上下布局：移除高度限制，允许描述区域正常扩展
            # 注释掉原有的高度限制：scroll_area.setMaximumHeight(200)
            pass

        desc_widget_container = QWidget()
        desc_layout = QVBoxLayout(desc_widget_container)
        desc_layout.setContentsMargins(15, 5, 15, 15)

        self.description_label = SelectableLabel(self.prompt, self)
        self.description_label.setProperty("class", "prompt-label")
        self.description_label.setWordWrap(True)
        # 在左右布局模式下，确保文字从顶部开始对齐
        if layout_direction == LAYOUT_HORIZONTAL:
            self.description_label.setAlignment(
                Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )
        desc_layout.addWidget(self.description_label)

        self.image_usage_label = SelectableLabel(
            "如果图片反馈异常，建议切换Claude 3.5 Sonnet模型。", self
        )
        self.image_usage_label.setWordWrap(True)
        self.image_usage_label.setVisible(False)
        desc_layout.addWidget(self.image_usage_label)

        self.status_label = SelectableLabel("", self)
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setVisible(False)
        desc_layout.addWidget(self.status_label)

        # 在左右布局模式下，添加弹性空间确保内容顶部对齐
        if layout_direction == LAYOUT_HORIZONTAL:
            desc_layout.addStretch()

        scroll_area.setWidget(desc_widget_container)
        parent_layout.addWidget(scroll_area)

    def _create_options_checkboxes(self, parent_layout: QVBoxLayout):
        self.option_checkboxes: list[QCheckBox] = []
        options_frame = QFrame()

        # 修复：设置选项框架的大小策略，防止异常扩大
        options_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        options_layout = QVBoxLayout(options_frame)
        # 使用负边距补偿复选框宽度(~20px)和间距(5px)，实现与提示文字的精确对齐
        options_layout.setContentsMargins(-10, 0, 0, 0)
        # 修复：设置固定间距，防止选项间距异常扩大
        options_layout.setSpacing(8)  # 从2改为8，提供合适的固定间距

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

    def _create_input_submission_area(self, parent_layout: QVBoxLayout):
        self.text_input = FeedbackTextEdit(self)
        # 设置包含拖拽和快捷键提示的placeholder text
        placeholder_text = "在此输入反馈... (可拖拽文件和图片到输入框，Enter提交反馈，Shift+Enter换行，Ctrl+V复制剪切板信息)"
        self.text_input.setPlaceholderText(placeholder_text)

        # 连接焦点事件来动态控制placeholder显示
        self.text_input.focusInEvent = self._on_text_input_focus_in
        self.text_input.focusOutEvent = self._on_text_input_focus_out

        # QTextEdit should expand vertically, so we give it a stretch factor
        parent_layout.addWidget(self.text_input, 1)

    def _setup_bottom_bar(self, parent_layout: QVBoxLayout):
        """Creates the bottom bar with canned responses, pin, and settings buttons."""
        bottom_bar_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar_widget)
        bottom_layout.setContentsMargins(0, 3, 0, 3)
        bottom_layout.setSpacing(10)

        current_language = self.settings_manager.get_current_language()

        # 使用语言相关的文本
        self.canned_responses_button = QPushButton(
            self.button_texts["canned_responses_button"][current_language]
        )
        self.canned_responses_button.setObjectName("secondary_button")
        self.canned_responses_button.setToolTip(
            self.tooltip_texts["canned_responses_button"][current_language]
        )

        # 为常用语按钮添加hover事件处理
        self.canned_responses_button.enterEvent = self._on_canned_responses_button_enter
        self.canned_responses_button.leaveEvent = self._on_canned_responses_button_leave

        # 初始化hover预览窗口变量
        self.canned_responses_preview_window = None

        bottom_layout.addWidget(self.canned_responses_button)

        self.pin_window_button = QPushButton(
            self.button_texts["pin_window_button"][current_language]
        )
        self.pin_window_button.setCheckable(True)
        self.pin_window_button.setObjectName("secondary_button")
        bottom_layout.addWidget(self.pin_window_button)

        # --- Settings Button (设置按钮) ---
        self.settings_button = QPushButton(
            self.button_texts["settings_button"][current_language]
        )
        self.settings_button.setObjectName("secondary_button")
        self.settings_button.setToolTip(
            self.tooltip_texts["settings_button"][current_language]
        )
        bottom_layout.addWidget(self.settings_button)

        bottom_layout.addStretch()  # Pushes buttons to the left

        parent_layout.addWidget(bottom_bar_widget)

    def _create_github_link_area(self, parent_layout: QVBoxLayout):
        """Creates the GitHub link at the bottom."""
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setContentsMargins(0, 5, 0, 0)

        github_label = QLabel(
            "<a href='https://github.com/lucas-710/interactive-feedback-mcp'>GitHub</a>"
        )
        github_label.setOpenExternalLinks(True)
        # 启用文本选择功能
        github_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        # 添加小字体样式
        github_label.setStyleSheet("font-size: 10pt; color: #888888;")

        # 设置选择文本时的高亮颜色为灰色
        set_selection_colors(github_label)

        github_layout.addStretch()
        github_layout.addWidget(github_label)
        github_layout.addStretch()
        parent_layout.addWidget(github_container)

    def _connect_signals(self):
        self.text_input.textChanged.connect(self._update_submit_button_text_status)
        self.canned_responses_button.clicked.connect(self._show_canned_responses_dialog)
        self.pin_window_button.toggled.connect(self._toggle_pin_window_action)
        self.settings_button.clicked.connect(self.open_settings_dialog)
        self.submit_button.clicked.connect(self._prepare_and_submit_feedback)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.WindowDeactivate:
            if (
                not self.window_pinned
                and self.isVisible()
                and not self.isMinimized()
                and not self.disable_auto_minimize
            ):
                QTimer.singleShot(100, self.showMinimized)
        return super().event(event)

    def closeEvent(self, event: QEvent):
        # 保存分割器状态
        if hasattr(self, "main_splitter"):
            sizes = self.main_splitter.sizes()
            self.settings_manager.set_splitter_sizes(sizes)
            self.settings_manager.set_splitter_state(self.main_splitter.saveState())

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

    def _update_submit_button_text_status(self):
        has_text = bool(self.text_input.toPlainText().strip())
        has_images = bool(self.image_widgets)

        has_options_selected = any(cb.isChecked() for cb in self.option_checkboxes)

        # 修改：按钮应始终可点击，即使没有内容，以支持提交空反馈
        # self.submit_button.setEnabled(has_text or has_images or has_options_selected)
        self.submit_button.setEnabled(True)

    def _show_canned_responses_dialog(self):
        self.disable_auto_minimize = True
        # 禁用预览功能，防止对话框触发预览窗口
        self._preview_disabled = True
        # 隐藏任何现有的预览窗口
        self._hide_canned_responses_preview()

        dialog = SelectCannedResponseDialog(self.canned_responses, self)
        dialog.exec()

        self.disable_auto_minimize = False
        # 延迟重新启用预览功能，确保双击操作完全完成且鼠标事件处理完毕
        QTimer.singleShot(500, self._re_enable_preview)
        # After the dialog closes, settings are updated internally by the dialog.
        # We just need to reload them here.
        self._load_canned_responses_from_settings()

    def _re_enable_preview(self):
        """重新启用预览功能"""
        self._preview_disabled = False

    def open_settings_dialog(self):
        """Opens the settings dialog."""
        self.disable_auto_minimize = True
        dialog = SettingsDialog(self)
        dialog.exec()
        self.disable_auto_minimize = False

    def _apply_pin_state_on_load(self):
        # 从设置中加载固定窗口状态，但不改变按钮样式
        self.pin_window_button.setChecked(self.window_pinned)

        # 应用窗口标志 - 使用明确的标志组合，确保关闭按钮等基本功能不受影响
        if self.window_pinned:
            # 固定窗口：添加置顶标志，保留所有标准窗口功能
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
            # 设置提示文本
            self.pin_window_button.setToolTip(
                "固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)"
            )
            self.pin_window_button.setObjectName("pin_window_active")
        else:
            # 标准窗口：使用标准窗口标志，确保所有按钮功能正常
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.WindowCloseButtonHint
            )
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

        # 保存当前窗口几何信息
        current_geometry = self.saveGeometry()

        # 设置窗口标志 - 使用明确的标志组合，确保关闭按钮等基本功能不受影响
        if self.window_pinned:
            # 固定窗口：添加置顶标志，保留所有标准窗口功能
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.WindowCloseButtonHint
                | Qt.WindowType.WindowStaysOnTopHint
            )
            # 只有当按钮被激活时才改变样式
            self.pin_window_button.setObjectName("pin_window_active")
            self.pin_window_button.setToolTip(
                "固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)"
            )
        else:
            # 取消固定：使用标准窗口标志，确保所有按钮功能正常
            self.setWindowFlags(
                Qt.WindowType.Window
                | Qt.WindowType.WindowTitleHint
                | Qt.WindowType.WindowSystemMenuHint
                | Qt.WindowType.WindowMinimizeButtonHint
                | Qt.WindowType.WindowMaximizeButtonHint
                | Qt.WindowType.WindowCloseButtonHint
            )
            # 恢复为普通按钮样式
            self.pin_window_button.setObjectName("secondary_button")
            self.pin_window_button.setToolTip("")

        # 只应用样式变化到固定窗口按钮，避免影响其他按钮
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        self.pin_window_button.update()

        # 重新显示窗口并恢复几何信息（因为改变了窗口标志）
        self.show()
        self.restoreGeometry(current_geometry)

    def add_image_preview(self, pixmap: QPixmap) -> int | None:
        if pixmap and not pixmap.isNull():
            image_id = self.next_image_id
            self.next_image_id += 1

            image_widget = ImagePreviewWidget(
                pixmap, image_id, self.text_input.images_container
            )
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
        final_content_list: list[ContentItem] = []
        feedback_plain_text = self.text_input.toPlainText().strip()

        # 获取选中的选项
        selected_options = []
        for i, checkbox in enumerate(self.option_checkboxes):
            if checkbox.isChecked() and i < len(self.predefined_options):
                # 使用预定义选项列表中的文本
                selected_options.append(self.predefined_options[i])

        combined_text_parts = []
        if selected_options:
            combined_text_parts.append("; ".join(selected_options))
        if feedback_plain_text:
            combined_text_parts.append(feedback_plain_text)

        final_text = "\n".join(combined_text_parts).strip()
        # 允许提交空内容，即使 final_text 为空
        if final_text:
            final_content_list.append({"type": "text", "text": final_text})

        image_items = get_image_items_from_widgets(self.image_widgets)
        final_content_list.extend(image_items)

        # 处理文件引用（恢复之前移除的代码）
        current_text_content_for_refs = self.text_input.toPlainText()
        file_references = {
            k: v
            for k, v in self.dropped_file_references.items()
            if k in current_text_content_for_refs
        }

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
        if hasattr(self, "text_input") and self.text_input:
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
            self.description_label.setText(
                self._filter_text_by_language(self.prompt, current_lang)
            )

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
                            child.setText(
                                self._filter_text_by_language(
                                    self.predefined_options[i], current_lang
                                )
                            )
                            break

        # 更新按钮文本
        self._update_button_texts(current_lang)

    def _update_button_texts(self, language_code):
        """根据当前语言更新所有按钮的文本"""
        # 更新提交按钮
        if hasattr(self, "submit_button") and self.submit_button:
            self.submit_button.setText(
                self.button_texts["submit_button"].get(language_code, "提交")
            )

        # 更新底部按钮
        if hasattr(self, "canned_responses_button") and self.canned_responses_button:
            self.canned_responses_button.setText(
                self.button_texts["canned_responses_button"].get(
                    language_code, "常用语"
                )
            )
            self.canned_responses_button.setToolTip(
                self.tooltip_texts["canned_responses_button"].get(
                    language_code, "选择或管理常用语"
                )
            )

        if hasattr(self, "pin_window_button") and self.pin_window_button:
            # 保存当前按钮的样式类名
            current_object_name = self.pin_window_button.objectName()
            self.pin_window_button.setText(
                self.button_texts["pin_window_button"].get(language_code, "固定窗口")
            )
            # 单独刷新固定窗口按钮的样式，避免影响其他按钮
            self.pin_window_button.style().unpolish(self.pin_window_button)
            self.pin_window_button.style().polish(self.pin_window_button)
            self.pin_window_button.update()

        if hasattr(self, "settings_button") and self.settings_button:
            self.settings_button.setText(
                self.button_texts["settings_button"].get(language_code, "设置")
            )
            self.settings_button.setToolTip(
                self.tooltip_texts["settings_button"].get(language_code, "打开设置面板")
            )

        # 单独为提交按钮、常用语按钮和设置按钮刷新样式
        for btn in [
            self.submit_button,
            self.canned_responses_button,
            self.settings_button,
        ]:
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
            match = re.match(r"^(.*?)[\s]*[\(（].*?[\)）](\s*|$)", text)
            if match:
                return match.group(1).strip()

            # 格式2：中英文之间有破折号或其他分隔符 "中文 - English"
            match = re.match(r"^(.*?)[\s]*[-—–][\s]*[A-Za-z].*?$", text)
            if match:
                return match.group(1).strip()

            # 如果都不匹配，可能是纯中文，直接返回
            return text

        # 如果是英文模式
        elif lang_code == "en_US":
            # 格式1：标准括号格式，提取括号内的英文
            match = re.search(r"[\(（](.*?)[\)）]", text)
            if match:
                return match.group(1).strip()

            # 格式2：中英文之间有破折号或其他分隔符 "中文 - English"
            match = re.search(r"[-—–][\s]*(.*?)$", text)
            if match and re.search(r"[A-Za-z]", match.group(1)):
                return match.group(1).strip()

            # 如果上述格式都不匹配，检查是否包含英文单词
            if re.search(r"[A-Za-z]{2,}", text):  # 至少包含2个连续英文字母
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

    def _on_text_input_focus_in(self, event):
        """输入框获得焦点时的处理 - 隐藏placeholder text"""
        # 调用原始的focusInEvent
        FeedbackTextEdit.focusInEvent(self.text_input, event)

        # 如果输入框为空，临时清除placeholder text以避免显示
        if not self.text_input.toPlainText().strip():
            self.text_input.setPlaceholderText("")

    def _on_text_input_focus_out(self, event):
        """输入框失去焦点时的处理 - 恢复placeholder text"""
        # 调用原始的focusOutEvent
        FeedbackTextEdit.focusOutEvent(self.text_input, event)

        # 如果输入框为空，恢复placeholder text
        if not self.text_input.toPlainText().strip():
            placeholder_text = "在此输入反馈... (可拖拽文件和图片到输入框，Enter提交反馈，Shift+Enter换行，Ctrl+V复制剪切板信息)"
            self.text_input.setPlaceholderText(placeholder_text)

    def _on_canned_responses_button_enter(self, event):
        """常用语按钮鼠标进入事件 - 显示常用语预览"""
        # 调用原始的enterEvent
        QPushButton.enterEvent(self.canned_responses_button, event)

        # 如果有常用语且没有禁用预览，显示预览窗口
        if self.canned_responses and not getattr(self, "_preview_disabled", False):
            self._show_canned_responses_preview()

    def _on_canned_responses_button_leave(self, event):
        """常用语按钮鼠标离开事件 - 延迟隐藏常用语预览"""
        # 调用原始的leaveEvent
        QPushButton.leaveEvent(self.canned_responses_button, event)

        # 延迟隐藏预览窗口，给用户时间移动到预览窗口
        QTimer.singleShot(200, self._delayed_hide_preview)

    def _on_preview_window_enter(self, event):
        """预览窗口鼠标进入事件 - 取消隐藏计时器"""
        # 取消延迟隐藏
        pass

    def _on_preview_window_leave(self, event):
        """预览窗口鼠标离开事件 - 隐藏预览窗口"""
        # 立即隐藏预览窗口
        self._hide_canned_responses_preview()

    def _delayed_hide_preview(self):
        """延迟隐藏预览窗口 - 检查鼠标是否在预览窗口内"""
        if (
            self.canned_responses_preview_window
            and self.canned_responses_preview_window.isVisible()
        ):
            # 获取鼠标位置
            from PySide6.QtGui import QCursor

            mouse_pos = QCursor.pos()

            # 检查鼠标是否在预览窗口内
            preview_rect = self.canned_responses_preview_window.geometry()
            if not preview_rect.contains(mouse_pos):
                # 鼠标不在预览窗口内，隐藏窗口
                self._hide_canned_responses_preview()

    def _show_canned_responses_preview(self):
        """显示常用语预览窗口"""
        if not self.canned_responses:
            return

        # 如果预览窗口已存在，先关闭
        if self.canned_responses_preview_window:
            self.canned_responses_preview_window.close()
            self.canned_responses_preview_window = None

        # 创建预览窗口
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont

        self.canned_responses_preview_window = QWidget()
        self.canned_responses_preview_window.setWindowFlags(
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint
        )
        self.canned_responses_preview_window.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )

        # 为预览窗口添加hover事件处理，支持鼠标移动到预览窗口
        self.canned_responses_preview_window.enterEvent = self._on_preview_window_enter
        self.canned_responses_preview_window.leaveEvent = self._on_preview_window_leave

        # 主布局
        main_layout = QVBoxLayout(self.canned_responses_preview_window)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # 滚动内容容器
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 获取当前主题
        current_theme = self.settings_manager.get_current_theme()
        is_dark = current_theme == "dark"

        # 根据主题设置颜色
        if is_dark:
            bg_color = "#2D2D2D"
            border_color = "#3A3A3A"
            text_color = "#CCCCCC"
            item_bg = "#333333"
            item_border = "#444444"
            item_hover_bg = "#0078d4"
            item_hover_border = "#1890ff"
            more_text_color = "#888888"
        else:
            bg_color = "#FFFFFF"
            border_color = "#CCCCCC"
            text_color = "#333333"
            item_bg = "#F8F9FA"
            item_border = "#E0E0E0"
            item_hover_bg = "#E8F4FD"
            item_hover_border = "#0078D4"
            more_text_color = "#666666"

        # 添加所有常用语项目
        for i, response in enumerate(self.canned_responses):
            # 限制显示长度，过长的文本进行截断
            display_text = response if len(response) <= 60 else response[:57] + "..."

            response_label = QLabel(display_text)
            response_label.setWordWrap(True)
            response_label.setStyleSheet(
                f"""
                QLabel {{
                    padding: 8px 12px;
                    border-radius: 6px;
                    background-color: {item_bg};
                    color: {text_color};
                    border: 1px solid {item_border};
                    margin: 2px 0px;
                }}
                QLabel:hover {{
                    background-color: {item_hover_bg};
                    border-color: {item_hover_border};
                    color: white;
                }}
            """
            )
            response_label.setCursor(Qt.CursorShape.PointingHandCursor)

            # 为每个标签添加点击事件
            response_label.mousePressEvent = (
                lambda event, text=response: self._on_preview_item_clicked(text)
            )

            layout.addWidget(response_label)

        # 设置滚动内容
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # 设置滚动区域样式
        scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                background-color: {bg_color};
                border: none;
                border-radius: 10px;
            }}
            QScrollBar:vertical {{
                background-color: {bg_color};
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {item_border};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {item_hover_border};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
        )

        # 设置窗口样式（包含阴影效果）
        self.canned_responses_preview_window.setStyleSheet(
            f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
        """
        )

        # 计算位置（在按钮上方显示）
        button_pos = self.canned_responses_button.mapToGlobal(
            self.canned_responses_button.rect().topLeft()
        )
        preview_width = 350

        # 计算高度：如果常用语超过10个，限制最大高度并启用滚动
        max_display_items = 10
        if len(self.canned_responses) > max_display_items:
            # 限制最大高度，大约10个项目的高度
            preview_height = min(
                400, max_display_items * 50 + 20
            )  # 每个项目约50px高度，加上边距
        else:
            # 使用实际内容高度
            preview_height = scroll_content.sizeHint().height() + 20

        # 在按钮上方显示
        x = button_pos.x()
        y = button_pos.y() - preview_height - 10

        self.canned_responses_preview_window.setGeometry(
            x, y, preview_width, preview_height
        )
        self.canned_responses_preview_window.show()

    def _hide_canned_responses_preview(self):
        """隐藏常用语预览窗口"""
        if self.canned_responses_preview_window:
            self.canned_responses_preview_window.close()
            self.canned_responses_preview_window = None

    def _on_preview_item_clicked(self, text):
        """预览项目被点击时插入到输入框"""
        if self.text_input:
            self.text_input.insertPlainText(text)
            self.text_input.setFocus()

            # 移动光标到末尾
            cursor = self.text_input.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.text_input.setTextCursor(cursor)

        # 隐藏预览窗口
        self._hide_canned_responses_preview()

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

            # 主题切换后重新应用分割器样式，确保颜色与新主题一致
            if hasattr(self, "main_splitter"):
                QTimer.singleShot(50, self._force_splitter_style)

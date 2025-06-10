from PySide6.QtCore import QCoreApplication, QEvent, QTranslator
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QGridLayout,
)

from ..utils.settings_manager import SettingsManager
from ..utils.style_manager import apply_theme


class TerminalItemWidget(QWidget):
    """终端项组件 - 封装终端名称、单选按钮和浏览按钮，防止布局相互影响"""

    def __init__(
        self,
        terminal_type: str,
        terminal_info: dict,
        terminal_manager,
        settings_manager,
        parent=None,
    ):
        super().__init__(parent)
        self.terminal_type = terminal_type
        self.terminal_info = terminal_info
        self.terminal_manager = terminal_manager
        self.settings_manager = settings_manager
        self.parent_dialog = parent

        # 设置固定高度，防止布局变化
        self.setFixedHeight(60)

        self._setup_ui()
        self._load_current_path()

    def _setup_ui(self):
        """设置UI布局 - 稳定的组件化布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 2, 0, 2)
        main_layout.setSpacing(3)

        # 第一行：单选按钮 + 浏览按钮
        first_row = QWidget()
        first_row.setFixedHeight(25)  # 固定高度
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setContentsMargins(0, 0, 0, 0)

        # 单选按钮
        self.radio = QRadioButton(self.terminal_info["display_name"])
        self.radio.toggled.connect(self._on_radio_changed)

        # 浏览按钮
        self.browse_button = QPushButton("浏览...")
        self.browse_button.setFixedSize(50, 20)
        self.browse_button.setStyleSheet(
            "font-size: 8pt; padding: 2px; padding-top: -3px;"
        )  # 向上调整文字位置
        self.browse_button.clicked.connect(self._browse_path)

        first_row_layout.addWidget(self.radio)
        first_row_layout.addStretch()
        first_row_layout.addWidget(self.browse_button)

        # 第二行：路径输入框
        second_row = QWidget()
        second_row.setFixedHeight(25)  # 固定高度
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setContentsMargins(20, 0, 0, 0)  # 左侧缩进

        # 路径输入框
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(False)
        self.path_edit.setCursorPosition(0)
        self.path_edit.textChanged.connect(self._on_path_changed)

        # 设置样式
        self._apply_theme_style()

        second_row_layout.addWidget(self.path_edit)

        main_layout.addWidget(first_row)
        main_layout.addWidget(second_row)

    def _load_current_path(self):
        """加载当前路径"""
        detected_path = self.terminal_manager.get_terminal_command(self.terminal_type)
        custom_path = self.settings_manager.get_terminal_path(self.terminal_type)
        path_text = custom_path if custom_path else detected_path
        self.path_edit.setText(path_text)
        self.path_edit.setCursorPosition(0)

    def _apply_theme_style(self):
        """应用主题样式"""
        current_theme = self.settings_manager.get_current_theme()
        if current_theme == "dark":
            self.path_edit.setStyleSheet(
                "QLineEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #555555; padding: 4px; }"
            )
        else:
            self.path_edit.setStyleSheet(
                "QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; padding: 4px; }"
            )

    def _on_radio_changed(self, checked):
        """单选按钮状态改变"""
        if checked:
            self.settings_manager.set_default_terminal_type(self.terminal_type)

    def _on_path_changed(self, text):
        """路径改变时的处理"""
        self.settings_manager.set_terminal_path(self.terminal_type, text.strip())
        self.path_edit.setCursorPosition(0)  # 保持光标在开头

    def _browse_path(self):
        """浏览文件路径"""
        from PySide6.QtWidgets import QFileDialog
        import os

        current_path = self.path_edit.text().strip()
        start_dir = (
            os.path.dirname(current_path)
            if current_path and os.path.exists(current_path)
            else ""
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"选择 {self.terminal_info['display_name']} 路径",
            start_dir,
            "可执行文件 (*.exe);;所有文件 (*.*)",
        )

        if file_path:
            self.path_edit.setText(file_path)
            self.settings_manager.set_terminal_path(self.terminal_type, file_path)

    def get_radio_button(self):
        """获取单选按钮，用于按钮组管理"""
        return self.radio

    def set_checked(self, checked):
        """设置选中状态"""
        self.radio.setChecked(checked)

    def update_texts(self, texts, current_lang):
        """更新文本"""
        if "browse_button" in texts:
            self.browse_button.setText(texts["browse_button"][current_lang])

        # 更新终端名称
        terminal_name_key = f"{self.terminal_type}_name"
        if terminal_name_key in texts:
            self.radio.setText(texts[terminal_name_key][current_lang])


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("设置"))
        self.settings_manager = SettingsManager(self)
        self.layout = QVBoxLayout(self)

        # 保存当前翻译器的引用
        self.translator = QTranslator()
        # 记录当前语言状态，方便切换时判断
        self.current_language = self.settings_manager.get_current_language()

        # 双语文本映射
        self.texts = {
            "title": {"zh_CN": "设置", "en_US": "Settings"},
            # 重新组织的设置组
            "theme_layout_group": {"zh_CN": "主题布局", "en_US": "Theme & Layout"},
            "dark_mode": {"zh_CN": "深色模式", "en_US": "Dark Mode"},
            "light_mode": {"zh_CN": "浅色模式", "en_US": "Light Mode"},
            "vertical_layout": {"zh_CN": "上下布局", "en_US": "Vertical Layout"},
            "horizontal_layout": {"zh_CN": "左右布局", "en_US": "Horizontal Layout"},
            "language_font_group": {"zh_CN": "语言字体", "en_US": "Language & Font"},
            "chinese": {"zh_CN": "中文", "en_US": "Chinese"},
            "english": {"zh_CN": "English", "en_US": "English"},
            "prompt_font_size": {
                "zh_CN": "提示区文字大小",
                "en_US": "Prompt Text Size",
            },
            "options_font_size": {
                "zh_CN": "选项区文字大小",
                "en_US": "Options Text Size",
            },
            "input_font_size": {"zh_CN": "输入框文字大小", "en_US": "Input Font Size"},
            # 终端设置相关文本
            "terminal_group": {"zh_CN": "终端设置", "en_US": "Terminal Settings"},
            "default_terminal": {"zh_CN": "默认终端:", "en_US": "Default Terminal:"},
            "terminal_path": {"zh_CN": "路径:", "en_US": "Path:"},
            "browse_button": {"zh_CN": "浏览...", "en_US": "Browse..."},
            "path_invalid": {
                "zh_CN": "路径无效：文件不存在",
                "en_US": "Invalid path: file does not exist",
            },
            # 终端类型名称
            "powershell_name": {
                "zh_CN": "PowerShell (pwsh)",
                "en_US": "PowerShell (pwsh)",
            },
            "gitbash_name": {"zh_CN": "Git Bash (bash)", "en_US": "Git Bash (bash)"},
            "cmd_name": {"zh_CN": "命令提示符 (cmd)", "en_US": "Command Prompt (cmd)"},
            # V3.2 新增：交互模式设置
            "interaction_group": {"zh_CN": "交互模式", "en_US": "Interaction Mode"},
            "simple_mode": {"zh_CN": "精简模式", "en_US": "Simple Mode"},
            "full_mode": {"zh_CN": "完整模式", "en_US": "Full Mode"},
            "simple_mode_desc": {
                "zh_CN": "仅显示AI提供的选项",
                "en_US": "Show only AI-provided options",
            },
            "full_mode_desc": {
                "zh_CN": "智能生成选项 + 用户自定义后备",
                "en_US": "Smart option generation + custom fallback",
            },
            # V3.2 新增：功能开关
            "enable_rule_engine": {
                "zh_CN": "启用规则引擎",
                "en_US": "Enable Rule Engine",
            },
            "enable_custom_options": {
                "zh_CN": "启用自定义选项",
                "en_US": "Enable Custom Options",
            },
            "fallback_options_group": {
                "zh_CN": "自定义后备选项",
                "en_US": "Custom Fallback Options",
            },
            "fallback_options_desc": {
                "zh_CN": "当AI未提供选项且无法自动生成时显示的选项：",
                "en_US": "Options shown when AI provides none and auto-generation fails:",
            },
            "option_label": {"zh_CN": "选项", "en_US": "Option"},
            "expand_options": {"zh_CN": "展开选项设置", "en_US": "Expand Options"},
            "collapse_options": {"zh_CN": "收起选项设置", "en_US": "Collapse Options"},
        }

        self._setup_ui()

        # 初始更新文本
        self._update_texts()

    def _setup_ui(self):
        self._setup_theme_layout_group()  # 整合主题和布局
        self._setup_language_font_group()  # 整合语言和字体
        self._setup_interaction_group()  # V3.2 新增
        self._setup_terminal_group()

        # 添加 OK 和 Cancel 按钮 - 自定义布局实现左右对称
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)  # 顶部留一些间距

        # 创建确定按钮（左对齐）
        self.ok_button = QPushButton("")  # 稍后设置文本
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept)

        # 创建取消按钮（右对齐）
        self.cancel_button = QPushButton("")  # 稍后设置文本
        self.cancel_button.clicked.connect(self.reject)

        # 布局：确定按钮左对齐，中间弹性空间，取消按钮右对齐
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()  # 弹性空间
        button_layout.addWidget(self.cancel_button)

        self.layout.addWidget(button_container)

    def _setup_theme_layout_group(self):
        """整合主题和布局设置 - 2x2网格布局"""
        self.theme_layout_group = QGroupBox("")  # 稍后设置文本
        grid_layout = QGridLayout()

        # 获取当前设置
        current_theme = self.settings_manager.get_current_theme()
        from ..utils.constants import LAYOUT_HORIZONTAL, LAYOUT_VERTICAL

        current_layout = self.settings_manager.get_layout_direction()

        # 第一行：主题设置
        self.dark_theme_radio = QRadioButton("")  # 稍后设置文本
        self.light_theme_radio = QRadioButton("")  # 稍后设置文本

        if current_theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)

        # 第二行：布局设置
        self.vertical_layout_radio = QRadioButton("")  # 稍后设置文本
        self.horizontal_layout_radio = QRadioButton("")  # 稍后设置文本

        if current_layout == LAYOUT_HORIZONTAL:
            self.horizontal_layout_radio.setChecked(True)
        else:
            self.vertical_layout_radio.setChecked(True)

        # 网格布局：左上(深色) 右上(浅色) 左下(上下) 右下(左右)
        grid_layout.addWidget(self.dark_theme_radio, 0, 0)
        grid_layout.addWidget(self.light_theme_radio, 0, 1)
        grid_layout.addWidget(self.vertical_layout_radio, 1, 0)
        grid_layout.addWidget(self.horizontal_layout_radio, 1, 1)

        # 连接信号
        self.dark_theme_radio.toggled.connect(
            lambda checked: self.switch_theme("dark", checked)
        )
        self.light_theme_radio.toggled.connect(
            lambda checked: self.switch_theme("light", checked)
        )
        self.vertical_layout_radio.toggled.connect(
            lambda checked: self.switch_layout(LAYOUT_VERTICAL, checked)
        )
        self.horizontal_layout_radio.toggled.connect(
            lambda checked: self.switch_layout(LAYOUT_HORIZONTAL, checked)
        )

        self.theme_layout_group.setLayout(grid_layout)
        self.layout.addWidget(self.theme_layout_group)

    def _setup_language_font_group(self):
        """整合语言和字体设置"""
        self.language_font_group = QGroupBox("")  # 稍后设置文本
        layout = QVBoxLayout()

        # 第一行：语言设置
        lang_layout = QHBoxLayout()
        self.chinese_radio = QRadioButton("")  # 稍后设置文本
        self.english_radio = QRadioButton("")  # 稍后设置文本

        current_lang = self.settings_manager.get_current_language()
        if current_lang == "zh_CN":
            self.chinese_radio.setChecked(True)
        else:
            self.english_radio.setChecked(True)

        # 连接语言切换信号
        self.chinese_radio.toggled.connect(
            lambda checked: self.switch_language_radio("zh_CN", checked)
        )
        self.english_radio.toggled.connect(
            lambda checked: self.switch_language_radio("en_US", checked)
        )

        lang_layout.addWidget(self.chinese_radio)
        lang_layout.addWidget(self.english_radio)
        layout.addLayout(lang_layout)

        # 字体大小设置 - 更紧凑的布局
        font_sizes = [
            (
                "prompt_font_size",
                self.settings_manager.get_prompt_font_size(),
                12,
                24,
                self.update_prompt_font_size,
            ),
            (
                "options_font_size",
                self.settings_manager.get_options_font_size(),
                10,
                20,
                self.update_options_font_size,
            ),
            (
                "input_font_size",
                self.settings_manager.get_input_font_size(),
                10,
                20,
                self.update_input_font_size,
            ),
        ]

        self.font_labels = {}
        self.font_spinners = {}

        for key, current_value, min_val, max_val, callback in font_sizes:
            font_layout = QHBoxLayout()

            # 标签 - 调小字体
            label = QLabel("")  # 稍后设置文本
            label.setStyleSheet("font-size: 10pt;")  # 调小字体
            self.font_labels[key] = label

            # 数值选择器
            spinner = QSpinBox()
            spinner.setRange(min_val, max_val)
            spinner.setValue(current_value)
            spinner.valueChanged.connect(callback)
            self.font_spinners[key] = spinner

            font_layout.addWidget(label)
            font_layout.addWidget(spinner)
            layout.addLayout(font_layout)

        self.language_font_group.setLayout(layout)
        self.layout.addWidget(self.language_font_group)

    def _setup_interaction_group(self):
        """V3.2 新增：设置交互模式配置区域 - 简洁布局"""
        self.interaction_group = QGroupBox("")  # 稍后设置文本
        interaction_layout = QVBoxLayout()

        # 获取当前配置和UI工厂 - 合并导入
        from src.interactive_feedback_server.utils import safe_get_config
        from ..utils.ui_factory import create_radio_button_pair

        config, current_mode = safe_get_config()

        checked_index = 1 if current_mode == "full" else 0
        self.simple_mode_radio, self.full_mode_radio, mode_layout = (
            create_radio_button_pair(
                "",
                "",  # 文本稍后设置
                checked_index=checked_index,
                callback1=lambda checked: self._on_display_mode_changed(
                    "simple", checked
                ),
                callback2=lambda checked: self._on_display_mode_changed(
                    "full", checked
                ),
            )
        )

        interaction_layout.addLayout(mode_layout)

        # 第二行：功能开关 - 左右布局
        self._setup_feature_toggles(interaction_layout, config)

        # 第三行：自定义后备选项 - 简洁设计
        self._setup_simple_fallback_options(interaction_layout, config)

        self.interaction_group.setLayout(interaction_layout)
        self.layout.addWidget(self.interaction_group)

    def _setup_feature_toggles(self, parent_layout, config):
        """V3.2 新增：设置功能开关 - 启用规则引擎和自定义选项"""
        # 获取功能状态和UI工厂 - 合并导入
        from src.interactive_feedback_server.utils import safe_get_feature_states
        from ..utils.ui_factory import create_toggle_radio_button

        rule_engine_enabled, custom_options_enabled = safe_get_feature_states(config)

        toggles_layout = QHBoxLayout()

        self.enable_rule_engine_radio = create_toggle_radio_button(
            "", rule_engine_enabled, self._on_rule_engine_toggled
        )
        self.enable_custom_options_radio = create_toggle_radio_button(
            "", custom_options_enabled, self._on_custom_options_toggled
        )

        toggles_layout.addWidget(self.enable_rule_engine_radio)
        toggles_layout.addWidget(self.enable_custom_options_radio)

        parent_layout.addLayout(toggles_layout)

    def _on_rule_engine_toggled(self, checked: bool):
        """规则引擎开关切换处理"""
        try:
            from src.interactive_feedback_server.utils import set_rule_engine_enabled

            set_rule_engine_enabled(checked)
        except Exception as e:
            from src.interactive_feedback_server.utils import handle_config_error

            handle_config_error("设置规则引擎状态", e)

    def _on_custom_options_toggled(self, checked: bool):
        """自定义选项开关切换处理"""
        try:
            from src.interactive_feedback_server.utils import set_custom_options_enabled

            set_custom_options_enabled(checked)
        except Exception as e:
            from src.interactive_feedback_server.utils import handle_config_error

            handle_config_error("设置自定义选项状态", e)

    def _setup_simple_fallback_options(self, parent_layout, config):
        """设置可折叠的后备选项区域 - 简洁设计"""
        # 创建展开/收起按钮 - 简洁样式
        self.fallback_toggle_button = QPushButton("")  # 稍后设置文本
        self.fallback_toggle_button.setCheckable(True)
        self.fallback_toggle_button.setChecked(False)  # 默认收起
        self.fallback_toggle_button.clicked.connect(self._toggle_fallback_options)

        # 简洁的按钮样式
        self.fallback_toggle_button.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 4px 8px;
                border: none;
                background-color: transparent;
                font-size: 10pt;
                color: gray;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 0.1);
            }
        """
        )

        parent_layout.addWidget(self.fallback_toggle_button)

        # 获取当前选项 - 使用优化后的辅助函数
        from src.interactive_feedback_server.utils import safe_get_fallback_options

        current_options = safe_get_fallback_options(config)

        # 创建可折叠的选项容器
        self.fallback_options_container = QWidget()
        self.fallback_options_container.setVisible(False)  # 默认隐藏
        options_layout = QVBoxLayout(self.fallback_options_container)
        options_layout.setContentsMargins(15, 5, 0, 5)  # 左侧缩进
        options_layout.setSpacing(3)  # 紧凑间距

        self.fallback_option_edits = []
        self.fallback_option_labels = []

        for i in range(5):
            option_layout = QHBoxLayout()
            option_layout.setContentsMargins(0, 0, 0, 0)

            # 选项标签 - 更小的字体
            option_label = QLabel("")  # 稍后设置文本
            option_label.setFixedWidth(50)
            option_label.setStyleSheet("font-size: 9pt;")  # 小字体
            self.fallback_option_labels.append(option_label)

            # 选项输入框 - 更紧凑
            option_edit = QLineEdit()
            option_edit.setMaxLength(50)
            option_edit.setStyleSheet("font-size: 10pt; padding: 2px;")  # 紧凑样式
            if i < len(current_options):
                option_edit.setText(current_options[i])

            # 连接信号
            option_edit.textChanged.connect(self._on_fallback_option_changed)
            self.fallback_option_edits.append(option_edit)

            option_layout.addWidget(option_label)
            option_layout.addWidget(option_edit)
            options_layout.addLayout(option_layout)

        parent_layout.addWidget(self.fallback_options_container)

    def _toggle_fallback_options(self):
        """切换后备选项区域的显示/隐藏"""
        is_expanded = self.fallback_toggle_button.isChecked()
        self.fallback_options_container.setVisible(is_expanded)

        # 更新按钮文本
        current_lang = self.current_language
        if is_expanded:
            self.fallback_toggle_button.setText(
                f"▼ {self.texts['collapse_options'][current_lang]}"
            )
        else:
            self.fallback_toggle_button.setText(
                f"▶ {self.texts['expand_options'][current_lang]}"
            )

        # 强制重新计算最小尺寸并调整
        self.setMinimumSize(0, 0)  # 清除最小尺寸限制
        self.adjustSize()  # 重新计算合适的尺寸

        # 如果是收起状态，强制收缩到内容大小
        if not is_expanded:
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()  # 处理布局更新
            self.resize(self.sizeHint())  # 调整到推荐尺寸

    def _setup_terminal_group(self):
        """设置终端配置区域 - 使用组件化设计"""
        self.terminal_group = QGroupBox("")  # 稍后设置文本
        terminal_layout = QVBoxLayout()

        # 获取终端管理器
        from ..utils.terminal_manager import get_terminal_manager
        from ..utils.constants import TERMINAL_TYPES

        self.terminal_manager = get_terminal_manager()

        # 默认终端选择标签
        self.default_terminal_label = QLabel("")  # 稍后设置文本
        terminal_layout.addWidget(self.default_terminal_label)

        # 创建按钮组确保互斥
        from PySide6.QtWidgets import QButtonGroup

        self.terminal_button_group = QButtonGroup()

        # 使用组件化的终端项
        self.terminal_items = {}
        current_default = self.settings_manager.get_default_terminal_type()

        for terminal_type, terminal_info in TERMINAL_TYPES.items():
            # 创建终端项组件
            terminal_item = TerminalItemWidget(
                terminal_type,
                terminal_info,
                self.terminal_manager,
                self.settings_manager,
                self,
            )

            # 添加到布局
            terminal_layout.addWidget(terminal_item)

            # 保存引用
            self.terminal_items[terminal_type] = terminal_item

            # 将单选按钮添加到按钮组
            self.terminal_button_group.addButton(terminal_item.get_radio_button())

            # 设置默认选中项
            if terminal_type == current_default:
                terminal_item.set_checked(True)

        self.terminal_group.setLayout(terminal_layout)
        self.layout.addWidget(self.terminal_group)

    def _on_display_mode_changed(self, mode: str, checked: bool):
        """V3.2 新增：显示模式改变时的处理"""
        if checked:
            try:
                from src.interactive_feedback_server.utils import (
                    get_config,
                    save_config,
                )

                config = get_config()
                config["display_mode"] = mode
                save_config(config)
            except Exception as e:
                from src.interactive_feedback_server.utils import handle_config_error

                handle_config_error("保存显示模式", e)

    def _on_fallback_option_changed(self):
        """V3.2 新增：后备选项改变时的处理"""
        try:
            from src.interactive_feedback_server.utils import get_config, save_config

            # 收集所有选项
            options = []
            for edit in self.fallback_option_edits:
                text = edit.text().strip()
                if text:  # 只添加非空选项
                    options.append(text)
                else:
                    options.append("请输入选项")  # 空选项的默认值

            # 确保有5个选项
            while len(options) < 5:
                options.append("请输入选项")

            # 保存配置
            config = get_config()
            config["fallback_options"] = options[:5]  # 只取前5个
            save_config(config)

        except Exception as e:
            from src.interactive_feedback_server.utils import handle_config_error

            handle_config_error("保存后备选项", e)

    def switch_theme(self, theme_name: str, checked: bool):
        # The 'checked' boolean comes directly from the toggled signal.
        # We only act when a radio button is checked, not when it's unchecked.
        if checked:
            self.settings_manager.set_current_theme(theme_name)
            app_instance = QApplication.instance()
            if app_instance:
                apply_theme(app_instance, theme_name)

                # 更新终端项组件的主题样式
                self._update_terminal_items_theme(theme_name)

                # 通知主窗口更新分割器样式以匹配新主题
                for widget in app_instance.topLevelWidgets():
                    if widget.__class__.__name__ == "FeedbackUI":
                        if hasattr(widget, "update_font_sizes"):
                            widget.update_font_sizes()
                        break

    def _update_terminal_items_theme(self, theme_name: str):
        """更新终端项组件的主题样式"""
        if hasattr(self, "terminal_items"):
            for terminal_item in self.terminal_items.values():
                terminal_item._apply_theme_style()

    def switch_layout(self, layout_direction: str, checked: bool):
        """切换界面布局方向"""
        if checked:
            self.settings_manager.set_layout_direction(layout_direction)

            # 通知主窗口重新创建布局
            app_instance = QApplication.instance()
            if app_instance:
                for widget in app_instance.topLevelWidgets():
                    if widget.__class__.__name__ == "FeedbackUI":
                        if hasattr(widget, "_recreate_layout"):
                            widget._recreate_layout()
                        break

    def switch_language_radio(self, language_code: str, checked: bool):
        """
        通过单选按钮切换语言设置
        """
        if checked:
            self.switch_language_internal(language_code)

    def switch_language(self, index: int):
        """
        切换语言设置（下拉框版本，保留兼容性）
        通过直接设置和触发特定更新方法来实现语言切换
        """
        # 这个方法现在已经不使用，但保留以防有其他地方调用
        pass

    def switch_language_internal(self, selected_lang: str):
        """
        内部语言切换逻辑
        """
        # 如果语言没有变化，则不需要处理
        if selected_lang == self.current_language:
            return

        # 保存设置
        self.settings_manager.set_current_language(selected_lang)
        old_language = self.current_language
        self.current_language = selected_lang  # 更新当前语言记录

        # 应用翻译
        app = QApplication.instance()
        if app:
            # 1. 移除旧翻译器
            app.removeTranslator(self.translator)

            # 2. 准备新翻译器
            self.translator = QTranslator(self)

            # 3. 根据语言选择加载/移除翻译器
            if selected_lang == "zh_CN":
                # 中文是默认语言，不需要翻译器
                print("设置对话框：切换到中文")
            elif selected_lang == "en_US":
                # 英文需要加载翻译
                if self.translator.load(f":/translations/{selected_lang}.qm"):
                    app.installTranslator(self.translator)
                    print("设置对话框：加载英文翻译")
                else:
                    print("设置对话框：无法加载英文翻译")

            # 4. 处理特殊情况：英文->中文
            if old_language == "en_US" and selected_lang == "zh_CN":
                self._handle_english_to_chinese_switch(app)
            else:
                # 5. 标准更新流程
                self._handle_standard_language_switch(app)

            # 6. 更新自身的文本
            self._update_texts()

    def _handle_standard_language_switch(self, app):
        """处理标准的语言切换流程"""
        # 1. 等待事件处理
        app.processEvents()

        # 2. 发送语言变更事件
        QCoreApplication.sendEvent(app, QEvent(QEvent.Type.LanguageChange))

        # 3. 更新所有窗口
        for widget in app.topLevelWidgets():
            if widget is not self:
                # 发送语言变更事件
                QCoreApplication.sendEvent(widget, QEvent(QEvent.Type.LanguageChange))

                # 如果是FeedbackUI，直接调用其更新方法
                if widget.__class__.__name__ == "FeedbackUI":
                    if hasattr(widget, "_update_displayed_texts"):
                        widget._update_displayed_texts()
                # 如果有retranslateUi方法，尝试调用
                elif hasattr(widget, "retranslateUi"):
                    try:
                        widget.retranslateUi()
                    except Exception as e:
                        print(f"更新窗口 {type(widget).__name__} 失败: {str(e)}")

    def _handle_english_to_chinese_switch(self, app):
        """专门处理从英文到中文的切换"""
        # 1. 处理事件队列
        app.processEvents()

        # 2. 发送语言变更事件给应用程序
        QCoreApplication.sendEvent(app, QEvent(QEvent.Type.LanguageChange))

        # 3. 查找并特别处理主窗口
        for widget in app.topLevelWidgets():
            if widget.__class__.__name__ == "FeedbackUI":
                # 直接调用主窗口的按钮文本更新方法
                if hasattr(widget, "_update_button_texts"):
                    widget._update_button_texts("zh_CN")
                # 更新其他文本
                if hasattr(widget, "_update_displayed_texts"):
                    widget._update_displayed_texts()
                print("设置对话框：已强制更新主窗口按钮文本")
            else:
                # 对其他窗口发送语言变更事件
                QCoreApplication.sendEvent(widget, QEvent(QEvent.Type.LanguageChange))

    def _update_texts(self):
        """根据当前语言设置更新所有文本"""
        current_lang = self.current_language

        # 更新窗口标题
        self.setWindowTitle(self.texts["title"][current_lang])

        # 更新整合后的主题布局组
        if hasattr(self, "theme_layout_group"):
            self.theme_layout_group.setTitle(
                self.texts["theme_layout_group"][current_lang]
            )

        if hasattr(self, "dark_theme_radio"):
            self.dark_theme_radio.setText(self.texts["dark_mode"][current_lang])

        if hasattr(self, "light_theme_radio"):
            self.light_theme_radio.setText(self.texts["light_mode"][current_lang])

        if hasattr(self, "vertical_layout_radio"):
            self.vertical_layout_radio.setText(
                self.texts["vertical_layout"][current_lang]
            )

        if hasattr(self, "horizontal_layout_radio"):
            self.horizontal_layout_radio.setText(
                self.texts["horizontal_layout"][current_lang]
            )

        # 更新整合后的语言字体组
        if hasattr(self, "language_font_group"):
            self.language_font_group.setTitle(
                self.texts["language_font_group"][current_lang]
            )

        if hasattr(self, "chinese_radio"):
            self.chinese_radio.setText(self.texts["chinese"][current_lang])

        if hasattr(self, "english_radio"):
            self.english_radio.setText(self.texts["english"][current_lang])

        # 更新字体标签
        if hasattr(self, "font_labels"):
            for key, label in self.font_labels.items():
                if key in self.texts:
                    label.setText(self.texts[key][current_lang])

        # 更新终端设置组标题和标签
        if hasattr(self, "terminal_group"):
            self.terminal_group.setTitle(self.texts["terminal_group"][current_lang])

        if hasattr(self, "default_terminal_label"):
            self.default_terminal_label.setText(
                self.texts["default_terminal"][current_lang]
            )

        # 更新终端项组件的文本
        if hasattr(self, "terminal_items"):
            for terminal_item in self.terminal_items.values():
                terminal_item.update_texts(self.texts, current_lang)

        # V3.2 新增：更新交互模式设置文本
        if hasattr(self, "interaction_group"):
            self.interaction_group.setTitle(
                self.texts["interaction_group"][current_lang]
            )

        if hasattr(self, "simple_mode_radio"):
            self.simple_mode_radio.setText(self.texts["simple_mode"][current_lang])

        if hasattr(self, "full_mode_radio"):
            self.full_mode_radio.setText(self.texts["full_mode"][current_lang])

        # V3.2 新增：更新功能开关单选按钮文本
        if hasattr(self, "enable_rule_engine_radio"):
            self.enable_rule_engine_radio.setText(
                self.texts["enable_rule_engine"][current_lang]
            )

        if hasattr(self, "enable_custom_options_radio"):
            self.enable_custom_options_radio.setText(
                self.texts["enable_custom_options"][current_lang]
            )

        # 更新可折叠按钮文本
        if hasattr(self, "fallback_toggle_button"):
            is_expanded = self.fallback_toggle_button.isChecked()
            if is_expanded:
                self.fallback_toggle_button.setText(
                    f"▼ {self.texts['collapse_options'][current_lang]}"
                )
            else:
                self.fallback_toggle_button.setText(
                    f"▶ {self.texts['expand_options'][current_lang]}"
                )

        # 更新后备选项标签
        if hasattr(self, "fallback_option_labels"):
            for i, label in enumerate(self.fallback_option_labels):
                label.setText(f"{self.texts['option_label'][current_lang]} {i+1}:")

        # 更新按钮文本
        if hasattr(self, "ok_button"):
            if current_lang == "zh_CN":
                self.ok_button.setText("确定")
            else:
                self.ok_button.setText("OK")

        if hasattr(self, "cancel_button"):
            if current_lang == "zh_CN":
                self.cancel_button.setText("取消")
            else:
                self.cancel_button.setText("Cancel")

    def changeEvent(self, event: QEvent):
        """处理语言变化事件"""
        if event.type() == QEvent.Type.LanguageChange:
            self._update_texts()
        super().changeEvent(event)

    def accept(self):
        super().accept()

    def update_prompt_font_size(self, size: int):
        """更新提示区字体大小"""
        self.settings_manager.set_prompt_font_size(size)
        self.apply_font_sizes()

    def update_options_font_size(self, size: int):
        """更新选项区字体大小"""
        self.settings_manager.set_options_font_size(size)
        self.apply_font_sizes()

    def update_input_font_size(self, size: int):
        """更新输入框字体大小"""
        self.settings_manager.set_input_font_size(size)
        self.apply_font_sizes()

    def apply_font_sizes(self):
        """应用字体大小设置"""
        # 查找并更新主窗口的字体大小
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.__class__.__name__ == "FeedbackUI":
                    if hasattr(widget, "update_font_sizes"):
                        widget.update_font_sizes()
                        return

    def reject(self):
        super().reject()

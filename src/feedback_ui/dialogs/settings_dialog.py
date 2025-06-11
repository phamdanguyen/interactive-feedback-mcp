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


def _setup_project_path():
    """设置项目路径到sys.path，避免重复代码"""
    import sys
    import os

    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    return project_root


def _get_collapsible_button_style():
    """获取可折叠按钮的通用样式"""
    return """
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
            # V4.0 简化：自定义选项开关
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
            # V4.0 新增：输入表达优化设置
            "optimization_group": {
                "zh_CN": "输入表达优化",
                "en_US": "Input Expression Optimization",
            },
            "enable_optimization": {
                "zh_CN": "启用优化功能",
                "en_US": "Enable Optimization",
            },
            "optimization_provider": {"zh_CN": "LLM提供商", "en_US": "LLM Provider"},
            "openai_provider": {"zh_CN": "OpenAI", "en_US": "OpenAI"},
            "gemini_provider": {"zh_CN": "Google Gemini", "en_US": "Google Gemini"},
            "deepseek_provider": {"zh_CN": "DeepSeek", "en_US": "DeepSeek"},
            "huoshan_provider": {"zh_CN": "火山引擎", "en_US": "Huoshan"},
            "api_key_label": {"zh_CN": "API密钥:", "en_US": "API Key:"},
            "api_key_placeholder": {"zh_CN": "请输入API密钥", "en_US": "Enter API key"},
            "test_connection": {"zh_CN": "测试连接", "en_US": "Test Connection"},
            "connection_success": {
                "zh_CN": "连接成功！",
                "en_US": "Connection successful!",
            },
            "connection_failed": {"zh_CN": "连接失败", "en_US": "Connection failed"},
            # V4.1 新增：自定义提示词设置
            "expand_prompts": {
                "zh_CN": "展开提示词设置",
                "en_US": "Expand Prompt Settings",
            },
            "collapse_prompts": {
                "zh_CN": "收起提示词设置",
                "en_US": "Collapse Prompt Settings",
            },
            "optimize_prompt_label": {
                "zh_CN": "优化提示词:",
                "en_US": "Optimize Prompt:",
            },
            "reinforce_prompt_label": {
                "zh_CN": "增强提示词:",
                "en_US": "Reinforce Prompt:",
            },
            "prompt_placeholder": {
                "zh_CN": "输入自定义提示词...",
                "en_US": "Enter custom prompt...",
            },
            # 音频设置相关文本
            "audio_group": {"zh_CN": "音频设置", "en_US": "Audio Settings"},
            "enable_audio": {
                "zh_CN": "启用提示音",
                "en_US": "Enable Notification Sound",
            },
            "audio_volume": {"zh_CN": "音量:", "en_US": "Volume:"},
            "custom_sound_file": {
                "zh_CN": "自定义音频文件:",
                "en_US": "Custom Sound File:",
            },
            "browse_sound": {"zh_CN": "浏览...", "en_US": "Browse..."},
            "test_sound": {"zh_CN": "测试", "en_US": "Test"},
            "sound_file_filter": {
                "zh_CN": "音频文件 (*.wav *.mp3 *.ogg *.flac *.aac);;WAV文件 (*.wav);;MP3文件 (*.mp3);;所有文件 (*.*)",
                "en_US": "Audio Files (*.wav *.mp3 *.ogg *.flac *.aac);;WAV Files (*.wav);;MP3 Files (*.mp3);;All Files (*.*)",
            },
        }

        self._setup_ui()

        # 初始更新文本
        self._update_texts()

    def _setup_ui(self):
        self._setup_theme_layout_group()  # 整合主题和布局
        self._setup_language_font_group()  # 整合语言和字体
        self._setup_audio_group()  # 新增：音频设置
        self._setup_interaction_group()  # V3.2 新增
        self._setup_optimization_group()  # V4.0 新增：输入表达优化
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

    def _setup_audio_group(self):
        """设置音频配置区域"""
        self.audio_group = QGroupBox("")  # 稍后设置文本
        audio_layout = QVBoxLayout()

        # 初始化音频管理器引用（避免重复导入）
        try:
            from ..utils.audio_manager import get_audio_manager

            self._audio_manager = get_audio_manager()
        except Exception:
            self._audio_manager = None

        # 第一行：启用提示音开关
        from ..utils.ui_factory import create_toggle_radio_button

        current_audio_enabled = self.settings_manager.get_audio_enabled()
        self.enable_audio_radio = create_toggle_radio_button(
            "", current_audio_enabled, self._on_audio_enabled_changed
        )
        audio_layout.addWidget(self.enable_audio_radio)

        # 第二行：音量控制
        volume_layout = QHBoxLayout()

        self.audio_volume_label = QLabel("")  # 稍后设置文本
        self.audio_volume_label.setStyleSheet("font-size: 10pt;")

        from PySide6.QtWidgets import QSlider
        from PySide6.QtCore import Qt

        self.audio_volume_slider = QSlider()
        self.audio_volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.audio_volume_slider.setRange(0, 100)
        current_volume = int(self.settings_manager.get_audio_volume() * 100)
        self.audio_volume_slider.setValue(current_volume)
        self.audio_volume_slider.valueChanged.connect(self._on_audio_volume_changed)

        # 音量数值显示
        self.audio_volume_value = QLabel(f"{current_volume}%")
        self.audio_volume_value.setStyleSheet("font-size: 10pt; min-width: 35px;")

        volume_layout.addWidget(self.audio_volume_label)
        volume_layout.addWidget(self.audio_volume_slider)
        volume_layout.addWidget(self.audio_volume_value)
        audio_layout.addLayout(volume_layout)

        # 第三行：自定义音频文件
        file_layout = QHBoxLayout()

        self.custom_sound_label = QLabel("")  # 稍后设置文本
        self.custom_sound_label.setStyleSheet("font-size: 10pt;")

        self.custom_sound_edit = QLineEdit()
        self.custom_sound_edit.setStyleSheet("font-size: 10pt; padding: 4px;")
        current_sound_path = self.settings_manager.get_notification_sound_path()
        if current_sound_path:
            self.custom_sound_edit.setText(current_sound_path)
        self.custom_sound_edit.textChanged.connect(self._on_custom_sound_changed)

        self.browse_sound_button = QPushButton("")  # 稍后设置文本
        self.browse_sound_button.clicked.connect(self._browse_sound_file)

        self.test_sound_button = QPushButton("")  # 稍后设置文本
        self.test_sound_button.clicked.connect(self._test_sound)

        file_layout.addWidget(self.custom_sound_label)
        file_layout.addWidget(self.custom_sound_edit)
        file_layout.addWidget(self.browse_sound_button)
        file_layout.addWidget(self.test_sound_button)
        audio_layout.addLayout(file_layout)

        self.audio_group.setLayout(audio_layout)
        self.layout.addWidget(self.audio_group)

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

    def _setup_optimization_group(self):
        """V4.0 新增：设置输入表达优化配置区域"""
        self.optimization_group = QGroupBox("")  # 稍后设置文本
        optimization_layout = QVBoxLayout()

        # 获取当前优化配置
        try:
            _setup_project_path()
            from src.interactive_feedback_server.utils import get_config

            config = get_config()
            optimizer_config = config.get("expression_optimizer", {})
        except Exception:
            # 如果无法获取配置，使用默认值
            try:
                from src.interactive_feedback_server.llm.constants import (
                    DEFAULT_OPTIMIZER_CONFIG,
                )

                optimizer_config = DEFAULT_OPTIMIZER_CONFIG.copy()
            except ImportError:
                # 如果导入失败，使用硬编码的默认值
                optimizer_config = {
                    "enabled": False,
                    "active_provider": "openai",
                    "providers": {
                        "openai": {
                            "api_key": "",
                            "model": "gpt-4o-mini",
                            "base_url": "https://api.openai.com/v1",
                        },
                        "gemini": {"api_key": "", "model": "gemini-2.0-flash"},
                        "deepseek": {
                            "api_key": "",
                            "base_url": "https://api.deepseek.com/v1",
                            "model": "deepseek-chat",
                        },
                        "volcengine": {
                            "api_key": "",
                            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                            "model": "deepseek-v3-250324",
                        },
                    },
                }

        # 第一行：启用优化功能开关
        from ..utils.ui_factory import create_toggle_radio_button

        self.enable_optimization_radio = create_toggle_radio_button(
            "", optimizer_config.get("enabled", False), self._on_optimization_toggled
        )
        optimization_layout.addWidget(self.enable_optimization_radio)

        # 第二行：LLM提供商选择
        provider_layout = QHBoxLayout()

        self.openai_radio = QRadioButton("")  # 稍后设置文本
        self.gemini_radio = QRadioButton("")  # 稍后设置文本
        self.deepseek_radio = QRadioButton("")  # 稍后设置文本
        self.huoshan_radio = QRadioButton("")  # 稍后设置文本

        # 设置当前选中的提供商
        active_provider = optimizer_config.get("active_provider", "openai")
        if active_provider == "openai":
            self.openai_radio.setChecked(True)
        elif active_provider == "gemini":
            self.gemini_radio.setChecked(True)
        elif active_provider == "deepseek":
            self.deepseek_radio.setChecked(True)
        elif active_provider == "volcengine":
            self.huoshan_radio.setChecked(True)

        # 连接信号
        self.openai_radio.toggled.connect(
            lambda checked: self._on_provider_changed("openai", checked)
        )
        self.gemini_radio.toggled.connect(
            lambda checked: self._on_provider_changed("gemini", checked)
        )
        self.deepseek_radio.toggled.connect(
            lambda checked: self._on_provider_changed("deepseek", checked)
        )
        self.huoshan_radio.toggled.connect(
            lambda checked: self._on_provider_changed("volcengine", checked)
        )

        provider_layout.addWidget(self.openai_radio)
        provider_layout.addWidget(self.gemini_radio)
        provider_layout.addWidget(self.deepseek_radio)
        provider_layout.addWidget(self.huoshan_radio)
        optimization_layout.addLayout(provider_layout)

        # 第三行：API密钥输入和测试
        api_layout = QHBoxLayout()

        self.api_key_label = QLabel("")  # 稍后设置文本
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("")  # 稍后设置文本
        self.api_key_edit.textChanged.connect(self._on_api_key_changed)

        self.test_connection_button = QPushButton("")  # 稍后设置文本
        self.test_connection_button.clicked.connect(self._test_api_connection)

        # 加载当前API密钥
        current_provider_config = optimizer_config.get("providers", {}).get(
            active_provider, {}
        )
        current_api_key = current_provider_config.get("api_key", "")
        if current_api_key and not current_api_key.startswith("YOUR_"):
            self.api_key_edit.setText(current_api_key)

        api_layout.addWidget(self.api_key_label)
        api_layout.addWidget(self.api_key_edit)
        api_layout.addWidget(self.test_connection_button)
        optimization_layout.addLayout(api_layout)

        # V4.1 新增：可展开的提示词自定义区域
        self._setup_prompt_customization(optimization_layout, optimizer_config)

        self.optimization_group.setLayout(optimization_layout)
        self.layout.addWidget(self.optimization_group)

    def _setup_prompt_customization(self, parent_layout, optimizer_config):
        """V4.1 新增：设置可展开的提示词自定义区域"""
        # 创建展开/收起按钮
        self.prompts_toggle_button = QPushButton("")  # 稍后设置文本
        self.prompts_toggle_button.setCheckable(True)
        self.prompts_toggle_button.setChecked(False)  # 默认收起
        self.prompts_toggle_button.clicked.connect(self._toggle_prompt_options)

        # 使用通用的按钮样式
        self.prompts_toggle_button.setStyleSheet(_get_collapsible_button_style())

        parent_layout.addWidget(self.prompts_toggle_button)

        # 获取当前提示词配置
        current_prompts = optimizer_config.get("prompts", {})

        # 创建可折叠的提示词容器
        self.prompts_container = QWidget()
        self.prompts_container.setVisible(False)  # 默认隐藏
        prompts_layout = QVBoxLayout(self.prompts_container)
        prompts_layout.setContentsMargins(15, 5, 0, 5)  # 左侧缩进
        prompts_layout.setSpacing(8)  # 适当间距

        # 优化提示词设置
        optimize_layout = QHBoxLayout()
        self.optimize_prompt_label = QLabel("")  # 稍后设置文本
        self.optimize_prompt_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        self.optimize_prompt_label.setFixedWidth(80)  # 固定标签宽度

        self.optimize_prompt_edit = QLineEdit()
        self.optimize_prompt_edit.setPlaceholderText("")  # 稍后设置文本
        self.optimize_prompt_edit.setStyleSheet("font-size: 10pt; padding: 4px;")

        # 设置当前值
        optimize_prompt = current_prompts.get("optimize", "")
        if optimize_prompt:
            self.optimize_prompt_edit.setText(optimize_prompt)

        self.optimize_prompt_edit.textChanged.connect(self._on_optimize_prompt_changed)

        optimize_layout.addWidget(self.optimize_prompt_label)
        optimize_layout.addWidget(self.optimize_prompt_edit)
        prompts_layout.addLayout(optimize_layout)

        # 增强提示词设置
        reinforce_layout = QHBoxLayout()
        self.reinforce_prompt_label = QLabel("")  # 稍后设置文本
        self.reinforce_prompt_label.setStyleSheet("font-size: 10pt; font-weight: bold;")
        self.reinforce_prompt_label.setFixedWidth(80)  # 固定标签宽度

        self.reinforce_prompt_edit = QLineEdit()
        self.reinforce_prompt_edit.setPlaceholderText("")  # 稍后设置文本
        self.reinforce_prompt_edit.setStyleSheet("font-size: 10pt; padding: 4px;")

        # 设置当前值
        reinforce_prompt = current_prompts.get("reinforce", "")
        if reinforce_prompt:
            self.reinforce_prompt_edit.setText(reinforce_prompt)

        self.reinforce_prompt_edit.textChanged.connect(
            self._on_reinforce_prompt_changed
        )

        reinforce_layout.addWidget(self.reinforce_prompt_label)
        reinforce_layout.addWidget(self.reinforce_prompt_edit)
        prompts_layout.addLayout(reinforce_layout)

        parent_layout.addWidget(self.prompts_container)

    def _toggle_prompt_options(self):
        """切换提示词设置区域的显示/隐藏"""
        is_expanded = self.prompts_toggle_button.isChecked()
        self.prompts_container.setVisible(is_expanded)

        # 更新按钮文本
        current_lang = self.current_language
        if is_expanded:
            self.prompts_toggle_button.setText(
                f"▼ {self.texts['collapse_prompts'][current_lang]}"
            )
        else:
            self.prompts_toggle_button.setText(
                f"▶ {self.texts['expand_prompts'][current_lang]}"
            )

        # 强制重新计算最小尺寸并调整
        self.setMinimumSize(0, 0)  # 清除最小尺寸限制
        self.adjustSize()  # 重新计算合适的尺寸

        # 如果是收起状态，强制收缩到内容大小
        if not is_expanded:
            from PySide6.QtWidgets import QApplication

            QApplication.processEvents()  # 处理布局更新
            self.resize(self.sizeHint())  # 调整到推荐尺寸

    def _get_optimizer_config_safely(self):
        """
        安全获取优化器配置 - V4.1 新增
        Safely get optimizer configuration - V4.1 New
        """
        try:
            _setup_project_path()
            from src.interactive_feedback_server.utils import get_config

            config = get_config()
            if "expression_optimizer" not in config:
                # 创建默认配置
                config["expression_optimizer"] = {
                    "enabled": False,
                    "active_provider": "openai",
                    "providers": {},
                    "prompts": {},
                }

            return config
        except Exception as e:
            print(f"获取配置失败: {e}")
            return None

    def _save_config_safely(self, config, operation_name="配置保存"):
        """
        安全保存配置 - V4.1 新增
        Safely save configuration - V4.1 New
        """
        try:
            _setup_project_path()
            from src.interactive_feedback_server.utils import save_config

            save_config(config)
            return True
        except Exception as e:
            print(f"{operation_name}失败: {e}")
            return False

    def _save_prompt_config(self, prompt_type: str, value: str):
        """通用的提示词保存方法 - V4.1 优化"""
        config = self._get_optimizer_config_safely()
        if not config:
            return

        # 确保prompts字段存在
        if "prompts" not in config["expression_optimizer"]:
            config["expression_optimizer"]["prompts"] = {}

        # 更新提示词
        config["expression_optimizer"]["prompts"][prompt_type] = value.strip()
        self._save_config_safely(config, f"{prompt_type}提示词保存")

    def _on_optimize_prompt_changed(self):
        """优化提示词改变时的处理"""
        self._save_prompt_config("optimize", self.optimize_prompt_edit.text())

    def _on_reinforce_prompt_changed(self):
        """增强提示词改变时的处理"""
        self._save_prompt_config("reinforce", self.reinforce_prompt_edit.text())

    def _setup_feature_toggles(self, parent_layout, config):
        """V4.0 简化：设置自定义选项开关"""
        # 获取功能状态和UI工厂
        from src.interactive_feedback_server.utils import get_custom_options_enabled
        from ..utils.ui_factory import create_toggle_radio_button

        custom_options_enabled = get_custom_options_enabled(config)

        toggles_layout = QHBoxLayout()

        self.enable_custom_options_radio = create_toggle_radio_button(
            "", custom_options_enabled, self._on_custom_options_toggled
        )

        toggles_layout.addWidget(self.enable_custom_options_radio)

        parent_layout.addLayout(toggles_layout)

    # V4.0 移除：_on_rule_engine_toggled 函数已删除

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

        # 更新音频设置组
        if hasattr(self, "audio_group"):
            self.audio_group.setTitle(self.texts["audio_group"][current_lang])

        if hasattr(self, "enable_audio_radio"):
            self.enable_audio_radio.setText(self.texts["enable_audio"][current_lang])

        if hasattr(self, "audio_volume_label"):
            self.audio_volume_label.setText(self.texts["audio_volume"][current_lang])

        if hasattr(self, "custom_sound_label"):
            self.custom_sound_label.setText(
                self.texts["custom_sound_file"][current_lang]
            )

        if hasattr(self, "browse_sound_button"):
            self.browse_sound_button.setText(self.texts["browse_sound"][current_lang])

        if hasattr(self, "test_sound_button"):
            self.test_sound_button.setText(self.texts["test_sound"][current_lang])

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

        # V4.0 简化：更新自定义选项开关文本
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

        # V4.0 新增：更新优化功能设置文本
        if hasattr(self, "optimization_group"):
            self.optimization_group.setTitle(
                self.texts["optimization_group"][current_lang]
            )

        if hasattr(self, "enable_optimization_radio"):
            self.enable_optimization_radio.setText(
                self.texts["enable_optimization"][current_lang]
            )

        if hasattr(self, "openai_radio"):
            self.openai_radio.setText(self.texts["openai_provider"][current_lang])

        if hasattr(self, "gemini_radio"):
            self.gemini_radio.setText(self.texts["gemini_provider"][current_lang])

        if hasattr(self, "deepseek_radio"):
            self.deepseek_radio.setText(self.texts["deepseek_provider"][current_lang])

        if hasattr(self, "huoshan_radio"):
            self.huoshan_radio.setText(self.texts["huoshan_provider"][current_lang])

        if hasattr(self, "api_key_label"):
            self.api_key_label.setText(self.texts["api_key_label"][current_lang])

        if hasattr(self, "api_key_edit"):
            self.api_key_edit.setPlaceholderText(
                self.texts["api_key_placeholder"][current_lang]
            )

        if hasattr(self, "test_connection_button"):
            self.test_connection_button.setText(
                self.texts["test_connection"][current_lang]
            )

        # V4.1 新增：更新提示词设置文本
        if hasattr(self, "prompts_toggle_button"):
            is_expanded = self.prompts_toggle_button.isChecked()
            if is_expanded:
                self.prompts_toggle_button.setText(
                    f"▼ {self.texts['collapse_prompts'][current_lang]}"
                )
            else:
                self.prompts_toggle_button.setText(
                    f"▶ {self.texts['expand_prompts'][current_lang]}"
                )

        if hasattr(self, "optimize_prompt_label"):
            self.optimize_prompt_label.setText(
                self.texts["optimize_prompt_label"][current_lang]
            )

        if hasattr(self, "reinforce_prompt_label"):
            self.reinforce_prompt_label.setText(
                self.texts["reinforce_prompt_label"][current_lang]
            )

        if hasattr(self, "optimize_prompt_edit"):
            self.optimize_prompt_edit.setPlaceholderText(
                self.texts["prompt_placeholder"][current_lang]
            )

        if hasattr(self, "reinforce_prompt_edit"):
            self.reinforce_prompt_edit.setPlaceholderText(
                self.texts["prompt_placeholder"][current_lang]
            )

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

    # V4.0 新增：输入表达优化功能的事件处理方法
    def _on_optimization_toggled(self, checked: bool):
        """优化功能开关切换处理 - V4.1 简化"""
        config = self._get_optimizer_config_safely()
        if not config:
            return

        config["expression_optimizer"]["enabled"] = checked

        if self._save_config_safely(config, "优化功能开关"):
            # 通知主窗口更新按钮可见性
            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if widget.__class__.__name__ == "FeedbackUI":
                        if hasattr(widget, "_update_optimization_buttons_visibility"):
                            widget._update_optimization_buttons_visibility()
                        break

    def _on_provider_changed(self, provider: str, checked: bool):
        """LLM提供商切换处理 - V4.1 简化"""
        if not checked:
            return

        config = self._get_optimizer_config_safely()
        if not config:
            return

        config["expression_optimizer"]["active_provider"] = provider

        if self._save_config_safely(config, "提供商切换"):
            # 更新API密钥输入框
            provider_config = config["expression_optimizer"]["providers"].get(
                provider, {}
            )
            current_api_key = provider_config.get("api_key", "")

            if current_api_key and not current_api_key.startswith("YOUR_"):
                self.api_key_edit.setText(current_api_key)
            else:
                self.api_key_edit.setText("")

    def _on_api_key_changed(self, text: str):
        """API密钥改变处理 - V4.1 简化"""
        config = self._get_optimizer_config_safely()
        if not config:
            return

        # 获取当前选中的提供商
        active_provider = config["expression_optimizer"]["active_provider"]

        # 确保providers字段存在
        if "providers" not in config["expression_optimizer"]:
            config["expression_optimizer"]["providers"] = {}

        # 确保当前提供商配置存在
        if active_provider not in config["expression_optimizer"]["providers"]:
            config["expression_optimizer"]["providers"][active_provider] = {}

        # 更新API密钥
        config["expression_optimizer"]["providers"][active_provider][
            "api_key"
        ] = text.strip()
        self._save_config_safely(config, "API密钥保存")

    def _convert_test_error_to_friendly(self, error_message: str) -> str:
        """
        将测试错误转换为用户友好的提示 - V4.1 新增
        Convert test errors to user-friendly messages - V4.1 New
        """
        if not error_message:
            return "连接测试失败，请检查配置"

        # 处理常见错误
        if "API密钥" in error_message or "api_key" in error_message.lower():
            return "API密钥无效或未配置，请检查并重新输入"

        if "网络" in error_message or "timeout" in error_message.lower():
            return "网络连接超时，请检查网络连接"

        if "模型" in error_message or "model" in error_message.lower():
            return "所选模型不可用，请尝试其他模型"

        if "配置" in error_message or "config" in error_message.lower():
            return "配置信息有误，请检查设置"

        return f"连接测试失败: {error_message}"

    def _test_api_connection(self):
        """测试API连接 - V4.1 增强用户体验"""
        from PySide6.QtWidgets import QMessageBox, QProgressDialog

        # 显示进度对话框
        progress = QProgressDialog("正在测试连接...", "取消", 0, 0, self)
        progress.setWindowTitle("API连接测试")
        progress.setModal(True)
        progress.show()

        try:
            config = self._get_optimizer_config_safely()
            if not config:
                progress.close()
                QMessageBox.warning(self, "测试结果", "无法获取配置信息")
                return

            _setup_project_path()
            from src.interactive_feedback_server.llm.factory import get_llm_provider

            optimizer_config = config.get("expression_optimizer", {})

            # 获取provider并测试
            provider, message = get_llm_provider(optimizer_config)

            current_lang = self.current_language

            if provider:
                # 测试配置验证
                is_valid, validation_message = provider.validate_config()

                progress.close()

                if is_valid:
                    success_msg = "✅ " + self.texts["connection_success"][current_lang]
                    QMessageBox.information(self, "测试结果", success_msg)
                else:
                    friendly_msg = self._convert_test_error_to_friendly(
                        validation_message
                    )
                    QMessageBox.warning(self, "测试结果", f"❌ {friendly_msg}")
            else:
                progress.close()
                friendly_msg = self._convert_test_error_to_friendly(message)
                QMessageBox.warning(self, "测试结果", f"❌ {friendly_msg}")

        except Exception as e:
            progress.close()
            friendly_msg = self._convert_test_error_to_friendly(str(e))
            QMessageBox.critical(self, "测试错误", f"❌ {friendly_msg}")

    # --- 音频设置相关方法 (Audio Settings Methods) ---
    def _on_audio_enabled_changed(self, enabled: bool):
        """音频启用状态改变处理"""
        self.settings_manager.set_audio_enabled(enabled)

        # 更新音频管理器状态
        if self._audio_manager:
            self._audio_manager.set_enabled(enabled)

    def _on_audio_volume_changed(self, value: int):
        """音量改变处理"""
        volume = value / 100.0  # 转换为0.0-1.0范围
        self.settings_manager.set_audio_volume(volume)

        # 更新显示的音量值
        self.audio_volume_value.setText(f"{value}%")

        # 更新音频管理器音量
        if self._audio_manager:
            self._audio_manager.set_volume(volume)

    def _on_custom_sound_changed(self):
        """自定义音频文件路径改变处理"""
        path = self.custom_sound_edit.text().strip()
        self.settings_manager.set_notification_sound_path(path)

        # 验证音频文件
        if path and self._audio_manager:
            is_valid, message = self._audio_manager.validate_audio_file(path)
            if not is_valid:
                # 设置警告样式
                self.custom_sound_edit.setStyleSheet(
                    "font-size: 10pt; padding: 4px; border: 1px solid orange;"
                )
                self.custom_sound_edit.setToolTip(f"⚠️ {message}")
            else:
                # 恢复正常样式
                self._reset_sound_edit_style()
        else:
            # 清空路径时恢复正常样式
            self._reset_sound_edit_style()

    def _reset_sound_edit_style(self):
        """重置音频文件输入框样式"""
        self.custom_sound_edit.setStyleSheet("font-size: 10pt; padding: 4px;")
        self.custom_sound_edit.setToolTip("")

    def _browse_sound_file(self):
        """浏览音频文件"""
        from PySide6.QtWidgets import QFileDialog

        current_lang = self.current_language
        filter_text = self.texts["sound_file_filter"][current_lang]

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件" if current_lang == "zh_CN" else "Select Audio File",
            "",
            filter_text,
        )

        if file_path:
            self.custom_sound_edit.setText(file_path)
            self._on_custom_sound_changed()

    def _test_sound(self):
        """测试音频播放"""
        from PySide6.QtWidgets import QMessageBox

        if not self._audio_manager or not self._audio_manager.is_enabled():
            QMessageBox.warning(self, "音频测试", "音频功能未启用或不可用")
            return

        # 获取自定义音频文件路径
        custom_path = self.custom_sound_edit.text().strip()

        # 播放音频
        success = self._audio_manager.play_notification_sound(
            custom_path if custom_path else None
        )

        if not success:
            QMessageBox.warning(self, "音频测试", "音频播放失败，请检查文件路径和格式")

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
    QSlider,
    QButtonGroup,
    QFileDialog,
)
from PySide6.QtCore import Qt

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


class ConfigManager:
    """配置管理工具类 - 减少重复代码"""

    @staticmethod
    def get_optimizer_config():
        """安全获取优化器配置"""
        try:
            # 兼容包安装模式和开发模式的导入
            try:
                from interactive_feedback_server.utils import get_config
            except ImportError:
                _setup_project_path()
                from src.interactive_feedback_server.utils import get_config

            config = get_config()
            if "expression_optimizer" not in config:
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

    @staticmethod
    def save_config(config, operation_name="配置保存"):
        """安全保存配置"""
        try:
            # 兼容包安装模式和开发模式的导入
            try:
                from interactive_feedback_server.utils import save_config
            except ImportError:
                _setup_project_path()
                from src.interactive_feedback_server.utils import save_config

            save_config(config)
            return True
        except Exception as e:
            print(f"{operation_name}失败: {e}")
            return False


class AudioSettingsDialog(QDialog):
    """音频设置弹窗"""

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("音频设置")
        self.setModal(True)
        self.resize(400, 300)

        # 初始化音频管理器
        try:
            from ..utils.audio_manager import get_audio_manager

            self._audio_manager = get_audio_manager()
        except Exception:
            self._audio_manager = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 启用提示音开关
        from ..utils.ui_factory import create_toggle_radio_button

        current_audio_enabled = self.settings_manager.get_audio_enabled()
        self.enable_audio_radio = create_toggle_radio_button(
            "启用提示音", current_audio_enabled, self._on_audio_enabled_changed
        )
        layout.addWidget(self.enable_audio_radio)

        # 音量控制
        volume_layout = QHBoxLayout()
        volume_label = QLabel("音量:")

        self.audio_volume_slider = QSlider()
        from PySide6.QtCore import Qt

        self.audio_volume_slider.setOrientation(Qt.Orientation.Horizontal)
        self.audio_volume_slider.setRange(0, 100)
        current_volume = int(self.settings_manager.get_audio_volume() * 100)
        self.audio_volume_slider.setValue(current_volume)
        self.audio_volume_slider.valueChanged.connect(self._on_audio_volume_changed)

        self.audio_volume_value = QLabel(f"{current_volume}%")
        self.audio_volume_value.setFixedWidth(45)  # 增加宽度以完全显示"100%"
        self.audio_volume_value.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐

        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.audio_volume_slider)
        volume_layout.addWidget(self.audio_volume_value)
        layout.addLayout(volume_layout)

        # 自定义音频文件
        file_layout = QHBoxLayout()
        file_label = QLabel("自定义音频文件:")

        self.custom_sound_edit = QLineEdit()
        current_sound_path = self.settings_manager.get_notification_sound_path()
        if current_sound_path:
            self.custom_sound_edit.setText(current_sound_path)
        self.custom_sound_edit.textChanged.connect(self._on_custom_sound_changed)

        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._browse_sound_file)

        test_button = QPushButton("测试")
        test_button.clicked.connect(self._test_sound)

        file_layout.addWidget(file_label)
        file_layout.addWidget(self.custom_sound_edit)
        file_layout.addWidget(browse_button)
        file_layout.addWidget(test_button)
        layout.addLayout(file_layout)

        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def _on_audio_enabled_changed(self, enabled):
        self.settings_manager.set_audio_enabled(enabled)

    def _on_audio_volume_changed(self, value):
        volume = value / 100.0
        self.settings_manager.set_audio_volume(volume)
        self.audio_volume_value.setText(f"{value}%")

    def _on_custom_sound_changed(self, path):
        self.settings_manager.set_notification_sound_path(path.strip())

    def _browse_sound_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "音频文件 (*.wav *.mp3 *.ogg *.flac *.aac);;WAV文件 (*.wav);;MP3文件 (*.mp3);;所有文件 (*.*)",
        )
        if file_path:
            self.custom_sound_edit.setText(file_path)

    def _test_sound(self):
        """测试音频播放"""
        if self._audio_manager:
            # 获取自定义音频文件路径
            custom_path = self.custom_sound_edit.text().strip()
            # 播放音频 - 修复方法名
            success = self._audio_manager.play_notification_sound(
                custom_path if custom_path else None
            )
            if not success:
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self, "音频测试", "音频播放失败，请检查文件路径和格式"
                )


class OptimizationSettingsDialog(QDialog):
    """输入表达优化设置弹窗"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("输入表达优化")
        self.setModal(True)
        self.resize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 获取当前优化配置
        config = ConfigManager.get_optimizer_config()
        optimizer_config = (
            config.get("expression_optimizer", {})
            if config
            else {
                "enabled": False,
                "active_provider": "openai",
                "providers": {},
                "prompts": {},
            }
        )

        # 启用优化功能开关
        from ..utils.ui_factory import create_toggle_radio_button

        self.enable_optimization_radio = create_toggle_radio_button(
            "启用优化功能",
            optimizer_config.get("enabled", False),
            self._on_optimization_toggled,
        )
        layout.addWidget(self.enable_optimization_radio)

        # LLM提供商选择
        provider_group = QGroupBox("LLM提供商")
        provider_layout = QHBoxLayout()

        self.openai_radio = QRadioButton("OpenAI")
        self.gemini_radio = QRadioButton("Google Gemini")
        self.deepseek_radio = QRadioButton("DeepSeek")
        self.huoshan_radio = QRadioButton("火山引擎")

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
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)

        # API密钥输入
        api_layout = QHBoxLayout()
        api_label = QLabel("API密钥:")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("请输入API密钥")
        self.api_key_edit.textChanged.connect(self._on_api_key_changed)

        test_button = QPushButton("测试连接")
        test_button.clicked.connect(self._test_api_connection)

        # 加载当前API密钥
        current_provider_config = optimizer_config.get("providers", {}).get(
            active_provider, {}
        )
        current_api_key = current_provider_config.get("api_key", "")
        if current_api_key and not current_api_key.startswith("YOUR_"):
            self.api_key_edit.setText(current_api_key)

        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_edit)
        api_layout.addWidget(test_button)
        layout.addLayout(api_layout)

        # 提示词自定义区域
        prompts_group = QGroupBox("提示词设置")
        prompts_layout = QVBoxLayout()

        # 获取当前提示词配置
        current_prompts = optimizer_config.get("prompts", {})

        # 优化提示词设置
        optimize_layout = QHBoxLayout()
        optimize_label = QLabel("优化提示词:")
        optimize_label.setFixedWidth(80)

        self.optimize_prompt_edit = QLineEdit()
        self.optimize_prompt_edit.setPlaceholderText("输入自定义优化提示词...")
        optimize_prompt = current_prompts.get("optimize", "")
        if optimize_prompt:
            self.optimize_prompt_edit.setText(optimize_prompt)
        self.optimize_prompt_edit.textChanged.connect(self._on_optimize_prompt_changed)

        optimize_layout.addWidget(optimize_label)
        optimize_layout.addWidget(self.optimize_prompt_edit)
        prompts_layout.addLayout(optimize_layout)

        # 增强提示词设置
        reinforce_layout = QHBoxLayout()
        reinforce_label = QLabel("增强提示词:")
        reinforce_label.setFixedWidth(80)

        self.reinforce_prompt_edit = QLineEdit()
        self.reinforce_prompt_edit.setPlaceholderText("输入自定义增强提示词...")
        reinforce_prompt = current_prompts.get("reinforce", "")
        if reinforce_prompt:
            self.reinforce_prompt_edit.setText(reinforce_prompt)
        self.reinforce_prompt_edit.textChanged.connect(
            self._on_reinforce_prompt_changed
        )

        reinforce_layout.addWidget(reinforce_label)
        reinforce_layout.addWidget(self.reinforce_prompt_edit)
        prompts_layout.addLayout(reinforce_layout)

        prompts_group.setLayout(prompts_layout)
        layout.addWidget(prompts_group)

        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

    def _on_optimization_toggled(self, checked):
        """优化功能开关切换处理"""
        config = ConfigManager.get_optimizer_config()
        if not config:
            return

        config["expression_optimizer"]["enabled"] = checked

        if ConfigManager.save_config(config, "优化功能开关"):
            # 通知主窗口更新按钮可见性
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                for widget in app.topLevelWidgets():
                    if widget.__class__.__name__ == "FeedbackUI":
                        if hasattr(widget, "_update_optimization_buttons_visibility"):
                            widget._update_optimization_buttons_visibility()
                        break

    def _on_provider_changed(self, provider, checked):
        """提供商切换处理"""
        if not checked:
            return

        config = ConfigManager.get_optimizer_config()
        if not config:
            return

        config["expression_optimizer"]["active_provider"] = provider

        if ConfigManager.save_config(config, "提供商切换"):
            # 更新API密钥输入框
            provider_config = (
                config["expression_optimizer"].get("providers", {}).get(provider, {})
            )
            current_api_key = provider_config.get("api_key", "")

            if current_api_key and not current_api_key.startswith("YOUR_"):
                self.api_key_edit.setText(current_api_key)
            else:
                self.api_key_edit.setText("")

    def _on_api_key_changed(self):
        """API密钥变更处理"""
        config = ConfigManager.get_optimizer_config()
        if not config:
            return

        # 获取当前选中的提供商
        active_provider = config["expression_optimizer"].get(
            "active_provider", "openai"
        )

        # 确保providers字段存在
        if "providers" not in config["expression_optimizer"]:
            config["expression_optimizer"]["providers"] = {}

        # 确保当前提供商配置存在
        if active_provider not in config["expression_optimizer"]["providers"]:
            config["expression_optimizer"]["providers"][active_provider] = {}

        # 更新API密钥
        config["expression_optimizer"]["providers"][active_provider][
            "api_key"
        ] = self.api_key_edit.text().strip()
        ConfigManager.save_config(config, "API密钥保存")

    def _test_api_connection(self):
        """API连接测试"""
        from PySide6.QtWidgets import QMessageBox, QProgressDialog

        # 显示进度对话框
        progress = QProgressDialog("正在测试连接...", "取消", 0, 0, self)
        progress.setWindowTitle("API连接测试")
        progress.setModal(True)
        progress.show()

        try:
            config = ConfigManager.get_optimizer_config()
            if not config:
                progress.close()
                QMessageBox.warning(self, "测试结果", "无法获取配置信息")
                return

            # 兼容包安装模式和开发模式的导入
            try:
                from interactive_feedback_server.llm.factory import get_llm_provider
            except ImportError:
                _setup_project_path()
                from src.interactive_feedback_server.llm.factory import get_llm_provider

            optimizer_config = config.get("expression_optimizer", {})

            # 获取provider并测试
            provider, message = get_llm_provider(optimizer_config)

            if provider:
                # 测试配置验证
                is_valid, validation_message = provider.validate_config()

                progress.close()

                if is_valid:
                    QMessageBox.information(self, "测试结果", "✅ 连接成功！")
                else:
                    QMessageBox.warning(
                        self, "测试结果", f"❌ 连接失败: {validation_message}"
                    )
            else:
                progress.close()
                QMessageBox.warning(self, "测试结果", f"❌ 连接失败: {message}")

        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "测试错误", f"❌ 测试失败: {str(e)}")

    def _on_optimize_prompt_changed(self):
        """优化提示词改变处理"""
        self._save_prompt_config("optimize", self.optimize_prompt_edit.text())

    def _on_reinforce_prompt_changed(self):
        """增强提示词改变处理"""
        self._save_prompt_config("reinforce", self.reinforce_prompt_edit.text())

    def _save_prompt_config(self, prompt_type: str, value: str):
        """保存提示词配置"""
        config = ConfigManager.get_optimizer_config()
        if not config:
            return

        # 确保prompts字段存在
        if "prompts" not in config["expression_optimizer"]:
            config["expression_optimizer"]["prompts"] = {}

        # 更新提示词
        config["expression_optimizer"]["prompts"][prompt_type] = value.strip()
        ConfigManager.save_config(config, f"{prompt_type}提示词保存")

    # 已删除终端设置对话框类

    # 已删除终端项组件类 - 第一部分

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

        # Mac系统兼容性设置
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        # 调整窗口大小，确保有足够空间显示所有内容
        self.resize(700, 650)
        self.setMinimumSize(650, 600)

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
            # 更多设置相关文本
            "more_settings_group": {"zh_CN": "更多设置", "en_US": "More Settings"},
            "audio_settings_button": {"zh_CN": "音频", "en_US": "Audio"},
            "optimization_settings_button": {
                "zh_CN": "输入表达优化",
                "en_US": "Input Optimization",
            },
            "terminal_settings_button": {"zh_CN": "终端", "en_US": "Terminal"},
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
        }

        self._setup_ui()

        # 初始更新文本
        self._update_texts()

    def _setup_ui(self):
        self._setup_theme_layout_group()  # 整合主题和布局
        self._setup_language_font_group()  # 整合语言和字体
        self._setup_interaction_group()  # V3.2 新增
        self._setup_more_settings_group()  # 新增：更多设置

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
        """整合主题和布局设置 - 优化左右对齐"""
        self.theme_layout_group = QGroupBox("")  # 稍后设置文本
        grid_layout = QGridLayout()

        # 设置列宽比例，确保左右对齐
        grid_layout.setColumnStretch(0, 1)  # 左列
        grid_layout.setColumnStretch(1, 1)  # 右列

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
        # 使用右对齐让右侧按钮更好地利用空间
        grid_layout.addWidget(self.dark_theme_radio, 0, 0, Qt.AlignmentFlag.AlignLeft)
        grid_layout.addWidget(self.light_theme_radio, 0, 1, Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(
            self.vertical_layout_radio, 1, 0, Qt.AlignmentFlag.AlignLeft
        )
        grid_layout.addWidget(
            self.horizontal_layout_radio, 1, 1, Qt.AlignmentFlag.AlignRight
        )

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

        # 第一行：语言设置 - 使用网格布局实现左右对齐
        lang_grid = QGridLayout()
        lang_grid.setColumnStretch(0, 1)  # 左列
        lang_grid.setColumnStretch(1, 1)  # 右列

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

        lang_grid.addWidget(self.chinese_radio, 0, 0, Qt.AlignmentFlag.AlignLeft)
        lang_grid.addWidget(self.english_radio, 0, 1, Qt.AlignmentFlag.AlignRight)

        # 创建容器widget来包装网格布局
        lang_widget = QWidget()
        lang_widget.setLayout(lang_grid)
        layout.addWidget(lang_widget)

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
            font_widget = QWidget()
            font_layout = QHBoxLayout(font_widget)
            font_layout.setContentsMargins(0, 0, 0, 0)

            # 创建标签
            label = QLabel("")
            self._apply_font_label_theme_style(label)
            label.setMinimumWidth(120)
            self.font_labels[key] = label

            # 创建数值选择器
            spinner = QSpinBox()
            spinner.setRange(min_val, max_val)
            spinner.setValue(current_value)
            spinner.valueChanged.connect(callback)
            spinner.setFixedSize(90, 32)
            self._apply_font_spinner_theme_style(spinner)
            self.font_spinners[key] = spinner

            font_layout.addWidget(label)
            font_layout.addStretch()
            font_layout.addWidget(spinner)
            layout.addWidget(font_widget)

        self.language_font_group.setLayout(layout)
        self.layout.addWidget(self.language_font_group)

    def _get_font_control_styles(self):
        """获取字体控件的主题样式配置"""
        is_dark = self.settings_manager.get_current_theme() == "dark"

        # 主题颜色配置
        colors = {
            "bg": "#2d2d2d" if is_dark else "white",
            "text": "#ffffff" if is_dark else "#000000",
            "border": "#555555" if is_dark else "#cccccc",
            "button_bg": "#404040" if is_dark else "#f8f8f8",
            "button_hover": "#505050" if is_dark else "#e8e8e8",
            "button_pressed": "#606060" if is_dark else "#d8d8d8",
            "label_text": "#ffffff" if is_dark else "#333333",
            "focus": "#0078d4",
        }

        return {
            "spinner": f"""
                QSpinBox {{
                    font-size: 11pt; padding: 3px 6px; border-radius: 4px;
                    border: 1px solid {colors['border']};
                    background-color: {colors['bg']}; color: {colors['text']};
                    selection-background-color: {colors['focus']};
                }}
                QSpinBox:focus {{ border: 2px solid {colors['focus']}; }}
                QSpinBox::up-button, QSpinBox::down-button {{
                    subcontrol-origin: border; width: 22px; height: 14px;
                    border-left: 1px solid {colors['border']};
                    background-color: {colors['button_bg']};
                }}
                QSpinBox::up-button {{
                    subcontrol-position: top right; border-bottom: 1px solid {colors['border']};
                    border-top-right-radius: 4px;
                }}
                QSpinBox::down-button {{
                    subcontrol-position: bottom right; border-top: 1px solid {colors['border']};
                    border-bottom-right-radius: 4px;
                }}
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                    background-color: {colors['button_hover']};
                }}
                QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
                    background-color: {colors['button_pressed']};
                }}
            """,
            "label": f"""
                font-size: 11pt; font-weight: 500; padding: 2px 0px;
                color: {colors['label_text']};
            """,
        }

    def _apply_font_spinner_theme_style(self, spinner):
        """为字体选择器应用主题感知的样式"""
        styles = self._get_font_control_styles()
        spinner.setStyleSheet(styles["spinner"])

    def _apply_font_label_theme_style(self, label):
        """为字体标签应用主题感知的样式"""
        styles = self._get_font_control_styles()
        label.setStyleSheet(styles["label"])

    def _update_font_spinners_theme(self):
        """更新所有字体控件的主题样式"""
        if hasattr(self, "font_spinners"):
            for spinner in self.font_spinners.values():
                self._apply_font_spinner_theme_style(spinner)
        if hasattr(self, "font_labels"):
            for label in self.font_labels.values():
                self._apply_font_label_theme_style(label)

    def _setup_more_settings_group(self):
        """设置更多设置组 - 包含三个按钮"""
        self.more_settings_group = QGroupBox("更多设置")
        layout = QHBoxLayout()

        # 音频设置按钮
        self.audio_settings_button = QPushButton("音频")
        self.audio_settings_button.clicked.connect(self._open_audio_settings)

        # 输入表达优化设置按钮
        self.optimization_settings_button = QPushButton("输入表达优化")
        self.optimization_settings_button.clicked.connect(
            self._open_optimization_settings
        )

        # 已删除终端设置按钮

        layout.addWidget(self.audio_settings_button)
        layout.addWidget(self.optimization_settings_button)
        # 已删除终端设置按钮的添加

        self.more_settings_group.setLayout(layout)
        self.layout.addWidget(self.more_settings_group)

    def _open_audio_settings(self):
        """打开音频设置弹窗"""
        dialog = AudioSettingsDialog(self.settings_manager, self)
        dialog.exec()

    def _open_optimization_settings(self):
        """打开输入表达优化设置弹窗"""
        dialog = OptimizationSettingsDialog(self)
        dialog.exec()

    # 已删除终端设置方法

    def _setup_interaction_group(self):
        """V3.2 新增：设置交互模式配置区域 - 简洁布局"""
        self.interaction_group = QGroupBox("")  # 稍后设置文本
        interaction_layout = QVBoxLayout()

        # 获取当前配置和UI工厂 - 合并导入
        try:
            from interactive_feedback_server.utils import safe_get_config
        except ImportError:
            _setup_project_path()
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

        # 修改布局以实现更好的对齐
        mode_layout.takeAt(0)  # 移除第一个按钮
        mode_layout.takeAt(0)  # 移除第二个按钮

        # 重新添加按钮，设置对齐
        mode_layout.addWidget(self.simple_mode_radio, 0, Qt.AlignmentFlag.AlignLeft)
        mode_layout.addWidget(self.full_mode_radio, 0, Qt.AlignmentFlag.AlignRight)

        interaction_layout.addLayout(mode_layout)

        # 第二行：功能开关 - 左右布局
        self._setup_feature_toggles(interaction_layout, config)

        # 第三行：自定义后备选项 - 简洁设计
        self._setup_simple_fallback_options(interaction_layout, config)

        self.interaction_group.setLayout(interaction_layout)
        self.layout.addWidget(self.interaction_group)

    def _setup_feature_toggles(self, parent_layout, config):
        """V4.0 简化：设置自定义选项开关"""
        # 获取功能状态和UI工厂
        try:
            from interactive_feedback_server.utils import get_custom_options_enabled
        except ImportError:
            _setup_project_path()
            from src.interactive_feedback_server.utils import get_custom_options_enabled
        from ..utils.ui_factory import create_toggle_radio_button

        custom_options_enabled = get_custom_options_enabled(config)

        # 记录初始状态，用于关闭时保存
        self._custom_options_enabled = custom_options_enabled

        toggles_layout = QHBoxLayout()

        self.enable_custom_options_radio = create_toggle_radio_button(
            "", custom_options_enabled, self._on_custom_options_toggled
        )

        toggles_layout.addWidget(self.enable_custom_options_radio)

        parent_layout.addLayout(toggles_layout)

    # V4.0 移除：_on_rule_engine_toggled 函数已删除

    def _on_custom_options_toggled(self, checked: bool):
        """自定义选项开关切换处理 - 简化版本"""
        # 只记录状态，在关闭时统一保存
        self._custom_options_enabled = checked

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

        # 获取当前选项 - 使用过滤后的有效选项
        from src.interactive_feedback_server.utils import get_fallback_options

        current_options = get_fallback_options(config)

        # 创建可折叠的选项容器
        self.fallback_options_container = QWidget()
        self.fallback_options_container.setVisible(False)  # 默认隐藏
        options_layout = QVBoxLayout(self.fallback_options_container)
        options_layout.setContentsMargins(15, 5, 0, 5)  # 左侧缩进
        options_layout.setSpacing(3)  # 紧凑间距

        # 移除复杂的状态指示器，采用简单的关闭时保存方案

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

            # 移除实时保存信号，改为关闭时统一保存
            self.fallback_option_edits.append(option_edit)

            option_layout.addWidget(option_label)
            option_layout.addWidget(option_edit)
            options_layout.addLayout(option_layout)

        parent_layout.addWidget(self.fallback_options_container)

    def _toggle_fallback_options(self):
        """切换后备选项区域的显示/隐藏 - 简洁优化版本"""
        from PySide6.QtCore import QTimer

        is_expanded = self.fallback_toggle_button.isChecked()
        current_width = self.width()

        # 更新按钮文本
        current_lang = self.current_language
        button_text = (
            f"▼ {self.texts['collapse_options'][current_lang]}"
            if is_expanded
            else f"▶ {self.texts['expand_options'][current_lang]}"
        )
        self.fallback_toggle_button.setText(button_text)

        # 设置容器可见性并调整窗口大小
        self.fallback_options_container.setVisible(is_expanded)

        # 延迟调整窗口大小，避免闪动
        QTimer.singleShot(
            10, lambda: self._adjust_window_size(current_width, is_expanded)
        )

    def _adjust_window_size(self, target_width, is_expanded):
        """调整窗口大小以适应内容变化"""
        # 激活布局计算并获取合适的高度
        self.layout.activate()
        target_height = self.sizeHint().height()

        # 调整窗口大小，保持宽度不变
        self.resize(target_width, target_height)

        # 设置合理的最小高度
        min_height = target_height if is_expanded else 600
        self.setMinimumHeight(min_height)

    def _on_display_mode_changed(self, mode: str, checked: bool):
        """V3.2 新增：显示模式改变时的处理"""
        if checked:
            try:
                # 兼容包安装模式和开发模式的导入
                try:
                    from interactive_feedback_server.utils import (
                        get_config,
                        save_config,
                    )
                except ImportError:
                    _setup_project_path()
                    from src.interactive_feedback_server.utils import (
                        get_config,
                        save_config,
                    )

                config = get_config()
                config["display_mode"] = mode
                save_config(config)
            except Exception as e:
                try:
                    from interactive_feedback_server.utils import handle_config_error
                except ImportError:
                    _setup_project_path()
                    from src.interactive_feedback_server.utils import (
                        handle_config_error,
                    )

                handle_config_error("保存显示模式", e)

    def _save_fallback_options(self):
        """保存后备选项 - 使用null占位符标记空选项"""
        try:
            from src.interactive_feedback_server.utils import get_config, save_config

            # 收集所有选项，空选项用"null"占位符
            options = []
            for edit in self.fallback_option_edits:
                text = edit.text().strip()
                if text:
                    options.append(text)
                else:
                    options.append("null")  # 空选项用null占位符

            # 确保有5个选项（保持配置结构完整）
            while len(options) < 5:
                options.append("null")

            # 保存配置
            config = get_config()
            config["fallback_options"] = options[:5]  # 保存5个选项
            save_config(config)

        except Exception as e:
            print(f"保存后备选项失败: {e}")

    def switch_theme(self, theme_name: str, checked: bool):
        # The 'checked' boolean comes directly from the toggled signal.
        # We only act when a radio button is checked, not when it's unchecked.
        if checked:
            self.settings_manager.set_current_theme(theme_name)
            app_instance = QApplication.instance()
            if app_instance:
                apply_theme(app_instance, theme_name)

                # 更新字体选择器的主题样式
                self._update_font_spinners_theme()

                # 通知主窗口更新分割器样式以匹配新主题
                for widget in app_instance.topLevelWidgets():
                    if widget.__class__.__name__ == "FeedbackUI":
                        if hasattr(widget, "update_font_sizes"):
                            widget.update_font_sizes()
                        break

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

        # 更新更多设置组
        if hasattr(self, "more_settings_group"):
            self.more_settings_group.setTitle(
                self.texts["more_settings_group"][current_lang]
            )

        if hasattr(self, "audio_settings_button"):
            self.audio_settings_button.setText(
                self.texts["audio_settings_button"][current_lang]
            )

        if hasattr(self, "optimization_settings_button"):
            self.optimization_settings_button.setText(
                self.texts["optimization_settings_button"][current_lang]
            )

        if hasattr(self, "terminal_settings_button"):
            self.terminal_settings_button.setText(
                self.texts["terminal_settings_button"][current_lang]
            )

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
        """关闭设置页面时统一保存所有配置"""
        try:
            # 保存自定义选项开关状态
            if hasattr(self, "_custom_options_enabled"):
                from src.interactive_feedback_server.utils import (
                    set_custom_options_enabled,
                )

                set_custom_options_enabled(self._custom_options_enabled)

            # 保存后备选项（过滤空选项）
            if hasattr(self, "fallback_option_edits"):
                self._save_fallback_options()

        except Exception as e:
            print(f"保存设置失败: {e}")

        super().accept()

    def _update_font_size(self, font_type: str, size: int):
        """统一的字体大小更新方法"""
        # 设置字体大小
        if font_type == "prompt":
            self.settings_manager.set_prompt_font_size(size)
        elif font_type == "options":
            self.settings_manager.set_options_font_size(size)
        elif font_type == "input":
            self.settings_manager.set_input_font_size(size)

        # 应用到主窗口
        app = QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if widget.__class__.__name__ == "FeedbackUI" and hasattr(
                    widget, "update_font_sizes"
                ):
                    widget.update_font_sizes()
                    break

    def update_prompt_font_size(self, size: int):
        """更新提示区字体大小"""
        self._update_font_size("prompt", size)

    def update_options_font_size(self, size: int):
        """更新选项区字体大小"""
        self._update_font_size("options", size)

    def update_input_font_size(self, size: int):
        """更新输入框字体大小"""
        self._update_font_size("input", size)

    def reject(self):
        super().reject()

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
)

from ..utils.settings_manager import SettingsManager
from ..utils.style_manager import apply_theme


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
            "theme_group": {"zh_CN": "外观主题", "en_US": "Theme"},
            "dark_mode": {"zh_CN": "深色模式", "en_US": "Dark Mode"},
            "light_mode": {"zh_CN": "浅色模式", "en_US": "Light Mode"},
            "language_group": {"zh_CN": "语言", "en_US": "Language"},
            "chinese": {"zh_CN": "中文", "en_US": "Chinese"},
            "english": {"zh_CN": "English", "en_US": "English"},
            "font_size_group": {"zh_CN": "字体大小", "en_US": "Font Size"},
            "prompt_font_size": {
                "zh_CN": "提示区文字大小:",
                "en_US": "Prompt Text Size:",
            },
            "options_font_size": {
                "zh_CN": "选项区文字大小:",
                "en_US": "Options Text Size:",
            },
            "input_font_size": {
                "zh_CN": "输入框文字大小:",
                "en_US": "Input Font Size:",
            },
            "layout_group": {"zh_CN": "界面布局", "en_US": "Interface Layout"},
            "vertical_layout": {"zh_CN": "上下布局", "en_US": "Vertical Layout"},
            "horizontal_layout": {"zh_CN": "左右布局", "en_US": "Horizontal Layout"},
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
        }

        self._setup_ui()

        # 初始更新文本
        self._update_texts()

    def _setup_ui(self):
        self._setup_theme_group()
        self._setup_layout_group()
        self._setup_language_group()
        self._setup_font_size_group()
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

    def _setup_theme_group(self):
        self.theme_group = QGroupBox("")  # 稍后设置文本
        theme_layout = QVBoxLayout()

        self.dark_theme_radio = QRadioButton("")  # 稍后设置文本
        self.light_theme_radio = QRadioButton("")  # 稍后设置文本

        current_theme = self.settings_manager.get_current_theme()
        if current_theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.light_theme_radio.setChecked(True)

        # 当选项变化时，立即应用主题
        self.dark_theme_radio.toggled.connect(
            lambda checked: self.switch_theme("dark", checked)
        )
        self.light_theme_radio.toggled.connect(
            lambda checked: self.switch_theme("light", checked)
        )

        theme_layout.addWidget(self.dark_theme_radio)
        theme_layout.addWidget(self.light_theme_radio)
        self.theme_group.setLayout(theme_layout)
        self.layout.addWidget(self.theme_group)

    def _setup_language_group(self):
        self.lang_group = QGroupBox("")  # 稍后设置文本
        lang_layout = QVBoxLayout()

        self.chinese_radio = QRadioButton("")  # 稍后设置文本
        self.english_radio = QRadioButton("")  # 稍后设置文本

        current_lang = self.settings_manager.get_current_language()
        if current_lang == "zh_CN":
            self.chinese_radio.setChecked(True)
        else:
            self.english_radio.setChecked(True)

        # 当选项变化时，立即应用语言
        self.chinese_radio.toggled.connect(
            lambda checked: self.switch_language_radio("zh_CN", checked)
        )
        self.english_radio.toggled.connect(
            lambda checked: self.switch_language_radio("en_US", checked)
        )

        lang_layout.addWidget(self.chinese_radio)
        lang_layout.addWidget(self.english_radio)
        self.lang_group.setLayout(lang_layout)
        self.layout.addWidget(self.lang_group)

    def _setup_layout_group(self):
        """设置界面布局选择区域"""
        self.layout_group = QGroupBox("")  # 稍后设置文本
        layout_layout = QVBoxLayout()

        self.vertical_layout_radio = QRadioButton("")  # 稍后设置文本
        self.horizontal_layout_radio = QRadioButton("")  # 稍后设置文本

        # 获取当前布局方向设置
        from ..utils.constants import LAYOUT_HORIZONTAL, LAYOUT_VERTICAL

        current_layout = self.settings_manager.get_layout_direction()

        if current_layout == LAYOUT_HORIZONTAL:
            self.horizontal_layout_radio.setChecked(True)
        else:
            self.vertical_layout_radio.setChecked(True)

        # 当选项变化时，立即应用布局
        self.vertical_layout_radio.toggled.connect(
            lambda checked: self.switch_layout(LAYOUT_VERTICAL, checked)
        )
        self.horizontal_layout_radio.toggled.connect(
            lambda checked: self.switch_layout(LAYOUT_HORIZONTAL, checked)
        )

        layout_layout.addWidget(self.vertical_layout_radio)
        layout_layout.addWidget(self.horizontal_layout_radio)
        self.layout_group.setLayout(layout_layout)
        self.layout.addWidget(self.layout_group)

    def _setup_font_size_group(self):
        """设置字体大小调整区域"""
        self.font_size_group = QGroupBox("")  # 稍后设置文本
        font_size_layout = QVBoxLayout()

        # 获取当前字体大小设置
        prompt_font_size = self.settings_manager.get_prompt_font_size()
        options_font_size = self.settings_manager.get_options_font_size()

        # 提示区字体大小设置
        prompt_layout = QHBoxLayout()
        self.prompt_font_label = QLabel("")  # 稍后设置文本
        self.prompt_font_spinner = QSpinBox()
        self.prompt_font_spinner.setRange(12, 24)  # 限制字体大小范围
        self.prompt_font_spinner.setValue(prompt_font_size)
        self.prompt_font_spinner.valueChanged.connect(self.update_prompt_font_size)

        prompt_layout.addWidget(self.prompt_font_label)
        prompt_layout.addWidget(self.prompt_font_spinner)
        font_size_layout.addLayout(prompt_layout)

        # 选项区字体大小设置
        options_layout = QHBoxLayout()
        self.options_font_label = QLabel("")  # 稍后设置文本
        self.options_font_spinner = QSpinBox()
        self.options_font_spinner.setRange(10, 20)  # 限制字体大小范围
        self.options_font_spinner.setValue(options_font_size)
        self.options_font_spinner.valueChanged.connect(self.update_options_font_size)

        options_layout.addWidget(self.options_font_label)
        options_layout.addWidget(self.options_font_spinner)
        font_size_layout.addLayout(options_layout)

        # 输入框字体大小设置
        input_layout = QHBoxLayout()
        self.input_font_label = QLabel("")  # 稍后设置文本
        self.input_font_spinner = QSpinBox()
        self.input_font_spinner.setRange(10, 20)  # 限制字体大小范围
        self.input_font_spinner.setValue(self.settings_manager.get_input_font_size())
        self.input_font_spinner.valueChanged.connect(self.update_input_font_size)
        input_layout.addWidget(self.input_font_label)
        input_layout.addWidget(self.input_font_spinner)
        font_size_layout.addLayout(input_layout)

        self.font_size_group.setLayout(font_size_layout)
        self.layout.addWidget(self.font_size_group)

    def _setup_terminal_group(self):
        """设置终端配置区域"""
        self.terminal_group = QGroupBox("")  # 稍后设置文本
        terminal_layout = QVBoxLayout()

        # 获取终端管理器
        from ..utils.terminal_manager import get_terminal_manager
        from ..utils.constants import TERMINAL_TYPES

        self.terminal_manager = get_terminal_manager()

        # 默认终端选择标签
        self.default_terminal_label = QLabel("")  # 稍后设置文本
        terminal_layout.addWidget(self.default_terminal_label)

        # 创建终端选项
        from PySide6.QtWidgets import QButtonGroup

        self.terminal_button_group = QButtonGroup()
        self.terminal_radios = {}
        self.terminal_path_edits = {}
        self.terminal_browse_buttons = {}

        # 获取当前默认终端类型
        current_default = self.settings_manager.get_default_terminal_type()

        for terminal_type, terminal_info in TERMINAL_TYPES.items():
            option_widget = self._create_terminal_option(terminal_type, terminal_info)
            terminal_layout.addWidget(option_widget)

            # 将单选按钮添加到按钮组确保互斥
            self.terminal_button_group.addButton(self.terminal_radios[terminal_type])

            # 设置默认选中项
            if terminal_type == current_default:
                self.terminal_radios[terminal_type].setChecked(True)

        self.terminal_group.setLayout(terminal_layout)
        self.layout.addWidget(self.terminal_group)

    def _create_terminal_option(self, terminal_type: str, terminal_info: dict):
        """创建单个终端选项"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 第一行：单选按钮 + 浏览按钮（在同一水平线上）
        first_row_layout = QHBoxLayout()
        first_row_layout.setContentsMargins(0, 0, 0, 0)

        radio = QRadioButton(terminal_info["display_name"])
        self.terminal_radios[terminal_type] = radio

        # 创建浏览按钮容器，用于调整垂直位置
        browse_container = QWidget()
        browse_container_layout = QVBoxLayout(browse_container)
        browse_container_layout.setContentsMargins(0, 0, 0, 0)
        browse_container_layout.setSpacing(0)

        # 添加向上偏移的空间（负边距效果）
        browse_container_layout.addSpacing(-10)  # 向上移动10px

        browse_button = QPushButton("")  # 稍后设置文本
        browse_button.setFixedSize(40, 20)  # 合适的按钮大小
        browse_button.setStyleSheet("font-size: 8pt; padding: 2px;")  # 小字体
        self.terminal_browse_buttons[terminal_type] = browse_button

        browse_container_layout.addWidget(browse_button)
        browse_container_layout.addStretch()  # 底部弹性空间

        first_row_layout.addWidget(radio)
        first_row_layout.addStretch()  # 添加弹性空间，使浏览按钮右对齐
        first_row_layout.addWidget(browse_container)

        layout.addLayout(first_row_layout)

        # 第二行：路径标签和输入框（明显分离）
        path_container = QWidget()
        path_layout = QVBoxLayout(path_container)
        path_layout.setContentsMargins(20, 0, 0, 0)  # 缩进，与单选按钮对齐
        path_layout.setSpacing(3)

        # 路径标签（隐藏，但保持布局结构）
        path_label = QLabel("")  # 空标签，不显示文本
        path_label.setVisible(False)  # 隐藏标签，但保持布局空间

        # 路径输入框
        path_edit = QLineEdit()
        path_edit.setReadOnly(False)  # 允许用户直接编辑

        # 设置文本省略方向为末尾省略
        from PySide6.QtCore import Qt

        path_edit.setCursorPosition(0)  # 光标位置在开头

        # 根据主题设置样式（可编辑状态）
        current_theme = self.settings_manager.get_current_theme()
        if current_theme == "dark":
            path_edit.setStyleSheet(
                "QLineEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #555555; padding: 4px; }"
            )
        else:
            path_edit.setStyleSheet(
                "QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; padding: 4px; }"
            )

        self.terminal_path_edits[terminal_type] = path_edit

        # 设置当前检测到的路径或自定义路径
        detected_path = self.terminal_manager.get_terminal_command(terminal_type)
        custom_path = self.settings_manager.get_terminal_path(terminal_type)
        path_text = custom_path if custom_path else detected_path
        path_edit.setText(path_text)

        # 确保文本从开头显示（末尾省略）
        path_edit.setCursorPosition(0)
        path_edit.setSelection(0, 0)  # 清除选择，光标在开头

        # 连接事件
        radio.toggled.connect(
            lambda checked: self._on_terminal_radio_changed(terminal_type, checked)
        )
        browse_button.clicked.connect(lambda: self._browse_terminal_path(terminal_type))

        # 为路径输入框添加特殊的文本改变处理
        def on_path_text_changed(text):
            self._on_terminal_path_changed(terminal_type, text)
            # 确保光标在开头，显示路径开始部分
            path_edit.setCursorPosition(0)

        path_edit.textChanged.connect(on_path_text_changed)

        path_layout.addWidget(path_label)
        path_layout.addWidget(path_edit)

        layout.addWidget(path_container)

        return container

    def _on_terminal_radio_changed(self, terminal_type: str, checked: bool):
        """终端单选按钮状态改变"""
        if checked:
            self.settings_manager.set_default_terminal_type(terminal_type)

    def _browse_terminal_path(self, terminal_type: str):
        """浏览终端可执行文件"""
        from PySide6.QtWidgets import QFileDialog

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("可执行文件 (*.exe);;所有文件 (*.*)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                self.terminal_path_edits[terminal_type].setText(path)
                self._validate_terminal_path(terminal_type, path)
                # 直接保存路径和更新终端管理器
                self._on_terminal_path_changed(terminal_type, path)

    def _validate_terminal_path(self, terminal_type: str, path: str):
        """验证终端路径"""
        path_edit = self.terminal_path_edits[terminal_type]

        if self.terminal_manager.validate_terminal_path(path):
            # 路径有效，设置正常样式
            path_edit.setStyleSheet("")
            path_edit.setToolTip("")
        else:
            # 路径无效，设置错误样式
            path_edit.setStyleSheet("QLineEdit { border: 2px solid red; }")
            path_edit.setToolTip(self.texts["path_invalid"][self.current_language])

    def _on_terminal_path_changed(self, terminal_type: str, path: str):
        """终端路径改变时的处理"""
        self._validate_terminal_path(terminal_type, path)
        # 保存到设置
        self.settings_manager.set_terminal_path(terminal_type, path)
        # 更新终端管理器的自定义路径
        self.terminal_manager.set_custom_path(terminal_type, path)

    def switch_theme(self, theme_name: str, checked: bool):
        # The 'checked' boolean comes directly from the toggled signal.
        # We only act when a radio button is checked, not when it's unchecked.
        if checked:
            self.settings_manager.set_current_theme(theme_name)
            app_instance = QApplication.instance()
            if app_instance:
                apply_theme(app_instance, theme_name)

                # 更新终端路径输入框的主题样式
                self._update_terminal_path_styles(theme_name)

                # 通知主窗口更新分割器样式以匹配新主题
                for widget in app_instance.topLevelWidgets():
                    if widget.__class__.__name__ == "FeedbackUI":
                        if hasattr(widget, "update_font_sizes"):
                            widget.update_font_sizes()
                        break

    def _update_terminal_path_styles(self, theme_name: str):
        """更新终端路径输入框的主题样式"""
        if hasattr(self, "terminal_path_edits"):
            for path_edit in self.terminal_path_edits.values():
                if theme_name == "dark":
                    path_edit.setStyleSheet(
                        "QLineEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #555555; padding: 4px; }"
                    )
                else:
                    path_edit.setStyleSheet(
                        "QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; padding: 4px; }"
                    )
                # 确保文本从开头显示
                path_edit.setCursorPosition(0)

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

        # 更新主题组标题和按钮
        if hasattr(self, "theme_group"):
            self.theme_group.setTitle(self.texts["theme_group"][current_lang])

        if hasattr(self, "dark_theme_radio"):
            self.dark_theme_radio.setText(self.texts["dark_mode"][current_lang])

        if hasattr(self, "light_theme_radio"):
            self.light_theme_radio.setText(self.texts["light_mode"][current_lang])

        # 更新语言组标题和单选按钮
        if hasattr(self, "lang_group"):
            self.lang_group.setTitle(self.texts["language_group"][current_lang])

        if hasattr(self, "chinese_radio"):
            self.chinese_radio.setText(self.texts["chinese"][current_lang])

        if hasattr(self, "english_radio"):
            self.english_radio.setText(self.texts["english"][current_lang])

        # 更新字体大小组标题和标签
        if hasattr(self, "font_size_group"):
            self.font_size_group.setTitle(self.texts["font_size_group"][current_lang])

        if hasattr(self, "prompt_font_label"):
            self.prompt_font_label.setText(self.texts["prompt_font_size"][current_lang])

        if hasattr(self, "options_font_label"):
            self.options_font_label.setText(
                self.texts["options_font_size"][current_lang]
            )

        if hasattr(self, "input_font_label"):
            self.input_font_label.setText(self.texts["input_font_size"][current_lang])

        # 更新布局组标题和按钮
        if hasattr(self, "layout_group"):
            self.layout_group.setTitle(self.texts["layout_group"][current_lang])

        if hasattr(self, "vertical_layout_radio"):
            self.vertical_layout_radio.setText(
                self.texts["vertical_layout"][current_lang]
            )

        if hasattr(self, "horizontal_layout_radio"):
            self.horizontal_layout_radio.setText(
                self.texts["horizontal_layout"][current_lang]
            )

        # 更新终端设置组标题和标签
        if hasattr(self, "terminal_group"):
            self.terminal_group.setTitle(self.texts["terminal_group"][current_lang])

        if hasattr(self, "default_terminal_label"):
            self.default_terminal_label.setText(
                self.texts["default_terminal"][current_lang]
            )

        # 更新终端浏览按钮（路径标签已隐藏，不需要更新）
        if hasattr(self, "terminal_browse_buttons"):
            for terminal_type, browse_button in self.terminal_browse_buttons.items():
                browse_button.setText(self.texts["browse_button"][current_lang])

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

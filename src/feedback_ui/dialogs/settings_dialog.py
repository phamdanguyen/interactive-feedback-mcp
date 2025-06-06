from PySide6.QtCore import QCoreApplication, QEvent, QTranslator
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
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
        }

        self._setup_ui()

        # 初始更新文本
        self._update_texts()

    def _setup_ui(self):
        self._setup_theme_group()
        self._setup_language_group()
        self._setup_font_size_group()

        # 添加 OK 和 Cancel 按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

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

        self.lang_combo = QComboBox()
        # 稍后添加选项

        current_lang = self.settings_manager.get_current_language()

        # 当语言选择变化时，立即应用
        self.lang_combo.currentIndexChanged.connect(self.switch_language)

        lang_layout.addWidget(self.lang_combo)
        self.lang_group.setLayout(lang_layout)
        self.layout.addWidget(self.lang_group)

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

    def switch_theme(self, theme_name: str, checked: bool):
        # The 'checked' boolean comes directly from the toggled signal.
        # We only act when a radio button is checked, not when it's unchecked.
        if checked:
            self.settings_manager.set_current_theme(theme_name)
            app_instance = QApplication.instance()
            if app_instance:
                apply_theme(app_instance, theme_name)

    def switch_language(self, index: int):
        """
        切换语言设置
        通过直接设置和触发特定更新方法来实现语言切换
        """
        # 获取选择的语言代码
        selected_lang = self.lang_combo.currentData()

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
            translation_loaded = False

            # 3. 根据语言选择加载/移除翻译器
            if selected_lang == "zh_CN":
                # 中文是默认语言，不需要翻译器
                print("设置对话框：切换到中文")
            elif selected_lang == "en_US":
                # 英文需要加载翻译
                if self.translator.load(f":/translations/{selected_lang}.qm"):
                    app.installTranslator(self.translator)
                    translation_loaded = True
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

        # 更新语言组标题和下拉菜单
        if hasattr(self, "lang_group"):
            self.lang_group.setTitle(self.texts["language_group"][current_lang])

        if hasattr(self, "lang_combo"):
            # 清空旧选项并重新填充
            self.lang_combo.blockSignals(True)  # 阻止信号循环触发
            self.lang_combo.clear()
            self.lang_combo.addItem(self.texts["chinese"][current_lang], "zh_CN")
            self.lang_combo.addItem(self.texts["english"][current_lang], "en_US")
            self.lang_combo.blockSignals(False)

            # 查找与当前保存的语言代码匹配的索引
            index_to_set = self.lang_combo.findData(self.current_language)
            if index_to_set != -1:
                self.lang_combo.setCurrentIndex(index_to_set)

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

        # 更新按钮文本
        if hasattr(self, "button_box"):
            ok_button = self.button_box.button(QDialogButtonBox.Ok)
            cancel_button = self.button_box.button(QDialogButtonBox.Cancel)

            if ok_button:
                if current_lang == "zh_CN":
                    ok_button.setText("确定")
                else:
                    ok_button.setText("OK")

            if cancel_button:
                if current_lang == "zh_CN":
                    cancel_button.setText("取消")
                else:
                    cancel_button.setText("Cancel")

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

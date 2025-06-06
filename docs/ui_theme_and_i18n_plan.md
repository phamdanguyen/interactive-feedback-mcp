# UI 主题与多语言支持优化方案

## 1. 方案概述与目标

### 1.1. 当前状态

当前UI应用存在以下两个主要问题，限制了其可维护性和用户体验：
1.  **样式硬编码**: 所有UI样式（QSS）都硬编码在 `feedback_ui/utils/style_manager.py` 的一个全局字符串中，修改和扩展主题非常困难。
2.  **双语硬编码**: 所有面向用户的文本均采用 `中文 (English)` 的格式直接写在代码中，无法实现单语言的清爽界面，也无法动态切换语言。

### 1.2. 优化目标

本方案旨在通过引入专业的UI开发实践，解决上述问题，达成以下目标：
1.  **实现主题动态切换**: 用户可以通过UI设置，在"浅色"和"深色"主题之间自由切换，且无需重启应用。
2.  **实现语言动态切换**: 用户可以通过UI设置，在"中文"和"英文"之间切换，界面只显示选定的语言。
3.  **提升代码质量与可维护性**: 将样式、资源、逻辑和翻译内容彻底分离，使项目结构更清晰，便于未来高频率的UI迭代和功能扩展。

---

## 2. 第一阶段：实现主题动态切换

**目标**: 将QSS样式外部化，并建立一个可以动态切换浅色/深色主题的机制。

### 步骤 2.1: 创建新的文件与目录结构

为了更好地组织样式与资源，首先创建以下目录：

-   `feedback_ui/styles/` （feedback_ui目录已存在）
-   `feedback_ui/resources/` （feedback_ui目录已存在）

### 步骤 2.2: 创建QSS主题文件

1.  **深色主题 (`dark_theme.qss`)**:
    -   将 `feedback_ui/utils/style_manager.py` 中现有的 `GLOBAL_QSS` 字符串的**全部内容**，剪切并粘贴到一个新文件 `feedback_ui/styles/dark_theme.qss` 中。
2.  **浅色主题 (`light_theme.qss`)**:
    -   在 `feedback_ui/styles/` 目录下创建 `light_theme.qss`。
    -   填入一套全新的浅色UI样式。以下是一个基础模板，需要根据实际设计进行扩充：
        ```qss
        /* feedback_ui/styles/light_theme.qss */
        QWidget {
            background-color: #f0f0f0;
            color: #111111;
            font-size: 10pt; 
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QPushButton {
            background-color: #e1e1e1;
            color: #111111;
            border: 1px solid #adadad;
            border-radius: 6px; 
            padding: 8px 16px; 
            font-weight: bold;
        }
        QPushButton:hover { background-color: #cccccc; }
        QTextEdit {
            background-color: #ffffff;
            color: #111111;
            border: 1px solid #cccccc;
            border-radius: 10px;
        }
        /* ... 为其他所有控件添加对应的浅色样式 ... */
        ```

### 步骤 2.3: 创建并编译Qt资源文件 (`.qrc`)

1.  **创建 `resources.qrc`**:
    -   在 `feedback_ui/resources/` 目录下创建 `resources.qrc` 文件，内容如下。此文件用于索引所有需要打包进程序里的静态资源。
        ```xml
        <!DOCTYPE RCC>
        <RCC version="1.0">
          <qresource prefix="/">
            <file alias="styles/dark.qss">../styles/dark_theme.qss</file>
            <file alias="styles/light.qss">../styles/light_theme.qss</file>
            <!-- 预留位置，用于未来添加图标和翻译文件 -->
          </qresource>
        </RCC>
        ```
2.  **编译资源**:
    -   在项目**根目录**下打开终端，运行以下命令，将 `.qrc` 文件编译成Python模块：
        ```bash
        pyside6-rcc feedback_ui/resources/resources.qrc -o feedback_ui/resources_rc.py
        ```
    -   执行后，将在 `feedback_ui/` 目录下生成 `resources_rc.py` 文件。

### 步骤 2.4: 重构 `style_manager.py`

1.  **删除旧代码**: 删除 `style_manager.py` 中巨大的 `GLOBAL_QSS` 字符串。
2.  **修改应用函数**:
    -   重命名 `apply_global_style` 为 `apply_theme`。
    -   修改其实现，使其能从Qt资源系统加载指定的主题文件。
        ```python
        # feedback_ui/utils/style_manager.py (修改后)
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QFile, QIODevice
        
        # 必须导入刚刚编译的资源模块，否则无法访问资源路径
        import feedback_ui.resources_rc 
        
        def apply_theme(app: QApplication, theme_name: str = 'dark'):
            """根据主题名称加载并应用QSS样式。"""
            qss_path = f":/styles/{theme_name}.qss"
            qss_file = QFile(qss_path)
            
            if not qss_file.exists():
                print(f"错误：无法找到主题文件 {qss_path}")
                return

            if qss_file.open(QIODevice.ReadOnly | QIODevice.Text):
                stylesheet = qss_file.readAll().data().decode('utf-8')
                app.setStyleSheet(stylesheet)
                qss_file.close()
            else:
                print(f"错误：无法打开主题文件 {qss_path}")
        ```

### 步骤 2.5: 在 `SettingsManager` 中添加主题设置

在 `feedback_ui/utils/settings_manager.py` 的 `SettingsManager` 类中添加主题管理方法：
```python
def get_current_theme(self) -> str:
    # 从配置中读取主题设置，若无则默认为 'dark'
    return self.settings.value("ui/theme", "dark")

def set_current_theme(self, theme_name: str):
    self.settings.setValue("ui/theme", theme_name)
```

### 步骤 2.6: 在主窗口 `FeedbackUI` 中实现设置入口

此步骤取代原有的菜单栏方案。

1.  **在 `FeedbackUI` 中添加"设置"按钮**:
    -   在 `feedback_ui/main_window.py` 的 `_setup_bottom_bar` 或类似方法中，在"常用语"、"固定窗口"按钮所在的布局里，添加一个新的"设置"按钮。
        ```python
        # feedback_ui/main_window.py
        # 在 _setup_bottom_bar 方法内
        self.settings_button = QPushButton(self.tr("设置"))
        self.settings_button.setObjectName("secondary_button")
        self.settings_button.setToolTip(self.tr("打开设置面板"))
        self.settings_button.clicked.connect(self.open_settings_dialog)
        bottom_layout.addWidget(self.settings_button) # 假设已有 bottom_layout
        ```

2.  **创建新的 `SettingsDialog` 对话框**:
    -   创建一个新文件： `feedback_ui/dialogs/settings_dialog.py`。
    -   这个对话框将负责显示所有设置选项。
        ```python
        # feedback_ui/dialogs/settings_dialog.py
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QGroupBox, QRadioButton, QDialogButtonBox
        from ..utils.settings_manager import SettingsManager
        from ..utils.style_manager import apply_theme

        class SettingsDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle(self.tr("设置"))
                self.settings_manager = SettingsManager(self)
                self.layout = QVBoxLayout(self)

                self._setup_theme_group()

                # 添加 OK 和 Cancel 按钮
                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                button_box.accepted.connect(self.accept)
                button_box.rejected.connect(self.reject)
                self.layout.addWidget(button_box)

            def _setup_theme_group(self):
                theme_group = QGroupBox(self.tr("外观主题"))
                theme_layout = QVBoxLayout()
                
                self.dark_theme_radio = QRadioButton(self.tr("深色模式"))
                self.light_theme_radio = QRadioButton(self.tr("浅色模式"))

                current_theme = self.settings_manager.get_current_theme()
                if current_theme == 'dark':
                    self.dark_theme_radio.setChecked(True)
                else:
                    self.light_theme_radio.setChecked(True)

                # 当选项变化时，立即应用主题
                self.dark_theme_radio.toggled.connect(lambda: self.switch_theme('dark'))
                self.light_theme_radio.toggled.connect(lambda: self.switch_theme('light'))

                theme_layout.addWidget(self.dark_theme_radio)
                theme_layout.addWidget(self.light_theme_radio)
                theme_group.setLayout(theme_layout)
                self.layout.addWidget(theme_group)

            def switch_theme(self, theme_name: str):
                if self.sender().isChecked(): # 确保只有被选中的按钮会触发
                    self.settings_manager.set_current_theme(theme_name)
                    apply_theme(QApplication.instance(), theme_name)
        ```

3.  **连接主窗口与设置对话框**:
    -   在 `FeedbackUI` 中实现 `open_settings_dialog` 方法。
        ```python
        # feedback_ui/main_window.py
        from .dialogs.settings_dialog import SettingsDialog # 新增导入

        class FeedbackUI(QMainWindow):
            # ...
            def open_settings_dialog(self):
                dialog = SettingsDialog(self)
                dialog.exec() # 以模态方式打开对话框
        ```

### 步骤 2.7: 启动时应用主题

在 `main.py` 中，初始化 `FeedbackUI` 之前，加载并应用保存的主题。
```python
# main.py
# ...
app = QApplication(sys.argv)
settings = SettingsManager()
initial_theme = settings.get_current_theme()
apply_theme(app, initial_theme)

ui_window = FeedbackUI(...)
# ...
```

---

## 3. 第二阶段：实现中/英文语言切换

**目标**: 移除硬编码的双语文本，引入Qt i18n框架，实现动态单语言显示。

### 步骤 3.1: 代码文本重构 (关键)

遍历所有 `.py` 文件，将所有面向用户的字符串修改为 `self.tr("...")` 的形式。
-   **原则**: 以中文为源语言。
-   **示例**:
    -   `self.submit_button.setText("提交 (Submit)")` -> `self.submit_button.setText(self.tr("提交"))`
    -   `self.setWindowTitle("交互式反馈")` -> `self.setWindowTitle(self.tr("交互式反馈"))`
    -   `"这是一个很棒的功能！ (This is a great feature!)"` -> `self.tr("这是一个很棒的功能！")`

### 步骤 3.2: 创建与管理翻译文件

1.  **创建目录**:
    -   `feedback_ui/resources/translations/`
2.  **生成翻译源文件 (`.ts`)**:
    -   在项目**根目录**下运行命令：
        ```bash
        pyside6-lupdate -no-obsolete *.py feedback_ui/**/*.py -ts feedback_ui/resources/translations/en_US.ts
        ```
3.  **翻译**:
    -   使用 `Qt Linguist` 工具打开 `en_US.ts` 文件，将所有源字符串（中文）翻译为目标语言（英文）。
4.  **编译翻译文件 (`.qm`)**:
    -   翻译完成后，在项目**根目录**下运行命令：
        ```bash
        pyside6-lrelease feedback_ui/resources/translations/en_US.ts
        ```
    -   这会生成 `en_US.qm` 文件。

### 步骤 3.3: 更新资源文件并重新编译

将 `.qm` 文件添加到 `feedback_ui/resources/resources.qrc` 中，然后**重新运行** `pyside6-rcc` 命令。
```xml
<!-- resources.qrc (更新后) -->
<RCC version="1.0">
  <qresource prefix="/">
    <file alias="styles/dark.qss">../styles/dark_theme.qss</file>
    <file alias="styles/light.qss">../styles/light_theme.qss</file>
    <file alias="translations/en_US.qm">translations/en_US.qm</file>
  </qresource>
</RCC>
```
**重新编译命令**:
```bash
pyside6-rcc feedback_ui/resources/resources.qrc -o feedback_ui/resources_rc.py
```

### 步骤 3.4: 在 `SettingsManager` 中添加语言设置

```python
# feedback_ui/utils/settings_manager.py
def get_current_language(self) -> str:
    # 默认为 'zh_CN' (中文)
    return self.settings.value("ui/language", "zh_CN")

def set_current_language(self, lang_code: str):
    self.settings.setValue("ui/language", lang_code)
```

### 步骤 3.5: 应用语言切换逻辑

此步骤取代原有的菜单栏方案，将逻辑整合进 `SettingsDialog`。

1.  **启动时加载翻译**:
    -   `main.py` 中的启动逻辑保持不变，它会在应用启动时根据保存的设置加载正确的翻译文件。

2.  **在 `SettingsDialog` 中添加语言切换选项**:
    -   修改 `feedback_ui/dialogs/settings_dialog.py`，增加一个新的"语言设置"区域。
        ```python
        # feedback_ui/dialogs/settings_dialog.py (扩展后)
        # ... 其他导入
        from PySide6.QtWidgets import QMessageBox, QComboBox

        class SettingsDialog(QDialog):
            def __init__(self, parent=None):
                # ...
                self._setup_theme_group()
                self._setup_language_group() # 新增
                # ...

            def _setup_language_group(self):
                lang_group = QGroupBox(self.tr("语言"))
                lang_layout = QVBoxLayout()

                self.lang_combo = QComboBox()
                self.lang_combo.addItem(self.tr("中文"), "zh_CN")
                self.lang_combo.addItem(self.tr("English"), "en_US")

                current_lang = self.settings_manager.get_current_language()
                index = self.lang_combo.findData(current_lang)
                if index != -1:
                    self.lang_combo.setCurrentIndex(index)

                lang_layout.addWidget(self.lang_combo)
                lang_group.setLayout(lang_layout)
                self.layout.addWidget(lang_group)

            def accept(self):
                # 当用户点击OK时，保存语言设置
                selected_lang = self.lang_combo.currentData()
                current_lang = self.settings_manager.get_current_language()
                
                if selected_lang != current_lang:
                    self.settings_manager.set_current_language(selected_lang)
                    QMessageBox.information(self,
                        self.tr("设置已保存"),
                        self.tr("语言更改将在您下次启动应用时生效。")
                    )
                super().accept()
        ```
    -   **注意**: `accept` 方法被重写，用于在对话框关闭前检查语言设置是否已更改，并保存设置和提示用户。主题设置因为是即时生效的，所以无需在 `accept` 中处理。

</rewritten_file> 
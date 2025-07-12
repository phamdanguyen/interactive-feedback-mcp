# feedback_ui/utils/style_manager.py
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtWidgets import QApplication

from .settings_manager import SettingsManager

# 必须导入刚刚编译的资源模块，否则无法访问资源路径
# 注意：此导入是动态生成的，如果不存在，需要先编译.qrc文件
try:
    import feedback_ui.resources_rc
except ImportError:
    # 在某些情况下，直接运行此模块可能无法找到 `resources_rc`。
    # 确保在应用程序启动前已生成此文件。
    print(
        "Warning: Could not import resources_rc.py. Make sure it has been generated from resources.qrc."
    )


def apply_theme(app: QApplication, theme_name: str = "dark"):
    """根据主题名称加载并应用QSS样式，并附加动态字体大小。"""
    qss_path = f":/styles/{theme_name}.qss"
    qss_file = QFile(qss_path)

    base_stylesheet = ""
    if qss_file.open(QIODevice.ReadOnly | QIODevice.Text):
        base_stylesheet = qss_file.readAll().data().decode("utf-8")
        qss_file.close()
    else:
        print(f"错误：无法打开主题文件 {qss_path}")
        # 如果主题文件加载失败，提供一个基础的回退样式
        app.setStyleSheet("QWidget { background-color: #333; color: white; }")
        return

    # 设置QPalette以确保复选框等控件使用正确的颜色
    _apply_theme_palette(app, theme_name)

    # 从设置中获取动态字体大小
    settings_manager = SettingsManager()
    prompt_font_size = settings_manager.get_prompt_font_size()
    options_font_size = settings_manager.get_options_font_size()
    input_font_size = settings_manager.get_input_font_size()

    # 创建动态字体样式 - 恢复输入框独立的字体大小控制
    dynamic_font_style = f"""
/* Dynamically Applied Font Sizes */
SelectableLabel[class="prompt-label"] {{
    font-size: {prompt_font_size}pt;
}}
SelectableLabel[class="option-label"] {{
    font-size: {options_font_size}pt;
}}
QTextEdit, FeedbackTextEdit {{
    font-size: {input_font_size}pt;
}}
"""

    # 合并基础样式和动态字体样式
    final_stylesheet = base_stylesheet + "\n" + dynamic_font_style
    app.setStyleSheet(final_stylesheet)


def _apply_theme_palette(app: QApplication, theme_name: str):
    """为指定主题设置QPalette，确保控件颜色正确"""
    from PySide6.QtGui import QPalette, QColor

    palette = app.palette()

    if theme_name == "dark":
        # 深色主题的QPalette设置
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#4D4D4D"))  # 深灰色高亮
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor("#FFFFFF")
        )  # 白色高亮文本

        # 设置按钮和选择控件的颜色
        palette.setColor(QPalette.ColorRole.Button, QColor("#3C3C3C"))  # 按钮背景
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))  # 按钮文字

        # 设置选择控件的强调色（影响单选按钮、复选框等）
        palette.setColor(QPalette.ColorRole.Accent, QColor("#4D4D4D"))  # 深灰色强调色

        # 设置窗口和基础颜色
        palette.setColor(QPalette.ColorRole.Window, QColor("#2c2c2c"))  # 窗口背景
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#f0f0f0"))  # 窗口文字
        palette.setColor(QPalette.ColorRole.Base, QColor("#272727"))  # 输入框背景
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))  # 输入框文字

    else:
        # 浅色主题的QPalette设置 - 使用灰色而不是蓝色
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#6B6B6B"))  # 灰色高亮
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor("#FFFFFF")
        )  # 白色高亮文本

        # 设置按钮和选择控件的颜色
        palette.setColor(QPalette.ColorRole.Button, QColor("#e1e1e1"))  # 按钮背景
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#111111"))  # 按钮文字

        # 设置选择控件的强调色（影响单选按钮、复选框等）
        palette.setColor(QPalette.ColorRole.Accent, QColor("#6B6B6B"))  # 灰色强调色

        # 设置窗口和基础颜色
        palette.setColor(QPalette.ColorRole.Window, QColor("#f0f0f0"))  # 窗口背景
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#111111"))  # 窗口文字
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))  # 输入框背景
        palette.setColor(QPalette.ColorRole.Text, QColor("#111111"))  # 输入框文字

    app.setPalette(palette)

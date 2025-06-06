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

    # 从设置中获取动态字体大小
    settings_manager = SettingsManager()
    prompt_font_size = settings_manager.get_prompt_font_size()
    options_font_size = settings_manager.get_options_font_size()
    input_font_size = settings_manager.get_input_font_size()

    # 创建动态字体样式
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

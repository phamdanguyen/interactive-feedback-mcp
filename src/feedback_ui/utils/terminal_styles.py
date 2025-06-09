"""
终端样式工具
Terminal Style Utilities

提供统一的终端组件样式设置，避免重复代码。
Provides unified terminal component styling to avoid code duplication.
"""

from PySide6.QtGui import QFont


def get_terminal_font() -> QFont:
    """获取标准的终端字体"""
    font = QFont("Consolas", 10)
    if not font.exactMatch():
        font = QFont("Courier New", 10)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def get_terminal_stylesheet() -> str:
    """获取标准的终端样式表"""
    return """
        QTextEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: none;
            selection-background-color: #264f78;
            padding: 8px;
        }
    """


def get_input_stylesheet() -> str:
    """获取输入框的样式表"""
    return """
        QLineEdit {
            background-color: #1e1e1e;
            color: #ffffff;
            border: 1px solid #3c3c3c;
            padding: 5px;
        }
        QLineEdit:focus {
            border: 1px solid #007acc;
        }
    """


def get_terminal_window_stylesheet() -> str:
    """获取终端窗口的样式表"""
    return """
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QToolBar {
            background-color: #2d2d2d;
            border: none;
            spacing: 3px;
            padding: 4px;
        }
        QToolBar QToolButton {
            background-color: #3c3c3c;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 6px 12px;
            border-radius: 3px;
        }
        QToolBar QToolButton:hover {
            background-color: #4a4a4a;
            border-color: #007acc;
        }
        QToolBar QToolButton:pressed {
            background-color: #007acc;
        }
    """


def apply_terminal_style(widget):
    """为终端组件应用标准样式"""
    widget.setFont(get_terminal_font())

    # 根据组件类型应用不同的样式
    if hasattr(widget, "setStyleSheet"):
        if "QTextEdit" in str(type(widget)):
            widget.setStyleSheet(get_terminal_stylesheet())
        elif "QLineEdit" in str(type(widget)):
            widget.setStyleSheet(get_input_stylesheet())


def apply_terminal_window_style(window):
    """为终端窗口应用完整的原生终端样式"""
    window.setStyleSheet(get_terminal_window_stylesheet())

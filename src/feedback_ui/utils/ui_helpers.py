from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QLabel


def set_selection_colors(label: QLabel) -> None:
    """
    设置标签选择文本时的高亮颜色为灰色。
    Sets the text selection highlight color to gray for a label.

    Args:
        label (QLabel): 要设置高亮颜色的标签
    """
    palette = label.palette()
    # 设置选择区域的背景色为灰色 (RGB: 153, 153, 153)
    palette.setColor(QPalette.ColorRole.Highlight, QColor(153, 153, 153))
    # 设置选择区域的文本颜色为白色，确保在灰色背景上可读
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    label.setPalette(palette)

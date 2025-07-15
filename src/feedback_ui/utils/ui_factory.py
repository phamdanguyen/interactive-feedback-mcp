# src/feedback_ui/utils/ui_factory.py
"""
UI组件工厂
UI Component Factory

提供通用的UI组件创建函数，减少重复代码。
Provides common UI component creation functions to reduce code duplication.
"""

from typing import Callable, Optional, List, Tuple
from PySide6.QtWidgets import (
    QRadioButton,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QWidget,
    QPushButton,
    QLineEdit,
    QLabel,
)
from PySide6.QtCore import Qt


def create_radio_button_pair(
    text1: str,
    text2: str,
    checked_index: int = 0,
    callback1: Optional[Callable] = None,
    callback2: Optional[Callable] = None,
) -> Tuple[QRadioButton, QRadioButton, QHBoxLayout]:
    """
    创建一对单选按钮
    Create a pair of radio buttons

    Args:
        text1: 第一个按钮的文本
        text2: 第二个按钮的文本
        checked_index: 默认选中的按钮索引 (0 或 1)
        callback1: 第一个按钮的回调函数
        callback2: 第二个按钮的回调函数

    Returns:
        Tuple[QRadioButton, QRadioButton, QHBoxLayout]: (按钮1, 按钮2, 布局)
    """
    layout = QHBoxLayout()

    radio1 = QRadioButton(text1)
    radio2 = QRadioButton(text2)

    # 设置默认选中状态
    if checked_index == 0:
        radio1.setChecked(True)
    else:
        radio2.setChecked(True)

    # 连接回调函数
    if callback1:
        radio1.toggled.connect(callback1)
    if callback2:
        radio2.toggled.connect(callback2)

    layout.addWidget(radio1)
    layout.addWidget(radio2)

    return radio1, radio2, layout


def create_toggle_radio_button(
    text: str, checked: bool = False, callback: Optional[Callable] = None
) -> QRadioButton:
    """
    创建可切换的单选按钮（独立工作，不与其他按钮互斥）
    Create a toggle radio button (works independently, not exclusive with others)

    Args:
        text: 按钮文本
        checked: 是否默认选中
        callback: 回调函数

    Returns:
        QRadioButton: 配置好的单选按钮
    """
    radio = QRadioButton(text)
    radio.setCheckable(True)
    radio.setAutoExclusive(False)  # 不与其他单选按钮互斥
    radio.setChecked(checked)

    if callback:
        radio.toggled.connect(callback)

    return radio


def create_grouped_layout(
    title: str, widgets: List[QWidget], layout_type: str = "vertical"
) -> QGroupBox:
    """
    创建分组布局
    Create grouped layout

    Args:
        title: 分组标题
        widgets: 要添加的组件列表
        layout_type: 布局类型 ("vertical" 或 "horizontal")

    Returns:
        QGroupBox: 配置好的分组框
    """
    group = QGroupBox(title)

    if layout_type == "horizontal":
        layout = QHBoxLayout()
    else:
        layout = QVBoxLayout()

    for widget in widgets:
        layout.addWidget(widget)

    group.setLayout(layout)
    return group


def create_collapsible_section(
    title: str,
    content_widget: QWidget,
    expanded: bool = False,
    toggle_callback: Optional[Callable] = None,
) -> Tuple[QPushButton, QWidget]:
    """
    创建可折叠区域
    Create collapsible section

    Args:
        title: 标题文本
        content_widget: 内容组件
        expanded: 是否默认展开
        toggle_callback: 切换回调函数

    Returns:
        Tuple[QPushButton, QWidget]: (切换按钮, 内容组件)
    """
    toggle_button = QPushButton(f"{'▼' if expanded else '▶'} {title}")
    toggle_button.setCheckable(True)
    toggle_button.setChecked(expanded)

    # 设置简洁的按钮样式
    toggle_button.setStyleSheet(
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

    content_widget.setVisible(expanded)

    def on_toggle():
        is_expanded = toggle_button.isChecked()
        content_widget.setVisible(is_expanded)
        toggle_button.setText(f"{'▼' if is_expanded else '▶'} {title}")
        if toggle_callback:
            toggle_callback(is_expanded)

    toggle_button.clicked.connect(on_toggle)

    return toggle_button, content_widget


def create_input_field_with_label(
    label_text: str,
    placeholder: str = "",
    default_value: str = "",
    callback: Optional[Callable] = None,
) -> Tuple[QLabel, QLineEdit]:
    """
    创建带标签的输入框
    Create input field with label

    Args:
        label_text: 标签文本
        placeholder: 占位符文本
        default_value: 默认值
        callback: 文本变化回调函数

    Returns:
        Tuple[QLabel, QLineEdit]: (标签, 输入框)
    """
    label = QLabel(label_text)
    input_field = QLineEdit()

    if placeholder:
        input_field.setPlaceholderText(placeholder)
    if default_value:
        input_field.setText(default_value)

    if callback:
        input_field.textChanged.connect(callback)

    return label, input_field


def apply_theme_aware_styling(widget: QWidget, theme: str = "dark") -> None:
    """
    应用主题感知的样式 - 增强版本
    Apply theme-aware styling - Enhanced version

    Args:
        widget: 要应用样式的组件
        theme: 主题名称 ("dark" 或 "light")
    """
    if theme == "dark":
        # 深色主题样式
        style = """
        QRadioButton {
            color: #aaaaaa;
            spacing: 8px;
            min-height: 28px;
            padding: 1px;
        }
        QRadioButton::indicator {
            width: 22px; height: 22px;
            border: 2px solid #444444;
            border-radius: 11px;
            background-color: #2c2c2c;
        }
        QRadioButton::indicator:checked {
            background-color: #555555;
            border: 2px solid #666666;
            background-image: radial-gradient(circle, #ffffff 25%, #555555 30%);
        }
        QRadioButton::indicator:hover:!checked {
            border: 2px solid #666666;
            background-color: #3a3a3a;
        }
        QRadioButton::indicator:checked:hover {
            background-color: #666666;
            border: 2px solid #777777;
            background-image: radial-gradient(circle, #ffffff 25%, #666666 30%);
        }
        QCheckBox {
            color: #aaaaaa;
            spacing: 8px;
            min-height: 28px;
            padding: 1px;
        }
        QCheckBox::indicator {
            width: 22px; height: 22px;
            border: 2px solid #444444;
            border-radius: 4px;
            background-color: #2c2c2c;
        }
        QCheckBox::indicator:checked {
            background-color: #555555;
            border: 2px solid #666666;
            background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='%23ffffff' stroke='%23ffffff' stroke-width='1' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
            background-position: center;
            background-repeat: no-repeat;
        }
        QCheckBox::indicator:hover:!checked {
            border: 2px solid #666666;
            background-color: #3a3a3a;
        }
        QCheckBox::indicator:checked:hover {
            background-color: #666666;
            border: 2px solid #777777;
        }
        """
    else:
        # 浅色主题样式
        style = """
        QRadioButton {
            color: #666666;
            spacing: 8px;
            min-height: 28px;
            padding: 1px;
        }
        QRadioButton::indicator {
            width: 22px; height: 22px;
            border: 2px solid #adadad;
            border-radius: 11px;
            background-color: #ffffff;
        }
        QRadioButton::indicator:checked {
            background-color: #6B6B6B;
            border: 2px solid #777777;
            background-image: radial-gradient(circle, #ffffff 25%, #6B6B6B 30%);
        }
        QRadioButton::indicator:hover:!checked {
            border: 2px solid #777777;
            background-color: #f5f5f5;
        }
        QRadioButton::indicator:checked:hover {
            background-color: #777777;
            border: 2px solid #888888;
            background-image: radial-gradient(circle, #ffffff 25%, #777777 30%);
        }
        QCheckBox {
            color: #666666;
            spacing: 8px;
            min-height: 28px;
            padding: 1px;
        }
        QCheckBox::indicator {
            width: 22px; height: 22px;
            border: 2px solid #adadad;
            border-radius: 4px;
            background-color: #ffffff;
        }
        QCheckBox::indicator:checked {
            background-color: #6B6B6B;
            border: 2px solid #777777;
            background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='%23ffffff' stroke='%23ffffff' stroke-width='1' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
            background-position: center;
            background-repeat: no-repeat;
        }
        QCheckBox::indicator:hover:!checked {
            border: 2px solid #777777;
            background-color: #f5f5f5;
        }
        QCheckBox::indicator:checked:hover {
            background-color: #777777;
            border: 2px solid #888888;
        }
        """

    widget.setStyleSheet(style)


# 常用样式常量
COMMON_STYLES = {
    "small_font_label": "font-size: 10pt;",
    "tiny_font_label": "font-size: 9pt;",
    "compact_input": "font-size: 10pt; padding: 2px;",
    "small_button": "font-size: 8pt; padding: 2px; padding-top: -3px;",
    "input_dark": "QLineEdit { background-color: #2d2d2d; color: #ffffff; border: 1px solid #555555; padding: 4px; }",
    "input_light": "QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; padding: 4px; }",
}


def apply_common_style(widget: QWidget, style_name: str) -> None:
    """
    应用常用样式
    Apply common style

    Args:
        widget: 要应用样式的组件
        style_name: 样式名称
    """
    if style_name in COMMON_STYLES:
        widget.setStyleSheet(COMMON_STYLES[style_name])


def apply_enhanced_control_styling(widget: QWidget, theme: str = "dark") -> None:
    """
    为设置对话框中的控件应用增强的样式
    Apply enhanced styling for controls in settings dialogs

    Args:
        widget: 要应用样式的组件（通常是对话框或容器）
        theme: 主题名称 ("dark" 或 "light")
    """
    # 递归查找并应用样式到所有单选按钮和复选框
    from PySide6.QtWidgets import QRadioButton, QCheckBox

    def apply_to_children(parent):
        for child in parent.findChildren(QRadioButton):
            apply_theme_aware_styling(child, theme)
        for child in parent.findChildren(QCheckBox):
            apply_theme_aware_styling(child, theme)

    apply_to_children(widget)


def apply_input_theme_style(widget: QWidget, theme: str = "dark") -> None:
    """
    应用输入框主题样式
    Apply input field theme style

    Args:
        widget: 输入框组件
        theme: 主题名称
    """
    if theme == "dark":
        widget.setStyleSheet(COMMON_STYLES["input_dark"])
    else:
        widget.setStyleSheet(COMMON_STYLES["input_light"])

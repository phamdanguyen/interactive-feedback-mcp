# src/feedback_ui/utils/platform_utils.py
"""
平台相关工具函数
Platform-related utility functions

提供跨平台兼容性支持，包括操作系统检测和平台特定的UI文本。
Provides cross-platform compatibility support, including OS detection and platform-specific UI text.
"""

import platform
from typing import Dict, Tuple


def get_platform_info() -> Dict[str, str]:
    """
    获取平台信息
    Get platform information

    Returns:
        Dict[str, str]: 包含平台信息的字典
            - system: 操作系统名称 ('Windows', 'Darwin', 'Linux')
            - platform: 平台标识 ('windows', 'macos', 'linux')
            - modifier_key: 修饰键名称 ('Ctrl', 'Cmd')
            - modifier_symbol: 修饰键符号 ('Ctrl', '⌘')
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        return {
            "system": system,
            "platform": "macos",
            "modifier_key": "Cmd",
            "modifier_symbol": "⌘",
        }
    elif system == "Windows":
        return {
            "system": system,
            "platform": "windows",
            "modifier_key": "Ctrl",
            "modifier_symbol": "Ctrl",
        }
    else:  # Linux and others
        return {
            "system": system,
            "platform": "linux",
            "modifier_key": "Ctrl",
            "modifier_symbol": "Ctrl",
        }


def get_submit_shortcut_text(submit_method: str = "enter") -> Tuple[str, str]:
    """
    获取提交快捷键的显示文本
    Get submit shortcut display text

    Args:
        submit_method: 提交方式 ('enter' 或 'ctrl_enter')

    Returns:
        Tuple[str, str]: (中文文本, 英文文本)
    """
    platform_info = get_platform_info()
    modifier_key = platform_info["modifier_key"]
    modifier_symbol = platform_info["modifier_symbol"]

    if submit_method == "ctrl_enter":
        zh_text = f"{modifier_symbol}+Enter提交"
        en_text = f"{modifier_key}+Enter to submit"
    else:  # enter
        zh_text = "Enter提交"
        en_text = "Enter to submit"

    return zh_text, en_text


def get_submit_method_options() -> Dict[str, Dict[str, str]]:
    """
    获取提交方式选项的显示文本
    Get submit method options display text

    Returns:
        Dict[str, Dict[str, str]]: 提交方式选项的多语言文本
    """
    platform_info = get_platform_info()
    modifier_key = platform_info["modifier_key"]
    modifier_symbol = platform_info["modifier_symbol"]

    return {
        "enter": {"zh_CN": "Enter键直接提交", "en_US": "Enter key to submit"},
        "ctrl_enter": {
            "zh_CN": f"{modifier_symbol}+Enter组合键提交",
            "en_US": f"{modifier_key}+Enter to submit",
        },
    }


def get_placeholder_text(submit_method: str = "enter", language: str = "zh_CN") -> str:
    """
    获取输入框占位符文本
    Get input placeholder text

    Args:
        submit_method: 提交方式 ('enter' 或 'ctrl_enter')
        language: 语言代码 ('zh_CN' 或 'en_US')

    Returns:
        str: 占位符文本
    """
    platform_info = get_platform_info()
    modifier_key = platform_info["modifier_key"]
    modifier_symbol = platform_info["modifier_symbol"]

    if language == "zh_CN":
        if submit_method == "ctrl_enter":
            return f"在此输入反馈... (可拖拽文件和图片到输入框，{modifier_symbol}+Enter提交反馈，Shift+Enter换行，Ctrl+V复制剪切板信息)"
        else:
            return "在此输入反馈... (可拖拽文件和图片到输入框，Enter提交反馈，Shift+Enter换行，Ctrl+V复制剪切板信息)"
    else:  # en_US
        if submit_method == "ctrl_enter":
            return f"Enter feedback here... (Drag files and images to input box, {modifier_key}+Enter to submit, Shift+Enter for newline, Ctrl+V to paste)"
        else:
            return "Enter feedback here... (Drag files and images to input box, Enter to submit, Shift+Enter for newline, Ctrl+V to paste)"


def is_macos() -> bool:
    """
    检查是否为macOS系统
    Check if running on macOS

    Returns:
        bool: 是否为macOS
    """
    return platform.system() == "Darwin"


def is_windows() -> bool:
    """
    检查是否为Windows系统
    Check if running on Windows

    Returns:
        bool: 是否为Windows
    """
    return platform.system() == "Windows"


def is_linux() -> bool:
    """
    检查是否为Linux系统
    Check if running on Linux

    Returns:
        bool: 是否为Linux
    """
    return platform.system() == "Linux"


# 注意：get_modifier_key_for_platform 和 get_modifier_symbol_for_platform 函数已移除
# 请直接使用 get_platform_info()["modifier_key"] 和 get_platform_info()["modifier_symbol"]

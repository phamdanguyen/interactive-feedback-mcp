# feedback_ui/utils/constants.py
from typing import Optional, TypedDict, List

# --- 常量定义 (Constant Definitions) ---
APP_NAME = "InteractiveFeedbackMCP"
SETTINGS_GROUP_MAIN = "MainWindow_General"
SETTINGS_GROUP_CANNED_RESPONSES = "CannedResponses"
SETTINGS_KEY_GEOMETRY = "geometry"
SETTINGS_KEY_WINDOW_STATE = "windowState"
SETTINGS_KEY_WINDOW_PINNED = "windowPinned"
SETTINGS_KEY_PHRASES = "phrases"
SETTINGS_KEY_SHOW_SHORTCUT_ICONS = "showShortcutIcons"
SETTINGS_KEY_NUMBER_ICONS_VISIBLE = "numberIconsVisible"

# 字体大小设置 (Font Size Settings)
SETTINGS_GROUP_FONTS = "FontSettings"
SETTINGS_KEY_PROMPT_FONT_SIZE = "promptFontSize"
SETTINGS_KEY_OPTIONS_FONT_SIZE = "optionsFontSize"
SETTINGS_KEY_INPUT_FONT_SIZE = "inputFontSize"

# 默认字体大小 (Default Font Sizes)
DEFAULT_PROMPT_FONT_SIZE = 16
DEFAULT_OPTIONS_FONT_SIZE = 13
DEFAULT_INPUT_FONT_SIZE = 13

MAX_IMAGE_WIDTH = 512
MAX_IMAGE_HEIGHT = 512
MAX_IMAGE_BYTES = 1048576  # 1MB (1兆字节)

# --- 类型定义 (Type Definitions) ---
class ContentItem(TypedDict):
    """
    Represents a single piece of content, which can be text, image, or file reference.
    Corresponds to MCP message format.
    表示单个内容项，可以是文本、图像或文件引用。
    对应 MCP 消息格式。
    """
    type: str
    text: Optional[str]  # Used for text type (用于文本类型)
    data: Optional[str]  # Used for image type (base64 encoded) (用于图像类型，base64编码)
    mimeType: Optional[str]  # Used for image type (e.g., "image/jpeg") (用于图像类型)
    display_name: Optional[str] # For file_reference type (e.g., "@filename.txt") (用于文件引用类型)
    path: Optional[str]         # Full path to the file for file_reference type (文件引用的完整路径)


class FeedbackResult(TypedDict):
    """
    The structured result returned by the feedback UI, containing a list of content items.
    反馈UI返回的结构化结果，包含内容项列表。
    """
    content: List[ContentItem]

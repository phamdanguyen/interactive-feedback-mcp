# feedback_ui/utils/constants.py
from typing import TypedDict

# --- 常量定义 (Constant Definitions) ---
APP_NAME = "InteractiveFeedbackMCP"
SETTINGS_GROUP_MAIN = "MainWindow_General"
SETTINGS_GROUP_CANNED_RESPONSES = "CannedResponses"
SETTINGS_KEY_GEOMETRY = "geometry"
SETTINGS_KEY_WINDOW_STATE = "windowState"
SETTINGS_KEY_WINDOW_PINNED = "windowPinned"
SETTINGS_KEY_PHRASES = "phrases"

# 分割器设置 (Splitter Settings)
SETTINGS_KEY_SPLITTER_SIZES = "splitterSizes"
SETTINGS_KEY_SPLITTER_STATE = "splitterState"

# 字体大小设置 (Font Size Settings)
SETTINGS_GROUP_FONTS = "FontSettings"
SETTINGS_KEY_PROMPT_FONT_SIZE = "promptFontSize"
SETTINGS_KEY_OPTIONS_FONT_SIZE = "optionsFontSize"
SETTINGS_KEY_INPUT_FONT_SIZE = "inputFontSize"

# 默认字体大小 (Default Font Sizes)
DEFAULT_PROMPT_FONT_SIZE = 16
DEFAULT_OPTIONS_FONT_SIZE = 13
DEFAULT_INPUT_FONT_SIZE = 13

# 默认分割器配置 (Default Splitter Configuration)
DEFAULT_UPPER_AREA_HEIGHT = 250
DEFAULT_LOWER_AREA_HEIGHT = 400
DEFAULT_SPLITTER_RATIO = [250, 400]  # 上:下 = 250:400

# 最小区域高度限制 (Minimum Area Height Limits)
MIN_UPPER_AREA_HEIGHT = 150
MIN_LOWER_AREA_HEIGHT = 200

# 布局方向常量 (Layout Direction Constants)
LAYOUT_VERTICAL = "vertical"  # 上下布局
LAYOUT_HORIZONTAL = "horizontal"  # 左右布局
DEFAULT_LAYOUT_DIRECTION = LAYOUT_VERTICAL

# 布局设置键 (Layout Settings Keys)
SETTINGS_KEY_LAYOUT_DIRECTION = "ui/layout_direction"
SETTINGS_KEY_HORIZONTAL_SPLITTER_SIZES = "ui/horizontal_splitter_sizes"
SETTINGS_KEY_HORIZONTAL_SPLITTER_STATE = "ui/horizontal_splitter_state"

# 默认水平分割比例 (Default Horizontal Splitter Configuration)
# 调整为5:5比例，给左侧更多空间展示长文本和选项
DEFAULT_HORIZONTAL_SPLITTER_RATIO = [500, 500]  # 左右比例 5:5
MIN_LEFT_AREA_WIDTH = 350  # 增加左侧最小宽度以容纳更多内容
MIN_RIGHT_AREA_WIDTH = 400

MAX_IMAGE_WIDTH = 512
MAX_IMAGE_HEIGHT = 512
MAX_IMAGE_BYTES = 2097152  # 2MB (2兆字节)

# 图像压缩相关常量 (Image Compression Constants)
IMAGE_QUALITY = 100  # JPEG质量 (100% = 无损压缩)
IMAGE_SCALE_FACTOR = 0.8  # 尺寸缩放因子

# 支持的图片文件扩展名 (Supported Image File Extensions)
SUPPORTED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]


# --- 类型定义 (Type Definitions) ---
class ContentItem(TypedDict):
    """
    Represents a single piece of content, which can be text, image, or file reference.
    Corresponds to MCP message format.
    表示单个内容项，可以是文本、图像或文件引用。
    对应 MCP 消息格式。
    """

    type: str
    text: str | None  # Used for text type (用于文本类型)
    data: str | None  # Used for image type (base64 encoded) (用于图像类型，base64编码)
    mimeType: str | None  # Used for image type (e.g., "image/jpeg") (用于图像类型)
    display_name: (
        str | None
    )  # For file_reference type (e.g., "@filename.txt") (用于文件引用类型)
    path: (
        str | None
    )  # Full path to the file for file_reference type (文件引用的完整路径)


class FeedbackResult(TypedDict):
    """
    The structured result returned by the feedback UI, containing a list of content items.
    反馈UI返回的结构化结果，包含内容项列表。
    """

    content: list[ContentItem]


# --- 终端相关常量 (Terminal Constants) ---
TERMINAL_POWERSHELL = "powershell"
TERMINAL_GITBASH = "gitbash"
TERMINAL_CMD = "cmd"

DEFAULT_TERMINAL_TYPE = TERMINAL_POWERSHELL

# 终端类型定义
TERMINAL_TYPES = {
    TERMINAL_POWERSHELL: {
        "name": "PowerShell",
        "display_name": "PowerShell (pwsh)",
        "icon": "🔷",
        "description": "Windows PowerShell 或 PowerShell Core",
        "detection_commands": ["pwsh.exe", "powershell.exe"],
        "detection_paths": [
            r"C:\Program Files\PowerShell\7\pwsh.exe",
            r"C:\Program Files\PowerShell\6\pwsh.exe",
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        ],
    },
    TERMINAL_GITBASH: {
        "name": "Git Bash",
        "display_name": "Git Bash (bash)",
        "icon": "🔶",
        "description": "Git for Windows 提供的 Bash 环境",
        "detection_commands": ["bash.exe"],
        "detection_paths": [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ],
    },
    TERMINAL_CMD: {
        "name": "Command Prompt",
        "display_name": "Command Prompt (cmd)",
        "icon": "⬛",
        "description": "Windows 命令提示符",
        "detection_commands": ["cmd.exe"],
        "detection_paths": [r"C:\Windows\System32\cmd.exe"],
    },
}

# 终端设置相关常量
SETTINGS_GROUP_TERMINAL = "Terminal"
SETTINGS_KEY_DEFAULT_TERMINAL = "default_terminal_type"
SETTINGS_KEY_TERMINAL_PATH_PREFIX = "terminal_path_"

# 选项间距相关常量 (Option Spacing Constants)
DEFAULT_OPTION_SPACING = 8  # 默认选项间距
MAX_OPTION_SPACING = 24  # 最大选项间距（3倍限制）
MIN_OPTION_SPACING = 6  # 最小选项间距
OPTION_SPACING_MULTIPLIER = 3  # 间距倍数限制

# 截图功能相关常量 (Screenshot Feature Constants)
SCREENSHOT_MIN_SIZE = 10  # 最小截图尺寸（像素）
SCREENSHOT_OVERLAY_OPACITY = 100  # 遮罩透明度 (0-255)
SCREENSHOT_BORDER_COLOR = (0, 120, 215)  # 选择框边框颜色 (RGB)
SCREENSHOT_BORDER_WIDTH = 2  # 选择框边框宽度
SCREENSHOT_TEXT_COLOR = (255, 255, 255)  # 尺寸文本颜色 (RGB)
SCREENSHOT_WINDOW_MINIMIZE_DELAY = 500  # 主窗口最小化延迟（毫秒）
SCREENSHOT_FOCUS_DELAY = 100  # 截图后焦点设置延迟（毫秒）

# feedback_ui/utils/settings_manager.py

from PySide6.QtCore import QByteArray, QObject, QSettings

from .constants import (
    APP_NAME,
    DEFAULT_HORIZONTAL_SPLITTER_RATIO,
    DEFAULT_INPUT_FONT_SIZE,
    DEFAULT_LAYOUT_DIRECTION,
    DEFAULT_OPTIONS_FONT_SIZE,
    DEFAULT_PROMPT_FONT_SIZE,
    DEFAULT_SPLITTER_RATIO,
    SETTINGS_GROUP_CANNED_RESPONSES,
    SETTINGS_GROUP_FONTS,
    SETTINGS_GROUP_MAIN,
    SETTINGS_KEY_GEOMETRY,
    SETTINGS_KEY_HORIZONTAL_SPLITTER_SIZES,
    SETTINGS_KEY_HORIZONTAL_SPLITTER_STATE,
    SETTINGS_KEY_INPUT_FONT_SIZE,
    SETTINGS_KEY_LAYOUT_DIRECTION,
    SETTINGS_KEY_OPTIONS_FONT_SIZE,
    SETTINGS_KEY_PHRASES,
    SETTINGS_KEY_PROMPT_FONT_SIZE,
    SETTINGS_KEY_SPLITTER_SIZES,
    SETTINGS_KEY_SPLITTER_STATE,
    SETTINGS_KEY_WINDOW_PINNED,
    SETTINGS_KEY_WINDOW_STATE,
)


class SettingsManager(QObject):
    """
    Manages application settings using QSettings.
    使用 QSettings 管理应用程序设置。
    """

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        # 在 Qt 中，通常使用组织名称和应用程序名称。
        # 如果您的应用程序很简单，可以为两者使用相同的名称。
        # In Qt, organization name and application name are typically used.
        # If your app is simple, you can use the same name for both.
        self.settings = QSettings(APP_NAME, APP_NAME)

    # --- Main Window Settings (主窗口设置) ---
    def get_main_window_geometry(self) -> QByteArray | None:
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        # Provide a default value of None if not found or wrong type
        # 如果未找到或类型错误，则提供默认值 None
        geometry = self.settings.value(SETTINGS_KEY_GEOMETRY, defaultValue=None)
        self.settings.endGroup()
        return geometry if isinstance(geometry, QByteArray) else None

    def set_main_window_geometry(self, geometry: QByteArray):
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_GEOMETRY, geometry)
        self.settings.endGroup()
        self.settings.sync()  # 确保设置立即写入 (Ensure settings are written immediately)

    def get_main_window_state(self) -> QByteArray | None:
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        state = self.settings.value(SETTINGS_KEY_WINDOW_STATE, defaultValue=None)
        self.settings.endGroup()
        return state if isinstance(state, QByteArray) else None

    def set_main_window_state(self, state: QByteArray):
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_WINDOW_STATE, state)
        self.settings.endGroup()
        self.settings.sync()

    def get_main_window_size(self) -> tuple | None:
        """获取保存的窗口大小 (宽, 高)"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        width = self.settings.value("window_width", defaultValue=None, type=int)
        height = self.settings.value("window_height", defaultValue=None, type=int)
        self.settings.endGroup()

        if width is not None and height is not None:
            return (width, height)
        return None

    def set_main_window_size(self, width: int, height: int):
        """单独保存窗口大小 (宽, 高)"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue("window_width", width)
        self.settings.setValue("window_height", height)
        self.settings.endGroup()
        self.settings.sync()

    def get_main_window_position(self) -> tuple[int, int] | None:
        """获取保存的窗口位置 (x, y)"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        x = self.settings.value("window_x", defaultValue=None, type=int)
        y = self.settings.value("window_y", defaultValue=None, type=int)
        self.settings.endGroup()

        if x is not None and y is not None:
            return (x, y)
        return None

    def set_main_window_position(self, x: int, y: int):
        """保存窗口位置 (x, y)"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue("window_x", x)
        self.settings.setValue("window_y", y)
        self.settings.endGroup()
        self.settings.sync()

    def get_main_window_pinned(self) -> bool:
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        # Default to False if not found
        pinned = self.settings.value(SETTINGS_KEY_WINDOW_PINNED, False, type=bool)
        self.settings.endGroup()
        return pinned

    def set_main_window_pinned(self, pinned: bool):
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_WINDOW_PINNED, pinned)
        self.settings.endGroup()
        self.settings.sync()

    # --- Canned Responses Settings (常用语设置) ---
    def get_canned_responses(self) -> list[str]:
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        responses = self.settings.value(
            SETTINGS_KEY_PHRASES, []
        )  # Default to empty list
        self.settings.endGroup()

        if responses is None:
            return []
        # 确保它是字符串列表，并过滤掉空/仅空白的字符串
        # Ensure it's a list of strings, filter out empty/whitespace-only strings
        return (
            [str(r) for r in responses if isinstance(r, str) and str(r).strip()]
            if isinstance(responses, list)
            else []
        )

    def set_canned_responses(self, responses: list[str]):
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        self.settings.setValue(SETTINGS_KEY_PHRASES, responses)
        self.settings.endGroup()
        self.settings.sync()

    # --- Splitter Settings (分割器设置) ---
    def get_splitter_sizes(self) -> list[int]:
        """获取保存的分割器尺寸比例"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        sizes = self.settings.value(SETTINGS_KEY_SPLITTER_SIZES, DEFAULT_SPLITTER_RATIO)
        self.settings.endGroup()

        # 确保返回有效的整数列表
        if isinstance(sizes, list) and len(sizes) == 2:
            try:
                return [int(sizes[0]), int(sizes[1])]
            except (ValueError, TypeError):
                return DEFAULT_SPLITTER_RATIO
        return DEFAULT_SPLITTER_RATIO

    def set_splitter_sizes(self, sizes: list[int]):
        """保存分割器尺寸比例"""
        if len(sizes) == 2:
            self.settings.beginGroup(SETTINGS_GROUP_MAIN)
            self.settings.setValue(SETTINGS_KEY_SPLITTER_SIZES, sizes)
            self.settings.endGroup()
            self.settings.sync()

    def get_splitter_state(self) -> QByteArray | None:
        """获取分割器状态"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        state = self.settings.value(SETTINGS_KEY_SPLITTER_STATE, None)
        self.settings.endGroup()
        return state if isinstance(state, (QByteArray, type(None))) else None

    def set_splitter_state(self, state: QByteArray):
        """保存分割器状态"""
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_SPLITTER_STATE, state)
        self.settings.endGroup()
        self.settings.sync()

    def get_current_theme(self) -> str:
        # 从配置中读取主题设置，若无则默认为 'dark'
        return self.settings.value("ui/theme", "dark")

    def set_current_theme(self, theme_name: str):
        self.settings.setValue("ui/theme", theme_name)
        self.settings.sync()

    def get_current_language(self) -> str:
        # 默认为 'zh_CN' (中文)
        return self.settings.value("ui/language", "zh_CN")

    def set_current_language(self, lang_code: str):
        self.settings.setValue("ui/language", lang_code)
        self.settings.sync()

    # --- 布局方向设置 (Layout Direction Settings) ---
    def get_layout_direction(self) -> str:
        """获取布局方向设置"""
        return self.settings.value(
            SETTINGS_KEY_LAYOUT_DIRECTION, DEFAULT_LAYOUT_DIRECTION
        )

    def set_layout_direction(self, direction: str):
        """设置布局方向"""
        self.settings.setValue(SETTINGS_KEY_LAYOUT_DIRECTION, direction)
        self.settings.sync()

    # --- 水平分割器设置 (Horizontal Splitter Settings) ---
    def get_horizontal_splitter_sizes(self) -> list:
        """获取水平分割器尺寸"""
        try:
            sizes = self.settings.value(
                SETTINGS_KEY_HORIZONTAL_SPLITTER_SIZES,
                DEFAULT_HORIZONTAL_SPLITTER_RATIO,
            )
            if isinstance(sizes, list) and len(sizes) == 2:
                return [int(size) for size in sizes]
        except (ValueError, TypeError):
            pass
        return DEFAULT_HORIZONTAL_SPLITTER_RATIO

    def set_horizontal_splitter_sizes(self, sizes: list):
        """设置水平分割器尺寸"""
        if isinstance(sizes, list) and len(sizes) == 2:
            self.settings.setValue(SETTINGS_KEY_HORIZONTAL_SPLITTER_SIZES, sizes)
            self.settings.sync()

    def get_horizontal_splitter_state(self) -> bytes:
        """获取水平分割器状态"""
        state = self.settings.value(SETTINGS_KEY_HORIZONTAL_SPLITTER_STATE, b"")
        return state if isinstance(state, bytes) else b""

    def set_horizontal_splitter_state(self, state: bytes):
        """设置水平分割器状态"""
        if isinstance(state, bytes):
            self.settings.setValue(SETTINGS_KEY_HORIZONTAL_SPLITTER_STATE, state)
            self.settings.sync()

    # --- 字体大小设置 (Font Size Settings) ---
    def get_prompt_font_size(self) -> int:
        """获取提示区域字体大小"""
        self.settings.beginGroup(SETTINGS_GROUP_FONTS)
        size = self.settings.value(
            SETTINGS_KEY_PROMPT_FONT_SIZE, DEFAULT_PROMPT_FONT_SIZE, type=int
        )
        self.settings.endGroup()
        return size

    def set_prompt_font_size(self, size: int):
        """设置提示区域字体大小"""
        self.settings.beginGroup(SETTINGS_GROUP_FONTS)
        self.settings.setValue(SETTINGS_KEY_PROMPT_FONT_SIZE, size)
        self.settings.endGroup()
        self.settings.sync()

    def get_options_font_size(self) -> int:
        """获取选项区域字体大小"""
        self.settings.beginGroup(SETTINGS_GROUP_FONTS)
        size = self.settings.value(
            SETTINGS_KEY_OPTIONS_FONT_SIZE, DEFAULT_OPTIONS_FONT_SIZE, type=int
        )
        self.settings.endGroup()
        return size

    def set_options_font_size(self, size: int):
        """设置选项区域字体大小"""
        self.settings.beginGroup(SETTINGS_GROUP_FONTS)
        self.settings.setValue(SETTINGS_KEY_OPTIONS_FONT_SIZE, size)
        self.settings.endGroup()
        self.settings.sync()

    def get_input_font_size(self) -> int:
        """获取输入框字体大小"""
        self.settings.beginGroup(SETTINGS_GROUP_FONTS)
        size = self.settings.value(
            SETTINGS_KEY_INPUT_FONT_SIZE, DEFAULT_INPUT_FONT_SIZE, type=int
        )
        self.settings.endGroup()
        return size

    def set_input_font_size(self, size: int):
        """设置输入框字体大小"""
        self.settings.beginGroup(SETTINGS_GROUP_FONTS)
        self.settings.setValue(SETTINGS_KEY_INPUT_FONT_SIZE, size)
        self.settings.endGroup()
        self.settings.sync()

    # --- Terminal Window Settings (终端窗口设置) ---
    def get_terminal_window_geometry(self) -> QByteArray | None:
        """获取终端窗口几何信息"""
        self.settings.beginGroup("TerminalWindow")
        geometry = self.settings.value("geometry", defaultValue=None)
        self.settings.endGroup()
        return geometry if isinstance(geometry, QByteArray) else None

    def set_terminal_window_geometry(self, geometry: QByteArray):
        """保存终端窗口几何信息"""
        self.settings.beginGroup("TerminalWindow")
        self.settings.setValue("geometry", geometry)
        self.settings.endGroup()
        self.settings.sync()

    # --- Terminal Settings (终端设置) ---
    def get_default_terminal_type(self) -> str:
        """获取默认终端类型"""
        from .constants import DEFAULT_TERMINAL_TYPE, SETTINGS_KEY_DEFAULT_TERMINAL

        self.settings.beginGroup("Terminal")
        terminal_type = self.settings.value(
            SETTINGS_KEY_DEFAULT_TERMINAL, DEFAULT_TERMINAL_TYPE
        )
        self.settings.endGroup()
        return terminal_type

    def set_default_terminal_type(self, terminal_type: str):
        """设置默认终端类型"""
        from .constants import SETTINGS_KEY_DEFAULT_TERMINAL

        self.settings.beginGroup("Terminal")
        self.settings.setValue(SETTINGS_KEY_DEFAULT_TERMINAL, terminal_type)
        self.settings.endGroup()
        self.settings.sync()

    def get_terminal_path(self, terminal_type: str) -> str:
        """获取指定终端的自定义路径"""
        from .constants import SETTINGS_KEY_TERMINAL_PATH_PREFIX

        self.settings.beginGroup("Terminal")
        path = self.settings.value(
            f"{SETTINGS_KEY_TERMINAL_PATH_PREFIX}{terminal_type}", ""
        )
        self.settings.endGroup()
        return path

    def set_terminal_path(self, terminal_type: str, path: str):
        """设置指定终端的自定义路径"""
        from .constants import SETTINGS_KEY_TERMINAL_PATH_PREFIX

        self.settings.beginGroup("Terminal")
        self.settings.setValue(
            f"{SETTINGS_KEY_TERMINAL_PATH_PREFIX}{terminal_type}", path
        )
        self.settings.endGroup()
        self.settings.sync()

    # --- Audio Settings (音频设置) ---
    def get_audio_enabled(self) -> bool:
        """获取音频是否启用"""
        return self.settings.value("audio/enabled", True, type=bool)

    def set_audio_enabled(self, enabled: bool):
        """设置音频是否启用"""
        self.settings.setValue("audio/enabled", enabled)
        self.settings.sync()

    def get_audio_volume(self) -> float:
        """获取音频音量 (0.0-1.0)"""
        volume = self.settings.value("audio/volume", 0.5, type=float)
        return max(0.0, min(1.0, volume))  # 确保在有效范围内

    def set_audio_volume(self, volume: float):
        """设置音频音量 (0.0-1.0)"""
        volume = max(0.0, min(1.0, volume))  # 确保在有效范围内
        self.settings.setValue("audio/volume", volume)
        self.settings.sync()

    def get_notification_sound_path(self) -> str:
        """获取提示音文件路径"""
        return self.settings.value("audio/notification_sound_path", "")

    def set_notification_sound_path(self, path: str):
        """设置提示音文件路径"""
        self.settings.setValue("audio/notification_sound_path", path)
        self.settings.sync()

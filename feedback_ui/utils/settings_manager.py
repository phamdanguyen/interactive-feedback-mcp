# feedback_ui/utils/settings_manager.py
from PySide6.QtCore import QSettings, QByteArray, QObject
from typing import Any, List, Optional

from .constants import (
    APP_NAME, SETTINGS_GROUP_MAIN, SETTINGS_GROUP_CANNED_RESPONSES,
    SETTINGS_KEY_GEOMETRY, SETTINGS_KEY_WINDOW_STATE, SETTINGS_KEY_WINDOW_PINNED,
    SETTINGS_KEY_PHRASES, SETTINGS_KEY_SHOW_SHORTCUT_ICONS, SETTINGS_KEY_NUMBER_ICONS_VISIBLE
)

class SettingsManager(QObject):
    """
    Manages application settings using QSettings.
    使用 QSettings 管理应用程序设置。
    """
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        # 在 Qt 中，通常使用组织名称和应用程序名称。
        # 如果您的应用程序很简单，可以为两者使用相同的名称。
        # In Qt, organization name and application name are typically used.
        # If your app is simple, you can use the same name for both.
        self.settings = QSettings(APP_NAME, APP_NAME) 

    # --- Main Window Settings (主窗口设置) ---
    def get_main_window_geometry(self) -> Optional[QByteArray]:
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
        self.settings.sync() #确保设置立即写入 (Ensure settings are written immediately)

    def get_main_window_state(self) -> Optional[QByteArray]:
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        state = self.settings.value(SETTINGS_KEY_WINDOW_STATE, defaultValue=None)
        self.settings.endGroup()
        return state if isinstance(state, QByteArray) else None

    def set_main_window_state(self, state: QByteArray):
        self.settings.beginGroup(SETTINGS_GROUP_MAIN)
        self.settings.setValue(SETTINGS_KEY_WINDOW_STATE, state)
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
    def get_canned_responses(self) -> List[str]:
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        responses = self.settings.value(SETTINGS_KEY_PHRASES, []) # Default to empty list
        self.settings.endGroup()
        
        if responses is None: return []
        # 确保它是字符串列表，并过滤掉空/仅空白的字符串
        # Ensure it's a list of strings, filter out empty/whitespace-only strings
        return [str(r) for r in responses if isinstance(r, str) and str(r).strip()] if isinstance(responses, list) else []


    def set_canned_responses(self, responses: List[str]):
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        self.settings.setValue(SETTINGS_KEY_PHRASES, responses)
        self.settings.endGroup()
        self.settings.sync()

    def get_show_shortcut_icons(self) -> bool:
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        show = self.settings.value(SETTINGS_KEY_SHOW_SHORTCUT_ICONS, True, type=bool)
        self.settings.endGroup()
        return show

    def set_show_shortcut_icons(self, show: bool):
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        self.settings.setValue(SETTINGS_KEY_SHOW_SHORTCUT_ICONS, show)
        self.settings.endGroup()
        self.settings.sync()

    def get_number_icons_visible(self) -> bool:
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        visible = self.settings.value(SETTINGS_KEY_NUMBER_ICONS_VISIBLE, True, type=bool)
        self.settings.endGroup()
        return visible

    def set_number_icons_visible(self, visible: bool):
        self.settings.beginGroup(SETTINGS_GROUP_CANNED_RESPONSES)
        self.settings.setValue(SETTINGS_KEY_NUMBER_ICONS_VISIBLE, visible)
        self.settings.endGroup()
        self.settings.sync()

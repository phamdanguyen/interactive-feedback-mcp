# interactive_feedback_server/plugins/__init__.py

"""
插件系统模块
Plugin System Module

提供插件化架构的核心功能，支持动态加载和热重载。
Provides core functionality for plugin architecture with dynamic loading and hot reload support.
"""

from .plugin_interface import (
    PluginInterface,
    BasePlugin,
    PluginMetadata,
    PluginContext,
    PluginType,
    PluginStatus,
    PluginEventHandler,
)

from .plugin_manager import PluginManager, get_plugin_manager

__all__ = [
    # 插件接口
    "PluginInterface",
    "BasePlugin",
    "PluginMetadata",
    "PluginContext",
    "PluginType",
    "PluginStatus",
    "PluginEventHandler",
    # 插件管理器
    "PluginManager",
    "get_plugin_manager",
]

__version__ = "3.3.0"

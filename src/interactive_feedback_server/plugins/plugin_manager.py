# interactive_feedback_server/plugins/plugin_manager.py

"""
插件管理器 - V3.3 架构改进版本
Plugin Manager - V3.3 Architecture Improvement Version

提供插件的发现、加载、管理和热重载功能。
Provides plugin discovery, loading, management and hot reload functionality.
"""

import os
import sys
import importlib
import importlib.util
import threading
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import json

from .plugin_interface import (
    PluginInterface,
    PluginMetadata,
    PluginContext,
    PluginType,
    PluginStatus,
    PluginEventHandler,
)


class PluginManager:
    """
    插件管理器
    Plugin Manager

    负责插件的生命周期管理、发现和加载
    Responsible for plugin lifecycle management, discovery and loading
    """

    def __init__(self, plugin_dirs: List[str] = None, system_version: str = "3.3.0"):
        """
        初始化插件管理器
        Initialize plugin manager

        Args:
            plugin_dirs: 插件目录列表
            system_version: 系统版本
        """
        self.system_version = system_version
        self.plugin_dirs = plugin_dirs or []

        # 插件存储
        self._plugins: Dict[str, PluginInterface] = {}
        self._plugin_modules: Dict[str, Any] = {}

        # 线程安全
        self._lock = threading.RLock()

        # 事件处理
        self.event_handler = PluginEventHandler()

        # 管理器统计
        self._stats = {
            "total_discovered": 0,
            "total_loaded": 0,
            "total_active": 0,
            "total_errors": 0,
            "discovery_count": 0,
        }

        # 默认插件目录
        self._add_default_plugin_dirs()

    def _add_default_plugin_dirs(self) -> None:
        """添加默认插件目录"""
        # 当前项目的插件目录
        current_dir = Path(__file__).parent
        default_dirs = [
            str(current_dir / "builtin"),  # 内置插件
            str(current_dir / "external"),  # 外部插件
            str(current_dir / "user"),  # 用户插件
        ]

        for dir_path in default_dirs:
            if dir_path not in self.plugin_dirs:
                self.plugin_dirs.append(dir_path)

    def add_plugin_directory(self, directory: str) -> bool:
        """
        添加插件目录
        Add plugin directory

        Args:
            directory: 插件目录路径

        Returns:
            bool: 是否添加成功
        """
        try:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                abs_path = str(dir_path.absolute())
                if abs_path not in self.plugin_dirs:
                    self.plugin_dirs.append(abs_path)
                    return True
            return False
        except Exception:
            return False

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        发现插件
        Discover plugins

        Returns:
            List[Dict[str, Any]]: 发现的插件信息列表
        """
        with self._lock:
            self._stats["discovery_count"] += 1
            discovered = []

            for plugin_dir in self.plugin_dirs:
                try:
                    discovered.extend(self._discover_plugins_in_directory(plugin_dir))
                except Exception as e:
                    print(f"发现插件失败 {plugin_dir}: {e}")

            self._stats["total_discovered"] = len(discovered)
            return discovered

    def _discover_plugins_in_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        在指定目录中发现插件
        Discover plugins in specified directory

        Args:
            directory: 目录路径

        Returns:
            List[Dict[str, Any]]: 发现的插件信息
        """
        discovered = []
        dir_path = Path(directory)

        if not dir_path.exists():
            return discovered

        # 查找插件文件
        for item in dir_path.iterdir():
            if (
                item.is_file()
                and item.suffix == ".py"
                and not item.name.startswith("_")
            ):
                # Python文件插件
                plugin_info = self._analyze_python_plugin(item)
                if plugin_info:
                    discovered.append(plugin_info)
            elif item.is_dir() and not item.name.startswith("_"):
                # 插件包
                plugin_info = self._analyze_plugin_package(item)
                if plugin_info:
                    discovered.append(plugin_info)

        return discovered

    def _analyze_python_plugin(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        分析Python插件文件
        Analyze Python plugin file

        Args:
            file_path: 插件文件路径

        Returns:
            Optional[Dict[str, Any]]: 插件信息
        """
        try:
            # 读取文件内容查找插件元数据
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单的元数据提取（实际应用中可能需要更复杂的解析）
            if "PluginInterface" in content or "BasePlugin" in content:
                return {
                    "type": "python_file",
                    "path": str(file_path),
                    "name": file_path.stem,
                    "discovered_at": self._get_current_timestamp(),
                }
        except Exception:
            pass

        return None

    def _analyze_plugin_package(self, package_path: Path) -> Optional[Dict[str, Any]]:
        """
        分析插件包
        Analyze plugin package

        Args:
            package_path: 插件包路径

        Returns:
            Optional[Dict[str, Any]]: 插件信息
        """
        try:
            # 查找插件清单文件
            manifest_file = package_path / "plugin.json"
            if manifest_file.exists():
                with open(manifest_file, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

                return {
                    "type": "plugin_package",
                    "path": str(package_path),
                    "name": manifest.get("name", package_path.name),
                    "manifest": manifest,
                    "discovered_at": self._get_current_timestamp(),
                }

            # 查找__init__.py文件
            init_file = package_path / "__init__.py"
            if init_file.exists():
                return {
                    "type": "python_package",
                    "path": str(package_path),
                    "name": package_path.name,
                    "discovered_at": self._get_current_timestamp(),
                }
        except Exception:
            pass

        return None

    def load_plugin(self, plugin_path: str, plugin_name: str = None) -> bool:
        """
        加载插件
        Load plugin

        Args:
            plugin_path: 插件路径
            plugin_name: 插件名称

        Returns:
            bool: 是否加载成功
        """
        with self._lock:
            try:
                if plugin_name is None:
                    plugin_name = Path(plugin_path).stem

                # 检查是否已加载
                if plugin_name in self._plugins:
                    return True

                # 加载插件模块
                plugin_module = self._load_plugin_module(plugin_path, plugin_name)
                if not plugin_module:
                    return False

                # 查找插件类
                plugin_class = self._find_plugin_class(plugin_module)
                if not plugin_class:
                    print(f"未找到插件类: {plugin_name}")
                    return False

                # 创建插件实例
                plugin_instance = self._create_plugin_instance(
                    plugin_class, plugin_name
                )
                if not plugin_instance:
                    return False

                # 初始化插件
                context = self._create_plugin_context()
                if not plugin_instance.initialize(context):
                    print(f"插件初始化失败: {plugin_name}")
                    return False

                # 注册插件
                self._plugins[plugin_name] = plugin_instance
                self._plugin_modules[plugin_name] = plugin_module

                self._stats["total_loaded"] += 1

                # 触发事件
                self.event_handler.emit_event(
                    "plugin_loaded", plugin_name, plugin_instance
                )

                return True

            except Exception as e:
                print(f"加载插件失败 {plugin_name}: {e}")
                self._stats["total_errors"] += 1
                return False

    def _load_plugin_module(self, plugin_path: str, plugin_name: str) -> Optional[Any]:
        """
        加载插件模块
        Load plugin module

        Args:
            plugin_path: 插件路径
            plugin_name: 插件名称

        Returns:
            Optional[Any]: 插件模块
        """
        try:
            path_obj = Path(plugin_path)

            if path_obj.is_file() and path_obj.suffix == ".py":
                # 加载Python文件
                spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module
            elif path_obj.is_dir():
                # 加载Python包
                if str(path_obj.parent) not in sys.path:
                    sys.path.insert(0, str(path_obj.parent))

                module = importlib.import_module(path_obj.name)
                return module

        except Exception as e:
            print(f"加载插件模块失败 {plugin_name}: {e}")

        return None

    def _find_plugin_class(self, module: Any) -> Optional[Type[PluginInterface]]:
        """
        在模块中查找插件类
        Find plugin class in module

        Args:
            module: 插件模块

        Returns:
            Optional[Type[PluginInterface]]: 插件类
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginInterface)
                and attr != PluginInterface
            ):
                return attr
        return None

    def _create_plugin_instance(
        self, plugin_class: Type[PluginInterface], plugin_name: str
    ) -> Optional[PluginInterface]:
        """
        创建插件实例
        Create plugin instance

        Args:
            plugin_class: 插件类
            plugin_name: 插件名称

        Returns:
            Optional[PluginInterface]: 插件实例
        """
        try:
            # 创建默认元数据（实际应用中应该从插件中读取）
            metadata = PluginMetadata(
                name=plugin_name,
                version="1.0.0",
                description=f"Plugin: {plugin_name}",
                author="Unknown",
                plugin_type=PluginType.INTEGRATION,
                dependencies=[],
            )

            return plugin_class(metadata)
        except Exception as e:
            print(f"创建插件实例失败 {plugin_name}: {e}")
            return None

    def _create_plugin_context(self) -> PluginContext:
        """
        创建插件上下文
        Create plugin context

        Returns:
            PluginContext: 插件上下文
        """
        return PluginContext(
            system_version=self.system_version, config={}, service_registry={}
        )

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        Unload plugin

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否卸载成功
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            try:
                plugin = self._plugins[plugin_name]

                # 清理插件
                if not plugin.cleanup():
                    print(f"插件清理失败: {plugin_name}")

                # 移除插件
                del self._plugins[plugin_name]
                if plugin_name in self._plugin_modules:
                    del self._plugin_modules[plugin_name]

                self._stats["total_loaded"] -= 1
                if plugin.get_status() == PluginStatus.ACTIVE:
                    self._stats["total_active"] -= 1

                # 触发事件
                self.event_handler.emit_event("plugin_unloaded", plugin_name)

                return True

            except Exception as e:
                print(f"卸载插件失败 {plugin_name}: {e}")
                return False

    def activate_plugin(self, plugin_name: str) -> bool:
        """
        激活插件
        Activate plugin

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否激活成功
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]
            if plugin.activate():
                if plugin.get_status() == PluginStatus.ACTIVE:
                    self._stats["total_active"] += 1

                # 触发事件
                self.event_handler.emit_event("plugin_activated", plugin_name, plugin)
                return True

            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        停用插件
        Deactivate plugin

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否停用成功
        """
        with self._lock:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]
            was_active = plugin.get_status() == PluginStatus.ACTIVE

            if plugin.deactivate():
                if was_active:
                    self._stats["total_active"] -= 1

                # 触发事件
                self.event_handler.emit_event("plugin_deactivated", plugin_name, plugin)
                return True

            return False

    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        获取插件实例
        Get plugin instance

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[PluginInterface]: 插件实例
        """
        with self._lock:
            return self._plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """
        获取所有插件
        Get all plugins

        Returns:
            Dict[str, PluginInterface]: 所有插件
        """
        with self._lock:
            return self._plugins.copy()

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """
        按类型获取插件
        Get plugins by type

        Args:
            plugin_type: 插件类型

        Returns:
            List[PluginInterface]: 指定类型的插件列表
        """
        with self._lock:
            return [
                plugin
                for plugin in self._plugins.values()
                if plugin.metadata.plugin_type == plugin_type
            ]

    def get_active_plugins(self) -> List[PluginInterface]:
        """
        获取活跃插件
        Get active plugins

        Returns:
            List[PluginInterface]: 活跃插件列表
        """
        with self._lock:
            return [
                plugin
                for plugin in self._plugins.values()
                if plugin.get_status() == PluginStatus.ACTIVE
            ]

    def get_manager_stats(self) -> Dict[str, Any]:
        """
        获取管理器统计信息
        Get manager statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            plugin_stats = {}
            for name, plugin in self._plugins.items():
                plugin_stats[name] = plugin.get_stats()

            return {
                "manager_stats": self._stats.copy(),
                "plugin_directories": self.plugin_dirs.copy(),
                "system_version": self.system_version,
                "plugins": plugin_stats,
            }

    def _get_current_timestamp(self) -> float:
        """获取当前时间戳"""
        import time

        return time.time()


# 全局插件管理器实例
_global_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """
    获取全局插件管理器实例
    Get global plugin manager instance

    Returns:
        PluginManager: 插件管理器实例
    """
    global _global_plugin_manager
    if _global_plugin_manager is None:
        _global_plugin_manager = PluginManager()
    return _global_plugin_manager

# interactive_feedback_server/plugins/plugin_interface.py

"""
插件接口定义 - V3.3 架构改进版本
Plugin Interface Definition - V3.3 Architecture Improvement Version

定义插件系统的核心接口和基础实现，支持热加载和动态扩展。
Defines core interfaces and base implementations for plugin system with hot loading and dynamic extension support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import threading


class PluginType(Enum):
    """插件类型枚举"""

    OPTION_STRATEGY = "option_strategy"  # 选项策略插件
    TEXT_PROCESSOR = "text_processor"  # 文本处理插件
    RULE_ENGINE = "rule_engine"  # 规则引擎插件
    UI_COMPONENT = "ui_component"  # UI组件插件
    DATA_PROCESSOR = "data_processor"  # 数据处理插件
    INTEGRATION = "integration"  # 第三方集成插件


class PluginStatus(Enum):
    """插件状态枚举"""

    UNLOADED = "unloaded"  # 未加载
    LOADING = "loading"  # 加载中
    LOADED = "loaded"  # 已加载
    ACTIVE = "active"  # 活跃状态
    INACTIVE = "inactive"  # 非活跃状态
    ERROR = "error"  # 错误状态
    UNLOADING = "unloading"  # 卸载中


@dataclass
class PluginMetadata:
    """
    插件元数据
    Plugin Metadata
    """

    name: str  # 插件名称
    version: str  # 版本号
    description: str  # 描述
    author: str  # 作者
    plugin_type: PluginType  # 插件类型
    dependencies: List[str]  # 依赖列表
    min_system_version: str = "3.3.0"  # 最小系统版本
    max_system_version: str = ""  # 最大系统版本
    config_schema: Optional[Dict[str, Any]] = None  # 配置模式
    permissions: List[str] = None  # 权限列表

    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []


@dataclass
class PluginContext:
    """
    插件上下文
    Plugin Context

    提供插件运行时需要的系统信息和服务
    Provides system information and services needed by plugins at runtime
    """

    system_version: str  # 系统版本
    config: Dict[str, Any]  # 系统配置
    logger: Optional[Any] = None  # 日志记录器
    event_bus: Optional[Any] = None  # 事件总线
    service_registry: Optional[Dict[str, Any]] = None  # 服务注册表

    def __post_init__(self):
        if self.service_registry is None:
            self.service_registry = {}


class PluginInterface(ABC):
    """
    插件接口抽象基类
    Plugin Interface Abstract Base Class

    所有插件必须实现的核心接口
    Core interface that all plugins must implement
    """

    def __init__(self, metadata: PluginMetadata):
        """
        初始化插件
        Initialize plugin

        Args:
            metadata: 插件元数据
        """
        self.metadata = metadata
        self.status = PluginStatus.UNLOADED
        self.context: Optional[PluginContext] = None
        self._lock = threading.RLock()

        # 插件统计
        self._stats = {
            "load_time": 0.0,
            "activation_count": 0,
            "error_count": 0,
            "last_error": None,
        }

    @abstractmethod
    def initialize(self, context: PluginContext) -> bool:
        """
        初始化插件
        Initialize plugin

        Args:
            context: 插件上下文

        Returns:
            bool: 是否初始化成功
        """
        pass

    @abstractmethod
    def activate(self) -> bool:
        """
        激活插件
        Activate plugin

        Returns:
            bool: 是否激活成功
        """
        pass

    @abstractmethod
    def deactivate(self) -> bool:
        """
        停用插件
        Deactivate plugin

        Returns:
            bool: 是否停用成功
        """
        pass

    @abstractmethod
    def cleanup(self) -> bool:
        """
        清理插件资源
        Cleanup plugin resources

        Returns:
            bool: 是否清理成功
        """
        pass

    def get_metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        return self.metadata

    def get_status(self) -> PluginStatus:
        """获取插件状态"""
        with self._lock:
            return self.status

    def set_status(self, status: PluginStatus) -> None:
        """设置插件状态"""
        with self._lock:
            self.status = status

    def get_stats(self) -> Dict[str, Any]:
        """
        获取插件统计信息
        Get plugin statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            return {
                "name": self.metadata.name,
                "version": self.metadata.version,
                "type": self.metadata.plugin_type.value,
                "status": self.status.value,
                "load_time": self._stats["load_time"],
                "activation_count": self._stats["activation_count"],
                "error_count": self._stats["error_count"],
                "last_error": self._stats["last_error"],
            }

    def _record_error(self, error: str) -> None:
        """记录错误"""
        with self._lock:
            self._stats["error_count"] += 1
            self._stats["last_error"] = error
            self.status = PluginStatus.ERROR

    def __str__(self) -> str:
        return f"Plugin({self.metadata.name} v{self.metadata.version}, {self.status.value})"


class BasePlugin(PluginInterface):
    """
    基础插件实现
    Base Plugin Implementation

    提供插件的通用实现基础
    Provides common implementation foundation for plugins
    """

    def __init__(self, metadata: PluginMetadata):
        """初始化基础插件"""
        super().__init__(metadata)
        self._initialized = False
        self._active = False
        self._config: Dict[str, Any] = {}

    def initialize(self, context: PluginContext) -> bool:
        """
        初始化插件
        Initialize plugin
        """
        try:
            with self._lock:
                if self._initialized:
                    return True

                import time

                start_time = time.time()

                self.set_status(PluginStatus.LOADING)
                self.context = context

                # 验证依赖
                if not self._check_dependencies():
                    self._record_error("依赖检查失败")
                    return False

                # 验证系统版本
                if not self._check_system_version():
                    self._record_error("系统版本不兼容")
                    return False

                # 加载配置
                self._load_config()

                # 执行自定义初始化
                if not self._do_initialize():
                    self._record_error("自定义初始化失败")
                    return False

                self._initialized = True
                self.set_status(PluginStatus.LOADED)

                # 记录加载时间
                self._stats["load_time"] = time.time() - start_time

                return True

        except Exception as e:
            self._record_error(f"初始化异常: {e}")
            return False

    def activate(self) -> bool:
        """
        激活插件
        Activate plugin
        """
        try:
            with self._lock:
                if not self._initialized:
                    self._record_error("插件未初始化")
                    return False

                if self._active:
                    return True

                # 执行自定义激活逻辑
                if not self._do_activate():
                    self._record_error("激活失败")
                    return False

                self._active = True
                self.set_status(PluginStatus.ACTIVE)
                self._stats["activation_count"] += 1

                return True

        except Exception as e:
            self._record_error(f"激活异常: {e}")
            return False

    def deactivate(self) -> bool:
        """
        停用插件
        Deactivate plugin
        """
        try:
            with self._lock:
                if not self._active:
                    return True

                # 执行自定义停用逻辑
                if not self._do_deactivate():
                    self._record_error("停用失败")
                    return False

                self._active = False
                self.set_status(PluginStatus.INACTIVE)

                return True

        except Exception as e:
            self._record_error(f"停用异常: {e}")
            return False

    def cleanup(self) -> bool:
        """
        清理插件资源
        Cleanup plugin resources
        """
        try:
            with self._lock:
                self.set_status(PluginStatus.UNLOADING)

                # 先停用
                if self._active:
                    self.deactivate()

                # 执行自定义清理逻辑
                if not self._do_cleanup():
                    self._record_error("清理失败")
                    return False

                self._initialized = False
                self.set_status(PluginStatus.UNLOADED)

                return True

        except Exception as e:
            self._record_error(f"清理异常: {e}")
            return False

    def _check_dependencies(self) -> bool:
        """检查依赖"""
        # 基础实现：假设所有依赖都满足
        # 子类可以重写此方法实现具体的依赖检查
        return True

    def _check_system_version(self) -> bool:
        """检查系统版本兼容性"""
        if not self.context:
            return False

        system_version = self.context.system_version
        min_version = self.metadata.min_system_version
        max_version = self.metadata.max_system_version

        # 简单的版本比较（实际应用中可能需要更复杂的版本比较逻辑）
        if min_version and system_version < min_version:
            return False

        if max_version and system_version > max_version:
            return False

        return True

    def _load_config(self) -> None:
        """加载插件配置"""
        if self.context and self.context.config:
            plugin_config_key = f"plugins.{self.metadata.name}"
            self._config = self.context.config.get(plugin_config_key, {})

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        Get configuration value

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        return self._config.get(key, default)

    def is_active(self) -> bool:
        """检查插件是否活跃"""
        with self._lock:
            return self._active

    def is_initialized(self) -> bool:
        """检查插件是否已初始化"""
        with self._lock:
            return self._initialized

    # 子类需要实现的方法
    def _do_initialize(self) -> bool:
        """执行自定义初始化逻辑"""
        return True

    def _do_activate(self) -> bool:
        """执行自定义激活逻辑"""
        return True

    def _do_deactivate(self) -> bool:
        """执行自定义停用逻辑"""
        return True

    def _do_cleanup(self) -> bool:
        """执行自定义清理逻辑"""
        return True


class PluginEventHandler:
    """
    插件事件处理器
    Plugin Event Handler

    处理插件生命周期事件
    Handles plugin lifecycle events
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def register_handler(self, event: str, handler: Callable) -> None:
        """
        注册事件处理器
        Register event handler

        Args:
            event: 事件名称
            handler: 处理函数
        """
        with self._lock:
            if event not in self._handlers:
                self._handlers[event] = []
            self._handlers[event].append(handler)

    def unregister_handler(self, event: str, handler: Callable) -> bool:
        """
        注销事件处理器
        Unregister event handler

        Args:
            event: 事件名称
            handler: 处理函数

        Returns:
            bool: 是否成功注销
        """
        with self._lock:
            if event in self._handlers and handler in self._handlers[event]:
                self._handlers[event].remove(handler)
                return True
            return False

    def emit_event(self, event: str, *args, **kwargs) -> None:
        """
        触发事件
        Emit event

        Args:
            event: 事件名称
            *args: 位置参数
            **kwargs: 关键字参数
        """
        with self._lock:
            if event in self._handlers:
                for handler in self._handlers[event]:
                    try:
                        handler(*args, **kwargs)
                    except Exception as e:
                        print(f"事件处理器执行失败 {event}: {e}")

    def get_handlers(self, event: str) -> List[Callable]:
        """获取事件处理器列表"""
        with self._lock:
            return self._handlers.get(event, []).copy()

# interactive_feedback_server/error_handling/error_types.py

"""
错误类型定义 - V3.3 架构改进版本
Error Types Definition - V3.3 Architecture Improvement Version

定义系统中的各种错误类型和分级处理策略。
Defines various error types and hierarchical handling strategies in the system.
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
import traceback


class ErrorLevel(Enum):
    """错误级别枚举"""

    DEBUG = "debug"  # 调试信息
    INFO = "info"  # 一般信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 严重错误
    FATAL = "fatal"  # 致命错误


class ErrorCategory(Enum):
    """错误分类枚举"""

    SYSTEM = "system"  # 系统错误
    NETWORK = "network"  # 网络错误
    DATABASE = "database"  # 数据库错误
    VALIDATION = "validation"  # 验证错误
    AUTHENTICATION = "authentication"  # 认证错误
    AUTHORIZATION = "authorization"  # 授权错误
    BUSINESS_LOGIC = "business_logic"  # 业务逻辑错误
    EXTERNAL_SERVICE = "external_service"  # 外部服务错误
    CONFIGURATION = "configuration"  # 配置错误
    PLUGIN = "plugin"  # 插件错误
    PERFORMANCE = "performance"  # 性能错误


class RecoveryStrategy(Enum):
    """恢复策略枚举"""

    NONE = "none"  # 无恢复策略
    RETRY = "retry"  # 重试
    FALLBACK = "fallback"  # 降级处理
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔断器
    GRACEFUL_DEGRADATION = "graceful_degradation"  # 优雅降级
    RESTART = "restart"  # 重启
    ESCALATE = "escalate"  # 升级处理


@dataclass
class ErrorContext:
    """
    错误上下文
    Error Context

    包含错误发生时的上下文信息
    Contains context information when error occurs
    """

    timestamp: float  # 错误发生时间
    component: str  # 发生错误的组件
    operation: str  # 执行的操作
    additional_data: Optional[Dict[str, Any]] = None  # 额外数据

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class ErrorInfo:
    """
    错误信息
    Error Information

    包含完整的错误信息和处理策略
    Contains complete error information and handling strategy
    """

    error_id: str  # 错误唯一标识
    level: ErrorLevel  # 错误级别
    category: ErrorCategory  # 错误分类
    message: str  # 错误消息
    description: str  # 详细描述
    context: ErrorContext  # 错误上下文
    exception: Optional[Exception] = None  # 原始异常
    stack_trace: Optional[str] = None  # 堆栈跟踪
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.NONE  # 恢复策略
    retry_count: int = 0  # 重试次数
    max_retries: int = 3  # 最大重试次数
    recovery_data: Optional[Dict[str, Any]] = None  # 恢复数据

    def __post_init__(self):
        if self.recovery_data is None:
            self.recovery_data = {}

        # 自动提取堆栈跟踪
        if self.exception and not self.stack_trace:
            self.stack_trace = "".join(
                traceback.format_exception(
                    type(self.exception), self.exception, self.exception.__traceback__
                )
            )


class SystemError(Exception):
    """
    系统错误基类
    System Error Base Class

    所有系统错误的基类，包含错误信息
    Base class for all system errors, contains error information
    """

    def __init__(self, error_info: ErrorInfo):
        """
        初始化系统错误
        Initialize system error

        Args:
            error_info: 错误信息
        """
        self.error_info = error_info
        super().__init__(error_info.message)

    def __str__(self) -> str:
        return f"[{self.error_info.level.value.upper()}] {self.error_info.category.value}: {self.error_info.message}"

    def __repr__(self) -> str:
        return f"SystemError(id={self.error_info.error_id}, level={self.error_info.level.value}, category={self.error_info.category.value})"


class ValidationError(SystemError):
    """验证错误"""

    def __init__(
        self,
        message: str,
        field: str = None,
        value: Any = None,
        context: ErrorContext = None,
    ):
        error_info = ErrorInfo(
            error_id=f"validation_{int(time.time() * 1000)}",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.VALIDATION,
            message=message,
            description=f"验证失败: {message}",
            context=context
            or ErrorContext(
                timestamp=time.time(),
                component="validation",
                operation="validate",
                additional_data={"field": field, "value": value},
            ),
            recovery_strategy=RecoveryStrategy.NONE,
        )
        super().__init__(error_info)


class ConfigurationError(SystemError):
    """配置错误"""

    def __init__(
        self, message: str, config_key: str = None, context: ErrorContext = None
    ):
        error_info = ErrorInfo(
            error_id=f"config_{int(time.time() * 1000)}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.CONFIGURATION,
            message=message,
            description=f"配置错误: {message}",
            context=context
            or ErrorContext(
                timestamp=time.time(),
                component="configuration",
                operation="load_config",
                additional_data={"config_key": config_key},
            ),
            recovery_strategy=RecoveryStrategy.FALLBACK,
        )
        super().__init__(error_info)


class PluginError(SystemError):
    """插件错误"""

    def __init__(
        self, message: str, plugin_name: str = None, context: ErrorContext = None
    ):
        error_info = ErrorInfo(
            error_id=f"plugin_{int(time.time() * 1000)}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.PLUGIN,
            message=message,
            description=f"插件错误: {message}",
            context=context
            or ErrorContext(
                timestamp=time.time(),
                component="plugin_manager",
                operation="plugin_operation",
                additional_data={"plugin_name": plugin_name},
            ),
            recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
        )
        super().__init__(error_info)


class PerformanceError(SystemError):
    """性能错误"""

    def __init__(
        self,
        message: str,
        metric_name: str = None,
        threshold: float = None,
        actual_value: float = None,
        context: ErrorContext = None,
    ):
        error_info = ErrorInfo(
            error_id=f"performance_{int(time.time() * 1000)}",
            level=ErrorLevel.WARNING,
            category=ErrorCategory.PERFORMANCE,
            message=message,
            description=f"性能问题: {message}",
            context=context
            or ErrorContext(
                timestamp=time.time(),
                component="performance_monitor",
                operation="performance_check",
                additional_data={
                    "metric_name": metric_name,
                    "threshold": threshold,
                    "actual_value": actual_value,
                },
            ),
            recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
        )
        super().__init__(error_info)


class ExternalServiceError(SystemError):
    """外部服务错误"""

    def __init__(
        self,
        message: str,
        service_name: str = None,
        status_code: int = None,
        context: ErrorContext = None,
    ):
        error_info = ErrorInfo(
            error_id=f"external_{int(time.time() * 1000)}",
            level=ErrorLevel.ERROR,
            category=ErrorCategory.EXTERNAL_SERVICE,
            message=message,
            description=f"外部服务错误: {message}",
            context=context
            or ErrorContext(
                timestamp=time.time(),
                component="external_service",
                operation="service_call",
                additional_data={
                    "service_name": service_name,
                    "status_code": status_code,
                },
            ),
            recovery_strategy=RecoveryStrategy.RETRY,
            max_retries=3,
        )
        super().__init__(error_info)


def create_error_context(
    component: str,
    operation: str,
    **additional_data,
) -> ErrorContext:
    """
    创建错误上下文
    Create error context

    Args:
        component: 组件名称
        operation: 操作名称
        **additional_data: 额外数据

    Returns:
        ErrorContext: 错误上下文
    """
    return ErrorContext(
        timestamp=time.time(),
        component=component,
        operation=operation,
        additional_data=additional_data,
    )


def create_system_error(
    level: ErrorLevel,
    category: ErrorCategory,
    message: str,
    description: str = None,
    context: ErrorContext = None,
    exception: Exception = None,
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.NONE,
    max_retries: int = 3,
) -> SystemError:
    """
    创建系统错误
    Create system error

    Args:
        level: 错误级别
        category: 错误分类
        message: 错误消息
        description: 详细描述
        context: 错误上下文
        exception: 原始异常
        recovery_strategy: 恢复策略
        max_retries: 最大重试次数

    Returns:
        SystemError: 系统错误
    """
    error_info = ErrorInfo(
        error_id=f"{category.value}_{int(time.time() * 1000)}",
        level=level,
        category=category,
        message=message,
        description=description or message,
        context=context
        or ErrorContext(
            timestamp=time.time(), component="unknown", operation="unknown"
        ),
        exception=exception,
        recovery_strategy=recovery_strategy,
        max_retries=max_retries,
    )

    return SystemError(error_info)

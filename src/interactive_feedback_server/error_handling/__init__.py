# interactive_feedback_server/error_handling/__init__.py

"""
错误处理模块
Error Handling Module

提供分级错误处理、自动恢复和系统稳定性保障功能。
Provides hierarchical error handling, automatic recovery and system stability assurance functionality.
"""

from .error_types import (
    ErrorLevel,
    ErrorCategory,
    RecoveryStrategy,
    ErrorContext,
    ErrorInfo,
    SystemError,
    ValidationError,
    ConfigurationError,
    PluginError,
    PerformanceError,
    ExternalServiceError,
    create_error_context,
    create_system_error,
)

from .error_handler import ErrorHandler, get_error_handler

from .recovery_manager import (
    RecoveryManager,
    RecoveryTask,
    RecoveryStatus,
    get_recovery_manager,
)

__all__ = [
    # 错误类型
    "ErrorLevel",
    "ErrorCategory",
    "RecoveryStrategy",
    "ErrorContext",
    "ErrorInfo",
    "SystemError",
    "ValidationError",
    "ConfigurationError",
    "PluginError",
    "PerformanceError",
    "ExternalServiceError",
    "create_error_context",
    "create_system_error",
    # 错误处理器
    "ErrorHandler",
    "get_error_handler",
    # 恢复管理器
    "RecoveryManager",
    "RecoveryTask",
    "RecoveryStatus",
    "get_recovery_manager",
]

__version__ = "3.3.0"

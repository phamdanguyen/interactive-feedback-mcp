# interactive_feedback_server/error_handling/error_handler.py

"""
错误处理器 - V3.3 架构改进版本
Error Handler - V3.3 Architecture Improvement Version

提供分级错误处理和自动恢复机制。
Provides hierarchical error handling and automatic recovery mechanisms.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from collections import defaultdict, deque
import logging

from .error_types import (
    ErrorLevel,
    ErrorCategory,
    RecoveryStrategy,
    ErrorContext,
    SystemError,
    create_error_context,
    create_system_error,
)


class ErrorHandler:
    """
    错误处理器
    Error Handler

    提供分级错误处理、恢复策略和错误统计功能
    Provides hierarchical error handling, recovery strategies and error statistics
    """

    def __init__(self, max_error_history: int = 1000):
        """
        初始化错误处理器
        Initialize error handler

        Args:
            max_error_history: 最大错误历史记录数
        """
        self.max_error_history = max_error_history

        # 错误存储
        self._error_history: deque = deque(maxlen=max_error_history)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._recovery_handlers: Dict[RecoveryStrategy, Callable] = {}

        # 线程安全
        self._lock = threading.RLock()

        # 错误统计
        self._stats = {
            "total_errors": 0,
            "errors_by_level": defaultdict(int),
            "errors_by_category": defaultdict(int),
            "recovery_attempts": defaultdict(int),
            "recovery_successes": defaultdict(int),
        }

        # 熔断器状态
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # 初始化默认恢复处理器
        self._setup_default_recovery_handlers()

        # 日志记录器
        self.logger = logging.getLogger(__name__)

    def _setup_default_recovery_handlers(self) -> None:
        """设置默认恢复处理器"""
        self._recovery_handlers[RecoveryStrategy.RETRY] = self._handle_retry
        self._recovery_handlers[RecoveryStrategy.FALLBACK] = self._handle_fallback
        self._recovery_handlers[RecoveryStrategy.CIRCUIT_BREAKER] = (
            self._handle_circuit_breaker
        )
        self._recovery_handlers[RecoveryStrategy.GRACEFUL_DEGRADATION] = (
            self._handle_graceful_degradation
        )
        self._recovery_handlers[RecoveryStrategy.ESCALATE] = self._handle_escalate

    def handle_error(
        self, error: Union[SystemError, Exception], context: ErrorContext = None
    ) -> Optional[Any]:
        """
        处理错误
        Handle error

        Args:
            error: 错误对象
            context: 错误上下文

        Returns:
            Optional[Any]: 恢复结果
        """
        with self._lock:
            # 转换为SystemError
            if not isinstance(error, SystemError):
                system_error = self._convert_to_system_error(error, context)
            else:
                system_error = error

            # 记录错误
            self._record_error(system_error)

            # 执行恢复策略
            recovery_result = self._execute_recovery(system_error)

            # 记录日志
            self._log_error(system_error, recovery_result)

            return recovery_result

    def _convert_to_system_error(
        self, error: Exception, context: ErrorContext = None
    ) -> SystemError:
        """将普通异常转换为SystemError"""
        if context is None:
            context = create_error_context("unknown", "unknown")

        # 根据异常类型确定错误分类
        category = self._determine_error_category(error)
        level = self._determine_error_level(error)

        return create_system_error(
            level=level,
            category=category,
            message=str(error),
            description=f"未处理的异常: {type(error).__name__}",
            context=context,
            exception=error,
            recovery_strategy=self._determine_recovery_strategy(error),
        )

    def _determine_error_category(self, error: Exception) -> ErrorCategory:
        """确定错误分类"""
        error_type = type(error).__name__

        if "Network" in error_type or "Connection" in error_type:
            return ErrorCategory.NETWORK
        elif "Database" in error_type or "SQL" in error_type:
            return ErrorCategory.DATABASE
        elif "Validation" in error_type or "Value" in error_type:
            return ErrorCategory.VALIDATION
        elif "Permission" in error_type or "Auth" in error_type:
            return ErrorCategory.AUTHORIZATION
        elif "Config" in error_type:
            return ErrorCategory.CONFIGURATION
        else:
            return ErrorCategory.SYSTEM

    def _determine_error_level(self, error: Exception) -> ErrorLevel:
        """确定错误级别"""
        error_type = type(error).__name__

        if error_type in ["SystemExit", "KeyboardInterrupt"]:
            return ErrorLevel.FATAL
        elif error_type in ["MemoryError", "OSError"]:
            return ErrorLevel.CRITICAL
        elif error_type in ["ValueError", "TypeError", "AttributeError"]:
            return ErrorLevel.ERROR
        else:
            return ErrorLevel.WARNING

    def _determine_recovery_strategy(self, error: Exception) -> RecoveryStrategy:
        """确定恢复策略"""
        error_type = type(error).__name__

        if "Network" in error_type or "Connection" in error_type:
            return RecoveryStrategy.RETRY
        elif "Config" in error_type:
            return RecoveryStrategy.FALLBACK
        elif "Permission" in error_type:
            return RecoveryStrategy.ESCALATE
        else:
            return RecoveryStrategy.GRACEFUL_DEGRADATION

    def _record_error(self, error: SystemError) -> None:
        """记录错误"""
        self._error_history.append(error)
        self._stats["total_errors"] += 1
        self._stats["errors_by_level"][error.error_info.level.value] += 1
        self._stats["errors_by_category"][error.error_info.category.value] += 1

        # 更新错误计数
        error_key = (
            f"{error.error_info.category.value}_{error.error_info.context.component}"
        )
        self._error_counts[error_key] += 1

    def _execute_recovery(self, error: SystemError) -> Optional[Any]:
        """执行恢复策略"""
        strategy = error.error_info.recovery_strategy

        if strategy == RecoveryStrategy.NONE:
            return None

        self._stats["recovery_attempts"][strategy.value] += 1

        try:
            handler = self._recovery_handlers.get(strategy)
            if handler:
                result = handler(error)
                if result is not None:
                    self._stats["recovery_successes"][strategy.value] += 1
                return result
        except Exception as e:
            self.logger.error(f"恢复策略执行失败 {strategy.value}: {e}")

        return None

    def _handle_retry(self, error: SystemError) -> Optional[Any]:
        """处理重试策略"""
        error_info = error.error_info

        if error_info.retry_count >= error_info.max_retries:
            self.logger.warning(f"重试次数已达上限: {error_info.error_id}")
            return None

        error_info.retry_count += 1

        # 指数退避
        delay = min(2**error_info.retry_count, 60)  # 最大60秒
        time.sleep(delay)

        self.logger.info(
            f"重试 {error_info.retry_count}/{error_info.max_retries}: {error_info.error_id}"
        )

        return {"action": "retry", "delay": delay, "attempt": error_info.retry_count}

    def _handle_fallback(self, error: SystemError) -> Optional[Any]:
        """处理降级策略"""
        error_info = error.error_info

        # 根据错误类型提供不同的降级方案
        if error_info.category == ErrorCategory.CONFIGURATION:
            return {"action": "fallback", "data": "使用默认配置"}
        elif error_info.category == ErrorCategory.EXTERNAL_SERVICE:
            return {"action": "fallback", "data": "使用缓存数据"}
        else:
            return {"action": "fallback", "data": "使用简化功能"}

    def _handle_circuit_breaker(self, error: SystemError) -> Optional[Any]:
        """处理熔断器策略"""
        error_info = error.error_info
        component = error_info.context.component

        # 获取或创建熔断器状态
        if component not in self._circuit_breakers:
            self._circuit_breakers[component] = {
                "state": "closed",  # closed, open, half_open
                "failure_count": 0,
                "last_failure_time": 0,
                "failure_threshold": 5,
                "timeout": 60,  # 60秒后尝试半开
            }

        breaker = self._circuit_breakers[component]
        current_time = time.time()

        # 更新失败计数
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = current_time

        # 检查是否需要打开熔断器
        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["state"] = "open"
            self.logger.warning(f"熔断器打开: {component}")
            return {"action": "circuit_breaker", "state": "open"}

        return None

    def _handle_graceful_degradation(self, error: SystemError) -> Optional[Any]:
        """处理优雅降级策略"""
        error_info = error.error_info

        # 根据组件类型提供不同的降级方案
        if error_info.context.component == "plugin_manager":
            return {"action": "graceful_degradation", "data": "禁用插件，使用核心功能"}
        elif error_info.context.component == "performance_monitor":
            return {"action": "graceful_degradation", "data": "禁用监控，保持基本功能"}
        else:
            return {"action": "graceful_degradation", "data": "降级到基本功能"}

    def _handle_escalate(self, error: SystemError) -> Optional[Any]:
        """处理升级策略"""
        error_info = error.error_info

        # 记录需要人工干预的错误
        self.logger.critical(
            f"错误需要升级处理: {error_info.error_id} - {error_info.message}"
        )

        return {"action": "escalate", "data": "已通知管理员"}

    def _log_error(self, error: SystemError, recovery_result: Any) -> None:
        """记录错误日志"""
        error_info = error.error_info

        log_data = {
            "error_id": error_info.error_id,
            "level": error_info.level.value,
            "category": error_info.category.value,
            "component": error_info.context.component,
            "operation": error_info.context.operation,
            "message": error_info.message,
            "recovery_strategy": error_info.recovery_strategy.value,
            "recovery_result": recovery_result,
        }

        if error_info.level == ErrorLevel.FATAL:
            self.logger.critical(f"致命错误: {log_data}")
        elif error_info.level == ErrorLevel.CRITICAL:
            self.logger.critical(f"严重错误: {log_data}")
        elif error_info.level == ErrorLevel.ERROR:
            self.logger.error(f"错误: {log_data}")
        elif error_info.level == ErrorLevel.WARNING:
            self.logger.warning(f"警告: {log_data}")
        else:
            self.logger.info(f"信息: {log_data}")

    def register_recovery_handler(
        self, strategy: RecoveryStrategy, handler: Callable
    ) -> None:
        """
        注册自定义恢复处理器
        Register custom recovery handler

        Args:
            strategy: 恢复策略
            handler: 处理函数
        """
        with self._lock:
            self._recovery_handlers[strategy] = handler

    def get_error_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        Get error statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            return {
                "total_errors": self._stats["total_errors"],
                "errors_by_level": dict(self._stats["errors_by_level"]),
                "errors_by_category": dict(self._stats["errors_by_category"]),
                "recovery_attempts": dict(self._stats["recovery_attempts"]),
                "recovery_successes": dict(self._stats["recovery_successes"]),
                "error_counts": dict(self._error_counts),
                "circuit_breakers": dict(self._circuit_breakers),
                "error_history_size": len(self._error_history),
            }

    def get_recent_errors(self, limit: int = 10) -> List[SystemError]:
        """
        获取最近的错误
        Get recent errors

        Args:
            limit: 限制数量

        Returns:
            List[SystemError]: 最近的错误列表
        """
        with self._lock:
            return list(self._error_history)[-limit:]

    def clear_error_history(self) -> None:
        """清空错误历史"""
        with self._lock:
            self._error_history.clear()
            self._error_counts.clear()
            self._stats = {
                "total_errors": 0,
                "errors_by_level": defaultdict(int),
                "errors_by_category": defaultdict(int),
                "recovery_attempts": defaultdict(int),
                "recovery_successes": defaultdict(int),
            }

    def is_circuit_breaker_open(self, component: str) -> bool:
        """
        检查熔断器是否打开
        Check if circuit breaker is open

        Args:
            component: 组件名称

        Returns:
            bool: 是否打开
        """
        with self._lock:
            if component not in self._circuit_breakers:
                return False

            breaker = self._circuit_breakers[component]
            current_time = time.time()

            # 检查是否可以尝试半开
            if (
                breaker["state"] == "open"
                and current_time - breaker["last_failure_time"] > breaker["timeout"]
            ):
                breaker["state"] = "half_open"
                self.logger.info(f"熔断器半开: {component}")

            return breaker["state"] == "open"


# 使用统一的单例管理器
from ..core import register_singleton


@register_singleton("error_handler")
def create_error_handler() -> ErrorHandler:
    """创建错误处理器实例"""
    return ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """
    获取全局错误处理器实例
    Get global error handler instance

    Returns:
        ErrorHandler: 错误处理器实例
    """
    return create_error_handler()

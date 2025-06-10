# interactive_feedback_server/error_handling/recovery_manager.py

"""
恢复管理器 - V3.3 架构改进版本
Recovery Manager - V3.3 Architecture Improvement Version

提供自动恢复机制和系统稳定性保障。
Provides automatic recovery mechanisms and system stability assurance.
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

from .error_types import ErrorLevel, ErrorCategory, SystemError, ErrorContext
from .error_handler import get_error_handler


class RecoveryStatus(Enum):
    """恢复状态枚举"""

    PENDING = "pending"  # 等待中
    IN_PROGRESS = "in_progress"  # 进行中
    SUCCESS = "success"  # 成功
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class RecoveryTask:
    """
    恢复任务
    Recovery Task
    """

    task_id: str  # 任务ID
    component: str  # 组件名称
    operation: str  # 操作名称
    recovery_function: Callable  # 恢复函数
    priority: int  # 优先级 (1-10, 数字越小优先级越高)
    max_attempts: int  # 最大尝试次数
    timeout: float  # 超时时间(秒)
    dependencies: List[str]  # 依赖的任务ID
    created_at: float  # 创建时间
    status: RecoveryStatus = RecoveryStatus.PENDING  # 状态
    attempts: int = 0  # 已尝试次数
    last_attempt_at: Optional[float] = None  # 最后尝试时间
    error_message: Optional[str] = None  # 错误消息
    result: Optional[Any] = None  # 恢复结果


class RecoveryManager:
    """
    恢复管理器
    Recovery Manager

    管理系统的自动恢复任务和稳定性保障
    Manages automatic recovery tasks and system stability assurance
    """

    def __init__(self):
        """初始化恢复管理器"""
        self.error_handler = get_error_handler()

        # 恢复任务管理
        self._recovery_tasks: Dict[str, RecoveryTask] = {}
        self._task_queue: List[str] = []  # 按优先级排序的任务队列
        self._running_tasks: Dict[str, threading.Thread] = {}

        # 线程安全
        self._lock = threading.RLock()

        # 恢复统计
        self._stats = {
            "total_tasks": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "cancelled_recoveries": 0,
            "average_recovery_time": 0.0,
        }

        # 系统健康检查
        self._health_checks: Dict[str, Callable] = {}
        self._health_status: Dict[str, bool] = {}

        # 自动恢复配置
        self._auto_recovery_enabled = True
        self._max_concurrent_recoveries = 3

        # 启动恢复监控线程
        self._monitor_thread = threading.Thread(
            target=self._recovery_monitor, daemon=True
        )
        self._monitor_thread.start()

    def register_recovery_function(
        self,
        component: str,
        operation: str,
        recovery_function: Callable,
        priority: int = 5,
        max_attempts: int = 3,
        timeout: float = 30.0,
        dependencies: List[str] = None,
    ) -> str:
        """
        注册恢复函数
        Register recovery function

        Args:
            component: 组件名称
            operation: 操作名称
            recovery_function: 恢复函数
            priority: 优先级
            max_attempts: 最大尝试次数
            timeout: 超时时间
            dependencies: 依赖任务

        Returns:
            str: 任务ID
        """
        with self._lock:
            task_id = f"{component}_{operation}_{int(time.time() * 1000)}"

            task = RecoveryTask(
                task_id=task_id,
                component=component,
                operation=operation,
                recovery_function=recovery_function,
                priority=priority,
                max_attempts=max_attempts,
                timeout=timeout,
                dependencies=dependencies or [],
                created_at=time.time(),
            )

            self._recovery_tasks[task_id] = task
            self._add_to_queue(task_id)
            self._stats["total_tasks"] += 1

            return task_id

    def _add_to_queue(self, task_id: str) -> None:
        """将任务添加到队列"""
        task = self._recovery_tasks[task_id]

        # 按优先级插入队列
        inserted = False
        for i, existing_task_id in enumerate(self._task_queue):
            existing_task = self._recovery_tasks[existing_task_id]
            if task.priority < existing_task.priority:
                self._task_queue.insert(i, task_id)
                inserted = True
                break

        if not inserted:
            self._task_queue.append(task_id)

    def execute_recovery(self, task_id: str) -> bool:
        """
        执行恢复任务
        Execute recovery task

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功启动
        """
        with self._lock:
            if task_id not in self._recovery_tasks:
                return False

            task = self._recovery_tasks[task_id]

            # 检查任务状态
            if task.status != RecoveryStatus.PENDING:
                return False

            # 检查依赖
            if not self._check_dependencies(task):
                return False

            # 检查并发限制
            if len(self._running_tasks) >= self._max_concurrent_recoveries:
                return False

            # 启动恢复任务
            task.status = RecoveryStatus.IN_PROGRESS
            task.attempts += 1
            task.last_attempt_at = time.time()

            recovery_thread = threading.Thread(
                target=self._execute_recovery_task, args=(task_id,), daemon=True
            )

            self._running_tasks[task_id] = recovery_thread
            recovery_thread.start()

            return True

    def _check_dependencies(self, task: RecoveryTask) -> bool:
        """检查任务依赖"""
        for dep_id in task.dependencies:
            if dep_id in self._recovery_tasks:
                dep_task = self._recovery_tasks[dep_id]
                if dep_task.status != RecoveryStatus.SUCCESS:
                    return False
        return True

    def _execute_recovery_task(self, task_id: str) -> None:
        """执行恢复任务的具体逻辑"""
        task = self._recovery_tasks[task_id]
        start_time = time.time()

        try:
            # 设置超时
            def timeout_handler():
                time.sleep(task.timeout)
                if task.status == RecoveryStatus.IN_PROGRESS:
                    task.status = RecoveryStatus.FAILED
                    task.error_message = "恢复任务超时"

            timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
            timeout_thread.start()

            # 执行恢复函数
            result = task.recovery_function()

            # 检查是否超时
            if task.status == RecoveryStatus.IN_PROGRESS:
                task.status = RecoveryStatus.SUCCESS
                task.result = result
                self._stats["successful_recoveries"] += 1

                # 更新平均恢复时间
                recovery_time = time.time() - start_time
                self._update_average_recovery_time(recovery_time)

        except Exception as e:
            task.status = RecoveryStatus.FAILED
            task.error_message = str(e)
            self._stats["failed_recoveries"] += 1

            # 记录错误
            error_context = ErrorContext(
                timestamp=time.time(),
                component=task.component,
                operation=f"recovery_{task.operation}",
                additional_data={"task_id": task_id, "attempt": task.attempts},
            )

            self.error_handler.handle_error(e, error_context)

        finally:
            # 清理运行任务
            with self._lock:
                if task_id in self._running_tasks:
                    del self._running_tasks[task_id]

                # 如果失败且还有重试机会，重新加入队列
                if (
                    task.status == RecoveryStatus.FAILED
                    and task.attempts < task.max_attempts
                ):
                    task.status = RecoveryStatus.PENDING
                    self._add_to_queue(task_id)

    def _update_average_recovery_time(self, recovery_time: float) -> None:
        """更新平均恢复时间"""
        current_avg = self._stats["average_recovery_time"]
        successful_count = self._stats["successful_recoveries"]

        if successful_count == 1:
            self._stats["average_recovery_time"] = recovery_time
        else:
            # 计算新的平均值
            total_time = current_avg * (successful_count - 1) + recovery_time
            self._stats["average_recovery_time"] = total_time / successful_count

    def _recovery_monitor(self) -> None:
        """恢复监控线程"""
        while True:
            try:
                if self._auto_recovery_enabled:
                    self._process_recovery_queue()
                    self._perform_health_checks()

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                print(f"恢复监控线程错误: {e}")
                time.sleep(10)

    def _process_recovery_queue(self) -> None:
        """处理恢复队列"""
        with self._lock:
            # 处理队列中的任务
            tasks_to_process = []
            for task_id in self._task_queue[:]:
                if len(self._running_tasks) >= self._max_concurrent_recoveries:
                    break

                task = self._recovery_tasks[task_id]
                if task.status == RecoveryStatus.PENDING and self._check_dependencies(
                    task
                ):
                    tasks_to_process.append(task_id)
                    self._task_queue.remove(task_id)

            # 启动任务
            for task_id in tasks_to_process:
                self.execute_recovery(task_id)

    def _perform_health_checks(self) -> None:
        """执行健康检查"""
        for component, health_check in self._health_checks.items():
            try:
                is_healthy = health_check()
                previous_status = self._health_status.get(component, True)
                self._health_status[component] = is_healthy

                # 如果组件从不健康变为健康，记录恢复
                if not previous_status and is_healthy:
                    print(f"组件 {component} 已恢复健康")
                elif previous_status and not is_healthy:
                    print(f"组件 {component} 健康检查失败")

                    # 触发自动恢复
                    self._trigger_auto_recovery(component)

            except Exception as e:
                self._health_status[component] = False
                print(f"健康检查异常 {component}: {e}")

    def _trigger_auto_recovery(self, component: str) -> None:
        """触发自动恢复"""
        # 查找该组件的恢复任务
        for task_id, task in self._recovery_tasks.items():
            if task.component == component and task.status == RecoveryStatus.PENDING:
                self.execute_recovery(task_id)
                break

    def register_health_check(self, component: str, health_check: Callable) -> None:
        """
        注册健康检查函数
        Register health check function

        Args:
            component: 组件名称
            health_check: 健康检查函数，返回bool
        """
        with self._lock:
            self._health_checks[component] = health_check
            self._health_status[component] = True

    def cancel_recovery(self, task_id: str) -> bool:
        """
        取消恢复任务
        Cancel recovery task

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        with self._lock:
            if task_id not in self._recovery_tasks:
                return False

            task = self._recovery_tasks[task_id]

            if task.status == RecoveryStatus.PENDING:
                task.status = RecoveryStatus.CANCELLED
                if task_id in self._task_queue:
                    self._task_queue.remove(task_id)
                self._stats["cancelled_recoveries"] += 1
                return True

            return False

    def get_recovery_status(self, task_id: str) -> Optional[RecoveryTask]:
        """
        获取恢复任务状态
        Get recovery task status

        Args:
            task_id: 任务ID

        Returns:
            Optional[RecoveryTask]: 任务信息
        """
        with self._lock:
            return self._recovery_tasks.get(task_id)

    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        获取恢复统计信息
        Get recovery statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            success_rate = 0.0
            if self._stats["total_tasks"] > 0:
                success_rate = (
                    self._stats["successful_recoveries"] / self._stats["total_tasks"]
                ) * 100

            return {
                "total_tasks": self._stats["total_tasks"],
                "successful_recoveries": self._stats["successful_recoveries"],
                "failed_recoveries": self._stats["failed_recoveries"],
                "cancelled_recoveries": self._stats["cancelled_recoveries"],
                "success_rate_percent": round(success_rate, 2),
                "average_recovery_time": round(self._stats["average_recovery_time"], 3),
                "running_tasks": len(self._running_tasks),
                "pending_tasks": len(self._task_queue),
                "health_status": dict(self._health_status),
                "auto_recovery_enabled": self._auto_recovery_enabled,
            }

    def set_auto_recovery(self, enabled: bool) -> None:
        """
        设置自动恢复开关
        Set auto recovery switch

        Args:
            enabled: 是否启用
        """
        with self._lock:
            self._auto_recovery_enabled = enabled

    def get_system_health(self) -> Dict[str, Any]:
        """
        获取系统健康状态
        Get system health status

        Returns:
            Dict[str, Any]: 健康状态
        """
        with self._lock:
            total_components = len(self._health_status)
            healthy_components = sum(
                1 for status in self._health_status.values() if status
            )

            overall_health = "healthy"
            if total_components == 0:
                overall_health = "unknown"
            elif healthy_components == 0:
                overall_health = "critical"
            elif healthy_components < total_components:
                overall_health = "degraded"

            return {
                "overall_health": overall_health,
                "healthy_components": healthy_components,
                "total_components": total_components,
                "health_percentage": round(
                    (healthy_components / max(total_components, 1)) * 100, 1
                ),
                "component_status": dict(self._health_status),
                "last_check_time": time.time(),
            }


# 全局恢复管理器实例
_global_recovery_manager: Optional[RecoveryManager] = None


def get_recovery_manager() -> RecoveryManager:
    """
    获取全局恢复管理器实例
    Get global recovery manager instance

    Returns:
        RecoveryManager: 恢复管理器实例
    """
    global _global_recovery_manager
    if _global_recovery_manager is None:
        _global_recovery_manager = RecoveryManager()
    return _global_recovery_manager

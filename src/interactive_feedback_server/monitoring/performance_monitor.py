# interactive_feedback_server/monitoring/performance_monitor.py

"""
性能监控系统 - V3.3 架构改进版本
Performance Monitoring System - V3.3 Architecture Improvement Version

提供全面的性能监控、指标收集和分析功能。
Provides comprehensive performance monitoring, metrics collection and analysis functionality.
"""

import time
import threading
import psutil
import statistics
from typing import Dict, List, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from enum import Enum


class MetricType(Enum):
    """指标类型枚举"""

    COUNTER = "counter"  # 计数器
    GAUGE = "gauge"  # 仪表
    HISTOGRAM = "histogram"  # 直方图
    TIMER = "timer"  # 计时器


@dataclass
class MetricData:
    """
    指标数据
    Metric Data
    """

    name: str  # 指标名称
    metric_type: MetricType  # 指标类型
    value: float  # 当前值
    timestamp: float  # 时间戳
    tags: Dict[str, str] = field(default_factory=dict)  # 标签
    unit: str = ""  # 单位
    description: str = ""  # 描述


@dataclass
class PerformanceSnapshot:
    """
    性能快照
    Performance Snapshot
    """

    timestamp: float  # 时间戳
    cpu_percent: float  # CPU使用率
    memory_percent: float  # 内存使用率
    memory_used_mb: float  # 已用内存(MB)
    disk_io_read_mb: float  # 磁盘读取(MB)
    disk_io_write_mb: float  # 磁盘写入(MB)
    network_sent_mb: float  # 网络发送(MB)
    network_recv_mb: float  # 网络接收(MB)
    active_threads: int  # 活跃线程数
    open_files: int  # 打开文件数


class MetricCollector:
    """
    指标收集器
    Metric Collector

    收集和管理各种性能指标
    Collects and manages various performance metrics
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化指标收集器
        Initialize metric collector

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history
        self._metrics: Dict[str, deque] = {}
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._timers: Dict[str, List[float]] = {}
        self._lock = threading.RLock()

        # 系统指标收集
        self._system_snapshots: deque = deque(maxlen=max_history)
        self._last_disk_io = None
        self._last_network_io = None

    def increment_counter(
        self, name: str, value: float = 1.0, tags: Dict[str, str] = None
    ) -> None:
        """
        增加计数器
        Increment counter

        Args:
            name: 指标名称
            value: 增加值
            tags: 标签
        """
        with self._lock:
            if name not in self._counters:
                self._counters[name] = 0.0
            self._counters[name] += value

            self._record_metric(
                MetricData(
                    name=name,
                    metric_type=MetricType.COUNTER,
                    value=self._counters[name],
                    timestamp=time.time(),
                    tags=tags or {},
                )
            )

    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None) -> None:
        """
        设置仪表值
        Set gauge value

        Args:
            name: 指标名称
            value: 值
            tags: 标签
        """
        with self._lock:
            self._gauges[name] = value

            self._record_metric(
                MetricData(
                    name=name,
                    metric_type=MetricType.GAUGE,
                    value=value,
                    timestamp=time.time(),
                    tags=tags or {},
                )
            )

    def record_timer(
        self, name: str, duration: float, tags: Dict[str, str] = None
    ) -> None:
        """
        记录计时器
        Record timer

        Args:
            name: 指标名称
            duration: 持续时间(秒)
            tags: 标签
        """
        with self._lock:
            if name not in self._timers:
                self._timers[name] = []

            self._timers[name].append(duration)

            # 保持最近的记录
            if len(self._timers[name]) > self.max_history:
                self._timers[name] = self._timers[name][-self.max_history :]

            self._record_metric(
                MetricData(
                    name=name,
                    metric_type=MetricType.TIMER,
                    value=duration,
                    timestamp=time.time(),
                    tags=tags or {},
                    unit="seconds",
                )
            )

    def _record_metric(self, metric: MetricData) -> None:
        """记录指标数据"""
        if metric.name not in self._metrics:
            self._metrics[metric.name] = deque(maxlen=self.max_history)

        self._metrics[metric.name].append(metric)

    def collect_system_metrics(self) -> PerformanceSnapshot:
        """
        收集系统指标
        Collect system metrics

        Returns:
            PerformanceSnapshot: 性能快照
        """
        try:
            # CPU和内存
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # 磁盘IO
            disk_io = psutil.disk_io_counters()
            disk_read_mb = 0.0
            disk_write_mb = 0.0

            if disk_io and self._last_disk_io:
                disk_read_mb = (
                    (disk_io.read_bytes - self._last_disk_io.read_bytes) / 1024 / 1024
                )
                disk_write_mb = (
                    (disk_io.write_bytes - self._last_disk_io.write_bytes) / 1024 / 1024
                )

            self._last_disk_io = disk_io

            # 网络IO
            network_io = psutil.net_io_counters()
            network_sent_mb = 0.0
            network_recv_mb = 0.0

            if network_io and self._last_network_io:
                network_sent_mb = (
                    (network_io.bytes_sent - self._last_network_io.bytes_sent)
                    / 1024
                    / 1024
                )
                network_recv_mb = (
                    (network_io.bytes_recv - self._last_network_io.bytes_recv)
                    / 1024
                    / 1024
                )

            self._last_network_io = network_io

            # 进程信息
            process = psutil.Process()
            active_threads = process.num_threads()
            open_files = len(process.open_files())

            snapshot = PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_threads=active_threads,
                open_files=open_files,
            )

            with self._lock:
                self._system_snapshots.append(snapshot)

            return snapshot

        except Exception as e:
            print(f"收集系统指标失败: {e}")
            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_sent_mb=0.0,
                network_recv_mb=0.0,
                active_threads=0,
                open_files=0,
            )

    def get_metric_history(self, name: str, limit: int = None) -> List[MetricData]:
        """
        获取指标历史
        Get metric history

        Args:
            name: 指标名称
            limit: 限制数量

        Returns:
            List[MetricData]: 指标历史
        """
        with self._lock:
            if name not in self._metrics:
                return []

            history = list(self._metrics[name])
            if limit:
                history = history[-limit:]

            return history

    def get_timer_stats(self, name: str) -> Dict[str, float]:
        """
        获取计时器统计
        Get timer statistics

        Args:
            name: 计时器名称

        Returns:
            Dict[str, float]: 统计信息
        """
        with self._lock:
            if name not in self._timers or not self._timers[name]:
                return {}

            durations = self._timers[name]
            return {
                "count": len(durations),
                "min": min(durations),
                "max": max(durations),
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "p95": self._percentile(durations, 95),
                "p99": self._percentile(durations, 99),
            }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)

        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def get_system_stats(self, minutes: int = 5) -> Dict[str, Any]:
        """
        获取系统统计
        Get system statistics

        Args:
            minutes: 统计时间范围(分钟)

        Returns:
            Dict[str, Any]: 系统统计
        """
        with self._lock:
            if not self._system_snapshots:
                return {}

            # 过滤指定时间范围内的快照
            cutoff_time = time.time() - (minutes * 60)
            recent_snapshots = [
                s for s in self._system_snapshots if s.timestamp >= cutoff_time
            ]

            if not recent_snapshots:
                return {}

            # 计算统计信息
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            memory_values = [s.memory_percent for s in recent_snapshots]

            return {
                "time_range_minutes": minutes,
                "sample_count": len(recent_snapshots),
                "cpu": {
                    "min": min(cpu_values),
                    "max": max(cpu_values),
                    "mean": statistics.mean(cpu_values),
                    "current": recent_snapshots[-1].cpu_percent,
                },
                "memory": {
                    "min": min(memory_values),
                    "max": max(memory_values),
                    "mean": statistics.mean(memory_values),
                    "current": recent_snapshots[-1].memory_percent,
                },
                "latest_snapshot": recent_snapshots[-1],
            }

    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """
        获取所有指标摘要
        Get all metrics summary

        Returns:
            Dict[str, Any]: 指标摘要
        """
        with self._lock:
            summary = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timers": {},
                "system": self.get_system_stats(),
                "collection_time": time.time(),
            }

            # 添加计时器统计
            for timer_name in self._timers:
                summary["timers"][timer_name] = self.get_timer_stats(timer_name)

            return summary


class PerformanceTimer:
    """
    性能计时器上下文管理器
    Performance Timer Context Manager
    """

    def __init__(
        self, collector: MetricCollector, name: str, tags: Dict[str, str] = None
    ):
        """
        初始化计时器
        Initialize timer

        Args:
            collector: 指标收集器
            name: 计时器名称
            tags: 标签
        """
        self.collector = collector
        self.name = name
        self.tags = tags or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration = time.perf_counter() - self.start_time
            self.collector.record_timer(self.name, duration, self.tags)
        # 忽略异常参数，不需要处理
        return False


def timer_decorator(
    collector: MetricCollector, name: str = None, tags: Dict[str, str] = None
):
    """
    计时器装饰器
    Timer decorator

    Args:
        collector: 指标收集器
        name: 计时器名称
        tags: 标签
    """

    def decorator(func: Callable) -> Callable:
        timer_name = name or f"{func.__module__}.{func.__name__}"

        def wrapper(*args, **kwargs):
            with PerformanceTimer(collector, timer_name, tags):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# 使用统一的单例管理器
from ..core import register_singleton


@register_singleton("metric_collector")
def create_metric_collector() -> MetricCollector:
    """创建指标收集器实例"""
    return MetricCollector()


def get_metric_collector() -> MetricCollector:
    """
    获取全局指标收集器实例
    Get global metric collector instance

    Returns:
        MetricCollector: 指标收集器实例
    """
    return create_metric_collector()

# interactive_feedback_server/utils/memory_monitor.py

"""
内存监控工具
Memory Monitoring Tools

提供实时内存使用监控、内存泄漏检测和性能分析功能。
Provides real-time memory usage monitoring, memory leak detection, and performance analysis.
"""

import gc
import sys
import time
import threading
import tracemalloc
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import deque

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class MemorySnapshot:
    """内存快照数据类"""

    timestamp: float
    label: str
    rss: int  # 物理内存
    vms: int  # 虚拟内存
    percent: float  # 内存使用百分比
    gc_objects: int  # GC对象数量
    gc_collections: Tuple[int, int, int]  # GC收集次数
    tracemalloc_current: Optional[int] = None  # tracemalloc当前内存
    tracemalloc_peak: Optional[int] = None  # tracemalloc峰值内存


class MemoryMonitor:
    """
    内存监控器
    Memory Monitor

    提供全面的内存使用监控和分析功能
    Provides comprehensive memory usage monitoring and analysis
    """

    def __init__(self, enable_tracemalloc: bool = True, max_snapshots: int = 1000):
        """
        初始化内存监控器
        Initialize memory monitor

        Args:
            enable_tracemalloc: 是否启用tracemalloc
            max_snapshots: 最大快照数量
        """
        self.enable_tracemalloc = enable_tracemalloc and sys.version_info >= (3, 4)
        self.max_snapshots = max_snapshots

        # 快照存储
        self.snapshots: deque[MemorySnapshot] = deque(maxlen=max_snapshots)

        # 进程信息
        if PSUTIL_AVAILABLE:
            self.process = psutil.Process()
        else:
            self.process = None

        # 监控状态
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = 1.0  # 监控间隔（秒）
        self._lock = threading.RLock()

        # 统计信息
        self._total_snapshots = 0
        self._leak_detections = 0
        self._peak_memory = 0

        # 启用tracemalloc
        if self.enable_tracemalloc and not tracemalloc.is_tracing():
            tracemalloc.start()

    def take_snapshot(self, label: str = "") -> MemorySnapshot:
        """
        拍摄内存快照
        Take memory snapshot

        Args:
            label: 快照标签

        Returns:
            MemorySnapshot: 内存快照
        """
        with self._lock:
            timestamp = time.time()

            # 获取GC信息
            gc_objects = len(gc.get_objects())
            gc_collections = tuple(gc.get_count())

            # 获取进程内存信息
            if self.process:
                try:
                    memory_info = self.process.memory_info()
                    rss = memory_info.rss
                    vms = memory_info.vms
                    percent = self.process.memory_percent()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    rss = vms = 0
                    percent = 0.0
            else:
                rss = vms = 0
                percent = 0.0

            # 获取tracemalloc信息
            tracemalloc_current = None
            tracemalloc_peak = None
            if self.enable_tracemalloc and tracemalloc.is_tracing():
                try:
                    current, peak = tracemalloc.get_traced_memory()
                    tracemalloc_current = current
                    tracemalloc_peak = peak
                except Exception:
                    pass

            # 创建快照
            snapshot = MemorySnapshot(
                timestamp=timestamp,
                label=label,
                rss=rss,
                vms=vms,
                percent=percent,
                gc_objects=gc_objects,
                gc_collections=gc_collections,
                tracemalloc_current=tracemalloc_current,
                tracemalloc_peak=tracemalloc_peak,
            )

            # 存储快照
            self.snapshots.append(snapshot)
            self._total_snapshots += 1

            # 更新峰值内存
            if rss > self._peak_memory:
                self._peak_memory = rss

            return snapshot

    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        开始自动监控
        Start automatic monitoring

        Args:
            interval: 监控间隔（秒）
        """
        with self._lock:
            if self._monitoring:
                return

            self._monitor_interval = interval
            self._monitoring = True

            def monitor_loop():
                while self._monitoring:
                    try:
                        self.take_snapshot("auto")
                        time.sleep(self._monitor_interval)
                    except Exception as e:
                        print(f"内存监控错误: {e}")
                        time.sleep(self._monitor_interval)

            self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """停止自动监控"""
        with self._lock:
            self._monitoring = False
            if self._monitor_thread:
                self._monitor_thread.join(timeout=2.0)
                self._monitor_thread = None

    def detect_leaks(
        self, threshold_mb: float = 10.0, min_snapshots: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检测内存泄漏
        Detect memory leaks

        Args:
            threshold_mb: 泄漏阈值（MB）
            min_snapshots: 最小快照数量

        Returns:
            List[Dict[str, Any]]: 检测到的泄漏信息
        """
        with self._lock:
            if len(self.snapshots) < min_snapshots:
                return []

            leaks = []
            threshold_bytes = threshold_mb * 1024 * 1024

            # 检查连续增长
            snapshots_list = list(self.snapshots)
            for i in range(min_snapshots, len(snapshots_list)):
                current = snapshots_list[i]
                previous = snapshots_list[i - min_snapshots]

                memory_growth = current.rss - previous.rss
                time_span = current.timestamp - previous.timestamp

                if memory_growth > threshold_bytes:
                    leak_info = {
                        "type": "memory_growth",
                        "growth_mb": memory_growth / (1024 * 1024),
                        "time_span_seconds": time_span,
                        "growth_rate_mb_per_second": (memory_growth / (1024 * 1024))
                        / time_span,
                        "from_snapshot": {
                            "label": previous.label,
                            "timestamp": previous.timestamp,
                            "rss_mb": previous.rss / (1024 * 1024),
                        },
                        "to_snapshot": {
                            "label": current.label,
                            "timestamp": current.timestamp,
                            "rss_mb": current.rss / (1024 * 1024),
                        },
                    }
                    leaks.append(leak_info)
                    self._leak_detections += 1

            return leaks

    def get_memory_trend(self, window_size: int = 10) -> Dict[str, Any]:
        """
        获取内存趋势分析
        Get memory trend analysis

        Args:
            window_size: 分析窗口大小

        Returns:
            Dict[str, Any]: 趋势分析结果
        """
        with self._lock:
            if len(self.snapshots) < 2:
                return {"trend": "insufficient_data"}

            recent_snapshots = list(self.snapshots)[-window_size:]

            if len(recent_snapshots) < 2:
                return {"trend": "insufficient_data"}

            # 计算趋势
            rss_values = [s.rss for s in recent_snapshots]
            gc_values = [s.gc_objects for s in recent_snapshots]

            rss_trend = "stable"
            if rss_values[-1] > rss_values[0] * 1.1:
                rss_trend = "increasing"
            elif rss_values[-1] < rss_values[0] * 0.9:
                rss_trend = "decreasing"

            gc_trend = "stable"
            if gc_values[-1] > gc_values[0] * 1.1:
                gc_trend = "increasing"
            elif gc_values[-1] < gc_values[0] * 0.9:
                gc_trend = "decreasing"

            return {
                "trend": rss_trend,
                "gc_trend": gc_trend,
                "rss_change_mb": (rss_values[-1] - rss_values[0]) / (1024 * 1024),
                "gc_change": gc_values[-1] - gc_values[0],
                "window_size": len(recent_snapshots),
                "time_span_seconds": recent_snapshots[-1].timestamp
                - recent_snapshots[0].timestamp,
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        获取监控统计信息
        Get monitoring statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            current_snapshot = None
            if self.snapshots:
                current_snapshot = self.snapshots[-1]

            stats = {
                "monitoring_active": self._monitoring,
                "total_snapshots": self._total_snapshots,
                "stored_snapshots": len(self.snapshots),
                "leak_detections": self._leak_detections,
                "peak_memory_mb": self._peak_memory / (1024 * 1024),
                "tracemalloc_enabled": self.enable_tracemalloc
                and tracemalloc.is_tracing(),
                "psutil_available": PSUTIL_AVAILABLE,
            }

            if current_snapshot:
                stats.update(
                    {
                        "current_rss_mb": current_snapshot.rss / (1024 * 1024),
                        "current_vms_mb": current_snapshot.vms / (1024 * 1024),
                        "current_memory_percent": current_snapshot.percent,
                        "current_gc_objects": current_snapshot.gc_objects,
                    }
                )

                if current_snapshot.tracemalloc_current:
                    stats.update(
                        {
                            "tracemalloc_current_mb": current_snapshot.tracemalloc_current
                            / (1024 * 1024),
                            "tracemalloc_peak_mb": current_snapshot.tracemalloc_peak
                            / (1024 * 1024),
                        }
                    )

            return stats

    def generate_report(self) -> str:
        """
        生成内存监控报告
        Generate memory monitoring report

        Returns:
            str: 报告内容
        """
        stats = self.get_stats()
        leaks = self.detect_leaks()
        trend = self.get_memory_trend()

        report_lines = [
            "=" * 60,
            "内存监控报告 (Memory Monitoring Report)",
            "=" * 60,
            f"监控状态: {'活跃' if stats['monitoring_active'] else '停止'}",
            f"总快照数: {stats['total_snapshots']}",
            f"存储快照数: {stats['stored_snapshots']}",
            f"检测到的泄漏: {stats['leak_detections']}",
            f"峰值内存: {stats['peak_memory_mb']:.2f} MB",
            "",
            "当前内存状态:",
            f"  物理内存: {stats.get('current_rss_mb', 0):.2f} MB",
            f"  虚拟内存: {stats.get('current_vms_mb', 0):.2f} MB",
            f"  内存使用率: {stats.get('current_memory_percent', 0):.2f}%",
            f"  GC对象数: {stats.get('current_gc_objects', 0)}",
            "",
            f"内存趋势: {trend.get('trend', 'unknown')}",
            f"GC趋势: {trend.get('gc_trend', 'unknown')}",
            f"内存变化: {trend.get('rss_change_mb', 0):.2f} MB",
            "",
            f"检测到 {len(leaks)} 个潜在内存泄漏:",
        ]

        for i, leak in enumerate(leaks, 1):
            report_lines.extend(
                [
                    f"  泄漏 {i}:",
                    f"    增长: {leak['growth_mb']:.2f} MB",
                    f"    时间跨度: {leak['time_span_seconds']:.2f} 秒",
                    f"    增长率: {leak['growth_rate_mb_per_second']:.4f} MB/秒",
                    "",
                ]
            )

        return "\n".join(report_lines)

    def cleanup(self) -> None:
        """清理监控器"""
        self.stop_monitoring()

        if self.enable_tracemalloc and tracemalloc.is_tracing():
            tracemalloc.stop()


# 全局内存监控器
_global_memory_monitor: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """获取全局内存监控器"""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        _global_memory_monitor = MemoryMonitor()
    return _global_memory_monitor


# 全局内存监控便捷函数 (优化版本)
def start_memory_monitoring(interval: float = 5.0) -> None:
    """开始全局内存监控"""
    get_memory_monitor().start_monitoring(interval)


def stop_memory_monitoring() -> None:
    """停止全局内存监控"""
    if _global_memory_monitor:
        _global_memory_monitor.stop_monitoring()


def take_memory_snapshot(label: str = "") -> MemorySnapshot:
    """拍摄内存快照"""
    return get_memory_monitor().take_snapshot(label)


def detect_memory_leaks(threshold_mb: float = 10.0) -> List[Dict[str, Any]]:
    """检测内存泄漏"""
    return get_memory_monitor().detect_leaks(threshold_mb)


def get_memory_stats() -> Dict[str, Any]:
    """获取内存统计信息"""
    return get_memory_monitor().get_stats()


def generate_memory_report() -> str:
    """生成内存报告"""
    return get_memory_monitor().generate_report()

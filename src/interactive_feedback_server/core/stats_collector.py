# interactive_feedback_server/core/stats_collector.py

"""
统一的统计收集器 - 优化版本
Unified Statistics Collector - Optimized Version

消除重复的统计收集逻辑，提供统一的统计管理。
Eliminates duplicate statistics collection logic, provides unified statistics management.
"""

import time
import threading
from typing import Dict, Any, Optional, List, Union
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class StatEntry:
    """统计条目"""

    name: str
    value: Union[int, float]
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    category: str = "general"


class UnifiedStatsCollector:
    """
    统一统计收集器
    Unified Statistics Collector

    提供统一的统计收集、聚合和查询功能
    Provides unified statistics collection, aggregation and query functionality
    """

    def __init__(self, max_history: int = 1000):
        """
        初始化统计收集器
        Initialize statistics collector

        Args:
            max_history: 最大历史记录数
        """
        self.max_history = max_history

        # 统计存储
        self._counters: Dict[str, Union[int, float]] = defaultdict(lambda: 0)
        self._gauges: Dict[str, Union[int, float]] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._history: deque = deque(maxlen=max_history)

        # 分类统计
        self._category_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "total": 0,
                "min": float("inf"),
                "max": float("-inf"),
                "avg": 0,
            }
        )

        # 线程安全
        self._lock = threading.RLock()

        # 元数据
        self._start_time = time.time()
        self._last_reset = time.time()

    def increment(
        self, name: str, value: Union[int, float] = 1, category: str = "general", **tags
    ) -> None:
        """
        增加计数器
        Increment counter

        Args:
            name: 统计名称
            value: 增加值
            category: 分类
            **tags: 标签
        """
        with self._lock:
            self._counters[name] += value

            # 记录历史
            entry = StatEntry(
                name=name,
                value=self._counters[name],
                timestamp=time.time(),
                tags=tags,
                category=category,
            )
            self._history.append(entry)

            # 更新分类统计
            self._update_category_stats(category, value)

    def set_gauge(
        self, name: str, value: Union[int, float], category: str = "general", **tags
    ) -> None:
        """
        设置仪表值
        Set gauge value

        Args:
            name: 统计名称
            value: 值
            category: 分类
            **tags: 标签
        """
        with self._lock:
            self._gauges[name] = value

            # 记录历史
            entry = StatEntry(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags,
                category=category,
            )
            self._history.append(entry)

    def record_value(
        self, name: str, value: float, category: str = "general", **tags
    ) -> None:
        """
        记录数值到直方图
        Record value to histogram

        Args:
            name: 统计名称
            value: 值
            category: 分类
            **tags: 标签
        """
        with self._lock:
            self._histograms[name].append(value)

            # 保持历史记录限制
            if len(self._histograms[name]) > self.max_history:
                self._histograms[name] = self._histograms[name][-self.max_history :]

            # 记录历史
            entry = StatEntry(
                name=name,
                value=value,
                timestamp=time.time(),
                tags=tags,
                category=category,
            )
            self._history.append(entry)

            # 更新分类统计
            self._update_category_stats(category, value)

    def _update_category_stats(self, category: str, value: Union[int, float]) -> None:
        """更新分类统计"""
        stats = self._category_stats[category]
        stats["count"] += 1
        stats["total"] += value
        stats["min"] = min(stats["min"], value)
        stats["max"] = max(stats["max"], value)
        stats["avg"] = stats["total"] / stats["count"]

    def get_counter(self, name: str) -> Union[int, float]:
        """获取计数器值"""
        with self._lock:
            return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> Optional[Union[int, float]]:
        """获取仪表值"""
        with self._lock:
            return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """获取直方图统计"""
        with self._lock:
            values = self._histograms.get(name, [])
            if not values:
                return {}

            sorted_values = sorted(values)
            count = len(sorted_values)

            return {
                "count": count,
                "min": min(sorted_values),
                "max": max(sorted_values),
                "mean": sum(sorted_values) / count,
                "median": sorted_values[count // 2],
                "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
                "p99": sorted_values[int(count * 0.99)] if count > 0 else 0,
            }

    def get_category_stats(self, category: str = None) -> Dict[str, Any]:
        """
        获取分类统计
        Get category statistics

        Args:
            category: 分类名称，None表示所有分类

        Returns:
            Dict[str, Any]: 分类统计
        """
        with self._lock:
            if category:
                return dict(self._category_stats.get(category, {}))
            else:
                return {cat: dict(stats) for cat, stats in self._category_stats.items()}

    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有统计信息
        Get all statistics

        Returns:
            Dict[str, Any]: 所有统计信息
        """
        with self._lock:
            current_time = time.time()

            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    name: self.get_histogram_stats(name) for name in self._histograms
                },
                "categories": self.get_category_stats(),
                "metadata": {
                    "start_time": self._start_time,
                    "last_reset": self._last_reset,
                    "uptime_seconds": current_time - self._start_time,
                    "total_entries": len(self._history),
                    "collection_time": current_time,
                },
            }

    def get_recent_entries(
        self, limit: int = 10, category: str = None
    ) -> List[StatEntry]:
        """
        获取最近的统计条目
        Get recent statistics entries

        Args:
            limit: 限制数量
            category: 分类过滤

        Returns:
            List[StatEntry]: 最近的条目
        """
        with self._lock:
            entries = list(self._history)

            if category:
                entries = [e for e in entries if e.category == category]

            return entries[-limit:]

    def reset_stats(self, category: str = None) -> None:
        """
        重置统计信息
        Reset statistics

        Args:
            category: 分类名称，None表示重置所有
        """
        with self._lock:
            if category:
                # 重置特定分类
                keys_to_remove = []
                for entry in self._history:
                    if entry.category == category:
                        if entry.name in self._counters:
                            keys_to_remove.append(entry.name)

                for key in keys_to_remove:
                    if key in self._counters:
                        del self._counters[key]
                    if key in self._gauges:
                        del self._gauges[key]
                    if key in self._histograms:
                        del self._histograms[key]

                if category in self._category_stats:
                    del self._category_stats[category]
            else:
                # 重置所有
                self._counters.clear()
                self._gauges.clear()
                self._histograms.clear()
                self._category_stats.clear()
                self._history.clear()

            self._last_reset = time.time()

    def export_stats(self, format: str = "json") -> str:
        """
        导出统计信息
        Export statistics

        Args:
            format: 导出格式 ('json', 'csv')

        Returns:
            str: 导出的数据
        """
        stats = self.get_all_stats()

        if format.lower() == "json":
            import json

            return json.dumps(stats, indent=2, ensure_ascii=False)
        elif format.lower() == "csv":
            lines = ["timestamp,category,name,value,type"]

            for entry in self._history:
                entry_type = (
                    "counter"
                    if entry.name in self._counters
                    else "gauge" if entry.name in self._gauges else "histogram"
                )
                lines.append(
                    f"{entry.timestamp},{entry.category},{entry.name},{entry.value},{entry_type}"
                )

            return "\n".join(lines)
        else:
            raise ValueError(f"不支持的导出格式: {format}")


# 全局统计收集器实例
_global_stats_collector: Optional[UnifiedStatsCollector] = None


def get_stats_collector() -> UnifiedStatsCollector:
    """
    获取全局统计收集器实例
    Get global statistics collector instance

    Returns:
        UnifiedStatsCollector: 统计收集器实例
    """
    global _global_stats_collector
    if _global_stats_collector is None:
        _global_stats_collector = UnifiedStatsCollector()
    return _global_stats_collector


# 便捷函数
def increment_stat(
    name: str, value: Union[int, float] = 1, category: str = "general", **tags
) -> None:
    """增加统计计数"""
    get_stats_collector().increment(name, value, category, **tags)


def set_stat_gauge(
    name: str, value: Union[int, float], category: str = "general", **tags
) -> None:
    """设置统计仪表"""
    get_stats_collector().set_gauge(name, value, category, **tags)


def record_stat_value(
    name: str, value: float, category: str = "general", **tags
) -> None:
    """记录统计值"""
    get_stats_collector().record_value(name, value, category, **tags)


def get_all_stats() -> Dict[str, Any]:
    """获取所有统计信息"""
    return get_stats_collector().get_all_stats()

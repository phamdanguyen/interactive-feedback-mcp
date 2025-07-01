# interactive_feedback_server/core/__init__.py

"""
核心模块 - 优化版本
Core Module - Optimized Version

提供统一的核心功能，消除重复代码和模式。
Provides unified core functionality, eliminates duplicate code and patterns.
"""

from .singleton_manager import (
    SingletonManager,
    SingletonBase,
    register_singleton,
    get_singleton,
    clear_singleton,
    get_singleton_manager,
)

from .stats_collector import (
    UnifiedStatsCollector,
    StatEntry,
    get_stats_collector,
    increment_stat,
    set_stat_gauge,
    record_stat_value,
    get_all_stats,
)

# 已删除未使用的统一配置加载器模块

__all__ = [
    # 单例管理
    "SingletonManager",
    "SingletonBase",
    "register_singleton",
    "get_singleton",
    "clear_singleton",
    "get_singleton_manager",
    # 统计收集
    "UnifiedStatsCollector",
    "StatEntry",
    "get_stats_collector",
    "increment_stat",
    "set_stat_gauge",
    "record_stat_value",
    "get_all_stats",
]

__version__ = "3.3.0"

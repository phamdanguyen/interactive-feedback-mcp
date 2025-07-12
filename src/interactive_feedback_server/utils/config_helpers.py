# src/interactive_feedback_server/utils/config_helpers.py
"""
配置获取辅助工具 (V3.2 写时复制优化版本)
Configuration helper utilities (V3.2 Copy-on-Write Optimized Version)

提供统一的配置获取和错误处理逻辑，减少代码重复。
使用写时复制配置对象优化内存使用和性能。

Provides unified configuration retrieval and error handling logic to reduce code duplication.
Uses copy-on-write configuration objects to optimize memory usage and performance.
"""

from typing import Dict, Any, Optional, Tuple, Callable
from .config_manager import (
    get_config,
    get_display_mode,
    get_fallback_options,
    get_custom_options_enabled,
    DEFAULT_CONFIG,
)
from .list_optimizer import smart_extend, smart_merge

# 已删除未使用的统一配置加载器导入


def safe_get_config() -> Tuple[Dict[str, Any], str]:
    """
    安全获取配置，包含错误处理 (传统版本)
    Safely get configuration with error handling (legacy version)

    Returns:
        Tuple[Dict[str, Any], str]: (配置字典, 当前显示模式)
    """
    try:
        config = get_config()
        current_mode = get_display_mode(config)
        return config, current_mode
    except Exception as e:
        print(f"获取配置失败，使用默认值: {e}")
        # 使用统一的默认配置
        return DEFAULT_CONFIG.copy(), DEFAULT_CONFIG["display_mode"]


# 已移除 safe_get_cow_config - 使用新的统一配置加载器替代


def safe_get_feature_states(
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, bool]:
    """
    安全获取功能开关状态 - V4.0 简化版本
    Safely get feature toggle states - V4.0 Simplified Version

    Args:
        config: 可选的配置字典，如果为None则自动获取

    Returns:
        Tuple[bool, bool]: (规则引擎启用状态[已移除，始终False], 自定义选项启用状态)
    """
    try:
        if config is None:
            config, _ = safe_get_config()

        # V4.0 简化：规则引擎已移除，始终返回False
        rule_engine_enabled = False
        custom_options_enabled = get_custom_options_enabled(config)
        return rule_engine_enabled, custom_options_enabled
    except Exception as e:
        print(f"获取功能开关状态失败，使用默认值: {e}")
        return False, False  # 默认都禁用，与DEFAULT_CONFIG保持一致


def safe_get_fallback_options(config: Optional[Dict[str, Any]] = None) -> list:
    """
    安全获取后备选项 - 简化版本，直接使用config_manager
    Safely get fallback options - simplified version using config_manager

    Args:
        config: 可选的配置字典，如果为None则自动获取

    Returns:
        list: 后备选项列表
    """
    try:
        # 直接使用config_manager的函数，避免重复逻辑
        return get_fallback_options(config)
    except Exception as e:
        print(f"获取后备选项失败，使用默认值: {e}")
        from .config_manager import filter_valid_options

        return filter_valid_options(DEFAULT_CONFIG["fallback_options"])


def handle_config_error(
    operation: str, error: Exception, default_value: Any = None
) -> Any:
    """
    统一的配置错误处理
    Unified configuration error handling

    Args:
        operation: 操作描述
        error: 异常对象
        default_value: 默认返回值

    Returns:
        Any: 默认值或None
    """
    print(f"{operation}失败: {error}")
    return default_value


def safe_config_operation(
    operation_func: Callable, operation_name: str, default_value: Any = None
) -> Any:
    """
    安全执行配置操作的通用函数
    Generic function to safely execute configuration operations

    Args:
        operation_func: 要执行的操作函数
        operation_name: 操作名称（用于错误信息）
        default_value: 操作失败时的默认返回值

    Returns:
        Any: 操作结果或默认值
    """
    try:
        return operation_func()
    except Exception as e:
        return handle_config_error(operation_name, e, default_value)


def merge_config_options(*option_lists: list, remove_duplicates: bool = True) -> list:
    """
    合并多个配置选项列表 (V3.2 优化版本)
    Merge multiple configuration option lists (V3.2 Optimized Version)

    Args:
        *option_lists: 要合并的选项列表
        remove_duplicates: 是否移除重复项

    Returns:
        list: 合并后的选项列表
    """
    return smart_merge(
        *option_lists, remove_duplicates=remove_duplicates, preserve_order=True
    )


# 已移除 create_config_hierarchy - 使用新的统一配置加载器替代


def get_config_stats() -> Dict[str, Any]:
    """
    获取配置系统统计信息 - 简化版本
    Get configuration system statistics - simplified version

    Returns:
        Dict[str, Any]: 统计信息
    """
    try:
        # 使用主配置管理器的统计信息
        config = get_config()

        return {
            "default_config_size": len(DEFAULT_CONFIG),
            "current_config_size": len(config),
            "optimization_enabled": True,
            "list_optimizer_available": True,
            "version": "V4.1-Simplified",
        }
    except Exception as e:
        return {
            "error": str(e),
            "optimization_enabled": False,
            "list_optimizer_available": False,
            "version": "V4.1-Error",
        }

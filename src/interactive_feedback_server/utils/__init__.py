"""
Interactive Feedback Server Utils

工具模块，包含配置管理、规则引擎等核心功能。
Utility modules containing configuration management, rule engine and other core features.
"""

# 导出主要功能模块
from .config_manager import (
    get_config,
    save_config,
    validate_config,
    get_display_mode,
    get_fallback_options,
    # V3.2 新增：功能开关
    get_rule_engine_enabled,
    get_custom_options_enabled,
    set_rule_engine_enabled,
    set_custom_options_enabled,
    # V3.2 性能优化：配置缓存管理
    get_config_cache_stats,
    clear_config_cache,
    preload_config_cache,
    benchmark_config_performance,
)
from .rule_engine import (
    extract_options_from_text,
    resolve_final_options,
    # V3.2 性能优化：缓存和监控功能
    get_rule_engine_performance_stats,
    clear_rule_engine_cache,
    benchmark_rule_engine,
    test_rule_engine_performance,
)

# V3.2 优化：新增配置辅助工具
from .config_helpers import (
    safe_get_config,
    safe_get_feature_states,
    safe_get_fallback_options,
    handle_config_error,
    safe_config_operation,
)

# V3.2 Day 3 优化：新增文本处理工具
from .text_processor import (
    fast_normalize_text,
    fast_extract_keywords,
    fast_find_match,
    get_text_processor,
    get_optimized_matcher,
    get_text_processing_stats,
)

__all__ = [
    "get_config",
    "save_config",
    "validate_config",
    "get_display_mode",
    "get_fallback_options",
    # V3.2 新增：功能开关
    "get_rule_engine_enabled",
    "get_custom_options_enabled",
    "set_rule_engine_enabled",
    "set_custom_options_enabled",
    # V3.2 性能优化：配置缓存管理
    "get_config_cache_stats",
    "clear_config_cache",
    "preload_config_cache",
    "benchmark_config_performance",
    # V3.2 Day 3 优化：文本处理工具
    "fast_normalize_text",
    "fast_extract_keywords",
    "fast_find_match",
    "get_text_processor",
    "get_optimized_matcher",
    "get_text_processing_stats",
    "extract_options_from_text",
    "resolve_final_options",
    # V3.2 性能优化：缓存和监控
    "get_rule_engine_performance_stats",
    "clear_rule_engine_cache",
    "benchmark_rule_engine",
    "test_rule_engine_performance",
    # V3.2 优化：配置辅助工具
    "safe_get_config",
    "safe_get_feature_states",
    "safe_get_fallback_options",
    "handle_config_error",
    "safe_config_operation",
]

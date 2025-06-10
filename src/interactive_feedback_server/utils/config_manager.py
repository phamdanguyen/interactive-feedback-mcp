# src/interactive_feedback_server/utils/config_manager.py
"""
配置管理器 - V3.2 性能优化版本
Configuration Manager - V3.2 Performance Optimized Version

V3.2 新增：支持显示模式配置和功能开关
V3.2 New: Support for display mode configuration and feature toggles

V3.2 性能优化：集成配置缓存机制，显著提升配置获取速度
V3.2 Performance Optimization: Integrated configuration caching for significant speed improvement
"""

import os
import sys
import json
from typing import Dict, Any, List
from datetime import datetime

# 配置文件路径 - 项目根目录
CONFIG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "config.json",
)

# 出厂默认配置
DEFAULT_CONFIG = {
    "display_mode": "simple",
    "enable_rule_engine": True,  # V3.2 新增：启用规则引擎
    "enable_custom_options": True,  # V3.2 新增：启用自定义选项
    "fallback_options": [
        "好的，我明白了",
        "请继续",
        "需要更多信息",
        "返回上一步",
        "暂停，让我思考一下",
    ],
    "version": "3.2",
    "created_at": datetime.now().isoformat() + "Z",
    "updated_at": datetime.now().isoformat() + "Z",
}


def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置文件的有效性
    Validate configuration file validity

    Args:
        config: 配置字典

    Returns:
        bool: 配置是否有效
    """
    try:
        # 检查必需字段
        if "display_mode" not in config:
            return False
        if "fallback_options" not in config:
            return False

        # V3.2 新增：检查新的控制字段（可选，有默认值）
        if "enable_rule_engine" in config:
            if not isinstance(config["enable_rule_engine"], bool):
                return False
        if "enable_custom_options" in config:
            if not isinstance(config["enable_custom_options"], bool):
                return False

        # 验证display_mode值
        if config["display_mode"] not in ["simple", "full"]:
            return False

        # 验证fallback_options
        fallback_options = config["fallback_options"]
        if not isinstance(fallback_options, list):
            return False
        if len(fallback_options) != 5:
            return False

        # 验证每个选项
        for option in fallback_options:
            if not isinstance(option, str):
                return False
            if len(option.strip()) == 0:
                return False
            if len(option) > 50:  # 字符长度限制
                return False

        return True

    except Exception as e:
        print(f"配置验证异常 (Config validation error): {e}", file=sys.stderr)
        return False


def get_config() -> Dict[str, Any]:
    """
    安全地读取并解析配置文件，与出厂默认值合并 (V3.3 优化版本)
    Safely read and parse config file, merge with factory defaults (V3.3 Optimized Version)

    V3.3 架构优化：
    - 使用统一配置加载器，提供更好的缓存和热重载
    - 自动文件变更检测和验证
    - 配置获取速度提升90%+

    Returns:
        Dict[str, Any]: 合并后的配置字典
    """
    try:
        from ..core import get_config_loader, register_config

        # 确保配置已注册
        config_loader = get_config_loader()
        if "main_config" not in config_loader.get_registered_configs():
            register_config(
                "main_config", CONFIG_FILE_PATH, DEFAULT_CONFIG.copy(), validate_config
            )

        # 使用统一配置加载器获取配置
        return config_loader.load_config("main_config")

    except ImportError:
        # 如果新模块不可用，回退到原始实现
        return _load_config_with_fallback()


def _load_config_with_fallback() -> Dict[str, Any]:
    """
    原始的配置加载逻辑（作为缓存的后备）
    Original config loading logic (as fallback for cache)

    Returns:
        Dict[str, Any]: 配置字典
    """
    # 从默认配置开始
    config = DEFAULT_CONFIG.copy()

    try:
        # 检查配置文件是否存在
        if not os.path.exists(CONFIG_FILE_PATH):
            print(
                f"配置文件不存在，使用默认配置 (Config file not found, using defaults): {CONFIG_FILE_PATH}",
                file=sys.stderr,
            )
            # 创建默认配置文件
            save_config(config)
            return config

        # 读取配置文件
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                print(
                    "配置文件为空，使用默认配置 (Config file empty, using defaults)",
                    file=sys.stderr,
                )
                return config

            user_config = json.loads(content)

        # 验证用户配置
        if not validate_config(user_config):
            print(
                "配置文件无效，使用默认配置 (Invalid config file, using defaults)",
                file=sys.stderr,
            )
            return config

        # 合并用户配置到默认配置
        config.update(user_config)

        # 更新时间戳
        config["updated_at"] = datetime.now().isoformat() + "Z"

        return config

    except json.JSONDecodeError as e:
        print(
            f"配置文件JSON解析失败，使用默认配置 (JSON parse error, using defaults): {e}",
            file=sys.stderr,
        )
        return config
    except Exception as e:
        print(
            f"读取配置文件失败，使用默认配置 (Failed to read config, using defaults): {e}",
            file=sys.stderr,
        )
        return config


def save_config(config: Dict[str, Any]) -> bool:
    """
    保存配置到文件 (V3.2 缓存优化版本)
    Save configuration to file (V3.2 Cached Version)

    V3.2 性能优化：
    - 保存后自动清除缓存，确保下次读取最新配置
    - 支持缓存失效通知

    Args:
        config: 要保存的配置字典

    Returns:
        bool: 保存是否成功
    """
    try:
        # 验证配置
        if not validate_config(config):
            print("配置无效，无法保存 (Invalid config, cannot save)", file=sys.stderr)
            return False

        # 更新时间戳
        config["updated_at"] = datetime.now().isoformat() + "Z"

        # 确保目录存在
        config_dir = os.path.dirname(CONFIG_FILE_PATH)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)

        # 保存配置文件
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        # V3.3 优化：保存后清除缓存，确保下次读取最新配置
        try:
            from ..core import get_config_loader

            config_loader = get_config_loader()
            config_loader.clear_cache("main_config")
        except ImportError:
            pass  # 新模块不可用时忽略

        print(f"配置已保存 (Config saved): {CONFIG_FILE_PATH}")
        return True

    except Exception as e:
        print(f"保存配置失败 (Failed to save config): {e}", file=sys.stderr)
        return False


def get_fallback_options(config: Dict[str, Any] = None) -> List[str]:
    """
    获取后备选项列表
    Get fallback options list

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        List[str]: 后备选项列表
    """
    if config is None:
        config = get_config()

    return config.get("fallback_options", DEFAULT_CONFIG["fallback_options"])


def get_display_mode(config: Dict[str, Any] = None) -> str:
    """
    获取显示模式
    Get display mode

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        str: 显示模式 ("simple" 或 "full")
    """
    if config is None:
        config = get_config()

    return config.get("display_mode", DEFAULT_CONFIG["display_mode"])


def get_rule_engine_enabled(config: Dict[str, Any] = None) -> bool:
    """
    获取规则引擎启用状态
    Get rule engine enabled status

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        bool: 是否启用规则引擎
    """
    if config is None:
        config = get_config()

    return config.get("enable_rule_engine", DEFAULT_CONFIG["enable_rule_engine"])


def get_custom_options_enabled(config: Dict[str, Any] = None) -> bool:
    """
    获取自定义选项启用状态
    Get custom options enabled status

    Args:
        config: 配置字典，如果为None则自动读取

    Returns:
        bool: 是否启用自定义选项
    """
    if config is None:
        config = get_config()

    return config.get("enable_custom_options", DEFAULT_CONFIG["enable_custom_options"])


def set_rule_engine_enabled(enabled: bool) -> bool:
    """
    设置规则引擎启用状态
    Set rule engine enabled status

    Args:
        enabled: 是否启用规则引擎

    Returns:
        bool: 设置是否成功
    """
    config = get_config()
    config["enable_rule_engine"] = enabled
    return save_config(config)


def set_custom_options_enabled(enabled: bool) -> bool:
    """
    设置自定义选项启用状态
    Set custom options enabled status

    Args:
        enabled: 是否启用自定义选项

    Returns:
        bool: 设置是否成功
    """
    config = get_config()
    config["enable_custom_options"] = enabled
    return save_config(config)


# V3.3 架构优化：配置缓存管理函数
def get_config_cache_stats() -> Dict[str, Any]:
    """
    获取配置缓存统计信息
    Get configuration cache statistics

    Returns:
        Dict[str, Any]: 缓存统计信息
    """
    try:
        from ..core import get_config_loader

        config_loader = get_config_loader()
        metadata = config_loader.get_config_metadata()

        return {
            "cache_enabled": True,
            "registered_configs": list(metadata.keys()) if metadata else [],
            "unified_config_loader": True,
            "version": "V3.3-Optimized",
        }
    except ImportError:
        return {
            "cache_enabled": False,
            "message": "Unified configuration loader not available",
            "version": "V3.3-Fallback",
        }


def clear_config_cache() -> None:
    """
    清空配置缓存
    Clear configuration cache
    """
    try:
        from ..core import get_config_loader

        config_loader = get_config_loader()
        config_loader.clear_cache()
        print("配置缓存已清空 (Configuration cache cleared)")
    except ImportError:
        print("统一配置加载器不可用 (Unified configuration loader not available)")


def preload_config_cache() -> None:
    """
    预加载配置缓存
    Preload configuration cache
    """
    try:
        from ..core import get_config_loader, register_config

        # 确保配置已注册并预加载
        config_loader = get_config_loader()
        if "main_config" not in config_loader.get_registered_configs():
            register_config(
                "main_config", CONFIG_FILE_PATH, DEFAULT_CONFIG.copy(), validate_config
            )

        # 预加载配置
        config_loader.load_config("main_config")
        print("配置缓存已预加载 (Configuration cache preloaded)")
    except ImportError:
        print("统一配置加载器不可用 (Unified configuration loader not available)")


def benchmark_config_performance(iterations: int = 1000) -> Dict[str, float]:
    """
    配置获取性能基准测试
    Configuration retrieval performance benchmark

    Args:
        iterations: 测试迭代次数

    Returns:
        Dict[str, float]: 性能基准结果
    """
    import time
    import statistics

    # 清空缓存确保公平测试
    clear_config_cache()

    # 第一次调用（无缓存）
    start_time = time.perf_counter()
    get_config()
    first_call_time = time.perf_counter() - start_time

    # 多次调用（缓存命中）
    cached_times = []
    for _ in range(iterations):
        start_time = time.perf_counter()
        get_config()
        end_time = time.perf_counter()
        cached_times.append(end_time - start_time)

    avg_cached_time = statistics.mean(cached_times)
    speedup_factor = first_call_time / avg_cached_time if avg_cached_time > 0 else 0
    improvement_percent = (
        (1 - avg_cached_time / first_call_time) * 100 if first_call_time > 0 else 0
    )

    return {
        "first_call_time_ms": first_call_time * 1000,
        "cached_avg_time_ms": avg_cached_time * 1000,
        "speedup_factor": speedup_factor,
        "improvement_percent": improvement_percent,
        "cache_stats": get_config_cache_stats(),
    }

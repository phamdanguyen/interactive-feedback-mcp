# src/interactive_feedback_server/utils/rule_engine.py
"""
规则引擎模块 - V3.3 架构改进版本
Rule Engine Module - V3.3 Architecture Improvement Version

V3.3 架构改进：集成可配置规则引擎，支持外部化配置
V3.3 Architecture Improvement: Integrated configurable rule engine with externalized configuration

V3.2 性能优化：集成缓存机制，显著提升处理速度
V3.2 Performance Optimization: Integrated caching mechanism for significant speed improvement

提供三层回退逻辑：
1. AI提供的选项（第一层）
2. 规则引擎生成的选项（第二层）
3. 用户配置的后备选项（第三层）

Three-layer fallback logic:
1. AI-provided options (first layer)
2. Rule engine generated options (second layer)
3. User-configured fallback options (third layer)
"""

from typing import List, Dict, Any
from .text_processor import fast_find_match
from .configurable_rule_engine import (
    get_configurable_rule_engine,
    extract_options_configurable,
)

# 核心模式定义 - 精选高频场景
CORE_PATTERNS = {
    # 疑问场景 - 最高优先级
    "question": {
        "triggers": [
            "?",
            "？",
            "是否",
            "如何",
            "怎么",
            "什么",
            "为什么",
            "哪个",
            "哪些",
        ],
        "options": ["是的", "不是", "需要更多信息"],
    },
    # 确认场景 - 高优先级
    "confirmation": {
        "triggers": ["确认", "同意", "继续", "下一步", "开始", "执行", "好的"],
        "options": ["好的，继续", "我明白了", "暂停一下"],
    },
    # 选择场景 - 中优先级
    "choice": {
        "triggers": ["选择", "决定", "考虑", "建议", "推荐", "方案", "选项"],
        "options": ["选择这个", "看看其他的", "让我想想"],
    },
    # 操作场景 - 中优先级
    "action": {
        "triggers": ["修改", "更改", "调整", "优化", "删除", "添加", "创建", "生成"],
        "options": ["执行操作", "先预览", "取消操作"],
    },
}


def extract_options_from_text(
    text: str, language: str = "zh_CN", use_configurable: bool = True
) -> List[str]:
    """
    智能提取用户选项 - V3.3 架构改进版本
    策略：可配置规则引擎 + 回退到传统匹配 + 智能缓存

    Intelligently extract user options - V3.3 Architecture Improvement Version
    Strategy: Configurable rule engine + fallback to traditional matching + intelligent caching

    V3.3 架构改进：
    - 优先使用可配置规则引擎，支持外部化配置
    - 支持多语言规则配置
    - 保持向后兼容，回退到传统匹配
    - 保留V3.2的缓存和性能优化

    Args:
        text: 要分析的文本内容
        language: 语言代码，默认为中文
        use_configurable: 是否使用可配置规则引擎

    Returns:
        List[str]: 提取的选项列表，最多3个
    """
    if not text or len(text.strip()) < 2:
        return []

    # V3.3 优先使用可配置规则引擎
    if use_configurable:
        try:
            configurable_options = extract_options_configurable(text.strip(), language)
            if configurable_options:
                return configurable_options[:3]  # 最多返回3个选项
        except Exception as e:
            # 可配置引擎失败，回退到传统方法
            print(f"可配置规则引擎失败，回退到传统方法: {e}")

    # V3.2 回退：使用传统的高性能文本处理器
    match_result = fast_find_match(text)
    if match_result:
        _, _, options = match_result  # 只需要选项列表
        return options[:3]  # 最多返回3个选项

    return []


def is_valid_ai_options(ai_options) -> bool:
    """
    严格验证AI选项的有效性 - V3.2边界控制
    Strictly validate the validity of AI options - V3.2 boundary control

    Args:
        ai_options: AI提供的选项

    Returns:
        bool: 是否为有效的AI选项
    """
    # 检查是否为None
    if ai_options is None:
        return False

    # 检查是否为空列表
    if isinstance(ai_options, list) and len(ai_options) == 0:
        return False

    # 检查是否为非列表类型
    if not isinstance(ai_options, list):
        return False

    # 检查列表中是否包含有效选项
    valid_count = 0
    for option in ai_options:
        if isinstance(option, str) and option.strip():
            valid_count += 1

    # 至少要有一个有效选项
    return valid_count > 0


def resolve_final_options(
    ai_options: List[str] = None, text: str = "", config: Dict[str, Any] = None
) -> List[str]:
    """
    V3.3 三层回退逻辑 - 架构改进版本
    V3.3 Three-layer fallback logic - Architecture Improvement Version

    V3.3 架构改进：
    - 优先使用策略模式的新选项解析器
    - 保持V3.2的严格边界控制作为回退
    - 统一的选项解析接口
    - 详细的解析统计

    严格的边界规则（回退模式）：
    1. 第一层：只有AI提供了有效选项时才使用，完全阻断后续层级
    2. 第二层：只有AI没有提供有效选项时才执行规则引擎
    3. 第三层：只有前两层都失败时才使用后备选项
    4. 每一层都有严格的有效性检查，确保边界清晰

    Args:
        ai_options: AI提供的预定义选项
        text: 用于动态生成选项的文本内容
        config: 配置字典，包含用户自定义的后备选项

    Returns:
        List[str]: 最终的选项列表
    """
    # V3.3 优先使用策略模式的新选项解析器
    try:
        from .option_resolver import resolve_final_options_v3

        return resolve_final_options_v3(text, ai_options, config, "zh_CN")
    except Exception as e:
        print(f"V3.3 选项解析器失败，回退到V3.2方法: {e}")

    # V3.2 回退：导入配置管理器（避免循环导入）
    from .config_manager import (
        get_config,
        get_fallback_options,
        get_rule_engine_enabled,
        get_custom_options_enabled,
    )

    if config is None:
        config = get_config()

    # 第一层：AI选项优先 - 严格边界检查
    if is_valid_ai_options(ai_options):
        # AI提供了有效选项，严格过滤并直接返回，完全阻断后续处理
        valid_ai_options = [
            option.strip()
            for option in ai_options
            if isinstance(option, str) and option.strip()
        ]
        if valid_ai_options:  # 双重检查确保有效性
            return valid_ai_options

    # 第二层：规则引擎动态生成 - 可控制启用/禁用
    rule_engine_enabled = get_rule_engine_enabled(config)
    if rule_engine_enabled and text and isinstance(text, str) and text.strip():
        try:
            # V3.3 使用可配置规则引擎
            dynamic_options = extract_options_from_text(text.strip(), "zh_CN", True)
            if dynamic_options and len(dynamic_options) > 0:
                # 规则引擎生成了有效选项，返回并阻断第三层
                return dynamic_options
        except Exception:
            # 规则引擎失败，静默继续到第三层
            pass

    # 第三层：用户自定义后备选项 - 可控制启用/禁用
    custom_options_enabled = get_custom_options_enabled(config)
    if custom_options_enabled:
        try:
            fallback_options = get_fallback_options(config)
            if fallback_options and len(fallback_options) > 0:
                return fallback_options
        except Exception:
            # 后备选项获取失败，静默处理
            pass

    # V3.2 严格边界控制：如果用户禁用了所有层级，返回空选项
    # 这样UI就不会显示任何选项，完全由用户手动输入
    return []


def get_options_summary(options: List[str]) -> str:
    """
    获取选项的简要描述，用于调试和日志
    Get brief description of options for debugging and logging

    Args:
        options: 选项列表

    Returns:
        str: 选项的简要描述
    """
    if not options:
        return "无选项 (No options)"

    if len(options) <= 3:
        return f"选项: {', '.join(options)}"
    else:
        return f"选项: {', '.join(options[:3])}... (共{len(options)}个)"


# V3.3 性能监控和缓存管理函数
def get_rule_engine_performance_stats() -> Dict[str, Any]:
    """
    获取规则引擎性能统计信息 (V3.3 架构改进版本)
    Get rule engine performance statistics (V3.3 Architecture Improvement Version)

    Returns:
        Dict[str, Any]: 包含缓存和性能统计的字典
    """
    from .text_processor import get_text_processing_stats
    from .configurable_rule_engine import get_configurable_engine_stats
    from ..core import get_stats_collector

    # 使用新的统一统计收集器
    stats_collector = get_stats_collector()
    rule_engine_stats = stats_collector.get_category_stats("rule_engine")

    text_processing_stats = get_text_processing_stats()
    configurable_stats = get_configurable_engine_stats()

    return {
        "rule_engine_stats": rule_engine_stats,
        "text_processing": text_processing_stats,
        "configurable_engine": configurable_stats,
        "optimization_enabled": True,
        "version": "V3.3-Optimized",
    }


def reload_configurable_rules() -> bool:
    """
    重新加载可配置规则 (V3.3 新增)
    Reload configurable rules (V3.3 New)

    Returns:
        bool: 是否重新加载成功
    """
    try:
        engine = get_configurable_rule_engine()
        return engine.reload_rules()
    except Exception as e:
        print(f"重新加载可配置规则失败: {e}")
        return False


def add_custom_rule_pattern(
    language: str,
    name: str,
    triggers: List[str],
    options: List[str],
    priority: int = 10,
) -> bool:
    """
    添加自定义规则模式 (V3.3 新增)
    Add custom rule pattern (V3.3 New)

    Args:
        language: 语言代码
        name: 模式名称
        triggers: 触发词列表
        options: 选项列表
        priority: 优先级

    Returns:
        bool: 是否添加成功
    """
    try:
        engine = get_configurable_rule_engine()
        pattern = {
            "triggers": triggers,
            "options": options,
            "priority": priority,
            "enabled": True,
            "description": f"自定义模式: {name}",
        }
        return engine.add_custom_pattern(language, name, pattern)
    except Exception as e:
        print(f"添加自定义规则模式失败: {e}")
        return False


def clear_rule_engine_cache() -> None:
    """
    清空规则引擎缓存 (V3.3 优化版本)
    Clear rule engine cache (V3.3 Optimized Version)
    """
    from .text_processor import clear_text_processing_cache
    from ..core import get_stats_collector

    # 清理文本处理缓存
    clear_text_processing_cache()

    # 重置规则引擎统计
    stats_collector = get_stats_collector()
    stats_collector.reset_stats("rule_engine")


def benchmark_rule_engine(iterations: int = 1000) -> Dict[str, float]:
    """
    规则引擎性能基准测试
    Rule engine performance benchmark

    Args:
        iterations: 测试迭代次数

    Returns:
        Dict[str, float]: 性能基准结果
    """
    import time
    import statistics

    test_texts = [
        "你觉得这个方案怎么样？",
        "请确认是否继续执行",
        "建议选择哪个选项",
        "需要修改这个文件吗",
        "这是一个普通的陈述句",
    ]

    # 清空缓存确保公平测试
    clear_rule_engine_cache()

    # 第一轮：无缓存性能测试
    first_run_times = []
    for text in test_texts:
        start_time = time.perf_counter()
        extract_options_from_text(text)
        end_time = time.perf_counter()
        first_run_times.append(end_time - start_time)

    # 第二轮：缓存命中性能测试
    cached_run_times = []
    for _ in range(iterations // len(test_texts)):
        for text in test_texts:
            start_time = time.perf_counter()
            extract_options_from_text(text)
            end_time = time.perf_counter()
            cached_run_times.append(end_time - start_time)

    # 获取统计信息
    stats = get_rule_engine_performance_stats()
    text_processing_stats = stats.get("text_processing", {})

    return {
        "first_run_avg_ms": statistics.mean(first_run_times) * 1000,
        "cached_run_avg_ms": statistics.mean(cached_run_times) * 1000,
        "speedup_factor": statistics.mean(first_run_times)
        / statistics.mean(cached_run_times),
        "cache_hit_rate": text_processing_stats.get("normalize_cache_info", {}).get(
            "hits", 0
        )
        / max(
            text_processing_stats.get("normalize_cache_info", {}).get("hits", 0)
            + text_processing_stats.get("normalize_cache_info", {}).get("misses", 0),
            1,
        )
        * 100,
    }


# 测试和调试函数
def test_rule_engine():
    """
    测试规则引擎的基本功能 (V3.2 增强版本)
    Test basic functionality of rule engine (V3.2 Enhanced Version)
    """
    test_cases = [
        "你觉得这个方案怎么样？",
        "请确认是否继续执行",
        "建议选择哪个选项",
        "需要修改这个文件吗",
        "这是一个普通的陈述句",
    ]

    print("规则引擎测试 - V3.2 缓存优化版本 (Rule Engine Test - V3.2 Cached Version):")
    print("-" * 60)

    # 清空缓存开始测试
    clear_rule_engine_cache()

    for i, text in enumerate(test_cases, 1):
        print(f"{i}. 输入: {text}")

        # 第一次调用（无缓存）
        import time

        start_time = time.perf_counter()
        options = extract_options_from_text(text)
        first_call_time = time.perf_counter() - start_time

        # 第二次调用（缓存命中）
        start_time = time.perf_counter()
        extract_options_from_text(text)  # 应该命中缓存
        second_call_time = time.perf_counter() - start_time

        print(f"   输出: {options}")
        print(f"   首次调用: {first_call_time*1000:.3f}ms")
        print(f"   缓存命中: {second_call_time*1000:.3f}ms")
        print(f"   性能提升: {(first_call_time/second_call_time):.1f}x")
        print()

    # 显示统计信息
    stats = get_rule_engine_performance_stats()
    print("规则引擎统计 (Rule Engine Statistics):")
    print(f"  文本处理统计: {stats.get('text_processing', {})}")
    print(f"  可配置引擎统计: {stats.get('configurable_engine', {})}")
    print(f"  优化版本: {stats.get('version', 'Unknown')}")
    print()


def test_rule_engine_performance():
    """
    专门的性能测试函数
    Dedicated performance test function
    """
    print("规则引擎性能基准测试 (Rule Engine Performance Benchmark):")
    print("-" * 60)

    benchmark_results = benchmark_rule_engine(1000)

    print(f"首次运行平均时间: {benchmark_results['first_run_avg_ms']:.3f}ms")
    print(f"缓存命中平均时间: {benchmark_results['cached_run_avg_ms']:.3f}ms")
    print(f"性能提升倍数: {benchmark_results['speedup_factor']:.1f}x")
    print(f"缓存命中率: {benchmark_results['cache_hit_rate']:.1f}%")

    # 性能目标验证
    if benchmark_results["speedup_factor"] >= 5:
        print("✅ 性能优化目标达成！(5x+ 提升)")
    else:
        print("⚠️  性能优化未达预期目标")

    if benchmark_results["cache_hit_rate"] >= 80:
        print("✅ 缓存命中率目标达成！(80%+)")
    else:
        print("⚠️  缓存命中率未达预期目标")


if __name__ == "__main__":
    # 运行测试
    test_rule_engine()

# interactive_feedback_server/utils/option_resolver.py

"""
选项解析器 - V3.3 架构改进版本
Option Resolver - V3.3 Architecture Improvement Version

统一的选项解析器，使用策略模式重构三层逻辑。
Unified option resolver using strategy pattern to refactor three-layer logic.
"""

from typing import List, Dict, Any, Optional
from .option_strategy import OptionContext, OptionResult, StrategyChain
from .option_strategies import (
    AIOptionsStrategy,
    FallbackOptionsStrategy,
)
from ..monitoring import get_metric_collector, PerformanceTimer
from ..error_handling import get_error_handler, create_error_context, SystemError
from ..core import get_stats_collector, increment_stat, register_singleton


class OptionResolver:
    """
    选项解析器
    Option Resolver

    使用策略链模式实现三层回退逻辑的统一解析
    Implements unified parsing of three-layer fallback logic using strategy chain pattern
    """

    def __init__(self):
        """初始化选项解析器"""
        self.strategy_chain = StrategyChain()
        self._setup_default_strategies()

        # 插件系统集成
        self._plugin_integration_enabled = True
        self._initialize_plugin_system()

        # 性能监控集成
        self._monitoring_enabled = True
        self._initialize_monitoring()

        # 错误处理集成
        self._error_handling_enabled = True
        self._initialize_error_handling()

        # 使用统一的统计收集器
        self.stats_collector = get_stats_collector()

    def _setup_default_strategies(self) -> None:
        """
        设置默认策略链
        Setup default strategy chain
        """
        # V4.0 简化：按优先级添加策略（移除规则引擎）
        self.strategy_chain.add_strategy(AIOptionsStrategy())
        self.strategy_chain.add_strategy(FallbackOptionsStrategy())

    def _initialize_plugin_system(self) -> None:
        """
        初始化插件系统
        Initialize plugin system
        """
        if not self._plugin_integration_enabled:
            return

        try:
            # 导入插件管理器
            from ..plugins import get_plugin_manager

            self.plugin_manager = get_plugin_manager()

            # 发现并加载内置插件
            self._load_builtin_plugins()

        except Exception as e:
            print(f"插件系统初始化失败: {e}")
            self._plugin_integration_enabled = False

    def _load_builtin_plugins(self) -> None:
        """
        加载内置插件
        Load built-in plugins
        """
        try:
            # 发现插件
            discovered_plugins = self.plugin_manager.discover_plugins()

            # 加载内置插件
            for plugin_info in discovered_plugins:
                if "builtin" in plugin_info.get("path", ""):
                    plugin_path = plugin_info["path"]
                    plugin_name = plugin_info["name"]

                    if self.plugin_manager.load_plugin(plugin_path, plugin_name):
                        # 激活插件
                        self.plugin_manager.activate_plugin(plugin_name)
                        print(f"已加载内置插件: {plugin_name}")

        except Exception as e:
            print(f"加载内置插件失败: {e}")

    def _initialize_monitoring(self) -> None:
        """
        初始化性能监控
        Initialize performance monitoring
        """
        if not self._monitoring_enabled:
            return

        try:
            # 获取指标收集器
            self.metric_collector = get_metric_collector()

            # 初始化监控指标
            self.metric_collector.set_gauge("option_resolver.initialized", 1.0)

        except Exception as e:
            print(f"性能监控初始化失败: {e}")
            self._monitoring_enabled = False

    def _initialize_error_handling(self) -> None:
        """
        初始化错误处理
        Initialize error handling
        """
        if not self._error_handling_enabled:
            return

        try:
            # 获取错误处理器
            self.error_handler = get_error_handler()

            # 注册恢复函数
            self._register_recovery_functions()

        except Exception as e:
            print(f"错误处理初始化失败: {e}")
            self._error_handling_enabled = False

    def _register_recovery_functions(self) -> None:
        """注册恢复函数"""
        try:
            from ..error_handling import get_recovery_manager

            recovery_manager = get_recovery_manager()

            # 注册选项解析器恢复函数
            def recover_option_resolver():
                """选项解析器恢复函数"""
                try:
                    # 重新初始化策略链
                    self.strategy_chain = StrategyChain()
                    self._setup_default_strategies()
                    return True
                except Exception:
                    return False

            recovery_manager.register_recovery_function(
                component="option_resolver",
                operation="recover",
                recovery_function=recover_option_resolver,
                priority=2,
                max_attempts=3,
                timeout=30.0,
            )

            # 注册健康检查
            def health_check():
                """选项解析器健康检查"""
                try:
                    # 简单的健康检查：测试解析功能
                    test_result = self.resolve_options("健康检查", None, None, "zh_CN")
                    return isinstance(test_result, list)
                except Exception:
                    return False

            recovery_manager.register_health_check("option_resolver", health_check)

        except Exception as e:
            print(f"注册恢复函数失败: {e}")

    def resolve_options(
        self,
        text: str,
        ai_options: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        language: str = "zh_CN",
    ) -> List[str]:
        """
        解析选项 - V3.3 策略模式版本
        Resolve options - V3.3 Strategy Pattern Version

        Args:
            text: 用户输入文本
            ai_options: AI提供的选项
            config: 配置信息
            language: 语言代码

        Returns:
            List[str]: 解析出的选项列表
        """
        # 性能监控
        if self._monitoring_enabled and hasattr(self, "metric_collector"):
            self.metric_collector.increment_counter("option_resolver.resolve_requests")
            timer = PerformanceTimer(
                self.metric_collector, "option_resolver.resolve_duration"
            )
            timer.__enter__()
        else:
            timer = None

        try:
            # 统一的统计收集
            self.stats_collector.increment(
                "total_resolutions", category="option_resolver"
            )

            # 创建解析上下文
            context = OptionContext(
                text=text,
                ai_options=ai_options,
                config=config,
                language=language,
                metadata={
                    "resolver_version": "V3.3",
                    "timestamp": self._get_current_timestamp(),
                },
            )

            # 执行策略链
            result = self.strategy_chain.execute(context)

            if result and result.options:
                # 统一的成功统计
                self.stats_collector.increment(
                    "successful_resolutions", category="option_resolver"
                )
                self.stats_collector.increment(
                    f"strategy_usage_{result.strategy_name}", category="option_resolver"
                )

                # 性能监控（如果启用）
                if self._monitoring_enabled and hasattr(self, "metric_collector"):
                    self.metric_collector.increment_counter(
                        "option_resolver.successful_resolutions"
                    )
                    self.metric_collector.increment_counter(
                        f"option_resolver.strategy_usage.{result.strategy_name}"
                    )

                return result.options

            # 失败统计
            self.stats_collector.increment(
                "failed_resolutions", category="option_resolver"
            )
            if self._monitoring_enabled and hasattr(self, "metric_collector"):
                self.metric_collector.increment_counter(
                    "option_resolver.failed_resolutions"
                )

            return []

        except Exception as e:
            # 错误处理
            if self._error_handling_enabled and hasattr(self, "error_handler"):
                error_context = create_error_context(
                    component="option_resolver",
                    operation="resolve_options",
                    additional_data={
                        "text_length": len(text) if text else 0,
                        "has_ai_options": bool(ai_options),
                        "language": language,
                    },
                )

                recovery_result = self.error_handler.handle_error(e, error_context)

                # 如果有恢复结果，尝试使用
                if recovery_result and recovery_result.get("action") == "fallback":
                    return ["是的", "不是", "需要更多信息"]  # 默认选项

            # 如果错误处理失败，返回默认选项
            return ["是的", "不是", "需要更多信息"]

        finally:
            # 结束性能计时
            if timer:
                timer.__exit__(None, None, None)

    def resolve_with_details(
        self,
        text: str,
        ai_options: Optional[List[str]] = None,
        config: Optional[Dict[str, Any]] = None,
        language: str = "zh_CN",
    ) -> Dict[str, Any]:
        """
        解析选项并返回详细信息
        Resolve options and return detailed information

        Args:
            text: 用户输入文本
            ai_options: AI提供的选项
            config: 配置信息
            language: 语言代码

        Returns:
            Dict[str, Any]: 包含选项和详细信息的字典
        """
        self._resolution_stats["total_resolutions"] += 1

        # 创建解析上下文
        context = OptionContext(
            text=text,
            ai_options=ai_options,
            config=config,
            language=language,
            metadata={
                "resolver_version": "V3.3",
                "timestamp": self._get_current_timestamp(),
                "detailed_mode": True,
            },
        )

        # 执行策略链
        result = self.strategy_chain.execute(context)

        if result and result.options:
            self._resolution_stats["successful_resolutions"] += 1

            # 更新层级使用统计
            strategy_name = result.strategy_name
            if strategy_name in self._resolution_stats["layer_usage"]:
                self._resolution_stats["layer_usage"][strategy_name] += 1

            return {
                "options": result.options,
                "strategy_used": result.strategy_name,
                "confidence": result.confidence,
                "metadata": result.metadata,
                "context": {
                    "text_length": len(text),
                    "has_ai_options": bool(ai_options),
                    "has_config": bool(config),
                    "language": language,
                },
                "success": True,
            }

        # 所有策略都失败
        return {
            "options": [],
            "strategy_used": None,
            "confidence": 0.0,
            "metadata": {},
            "context": {
                "text_length": len(text),
                "has_ai_options": bool(ai_options),
                "has_config": bool(config),
                "language": language,
            },
            "success": False,
            "error": "All strategies failed to generate options",
        }

    def add_strategy(self, strategy) -> None:
        """
        添加自定义策略
        Add custom strategy

        Args:
            strategy: 策略实例
        """
        self.strategy_chain.add_strategy(strategy)

    def remove_strategy(self, name: str) -> bool:
        """
        移除策略
        Remove strategy

        Args:
            name: 策略名称

        Returns:
            bool: 是否成功移除
        """
        return self.strategy_chain.remove_strategy(name)

    def enable_strategy(self, name: str) -> bool:
        """
        启用策略
        Enable strategy

        Args:
            name: 策略名称

        Returns:
            bool: 是否成功启用
        """
        strategy = self.strategy_chain.get_strategy(name)
        if strategy:
            strategy.enable()
            return True
        return False

    def disable_strategy(self, name: str) -> bool:
        """
        禁用策略
        Disable strategy

        Args:
            name: 策略名称

        Returns:
            bool: 是否成功禁用
        """
        strategy = self.strategy_chain.get_strategy(name)
        if strategy:
            strategy.disable()
            return True
        return False

    def get_strategy_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取策略详细信息
        Get detailed strategy information

        Args:
            name: 策略名称

        Returns:
            Optional[Dict[str, Any]]: 策略信息
        """
        strategy = self.strategy_chain.get_strategy(name)
        if strategy and hasattr(strategy, "get_strategy_info"):
            return strategy.get_strategy_info()
        return None

    def get_resolver_stats(self) -> Dict[str, Any]:
        """
        获取解析器统计信息
        Get resolver statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 使用统一的统计收集器
        resolver_stats = self.stats_collector.get_category_stats("option_resolver")
        chain_stats = self.strategy_chain.get_chain_stats()

        # 计算成功率
        total = resolver_stats.get("count", 0)
        successful = self.stats_collector.get_counter("successful_resolutions")
        success_rate = (successful / max(total, 1)) * 100

        # 插件统计
        plugin_stats = {}
        if self._plugin_integration_enabled and hasattr(self, "plugin_manager"):
            try:
                plugin_stats = self.plugin_manager.get_manager_stats()
            except Exception:
                plugin_stats = {"error": "Failed to get plugin stats"}

        return {
            "resolver_stats": {
                "total_resolutions": total,
                "successful_resolutions": successful,
                "failed_resolutions": self.stats_collector.get_counter(
                    "failed_resolutions"
                ),
                "success_rate_percent": round(success_rate, 2),
                "strategy_usage": {
                    "ai_options": self.stats_collector.get_counter(
                        "strategy_usage_ai_options"
                    ),
                    "fallback_options": self.stats_collector.get_counter(
                        "strategy_usage_fallback_options"
                    ),
                },
            },
            "strategy_chain_stats": chain_stats,
            "plugin_stats": plugin_stats,
            "plugin_integration_enabled": self._plugin_integration_enabled,
            "monitoring_enabled": self._monitoring_enabled,
            "error_handling_enabled": self._error_handling_enabled,
            "version": "V3.3-Optimized",
        }

    def load_plugin(self, plugin_path: str, plugin_name: str = None) -> bool:
        """
        加载插件
        Load plugin

        Args:
            plugin_path: 插件路径
            plugin_name: 插件名称

        Returns:
            bool: 是否加载成功
        """
        if not self._plugin_integration_enabled or not hasattr(self, "plugin_manager"):
            return False

        return self.plugin_manager.load_plugin(plugin_path, plugin_name)

    def activate_plugin(self, plugin_name: str) -> bool:
        """
        激活插件
        Activate plugin

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否激活成功
        """
        if not self._plugin_integration_enabled or not hasattr(self, "plugin_manager"):
            return False

        return self.plugin_manager.activate_plugin(plugin_name)

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """
        停用插件
        Deactivate plugin

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否停用成功
        """
        if not self._plugin_integration_enabled or not hasattr(self, "plugin_manager"):
            return False

        return self.plugin_manager.deactivate_plugin(plugin_name)

    def get_loaded_plugins(self) -> List[str]:
        """
        获取已加载的插件列表
        Get loaded plugins list

        Returns:
            List[str]: 插件名称列表
        """
        if not self._plugin_integration_enabled or not hasattr(self, "plugin_manager"):
            return []

        return list(self.plugin_manager.get_all_plugins().keys())

    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self.stats_collector.reset_stats("option_resolver")
        self.strategy_chain.reset_stats()

    def _get_current_timestamp(self) -> float:
        """获取当前时间戳"""
        import time

        return time.time()

    def __str__(self) -> str:
        return f"OptionResolver(strategies={len(self.strategy_chain)}, version=V3.3)"


# 使用单例管理器注册选项解析器
@register_singleton("option_resolver")
def create_option_resolver() -> OptionResolver:
    """创建选项解析器实例"""
    return OptionResolver()


def get_option_resolver() -> OptionResolver:
    """
    获取全局选项解析器实例
    Get global option resolver instance

    Returns:
        OptionResolver: 选项解析器实例
    """
    return create_option_resolver()


def resolve_final_options_v3(
    text: str,
    ai_options: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    language: str = "zh_CN",
) -> List[str]:
    """
    V3.3 版本的选项解析函数
    V3.3 version of option resolution function

    Args:
        text: 用户输入文本
        ai_options: AI提供的选项
        config: 配置信息
        language: 语言代码

    Returns:
        List[str]: 解析出的选项列表
    """
    resolver = get_option_resolver()
    return resolver.resolve_options(text, ai_options, config, language)


def get_resolver_stats() -> Dict[str, Any]:
    """
    获取全局解析器统计信息
    Get global resolver statistics

    Returns:
        Dict[str, Any]: 统计信息
    """
    resolver = get_option_resolver()
    return resolver.get_resolver_stats()

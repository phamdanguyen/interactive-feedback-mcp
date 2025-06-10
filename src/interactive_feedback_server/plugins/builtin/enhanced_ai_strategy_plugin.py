# interactive_feedback_server/plugins/builtin/enhanced_ai_strategy_plugin.py

"""
增强AI策略插件 - V3.3 架构改进版本
Enhanced AI Strategy Plugin - V3.3 Architecture Improvement Version

提供增强的AI选项处理策略，作为插件化架构的示例实现。
Provides enhanced AI option processing strategy as an example implementation of plugin architecture.
"""

from typing import List, Optional, Dict, Any
from ..plugin_interface import BasePlugin, PluginMetadata, PluginType, PluginContext
from ...utils.option_strategy import BaseOptionStrategy, OptionContext, OptionResult


class EnhancedAIStrategy(BaseOptionStrategy):
    """
    增强AI策略
    Enhanced AI Strategy

    提供比基础AI策略更智能的选项处理
    Provides more intelligent option processing than basic AI strategy
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化增强AI策略"""
        super().__init__(
            name="enhanced_ai_options",
            priority=0,  # 比基础AI策略优先级更高
            min_text_length=1,
            max_options=5,
        )
        self.config = config or {}

        # 增强功能配置
        self.enable_sentiment_analysis = self.config.get(
            "enable_sentiment_analysis", True
        )
        self.enable_context_awareness = self.config.get(
            "enable_context_awareness", True
        )
        self.enable_smart_filtering = self.config.get("enable_smart_filtering", True)

    def is_applicable(self, context: OptionContext) -> bool:
        """
        检查增强AI策略是否适用
        Check if enhanced AI strategy is applicable
        """
        # 基础检查
        if not super().is_applicable(context):
            return False

        # 检查是否有AI选项
        if not context.ai_options:
            return False

        # 检查AI选项质量
        if not self._has_quality_ai_options(context.ai_options):
            return False

        return True

    def parse_options(self, context: OptionContext) -> Optional[OptionResult]:
        """
        使用增强逻辑解析AI选项
        Parse AI options using enhanced logic
        """
        if not context.ai_options:
            return None

        # 智能过滤和增强
        enhanced_options = self._enhance_ai_options(context.ai_options, context)

        if not enhanced_options:
            return None

        # 计算增强置信度
        confidence = self._calculate_enhanced_confidence(enhanced_options, context)

        return self.create_result(
            options=enhanced_options,
            confidence=confidence,
            should_stop=True,
            source="enhanced_ai",
            original_count=len(context.ai_options),
            enhanced_count=len(enhanced_options),
            sentiment_analyzed=self.enable_sentiment_analysis,
            context_aware=self.enable_context_awareness,
        )

    def _has_quality_ai_options(self, ai_options: List[str]) -> bool:
        """
        检查AI选项质量
        Check AI options quality
        """
        if not ai_options:
            return False

        valid_count = 0
        for option in ai_options:
            if isinstance(option, str) and len(option.strip()) >= 2:
                valid_count += 1

        # 至少需要一个高质量选项
        return valid_count > 0

    def _enhance_ai_options(
        self, ai_options: List[str], context: OptionContext
    ) -> List[str]:
        """
        增强AI选项
        Enhance AI options
        """
        enhanced = []

        for option in ai_options:
            if not isinstance(option, str) or not option.strip():
                continue

            enhanced_option = option.strip()

            # 智能过滤
            if self.enable_smart_filtering:
                enhanced_option = self._smart_filter_option(enhanced_option, context)
                if not enhanced_option:
                    continue

            # 情感分析增强
            if self.enable_sentiment_analysis:
                enhanced_option = self._sentiment_enhance_option(
                    enhanced_option, context
                )

            # 上下文感知增强
            if self.enable_context_awareness:
                enhanced_option = self._context_enhance_option(enhanced_option, context)

            if enhanced_option and enhanced_option not in enhanced:
                enhanced.append(enhanced_option)

        return enhanced[: self.max_options]

    def _smart_filter_option(
        self, option: str, context: OptionContext
    ) -> Optional[str]:
        """
        智能过滤选项
        Smart filter option
        """
        # 过滤过短或过长的选项
        if len(option) < 1 or len(option) > 100:
            return None

        # 过滤纯数字或纯符号
        if option.isdigit() or not any(c.isalpha() for c in option):
            return None

        # 过滤重复词汇
        words = option.lower().split()
        if len(words) > 1 and len(set(words)) == 1:
            return None

        return option

    def _sentiment_enhance_option(self, option: str, context: OptionContext) -> str:
        """
        情感分析增强选项
        Sentiment analysis enhance option
        """
        # 简单的情感分析（实际应用中可以使用更复杂的NLP库）
        positive_words = ["好", "是", "同意", "确定", "yes", "ok", "good"]
        negative_words = ["不", "否", "拒绝", "取消", "no", "cancel", "bad"]

        option_lower = option.lower()

        # 根据情感倾向调整选项表达
        if any(word in option_lower for word in positive_words):
            # 积极选项，保持原样或稍作优化
            return option
        elif any(word in option_lower for word in negative_words):
            # 消极选项，保持原样
            return option
        else:
            # 中性选项，保持原样
            return option

    def _context_enhance_option(self, option: str, context: OptionContext) -> str:
        """
        上下文感知增强选项
        Context-aware enhance option
        """
        # 根据输入文本的上下文调整选项
        text_lower = context.text.lower()

        # 问题类文本的选项优化
        if any(word in text_lower for word in ["?", "？", "如何", "怎么", "什么"]):
            # 对于问题，确保选项是回答性的
            if not any(word in option.lower() for word in ["是", "不", "yes", "no"]):
                return option

        # 确认类文本的选项优化
        if any(
            word in text_lower for word in ["确认", "同意", "继续", "confirm", "agree"]
        ):
            # 对于确认类，优先确认/取消选项
            return option

        return option

    def _calculate_enhanced_confidence(
        self, options: List[str], context: OptionContext
    ) -> float:
        """
        计算增强置信度
        Calculate enhanced confidence
        """
        base_confidence = 0.95  # 增强AI策略基础置信度很高

        # 根据增强功能调整置信度
        enhancement_bonus = 0.0
        if self.enable_sentiment_analysis:
            enhancement_bonus += 0.02
        if self.enable_context_awareness:
            enhancement_bonus += 0.02
        if self.enable_smart_filtering:
            enhancement_bonus += 0.01

        # 根据选项质量调整
        quality_score = self._assess_enhanced_quality(options, context)

        final_confidence = (base_confidence + enhancement_bonus) * quality_score
        return min(1.0, max(0.0, final_confidence))

    def _assess_enhanced_quality(
        self, options: List[str], context: OptionContext
    ) -> float:
        """
        评估增强选项质量
        Assess enhanced option quality
        """
        if not options:
            return 0.0

        quality_factors = []

        for option in options:
            # 长度合理性
            length_score = 1.0
            if len(option) < 2:
                length_score = 0.5
            elif len(option) > 50:
                length_score = 0.8

            # 内容丰富性
            content_score = 1.0
            if len(option.split()) == 1:
                content_score = 0.9  # 单词选项稍微降分

            # 上下文相关性
            context_score = 1.0
            if context.text:
                # 简单的相关性检查
                common_chars = set(option.lower()) & set(context.text.lower())
                if len(common_chars) > 0:
                    context_score = 1.1  # 有共同字符加分

            option_quality = length_score * content_score * context_score
            quality_factors.append(min(1.2, option_quality))

        return sum(quality_factors) / len(quality_factors)


class EnhancedAIStrategyPlugin(BasePlugin):
    """
    增强AI策略插件
    Enhanced AI Strategy Plugin

    将增强AI策略封装为插件
    Wraps enhanced AI strategy as a plugin
    """

    def __init__(self, metadata: PluginMetadata):
        """初始化插件"""
        super().__init__(metadata)
        self.strategy: Optional[EnhancedAIStrategy] = None

    def _do_initialize(self) -> bool:
        """执行插件初始化"""
        try:
            # 获取插件配置
            strategy_config = self.get_config("strategy", {})

            # 创建增强AI策略实例
            self.strategy = EnhancedAIStrategy(strategy_config)

            return True
        except Exception as e:
            print(f"增强AI策略插件初始化失败: {e}")
            return False

    def _do_activate(self) -> bool:
        """执行插件激活"""
        try:
            if not self.strategy:
                return False

            # 注册策略到选项解析器
            from ...utils.option_resolver import get_option_resolver

            resolver = get_option_resolver()
            resolver.add_strategy(self.strategy)

            return True
        except Exception as e:
            print(f"增强AI策略插件激活失败: {e}")
            return False

    def _do_deactivate(self) -> bool:
        """执行插件停用"""
        try:
            if not self.strategy:
                return True

            # 从选项解析器移除策略
            from ...utils.option_resolver import get_option_resolver

            resolver = get_option_resolver()
            resolver.remove_strategy(self.strategy.name)

            return True
        except Exception as e:
            print(f"增强AI策略插件停用失败: {e}")
            return False

    def _do_cleanup(self) -> bool:
        """执行插件清理"""
        try:
            self.strategy = None
            return True
        except Exception as e:
            print(f"增强AI策略插件清理失败: {e}")
            return False

    def get_strategy(self) -> Optional[EnhancedAIStrategy]:
        """获取策略实例"""
        return self.strategy


# 插件工厂函数
def create_plugin() -> EnhancedAIStrategyPlugin:
    """
    创建插件实例
    Create plugin instance

    Returns:
        EnhancedAIStrategyPlugin: 插件实例
    """
    metadata = PluginMetadata(
        name="enhanced_ai_strategy",
        version="1.0.0",
        description="增强AI选项策略插件，提供智能选项处理功能",
        author="Interactive Feedback System",
        plugin_type=PluginType.OPTION_STRATEGY,
        dependencies=[],
        min_system_version="3.3.0",
    )

    return EnhancedAIStrategyPlugin(metadata)

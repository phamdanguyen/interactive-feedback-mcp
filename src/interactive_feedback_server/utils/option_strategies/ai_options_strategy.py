# interactive_feedback_server/utils/option_strategies/ai_options_strategy.py

"""
AI选项策略 - V3.3 架构改进版本
AI Options Strategy - V3.3 Architecture Improvement Version

处理AI提供的选项，作为第一层回退逻辑。
Handles AI-provided options as the first layer of fallback logic.
"""

from typing import List, Optional
from ..option_strategy import BaseOptionStrategy, OptionContext, OptionResult


class AIOptionsStrategy(BaseOptionStrategy):
    """
    AI选项策略
    AI Options Strategy

    处理AI直接提供的选项，优先级最高
    Handles AI-provided options with highest priority
    """

    def __init__(self):
        """初始化AI选项策略"""
        super().__init__(
            name="ai_options",
            priority=1,  # 最高优先级
            min_text_length=1,  # AI选项不依赖文本长度
            max_options=5,  # AI可能提供更多选项
        )

    def is_applicable(self, context: OptionContext) -> bool:
        """
        检查是否有AI提供的选项
        Check if AI-provided options are available

        Args:
            context: 选项解析上下文

        Returns:
            bool: 是否适用
        """
        # 检查是否有AI选项
        if not context.ai_options:
            return False

        # 检查AI选项是否有效
        if not isinstance(context.ai_options, list):
            return False

        # 检查是否有非空选项
        valid_options = [
            opt for opt in context.ai_options if isinstance(opt, str) and opt.strip()
        ]

        return len(valid_options) > 0

    def parse_options(self, context: OptionContext) -> Optional[OptionResult]:
        """
        解析AI提供的选项
        Parse AI-provided options

        Args:
            context: 选项解析上下文

        Returns:
            Optional[OptionResult]: 解析结果
        """
        if not context.ai_options:
            return None

        # 过滤和清理AI选项
        valid_options = []
        for option in context.ai_options:
            if isinstance(option, str) and option.strip():
                clean_option = option.strip()
                if clean_option not in valid_options:  # 去重
                    valid_options.append(clean_option)

        if not valid_options:
            return None

        # 计算置信度（基于选项质量）
        confidence = self._calculate_confidence(valid_options, context)

        return self.create_result(
            options=valid_options,
            confidence=confidence,
            should_stop=True,  # AI选项通常应该停止后续策略
            source="ai",
            original_count=len(context.ai_options),
            filtered_count=len(valid_options),
        )

    def _calculate_confidence(
        self, options: List[str], context: OptionContext
    ) -> float:
        """
        计算AI选项的置信度
        Calculate confidence of AI options

        Args:
            options: 有效选项列表
            context: 选项解析上下文

        Returns:
            float: 置信度 (0.0-1.0)
        """
        base_confidence = 0.9  # AI选项基础置信度较高

        # 根据选项数量调整
        if len(options) == 0:
            return 0.0
        elif len(options) == 1:
            confidence = base_confidence * 0.8  # 单选项置信度稍低
        elif len(options) <= 3:
            confidence = base_confidence  # 2-3个选项置信度最高
        else:
            confidence = base_confidence * 0.9  # 过多选项置信度稍低

        # 根据选项质量调整
        quality_score = self._assess_option_quality(options)
        confidence *= quality_score

        return min(1.0, max(0.0, confidence))

    def _assess_option_quality(self, options: List[str]) -> float:
        """
        评估选项质量
        Assess option quality

        Args:
            options: 选项列表

        Returns:
            float: 质量分数 (0.0-1.0)
        """
        if not options:
            return 0.0

        quality_factors = []

        for option in options:
            # 长度合理性 (2-50字符)
            length_score = 1.0
            if len(option) < 2:
                length_score = 0.3
            elif len(option) > 50:
                length_score = 0.7

            # 内容合理性（不全是标点符号或数字）
            content_score = 1.0
            if (
                option.replace(" ", "")
                .replace(".", "")
                .replace("?", "")
                .replace("!", "")
                .isdigit()
            ):
                content_score = 0.5
            elif not any(c.isalpha() for c in option):
                content_score = 0.6

            # 常见回复模式检测
            common_patterns = ["是", "否", "好的", "取消", "yes", "no", "ok", "cancel"]
            pattern_score = 1.0
            if option.lower().strip() in [p.lower() for p in common_patterns]:
                pattern_score = 1.2  # 常见模式加分

            option_quality = length_score * content_score * pattern_score
            quality_factors.append(min(1.0, option_quality))

        # 返回平均质量分数
        return sum(quality_factors) / len(quality_factors)

    def get_strategy_info(self) -> dict:
        """
        获取策略详细信息
        Get detailed strategy information

        Returns:
            dict: 策略信息
        """
        return {
            "name": self.name,
            "description": "AI选项策略 - 处理AI直接提供的选项",
            "priority": self.priority,
            "layer": 1,
            "features": [
                "优先级最高",
                "智能置信度计算",
                "选项质量评估",
                "自动去重和清理",
            ],
            "applicable_when": [
                "AI提供了有效选项",
                "选项列表非空",
                "至少包含一个有效字符串",
            ],
        }

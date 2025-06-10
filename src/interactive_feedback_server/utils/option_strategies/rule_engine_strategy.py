# interactive_feedback_server/utils/option_strategies/rule_engine_strategy.py

"""
规则引擎策略 - V3.3 架构改进版本
Rule Engine Strategy - V3.3 Architecture Improvement Version

使用可配置规则引擎动态生成选项，作为第二层回退逻辑。
Uses configurable rule engine to dynamically generate options as the second layer of fallback logic.
"""

from typing import List, Optional
from ..option_strategy import BaseOptionStrategy, OptionContext, OptionResult
from ..configurable_rule_engine import get_configurable_rule_engine


class RuleEngineStrategy(BaseOptionStrategy):
    """
    规则引擎策略
    Rule Engine Strategy

    使用可配置规则引擎根据文本内容动态生成选项
    Uses configurable rule engine to dynamically generate options based on text content
    """

    def __init__(self):
        """初始化规则引擎策略"""
        super().__init__(
            name="rule_engine",
            priority=2,  # 第二优先级
            min_text_length=2,  # 需要足够的文本进行分析
            max_options=3,  # 规则引擎通常生成2-3个选项
        )

        # 获取可配置规则引擎实例
        self._rule_engine = get_configurable_rule_engine()

    def is_applicable(self, context: OptionContext) -> bool:
        """
        检查规则引擎策略是否适用
        Check if rule engine strategy is applicable

        Args:
            context: 选项解析上下文

        Returns:
            bool: 是否适用
        """
        # 基础检查
        if not super().is_applicable(context):
            return False

        # 检查配置是否启用规则引擎
        if context.config:
            rule_engine_enabled = self._get_rule_engine_enabled(context.config)
            if not rule_engine_enabled:
                return False

        # 检查规则引擎是否可用
        if not self._rule_engine:
            return False

        return True

    def parse_options(self, context: OptionContext) -> Optional[OptionResult]:
        """
        使用规则引擎解析选项
        Parse options using rule engine

        Args:
            context: 选项解析上下文

        Returns:
            Optional[OptionResult]: 解析结果
        """
        try:
            # 使用可配置规则引擎提取选项
            options = self._rule_engine.extract_options(
                text=context.text.strip(), language=context.language
            )

            if not options:
                return None

            # 计算置信度
            confidence = self._calculate_confidence(options, context)

            # 获取规则引擎统计信息
            engine_stats = self._rule_engine.get_stats()

            return self.create_result(
                options=options,
                confidence=confidence,
                should_stop=True,  # 规则引擎成功时停止后续策略
                source="rule_engine",
                language=context.language,
                engine_stats=engine_stats,
                text_length=len(context.text),
            )

        except Exception as e:
            print(f"规则引擎策略执行失败: {e}")
            return None

    def _get_rule_engine_enabled(self, config: dict) -> bool:
        """
        检查配置中是否启用规则引擎
        Check if rule engine is enabled in configuration

        Args:
            config: 配置字典

        Returns:
            bool: 是否启用
        """
        # 检查多种可能的配置键
        rule_engine_keys = [
            "rule_engine_enabled",
            "enable_rule_engine",
            "rule_engine",
            "dynamic_options",
        ]

        for key in rule_engine_keys:
            if key in config:
                value = config[key]
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ["true", "1", "yes", "on", "enabled"]
                elif isinstance(value, int):
                    return value != 0

        # 默认启用
        return True

    def _calculate_confidence(
        self, options: List[str], context: OptionContext
    ) -> float:
        """
        计算规则引擎选项的置信度
        Calculate confidence of rule engine options

        Args:
            options: 选项列表
            context: 选项解析上下文

        Returns:
            float: 置信度 (0.0-1.0)
        """
        if not options:
            return 0.0

        base_confidence = 0.8  # 规则引擎基础置信度

        # 根据选项数量调整
        if len(options) == 1:
            confidence = base_confidence * 0.7  # 单选项置信度较低
        elif len(options) <= 3:
            confidence = base_confidence  # 2-3个选项置信度最高
        else:
            confidence = base_confidence * 0.8  # 过多选项置信度稍低

        # 根据文本长度调整（更长的文本通常匹配更准确）
        text_length = len(context.text.strip())
        if text_length < 5:
            confidence *= 0.7
        elif text_length > 20:
            confidence *= 1.1

        # 根据语言调整（中文规则可能更完善）
        if context.language == "zh_CN":
            confidence *= 1.05
        elif context.language == "en_US":
            confidence *= 1.0
        else:
            confidence *= 0.9  # 其他语言置信度稍低

        return min(1.0, max(0.0, confidence))

    def reload_rules(self) -> bool:
        """
        重新加载规则配置
        Reload rule configuration

        Returns:
            bool: 是否重新加载成功
        """
        try:
            return self._rule_engine.reload_rules()
        except Exception as e:
            print(f"重新加载规则失败: {e}")
            return False

    def add_custom_pattern(
        self,
        language: str,
        name: str,
        triggers: List[str],
        options: List[str],
        priority: int = 10,
    ) -> bool:
        """
        添加自定义规则模式
        Add custom rule pattern

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
            pattern = {
                "triggers": triggers,
                "options": options,
                "priority": priority,
                "enabled": True,
                "description": f"自定义模式: {name}",
            }
            return self._rule_engine.add_custom_pattern(language, name, pattern)
        except Exception as e:
            print(f"添加自定义模式失败: {e}")
            return False

    def get_available_languages(self) -> List[str]:
        """
        获取可用的语言列表
        Get available language list

        Returns:
            List[str]: 语言代码列表
        """
        try:
            return self._rule_engine.get_available_languages()
        except Exception:
            return ["zh_CN", "en_US"]  # 默认语言

    def get_engine_stats(self) -> dict:
        """
        获取规则引擎统计信息
        Get rule engine statistics

        Returns:
            dict: 统计信息
        """
        try:
            return self._rule_engine.get_stats()
        except Exception:
            return {}

    def get_strategy_info(self) -> dict:
        """
        获取策略详细信息
        Get detailed strategy information

        Returns:
            dict: 策略信息
        """
        return {
            "name": self.name,
            "description": "规则引擎策略 - 基于可配置规则动态生成选项",
            "priority": self.priority,
            "layer": 2,
            "features": [
                "可配置规则引擎",
                "多语言支持",
                "热重载配置",
                "自定义规则模式",
                "智能置信度计算",
            ],
            "applicable_when": ["文本长度 >= 2字符", "规则引擎已启用", "规则引擎可用"],
            "supported_languages": self.get_available_languages(),
            "engine_stats": self.get_engine_stats(),
        }

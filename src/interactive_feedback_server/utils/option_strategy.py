# interactive_feedback_server/utils/option_strategy.py

"""
选项策略接口 - V3.3 架构改进版本
Option Strategy Interface - V3.3 Architecture Improvement Version

定义统一的选项解析策略接口，实现策略模式重构三层逻辑。
Defines unified option parsing strategy interface, implementing strategy pattern to refactor three-layer logic.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OptionContext:
    """
    选项解析上下文
    Option parsing context

    包含解析过程中需要的所有信息
    Contains all information needed during parsing process
    """

    text: str  # 用户输入文本
    ai_options: Optional[List[str]] = None  # AI提供的选项
    config: Optional[Dict[str, Any]] = None  # 配置信息
    language: str = "zh_CN"  # 语言代码
    metadata: Optional[Dict[str, Any]] = None  # 额外元数据

    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class OptionResult:
    """
    选项解析结果
    Option parsing result

    包含解析结果和相关信息
    Contains parsing result and related information
    """

    options: List[str]  # 解析出的选项
    strategy_name: str  # 使用的策略名称
    confidence: float = 1.0  # 置信度 (0.0-1.0)
    metadata: Optional[Dict[str, Any]] = None  # 结果元数据
    should_stop: bool = True  # 是否应该停止后续策略

    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


class OptionStrategy(ABC):
    """
    选项策略抽象基类
    Option Strategy Abstract Base Class

    定义选项解析策略的统一接口
    Defines unified interface for option parsing strategies
    """

    def __init__(self, name: str, priority: int = 10):
        """
        初始化策略
        Initialize strategy

        Args:
            name: 策略名称
            priority: 优先级（数字越小优先级越高）
        """
        self.name = name
        self.priority = priority
        self._enabled = True
        self._stats = {"call_count": 0, "success_count": 0, "error_count": 0}

    @abstractmethod
    def is_applicable(self, context: OptionContext) -> bool:
        """
        检查策略是否适用于当前上下文
        Check if strategy is applicable to current context

        Args:
            context: 选项解析上下文

        Returns:
            bool: 是否适用
        """
        pass

    @abstractmethod
    def parse_options(self, context: OptionContext) -> Optional[OptionResult]:
        """
        解析选项
        Parse options

        Args:
            context: 选项解析上下文

        Returns:
            Optional[OptionResult]: 解析结果，如果无法解析则返回None
        """
        pass

    def execute(self, context: OptionContext) -> Optional[OptionResult]:
        """
        执行策略（包含统计和错误处理）
        Execute strategy (with statistics and error handling)

        Args:
            context: 选项解析上下文

        Returns:
            Optional[OptionResult]: 解析结果
        """
        if not self._enabled:
            return None

        self._stats["call_count"] += 1

        try:
            # 检查适用性
            if not self.is_applicable(context):
                return None

            # 执行解析
            result = self.parse_options(context)

            if result and result.options:
                self._stats["success_count"] += 1
                return result

            return None

        except Exception as e:
            self._stats["error_count"] += 1
            print(f"策略 {self.name} 执行失败: {e}")
            return None

    def enable(self) -> None:
        """启用策略"""
        self._enabled = True

    def disable(self) -> None:
        """禁用策略"""
        self._enabled = False

    def is_enabled(self) -> bool:
        """检查策略是否启用"""
        return self._enabled

    def get_stats(self) -> Dict[str, Any]:
        """
        获取策略统计信息
        Get strategy statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        success_rate = 0.0
        if self._stats["call_count"] > 0:
            success_rate = (
                self._stats["success_count"] / self._stats["call_count"]
            ) * 100

        return {
            "name": self.name,
            "priority": self.priority,
            "enabled": self._enabled,
            "call_count": self._stats["call_count"],
            "success_count": self._stats["success_count"],
            "error_count": self._stats["error_count"],
            "success_rate_percent": round(success_rate, 2),
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {"call_count": 0, "success_count": 0, "error_count": 0}

    def __str__(self) -> str:
        return f"OptionStrategy(name={self.name}, priority={self.priority}, enabled={self._enabled})"

    def __repr__(self) -> str:
        return self.__str__()


class BaseOptionStrategy(OptionStrategy):
    """
    基础选项策略实现
    Base Option Strategy Implementation

    提供通用的策略实现基础
    Provides common strategy implementation foundation
    """

    def __init__(
        self,
        name: str,
        priority: int = 10,
        min_text_length: int = 2,
        max_options: int = 3,
    ):
        """
        初始化基础策略
        Initialize base strategy

        Args:
            name: 策略名称
            priority: 优先级
            min_text_length: 最小文本长度
            max_options: 最大选项数量
        """
        super().__init__(name, priority)
        self.min_text_length = min_text_length
        self.max_options = max_options

    def is_applicable(self, context: OptionContext) -> bool:
        """
        基础适用性检查
        Basic applicability check
        """
        # 检查文本有效性
        if not context.text or not isinstance(context.text, str):
            return False

        # 检查文本长度
        if len(context.text.strip()) < self.min_text_length:
            return False

        return True

    def validate_options(self, options: List[str]) -> List[str]:
        """
        验证和清理选项列表
        Validate and clean options list

        Args:
            options: 原始选项列表

        Returns:
            List[str]: 清理后的选项列表
        """
        if not options:
            return []

        # 去重并保持顺序
        seen = set()
        cleaned_options = []

        for option in options:
            if isinstance(option, str) and option.strip():
                clean_option = option.strip()
                if clean_option not in seen:
                    seen.add(clean_option)
                    cleaned_options.append(clean_option)

        # 限制数量
        return cleaned_options[: self.max_options]

    def create_result(
        self,
        options: List[str],
        confidence: float = 1.0,
        should_stop: bool = True,
        **metadata,
    ) -> OptionResult:
        """
        创建选项结果
        Create option result

        Args:
            options: 选项列表
            confidence: 置信度
            should_stop: 是否停止后续策略
            **metadata: 额外元数据

        Returns:
            OptionResult: 选项结果
        """
        validated_options = self.validate_options(options)

        return OptionResult(
            options=validated_options,
            strategy_name=self.name,
            confidence=confidence,
            should_stop=should_stop,
            metadata=metadata,
        )


class StrategyChain:
    """
    策略链管理器
    Strategy Chain Manager

    管理多个策略的执行顺序和结果合并
    Manages execution order and result merging of multiple strategies
    """

    def __init__(self):
        """初始化策略链"""
        self.strategies: List[OptionStrategy] = []
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "strategy_usage": {},
        }

    def add_strategy(self, strategy: OptionStrategy) -> None:
        """
        添加策略到链中
        Add strategy to chain

        Args:
            strategy: 要添加的策略
        """
        self.strategies.append(strategy)
        # 按优先级排序
        self.strategies.sort(key=lambda s: s.priority)

    def remove_strategy(self, name: str) -> bool:
        """
        从链中移除策略
        Remove strategy from chain

        Args:
            name: 策略名称

        Returns:
            bool: 是否成功移除
        """
        for i, strategy in enumerate(self.strategies):
            if strategy.name == name:
                del self.strategies[i]
                return True
        return False

    def get_strategy(self, name: str) -> Optional[OptionStrategy]:
        """
        获取指定名称的策略
        Get strategy by name

        Args:
            name: 策略名称

        Returns:
            Optional[OptionStrategy]: 策略实例
        """
        for strategy in self.strategies:
            if strategy.name == name:
                return strategy
        return None

    def execute(self, context: OptionContext) -> Optional[OptionResult]:
        """
        执行策略链
        Execute strategy chain

        Args:
            context: 选项解析上下文

        Returns:
            Optional[OptionResult]: 第一个成功的策略结果
        """
        self._execution_stats["total_executions"] += 1

        for strategy in self.strategies:
            if not strategy.is_enabled():
                continue

            result = strategy.execute(context)

            if result and result.options:
                # 更新使用统计
                strategy_name = strategy.name
                if strategy_name not in self._execution_stats["strategy_usage"]:
                    self._execution_stats["strategy_usage"][strategy_name] = 0
                self._execution_stats["strategy_usage"][strategy_name] += 1

                self._execution_stats["successful_executions"] += 1

                # 如果策略要求停止，则返回结果
                if result.should_stop:
                    return result

        return None

    def get_chain_stats(self) -> Dict[str, Any]:
        """
        获取策略链统计信息
        Get strategy chain statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        success_rate = 0.0
        if self._execution_stats["total_executions"] > 0:
            success_rate = (
                self._execution_stats["successful_executions"]
                / self._execution_stats["total_executions"]
            ) * 100

        strategy_stats = [strategy.get_stats() for strategy in self.strategies]

        return {
            "total_strategies": len(self.strategies),
            "enabled_strategies": len([s for s in self.strategies if s.is_enabled()]),
            "total_executions": self._execution_stats["total_executions"],
            "successful_executions": self._execution_stats["successful_executions"],
            "success_rate_percent": round(success_rate, 2),
            "strategy_usage": self._execution_stats["strategy_usage"],
            "strategies": strategy_stats,
        }

    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "strategy_usage": {},
        }

        for strategy in self.strategies:
            strategy.reset_stats()

    def __len__(self) -> int:
        return len(self.strategies)

    def __iter__(self):
        return iter(self.strategies)

    def __str__(self) -> str:
        enabled_count = len([s for s in self.strategies if s.is_enabled()])
        return (
            f"StrategyChain(strategies={len(self.strategies)}, enabled={enabled_count})"
        )

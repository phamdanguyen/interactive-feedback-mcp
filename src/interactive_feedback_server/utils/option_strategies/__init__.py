# interactive_feedback_server/utils/option_strategies/__init__.py

"""
选项策略实现模块 - V4.0 简化版本
Option Strategy Implementation Module - V4.0 Simplified Version

包含简化的选项解析策略实现（移除规则引擎）
Contains simplified option parsing strategy implementations (rule engine removed)
"""

from .ai_options_strategy import AIOptionsStrategy
from .fallback_options_strategy import FallbackOptionsStrategy

__all__ = ["AIOptionsStrategy", "FallbackOptionsStrategy"]

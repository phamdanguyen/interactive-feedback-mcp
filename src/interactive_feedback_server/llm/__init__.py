"""
LLM模块：提供多种大语言模型的统一接口

此模块实现了适配器模式，支持多种LLM提供商：
- OpenAI (GPT系列)
- Google Gemini
- DeepSeek
- 其他兼容OpenAI API的模型

主要组件：
- base.py: 定义LLMProvider抽象基类
- factory.py: 工厂函数，根据配置创建provider实例
- openai_provider.py: OpenAI适配器实现
- 其他provider实现...
"""

from .base import LLMProvider
from .factory import get_llm_provider, validate_provider_config

# Provider implementations
try:
    from .openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None

try:
    from .gemini_provider import GeminiProvider
except ImportError:
    GeminiProvider = None

try:
    from .volcengine_provider import VolcEngineProvider
except ImportError:
    VolcEngineProvider = None

__all__ = [
    "LLMProvider",
    "get_llm_provider",
    "validate_provider_config",
    "OpenAIProvider",
    "GeminiProvider",
    "VolcEngineProvider",
]

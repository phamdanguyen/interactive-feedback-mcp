"""
LLM Provider工厂函数

根据配置动态创建和管理LLM provider实例
"""

from typing import Optional, Tuple
from .base import LLMProvider
from .config_validator import get_config_validator
from .config_manager import get_config_manager


def validate_provider_config(provider_name: str, config: dict) -> Tuple[bool, str]:
    """
    验证特定provider的配置是否有效

    Args:
        provider_name: provider名称 (如 'openai', 'gemini')
        config: provider的配置字典

    Returns:
        tuple[bool, str]: (是否有效, 状态信息)
    """
    validator = get_config_validator()
    return validator.validate_provider_config(provider_name, config)


def get_llm_provider(config: dict = None) -> Tuple[Optional[LLMProvider], str]:
    """
    根据配置，实例化并返回对应的 LLM Provider

    Args:
        config: expression_optimizer配置字典（可选，如果不提供则从配置管理器获取）

    Returns:
        tuple[LLMProvider | None, str]: (provider实例, 状态信息)
    """
    # 如果没有提供配置，从配置管理器获取
    if config is None:
        config_manager = get_config_manager()
        config = config_manager.get_optimizer_config()

    # 使用验证器验证配置
    validator = get_config_validator()
    is_valid, message = validator.validate_optimizer_config(config)
    if not is_valid:
        return None, f"配置无效: {message}"

    active_provider_name = config.get("active_provider")
    provider_config = config["providers"][active_provider_name]

    # 创建provider实例
    if active_provider_name == "openai":
        try:
            from .openai_provider import OpenAIProvider

            return (
                OpenAIProvider(
                    api_key=provider_config.get("api_key"),
                    base_url=provider_config.get("base_url"),
                    model=provider_config.get("model", "gpt-3.5-turbo"),
                ),
                "配置有效",
            )
        except ImportError:
            return None, "OpenAI provider未安装"

    elif active_provider_name == "gemini":
        try:
            from .gemini_provider import GeminiProvider

            return (
                GeminiProvider(
                    api_key=provider_config.get("api_key"),
                    model=provider_config.get("model", "gemini-2.0-flash"),
                    base_url=provider_config.get("base_url"),
                ),
                "配置有效",
            )
        except ImportError:
            return (
                None,
                "Gemini provider未安装，请安装: pip install google-generativeai",
            )

    elif active_provider_name == "deepseek":
        try:
            from .openai_provider import OpenAIProvider  # DeepSeek兼容OpenAI API

            return (
                OpenAIProvider(
                    api_key=provider_config.get("api_key"),
                    base_url=provider_config.get(
                        "base_url", "https://api.deepseek.com/v1"
                    ),
                    model=provider_config.get("model", "deepseek-chat"),
                ),
                "配置有效",
            )
        except ImportError:
            return None, "DeepSeek provider未安装"

    elif active_provider_name == "volcengine":
        try:
            from .volcengine_provider import VolcEngineProvider

            return (
                VolcEngineProvider(
                    api_key=provider_config.get("api_key"),
                    model=provider_config.get("model", "doubao-pro-4k"),
                    base_url=provider_config.get(
                        "base_url", "https://ark.cn-beijing.volces.com/api/v3"
                    ),
                ),
                "配置有效",
            )
        except ImportError:
            return None, "火山引擎 provider未安装"

    return None, f"不支持的provider: {active_provider_name}"

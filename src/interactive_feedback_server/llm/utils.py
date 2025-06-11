"""
LLM模块工具函数

提供通用的工具函数，减少代码重复
"""

from typing import Optional, Tuple
from .constants import ERROR_MESSAGES, COMMON_CONFIG


def create_openai_client(api_key: str, base_url: Optional[str] = None):
    """
    创建OpenAI兼容的客户端

    Args:
        api_key: API密钥
        base_url: 可选的API基础URL

    Returns:
        OpenAI客户端实例

    Raises:
        ImportError: 如果openai库未安装
    """
    try:
        from openai import OpenAI

        return OpenAI(api_key=api_key, base_url=base_url)
    except ImportError:
        raise ImportError("请安装openai库: pip install openai")


def handle_api_error(error: Exception, provider_name: str, model: str = "") -> str:
    """
    统一的API错误处理

    Args:
        error: 异常对象
        provider_name: Provider名称
        model: 模型名称（可选）

    Returns:
        str: 格式化的错误消息
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # 认证错误
    if any(keyword in error_str for keyword in ["authentication", "401", "api_key"]):
        return ERROR_MESSAGES["auth"].format(provider=provider_name)

    # 频率限制
    elif any(keyword in error_str for keyword in ["rate", "429", "quota"]):
        return ERROR_MESSAGES["rate"].format(provider=provider_name)

    # 超时错误
    elif "timeout" in error_str or "TimeoutError" in error_type:
        return ERROR_MESSAGES["timeout"].format(provider=provider_name)

    # 请求参数错误
    elif any(keyword in error_str for keyword in ["invalid", "400"]):
        return ERROR_MESSAGES["request"].format(provider=provider_name)

    # 安全过滤器
    elif any(keyword in error_str for keyword in ["blocked", "safety"]):
        return ERROR_MESSAGES["safety"].format(provider=provider_name)

    # 模型不存在
    elif "not found" in error_str or ("model" in error_str and model):
        return ERROR_MESSAGES["model"].format(provider=provider_name, model=model)

    # 未知错误
    else:
        return ERROR_MESSAGES["unknown"].format(
            provider=provider_name, error=str(error)
        )


def create_chat_completion(client, model: str, messages: list, **kwargs) -> str:
    """
    统一的聊天完成请求

    Args:
        client: OpenAI兼容的客户端
        model: 模型名称
        messages: 消息列表
        **kwargs: 额外参数

    Returns:
        str: 生成的文本

    Raises:
        Exception: API调用失败时抛出异常
    """
    # 合并默认配置和用户配置
    config = {**COMMON_CONFIG, **kwargs}

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=config.get("temperature", 0.7),
        max_tokens=config.get("max_tokens", 1024),
        timeout=config.get("timeout", 30),
    )

    if response.choices and response.choices[0].message.content:
        return response.choices[0].message.content
    else:
        return ""


# 验证函数已迁移到config_validator.py
# 为了向后兼容，提供简单的包装函数


def validate_api_key(provider_name: str, api_key: str) -> Tuple[bool, str]:
    """
    验证API密钥格式（向后兼容包装函数）

    Args:
        provider_name: Provider名称
        api_key: API密钥

    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    from .config_validator import get_config_validator

    validator = get_config_validator()
    return validator.validate_api_key(provider_name, api_key)


def validate_model(provider_name: str, model: str) -> Tuple[bool, str]:
    """
    验证模型是否支持（向后兼容包装函数）

    Args:
        provider_name: Provider名称
        model: 模型名称

    Returns:
        tuple[bool, str]: (是否支持, 错误信息)
    """
    from .config_validator import get_config_validator

    validator = get_config_validator()
    return validator.validate_model(provider_name, model)


def get_default_config(provider_name: str) -> dict:
    """
    获取Provider的默认配置

    Args:
        provider_name: Provider名称

    Returns:
        dict: 默认配置
    """
    from .constants import DEFAULT_PROVIDER_CONFIGS

    return DEFAULT_PROVIDER_CONFIGS.get(provider_name, {}).copy()


def get_provider_display_name(provider_name: str, language: str = "zh_CN") -> str:
    """
    获取Provider的显示名称

    Args:
        provider_name: Provider名称
        language: 语言代码

    Returns:
        str: 显示名称
    """
    from .constants import PROVIDER_DISPLAY_NAMES

    return PROVIDER_DISPLAY_NAMES.get(provider_name, {}).get(language, provider_name)

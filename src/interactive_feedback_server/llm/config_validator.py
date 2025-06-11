"""
配置验证器

专门负责LLM配置的验证逻辑，分离关注点
"""

from typing import Dict, Tuple, List, Any
from .constants import API_KEY_VALIDATION, SUPPORTED_MODELS, API_ENDPOINTS


class ConfigValidator:
    """
    配置验证器

    负责验证各种LLM Provider的配置是否正确
    """

    def __init__(self):
        """初始化配置验证器"""
        self.validation_rules = API_KEY_VALIDATION
        self.supported_models = SUPPORTED_MODELS
        self.api_endpoints = API_ENDPOINTS

    def validate_api_key(self, provider_name: str, api_key: str) -> Tuple[bool, str]:
        """
        验证API密钥格式

        Args:
            provider_name: Provider名称
            api_key: API密钥

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not api_key:
            return False, f"{provider_name} API密钥未配置"

        # 检查占位符
        placeholder_patterns = ["YOUR_", "_API_KEY_HERE", "your-actual-api-key"]
        if any(pattern in api_key for pattern in placeholder_patterns):
            return False, f"{provider_name} API密钥未配置（仍为占位符）"

        # 获取验证规则
        validation_rules = self.validation_rules.get(provider_name, {})

        # 检查前缀
        if "prefix" in validation_rules:
            prefix = validation_rules["prefix"]
            if not api_key.startswith(prefix):
                return False, f"{provider_name} API密钥格式可能无效（应以{prefix}开头）"

        # 检查长度
        if "min_length" in validation_rules:
            min_length = validation_rules["min_length"]
            if len(api_key) < min_length:
                return False, f"{provider_name} API密钥长度不足（至少{min_length}字符）"

        # 检查UUID格式（火山引擎）
        if validation_rules.get("format") == "uuid":
            if "contains" in validation_rules:
                required_char = validation_rules["contains"]
                if required_char not in api_key:
                    return False, f"{provider_name} API密钥格式可能无效（应为UUID格式）"

        return True, "API密钥格式有效"

    def validate_model(self, provider_name: str, model: str) -> Tuple[bool, str]:
        """
        验证模型是否支持

        Args:
            provider_name: Provider名称
            model: 模型名称

        Returns:
            tuple[bool, str]: (是否支持, 错误信息)
        """
        if not model:
            return True, "未指定模型，将使用默认模型"

        # 对于用户配置的模型，我们采用宽松验证策略
        # 只要模型名称不为空，就认为是有效的，让API自己验证
        # 这样用户可以使用任何新发布的模型，而不需要等待代码更新
        supported_models = self.supported_models.get(provider_name, [])
        if model not in supported_models:
            # 不再返回错误，而是给出警告信息
            return True, f"模型 {model} 不在预定义列表中，但将尝试使用（如果API支持）"

        return True, "模型支持"

    def validate_base_url(self, base_url: str) -> Tuple[bool, str]:
        """
        验证Base URL格式

        Args:
            base_url: API基础URL

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        if not base_url:
            return True, "未指定Base URL，将使用默认值"

        if not base_url.startswith(("http://", "https://")):
            return False, "Base URL格式无效（应以http://或https://开头）"

        return True, "Base URL格式有效"

    def validate_provider_config(
        self, provider_name: str, config: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        验证完整的Provider配置

        Args:
            provider_name: Provider名称
            config: 配置字典

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 验证API密钥
        api_key = config.get("api_key", "")
        is_valid, message = self.validate_api_key(provider_name, api_key)
        if not is_valid:
            return False, message

        # 验证模型
        model = config.get("model", "")
        is_valid, message = self.validate_model(provider_name, model)
        if not is_valid:
            return False, message

        # 验证Base URL（如果存在）
        base_url = config.get("base_url")
        if base_url:
            is_valid, message = self.validate_base_url(base_url)
            if not is_valid:
                return False, message

        return True, "配置有效"

    def validate_optimizer_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证完整的优化器配置

        Args:
            config: 优化器配置

        Returns:
            tuple[bool, str]: (是否有效, 错误信息)
        """
        # 检查基本结构
        if not isinstance(config, dict):
            return False, "配置格式无效（应为字典）"

        # 检查是否启用
        enabled = config.get("enabled", False)
        if not enabled:
            return True, "优化功能未启用"

        # 检查活动Provider
        active_provider = config.get("active_provider")
        if not active_provider:
            return False, "未指定活动的LLM Provider"

        # 检查Provider配置
        providers = config.get("providers", {})
        if not providers:
            return False, "未配置任何LLM Provider"

        if active_provider not in providers:
            return False, f"活动Provider '{active_provider}' 未在配置中找到"

        # 验证活动Provider的配置
        provider_config = providers[active_provider]
        is_valid, message = self.validate_provider_config(
            active_provider, provider_config
        )
        if not is_valid:
            return False, f"{active_provider} 配置无效: {message}"

        return True, f"优化器配置有效，使用 {active_provider}"

    def get_supported_providers(self) -> List[str]:
        """
        获取支持的Provider列表

        Returns:
            list[str]: 支持的Provider名称列表
        """
        return list(self.supported_models.keys())

    def get_supported_models_for_provider(self, provider_name: str) -> List[str]:
        """
        获取指定Provider支持的模型列表

        Args:
            provider_name: Provider名称

        Returns:
            list[str]: 支持的模型列表
        """
        return self.supported_models.get(provider_name, [])

    def get_default_endpoint(self, provider_name: str) -> str:
        """
        获取Provider的默认端点

        Args:
            provider_name: Provider名称

        Returns:
            str: 默认API端点
        """
        return self.api_endpoints.get(provider_name, "")


# 全局配置验证器实例
_global_validator = None


def get_config_validator() -> ConfigValidator:
    """
    获取全局配置验证器实例

    Returns:
        ConfigValidator: 验证器实例
    """
    global _global_validator
    if _global_validator is None:
        _global_validator = ConfigValidator()
    return _global_validator

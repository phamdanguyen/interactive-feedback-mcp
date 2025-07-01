"""
配置管理器

统一管理LLM相关的配置读写、缓存和默认值
"""

import json
import os
from typing import Dict, Any
from .constants import DEFAULT_OPTIMIZER_CONFIG, DEFAULT_PROVIDER_CONFIGS
from .config_validator import get_config_validator


class ConfigManager:
    """
    LLM配置管理器 - 简化版本
    LLM Configuration Manager - Simplified Version

    委托给主配置管理器，专注于LLM相关的配置处理
    Delegates to main config manager, focuses on LLM-related configuration handling
    """

    def __init__(self, config_file: str = "config.json"):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径（保留兼容性，实际使用主配置管理器）
        """
        self.config_file = config_file  # 保留兼容性
        self.validator = get_config_validator()

        # 使用主配置管理器
        from ..utils.config_manager import get_config, save_config

        self._get_config = get_config
        self._save_config = save_config

    def _load_config_from_file(self) -> Dict[str, Any]:
        """
        从文件加载配置 - 委托给主配置管理器
        Load configuration from file - delegate to main config manager

        Returns:
            dict: 配置字典
        """
        # 直接使用主配置管理器
        return self._get_config()

    def _save_config_to_file(self, config: Dict[str, Any]) -> bool:
        """
        保存配置到文件 - 委托给主配置管理器
        Save configuration to file - delegate to main config manager

        Args:
            config: 配置字典

        Returns:
            bool: 是否保存成功
        """
        # 直接使用主配置管理器
        return self._save_config(config)

    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置（支持环境变量）

        Returns:
            dict: 完整配置
        """
        # 直接从主配置管理器获取配置（包含环境变量支持）
        config = self._load_config_from_file()

        # 确保有默认的优化器配置
        if "expression_optimizer" not in config:
            config["expression_optimizer"] = DEFAULT_OPTIMIZER_CONFIG.copy()

        return config

    def get_optimizer_config(self) -> Dict[str, Any]:
        """
        获取优化器配置

        Returns:
            dict: 优化器配置
        """
        config = self.get_config()
        return config.get("expression_optimizer", DEFAULT_OPTIMIZER_CONFIG.copy())

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        获取指定Provider的配置

        Args:
            provider_name: Provider名称

        Returns:
            dict: Provider配置
        """
        optimizer_config = self.get_optimizer_config()
        providers = optimizer_config.get("providers", {})

        # 如果没有配置，返回默认配置
        if provider_name not in providers:
            return DEFAULT_PROVIDER_CONFIGS.get(provider_name, {}).copy()

        return providers[provider_name].copy()

    def set_optimizer_config(self, optimizer_config: Dict[str, Any]) -> bool:
        """
        设置优化器配置

        Args:
            optimizer_config: 优化器配置

        Returns:
            bool: 是否设置成功
        """
        # 验证配置
        is_valid, message = self.validator.validate_optimizer_config(optimizer_config)
        if not is_valid:
            return False

        # 获取完整配置
        config = self.get_config()
        config["expression_optimizer"] = optimizer_config

        # 保存到文件
        return self._save_config_to_file(config)

    def set_provider_config(
        self, provider_name: str, provider_config: Dict[str, Any]
    ) -> bool:
        """
        设置指定Provider的配置

        Args:
            provider_name: Provider名称
            provider_config: Provider配置

        Returns:
            bool: 是否设置成功
        """
        # 验证配置
        is_valid, message = self.validator.validate_provider_config(
            provider_name, provider_config
        )
        if not is_valid:
            return False

        # 获取优化器配置
        optimizer_config = self.get_optimizer_config()

        # 确保providers字段存在
        if "providers" not in optimizer_config:
            optimizer_config["providers"] = {}

        # 更新Provider配置
        optimizer_config["providers"][provider_name] = provider_config

        # 保存优化器配置
        return self.set_optimizer_config(optimizer_config)

    def set_active_provider(self, provider_name: str) -> bool:
        """
        设置活动的Provider

        Args:
            provider_name: Provider名称

        Returns:
            bool: 是否设置成功
        """
        # 检查Provider是否支持
        if provider_name not in self.validator.get_supported_providers():
            return False

        # 获取优化器配置
        optimizer_config = self.get_optimizer_config()

        # 检查Provider是否已配置
        providers = optimizer_config.get("providers", {})
        if provider_name not in providers:
            # 使用默认配置
            default_config = DEFAULT_PROVIDER_CONFIGS.get(provider_name, {})
            if not default_config:
                return False
            providers[provider_name] = default_config.copy()
            optimizer_config["providers"] = providers

        # 设置活动Provider
        optimizer_config["active_provider"] = provider_name

        # 保存配置
        return self.set_optimizer_config(optimizer_config)

    def enable_optimizer(self, enabled: bool = True) -> bool:
        """
        启用或禁用优化器

        Args:
            enabled: 是否启用

        Returns:
            bool: 是否设置成功
        """
        optimizer_config = self.get_optimizer_config()
        optimizer_config["enabled"] = enabled
        return self.set_optimizer_config(optimizer_config)


# 全局配置管理器实例
_global_config_manager = None


def get_config_manager(config_file: str = "config.json") -> ConfigManager:
    """
    获取全局配置管理器实例

    Args:
        config_file: 配置文件路径

    Returns:
        ConfigManager: 配置管理器实例
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_file)
    return _global_config_manager

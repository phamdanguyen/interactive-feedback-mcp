# interactive_feedback_server/core/config_loader.py

"""
统一的配置加载器 - 优化版本
Unified Configuration Loader - Optimized Version

消除重复的配置加载逻辑，提供统一的配置管理。
Eliminates duplicate configuration loading logic, provides unified configuration management.
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ConfigMetadata:
    """配置元数据"""

    file_path: str
    last_modified: float
    load_count: int
    last_error: Optional[str] = None


class UnifiedConfigLoader:
    """
    统一配置加载器
    Unified Configuration Loader

    提供统一的配置文件加载、缓存和热重载功能
    Provides unified configuration file loading, caching and hot reload functionality
    """

    def __init__(self):
        """初始化配置加载器"""
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, ConfigMetadata] = {}
        self._validators: Dict[str, Callable] = {}
        self._defaults: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def register_config(
        self,
        name: str,
        file_path: Union[str, Path],
        default_config: Dict[str, Any] = None,
        validator: Callable = None,
    ) -> None:
        """
        注册配置文件
        Register configuration file

        Args:
            name: 配置名称
            file_path: 配置文件路径
            default_config: 默认配置
            validator: 验证函数
        """
        with self._lock:
            file_path = str(file_path)
            self._metadata[name] = ConfigMetadata(
                file_path=file_path, last_modified=0, load_count=0
            )

            if default_config:
                self._defaults[name] = default_config.copy()

            if validator:
                self._validators[name] = validator

    def load_config(self, name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置
        Load configuration

        Args:
            name: 配置名称
            force_reload: 是否强制重新加载

        Returns:
            Dict[str, Any]: 配置字典
        """
        with self._lock:
            if name not in self._metadata:
                raise ValueError(f"未注册的配置: {name}")

            metadata = self._metadata[name]

            # 检查是否需要重新加载
            if not force_reload and name in self._configs:
                if self._is_file_unchanged(metadata):
                    return self._configs[name].copy()

            # 加载配置文件
            config = self._load_config_file(name, metadata)

            # 验证配置
            if name in self._validators:
                try:
                    if not self._validators[name](config):
                        print(f"配置验证失败: {name}")
                        config = self._get_default_config(name)
                except Exception as e:
                    print(f"配置验证异常: {name} - {e}")
                    config = self._get_default_config(name)

            # 缓存配置
            self._configs[name] = config
            metadata.load_count += 1

            return config.copy()

    def _is_file_unchanged(self, metadata: ConfigMetadata) -> bool:
        """检查文件是否未修改"""
        try:
            if not os.path.exists(metadata.file_path):
                return False

            current_modified = os.path.getmtime(metadata.file_path)
            return current_modified <= metadata.last_modified
        except Exception:
            return False

    def _load_config_file(self, name: str, metadata: ConfigMetadata) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(metadata.file_path):
                print(f"配置文件不存在: {metadata.file_path}")
                config = self._get_default_config(name)
                self._save_config_file(metadata.file_path, config)
                return config

            # 读取配置文件
            with open(metadata.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    print(f"配置文件为空: {metadata.file_path}")
                    return self._get_default_config(name)

                config = json.loads(content)

            # 更新修改时间
            metadata.last_modified = os.path.getmtime(metadata.file_path)
            metadata.last_error = None

            # 合并默认配置
            if name in self._defaults:
                merged_config = self._defaults[name].copy()
                merged_config.update(config)
                config = merged_config

            return config

        except Exception as e:
            error_msg = f"加载配置文件失败: {metadata.file_path} - {e}"
            print(error_msg)
            metadata.last_error = error_msg
            return self._get_default_config(name)

    def _get_default_config(self, name: str) -> Dict[str, Any]:
        """获取默认配置"""
        return self._defaults.get(name, {}).copy()

    def _save_config_file(self, file_path: str, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # 保存配置
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"保存配置文件失败: {file_path} - {e}")
            return False

    def save_config(self, name: str, config: Dict[str, Any]) -> bool:
        """
        保存配置
        Save configuration

        Args:
            name: 配置名称
            config: 配置字典

        Returns:
            bool: 是否保存成功
        """
        with self._lock:
            if name not in self._metadata:
                raise ValueError(f"未注册的配置: {name}")

            metadata = self._metadata[name]

            # 验证配置
            if name in self._validators:
                try:
                    if not self._validators[name](config):
                        print(f"配置验证失败，无法保存: {name}")
                        return False
                except Exception as e:
                    print(f"配置验证异常，无法保存: {name} - {e}")
                    return False

            # 保存配置文件
            if self._save_config_file(metadata.file_path, config):
                # 更新缓存
                self._configs[name] = config.copy()
                metadata.last_modified = os.path.getmtime(metadata.file_path)
                return True

            return False

    def get_config_value(self, name: str, key: str, default: Any = None) -> Any:
        """
        获取配置值
        Get configuration value

        Args:
            name: 配置名称
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值

        Returns:
            Any: 配置值
        """
        config = self.load_config(name)

        # 支持嵌套键
        keys = key.split(".")
        value = config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_config_value(self, name: str, key: str, value: Any) -> bool:
        """
        设置配置值
        Set configuration value

        Args:
            name: 配置名称
            key: 配置键（支持点号分隔的嵌套键）
            value: 配置值

        Returns:
            bool: 是否设置成功
        """
        config = self.load_config(name)

        # 支持嵌套键
        keys = key.split(".")
        current = config

        try:
            # 导航到父级
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            # 设置值
            current[keys[-1]] = value

            # 保存配置
            return self.save_config(name, config)
        except Exception as e:
            print(f"设置配置值失败: {name}.{key} - {e}")
            return False

    def reload_config(self, name: str) -> Dict[str, Any]:
        """
        重新加载配置
        Reload configuration

        Args:
            name: 配置名称

        Returns:
            Dict[str, Any]: 配置字典
        """
        return self.load_config(name, force_reload=True)

    def get_config_metadata(
        self, name: str = None
    ) -> Union[ConfigMetadata, Dict[str, ConfigMetadata]]:
        """
        获取配置元数据
        Get configuration metadata

        Args:
            name: 配置名称，None表示所有配置

        Returns:
            Union[ConfigMetadata, Dict[str, ConfigMetadata]]: 元数据
        """
        with self._lock:
            if name:
                return self._metadata.get(name)
            else:
                return self._metadata.copy()

    def clear_cache(self, name: str = None) -> None:
        """
        清除配置缓存
        Clear configuration cache

        Args:
            name: 配置名称，None表示清除所有缓存
        """
        with self._lock:
            if name:
                if name in self._configs:
                    del self._configs[name]
            else:
                self._configs.clear()

    def get_registered_configs(self) -> list:
        """获取已注册的配置名称列表"""
        with self._lock:
            return list(self._metadata.keys())


# 全局配置加载器实例
_global_config_loader: Optional[UnifiedConfigLoader] = None


def get_config_loader() -> UnifiedConfigLoader:
    """
    获取全局配置加载器实例
    Get global configuration loader instance

    Returns:
        UnifiedConfigLoader: 配置加载器实例
    """
    global _global_config_loader
    if _global_config_loader is None:
        _global_config_loader = UnifiedConfigLoader()
    return _global_config_loader


# 便捷函数
def register_config(
    name: str,
    file_path: Union[str, Path],
    default_config: Dict[str, Any] = None,
    validator: Callable = None,
) -> None:
    """注册配置文件"""
    get_config_loader().register_config(name, file_path, default_config, validator)


def load_config(name: str) -> Dict[str, Any]:
    """加载配置"""
    return get_config_loader().load_config(name)


def save_config(name: str, config: Dict[str, Any]) -> bool:
    """保存配置"""
    return get_config_loader().save_config(name, config)


def get_config_value(name: str, key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config_loader().get_config_value(name, key, default)

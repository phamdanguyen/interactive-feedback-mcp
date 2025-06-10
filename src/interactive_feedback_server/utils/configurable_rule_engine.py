# interactive_feedback_server/utils/configurable_rule_engine.py

"""
可配置规则引擎 - V3.3 架构改进版本
Configurable Rule Engine - V3.3 Architecture Improvement Version

提供外部化的规则配置，支持多语言、热重载和自定义规则扩展。
Provides externalized rule configuration with multi-language support, 
hot reload and custom rule extension capabilities.
"""

import json
import os
import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class ConfigurableRuleEngine:
    """
    可配置规则引擎
    Configurable Rule Engine

    支持外部配置文件、多语言、热重载和自定义规则
    Supports external configuration files, multi-language, hot reload and custom rules
    """

    def __init__(self, config_path: str = "config/rules.json"):
        """
        初始化可配置规则引擎
        Initialize configurable rule engine

        Args:
            config_path: 规则配置文件路径
        """
        self.config_path = Path(config_path)
        self.rules: Dict[str, Any] = {}
        self.last_modified = 0
        self._lock = threading.RLock()

        # 统计信息
        self._load_count = 0
        self._match_count = 0
        self._cache_hit_count = 0
        self._error_count = 0

        # 缓存
        self._pattern_cache: Dict[str, List[str]] = {}
        self._cache_enabled = True

        # 加载规则
        self.load_rules()

    def load_rules(self) -> bool:
        """
        加载规则配置文件
        Load rule configuration file

        Returns:
            bool: 是否加载成功
        """
        with self._lock:
            try:
                if not self.config_path.exists():
                    print(f"规则配置文件不存在: {self.config_path}")
                    self.rules = self._get_default_rules()
                    return False

                # 检查文件修改时间
                current_modified = self.config_path.stat().st_mtime
                if current_modified <= self.last_modified and self.rules:
                    return True  # 文件未修改，无需重新加载

                # 加载配置文件
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)

                self.last_modified = current_modified
                self._load_count += 1

                # 验证配置
                if not self._validate_rules():
                    print("规则配置验证失败，使用默认规则")
                    self.rules = self._get_default_rules()
                    return False

                # 清空缓存
                self._pattern_cache.clear()

                # 更新缓存设置
                global_settings = self.rules.get("global_settings", {})
                self._cache_enabled = global_settings.get("cache_enabled", True)

                return True

            except Exception as e:
                print(f"加载规则配置失败: {e}")
                self._error_count += 1
                self.rules = self._get_default_rules()
                return False

    def _validate_rules(self) -> bool:
        """
        验证规则配置的有效性
        Validate rule configuration validity

        Returns:
            bool: 配置是否有效
        """
        try:
            # 检查必需字段
            if "languages" not in self.rules:
                return False

            languages = self.rules["languages"]
            if not isinstance(languages, dict) or not languages:
                return False

            # 验证每种语言的配置
            for lang_code, lang_config in languages.items():
                if "patterns" not in lang_config:
                    return False

                patterns = lang_config["patterns"]
                if not isinstance(patterns, dict):
                    return False

                # 验证每个模式
                for pattern_name, pattern_config in patterns.items():
                    required_fields = ["triggers", "options", "priority"]
                    for field in required_fields:
                        if field not in pattern_config:
                            return False

                    # 验证字段类型
                    if not isinstance(pattern_config["triggers"], list):
                        return False
                    if not isinstance(pattern_config["options"], list):
                        return False
                    if not isinstance(pattern_config["priority"], int):
                        return False

            return True

        except Exception:
            return False

    def _get_default_rules(self) -> Dict[str, Any]:
        """
        获取默认规则配置
        Get default rule configuration

        Returns:
            Dict[str, Any]: 默认规则配置
        """
        return {
            "version": "1.0",
            "languages": {
                "zh_CN": {
                    "patterns": {
                        "question": {
                            "triggers": [
                                "?",
                                "？",
                                "是否",
                                "如何",
                                "怎么",
                                "什么",
                                "为什么",
                            ],
                            "options": ["是的", "不是", "需要更多信息"],
                            "priority": 1,
                            "enabled": True,
                        },
                        "confirmation": {
                            "triggers": [
                                "确认",
                                "同意",
                                "继续",
                                "下一步",
                                "开始",
                                "执行",
                                "好的",
                            ],
                            "options": ["好的，继续", "我明白了", "暂停一下"],
                            "priority": 2,
                            "enabled": True,
                        },
                    }
                }
            },
            "global_settings": {
                "max_options": 3,
                "case_sensitive": False,
                "cache_enabled": True,
                "hot_reload": True,
            },
        }

    def extract_options(self, text: str, language: str = "zh_CN") -> List[str]:
        """
        从文本中提取选项 (V3.3 可配置版本)
        Extract options from text (V3.3 Configurable Version)

        Args:
            text: 要分析的文本
            language: 语言代码

        Returns:
            List[str]: 提取的选项列表
        """
        with self._lock:
            self._match_count += 1

            # 检查是否需要重新加载配置
            if self.rules.get("global_settings", {}).get("hot_reload", True):
                self.load_rules()

            if not text or not text.strip():
                return []

            # 检查缓存
            cache_key = f"{language}:{text.lower()}"
            if self._cache_enabled and cache_key in self._pattern_cache:
                self._cache_hit_count += 1
                return self._pattern_cache[cache_key]

            # 获取语言配置
            languages = self.rules.get("languages", {})
            if language not in languages:
                language = "zh_CN"  # 回退到中文

            if language not in languages:
                return []

            patterns = languages[language]["patterns"]
            text_lower = text.lower()

            # 按优先级排序模式
            sorted_patterns = sorted(
                patterns.items(), key=lambda x: x[1].get("priority", 999)
            )

            # 匹配模式
            for pattern_name, pattern_config in sorted_patterns:
                # 检查模式是否启用
                if not pattern_config.get("enabled", True):
                    continue

                # 检查触发器
                for trigger in pattern_config["triggers"]:
                    if trigger.lower() in text_lower:
                        options = pattern_config["options"]
                        max_options = self.rules.get("global_settings", {}).get(
                            "max_options", 3
                        )
                        result = options[:max_options]

                        # 缓存结果
                        if self._cache_enabled:
                            self._pattern_cache[cache_key] = result

                        return result

            # 没有匹配的模式
            if self._cache_enabled:
                self._pattern_cache[cache_key] = []

            return []

    def add_custom_pattern(
        self, language: str, name: str, pattern: Dict[str, Any]
    ) -> bool:
        """
        添加自定义规则模式
        Add custom rule pattern

        Args:
            language: 语言代码
            name: 模式名称
            pattern: 模式配置

        Returns:
            bool: 是否添加成功
        """
        with self._lock:
            try:
                # 验证模式配置
                required_fields = ["triggers", "options", "priority"]
                for field in required_fields:
                    if field not in pattern:
                        return False

                # 确保语言存在
                if "languages" not in self.rules:
                    self.rules["languages"] = {}

                if language not in self.rules["languages"]:
                    self.rules["languages"][language] = {"patterns": {}}

                if "patterns" not in self.rules["languages"][language]:
                    self.rules["languages"][language]["patterns"] = {}

                # 添加模式
                self.rules["languages"][language]["patterns"][name] = pattern

                # 清空缓存
                self._pattern_cache.clear()

                # 保存到文件
                return self.save_rules()

            except Exception as e:
                print(f"添加自定义模式失败: {e}")
                self._error_count += 1
                return False

    def remove_pattern(self, language: str, name: str) -> bool:
        """
        移除规则模式
        Remove rule pattern

        Args:
            language: 语言代码
            name: 模式名称

        Returns:
            bool: 是否移除成功
        """
        with self._lock:
            try:
                if language in self.rules.get("languages", {}) and name in self.rules[
                    "languages"
                ][language].get("patterns", {}):

                    del self.rules["languages"][language]["patterns"][name]
                    self._pattern_cache.clear()
                    return self.save_rules()

                return False

            except Exception as e:
                print(f"移除模式失败: {e}")
                self._error_count += 1
                return False

    def save_rules(self) -> bool:
        """
        保存规则配置到文件
        Save rule configuration to file

        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, ensure_ascii=False, indent=2)

            # 更新修改时间
            self.last_modified = self.config_path.stat().st_mtime

            return True

        except Exception as e:
            print(f"保存规则配置失败: {e}")
            self._error_count += 1
            return False

    def get_available_languages(self) -> List[str]:
        """
        获取可用的语言列表
        Get available language list

        Returns:
            List[str]: 语言代码列表
        """
        return list(self.rules.get("languages", {}).keys())

    def get_patterns_for_language(self, language: str) -> Dict[str, Any]:
        """
        获取指定语言的所有模式
        Get all patterns for specified language

        Args:
            language: 语言代码

        Returns:
            Dict[str, Any]: 模式配置字典
        """
        languages = self.rules.get("languages", {})
        if language in languages:
            return languages[language].get("patterns", {})
        return {}

    def get_stats(self) -> Dict[str, Any]:
        """
        获取引擎统计信息
        Get engine statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            cache_hit_rate = 0
            if self._match_count > 0:
                cache_hit_rate = (self._cache_hit_count / self._match_count) * 100

            return {
                "load_count": self._load_count,
                "match_count": self._match_count,
                "cache_hit_count": self._cache_hit_count,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "error_count": self._error_count,
                "cache_size": len(self._pattern_cache),
                "cache_enabled": self._cache_enabled,
                "available_languages": self.get_available_languages(),
                "config_path": str(self.config_path),
                "last_modified": self.last_modified,
            }

    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._pattern_cache.clear()

    def reload_rules(self) -> bool:
        """
        强制重新加载规则
        Force reload rules

        Returns:
            bool: 是否重新加载成功
        """
        with self._lock:
            self.last_modified = 0  # 强制重新加载
            return self.load_rules()


# 全局可配置规则引擎实例
_global_configurable_engine: Optional[ConfigurableRuleEngine] = None


def get_configurable_rule_engine() -> ConfigurableRuleEngine:
    """获取全局可配置规则引擎实例"""
    global _global_configurable_engine
    if _global_configurable_engine is None:
        _global_configurable_engine = ConfigurableRuleEngine()
    return _global_configurable_engine


def extract_options_configurable(text: str, language: str = "zh_CN") -> List[str]:
    """
    使用可配置规则引擎提取选项
    Extract options using configurable rule engine

    Args:
        text: 要分析的文本
        language: 语言代码

    Returns:
        List[str]: 提取的选项列表
    """
    engine = get_configurable_rule_engine()
    return engine.extract_options(text, language)


def get_configurable_engine_stats() -> Dict[str, Any]:
    """获取可配置规则引擎统计信息"""
    engine = get_configurable_rule_engine()
    return engine.get_stats()

"""
简化的性能管理器

提供基本的缓存和统计功能，移除过度复杂的异步和重试逻辑
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
from .base import LLMProvider


class OptimizationManager:
    """
    简化的优化管理器

    提供以下功能：
    - 简单缓存：缓存相同输入的优化结果
    - 基本统计：记录请求和缓存统计
    """

    def __init__(self, cache_ttl_minutes: int = 10):
        """
        初始化优化管理器

        Args:
            cache_ttl_minutes: 缓存生存时间（分钟）
        """
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)

        # 缓存存储：{cache_key: (result, timestamp)}
        self.cache: Dict[str, Tuple[str, datetime]] = {}

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "successful_requests": 0,
            "failed_requests": 0,
        }

    def _get_cache_key(self, text: str, mode: str, reinforcement: str = "") -> str:
        """
        生成缓存键

        Args:
            text: 原始文本
            mode: 优化模式
            reinforcement: 强化指令

        Returns:
            str: 缓存键
        """
        content = f"{text}|{mode}|{reinforcement}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """
        检查缓存是否有效

        Args:
            timestamp: 缓存时间戳

        Returns:
            bool: 是否有效
        """
        return datetime.now() - timestamp < self.cache_ttl

    def _cleanup_expired_cache(self):
        """清理过期的缓存项"""
        current_time = datetime.now()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.cache_ttl
        ]

        for key in expired_keys:
            del self.cache[key]

    def _is_basic_valid_result(self, result: str) -> bool:
        """
        基本结果有效性检查 - V4.1 精简版本
        Basic result validity check - V4.1 Simplified Version

        Args:
            result: 优化结果

        Returns:
            bool: 是否有效
        """
        if not result or not isinstance(result, str):
            return False

        # 只检查明显的错误信息，移除复杂的污染检测
        if result.startswith("[ERROR") or result.startswith("[系统错误]"):
            return False

        # 基本长度检查
        if len(result.strip()) < 2:
            return False

        return True

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 统计信息
        """
        self._cleanup_expired_cache()

        return {
            "cache_size": len(self.cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / max(1, self.stats["total_requests"])
            )
            * 100,
            **self.stats,
        }

    def optimize_with_cache(
        self,
        provider: LLMProvider,
        text: str,
        mode: str,
        system_prompt: str,
        reinforcement: str = "",
    ) -> str:
        """
        带缓存的优化处理（简化的同步版本）

        Args:
            provider: LLM提供商实例
            text: 原始文本
            mode: 优化模式
            system_prompt: 系统提示词
            reinforcement: 强化指令

        Returns:
            str: 优化结果
        """
        self.stats["total_requests"] += 1

        # 检查缓存
        cache_key = self._get_cache_key(text, mode, reinforcement)
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                self.stats["cache_hits"] += 1
                return f"[CACHED] {result}"

        self.stats["cache_misses"] += 1

        # 直接调用provider（同步）
        try:
            # 使用统一的提示词格式化函数
            from ..cli import format_prompt_for_mode

            prompt = format_prompt_for_mode(text, mode, reinforcement)

            # 简化的重试机制：只重试一次
            max_retries = 1
            for attempt in range(max_retries + 1):
                result = provider.generate(prompt, system_prompt)

                # 检查API错误
                if result.startswith("[ERROR"):
                    self.stats["failed_requests"] += 1
                    return result

                # 基本有效性检查
                if self._is_basic_valid_result(result):
                    # 结果有效，缓存并返回
                    self.cache[cache_key] = (result, datetime.now())
                    self.stats["successful_requests"] += 1
                    return result

                # 如果还有重试机会且结果明显异常，进行重试
                if attempt < max_retries and len(result.strip()) < 5:
                    continue

                # 即使结果可能有小问题，也直接返回，避免过度检查
                self.cache[cache_key] = (result, datetime.now())
                self.stats["successful_requests"] += 1
                return result

        except Exception as e:
            self.stats["failed_requests"] += 1
            return f"[ERROR:UNKNOWN] 优化异常: {str(e)}"

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

    def reset_stats(self):
        """重置统计信息"""
        for key in self.stats:
            self.stats[key] = 0

    # V4.1 移除：复杂的健康检查和缓存污染检测功能已删除
    # 这些功能对于简单的文本优化来说过度复杂，影响性能


# 全局性能管理器实例
_global_manager: Optional[OptimizationManager] = None


def get_optimization_manager(config: Dict[str, Any]) -> OptimizationManager:
    """
    获取全局优化管理器实例

    Args:
        config: 性能配置

    Returns:
        OptimizationManager: 管理器实例
    """
    global _global_manager

    if _global_manager is None:
        performance_config = config.get("performance", {})

        _global_manager = OptimizationManager(
            cache_ttl_minutes=performance_config.get("cache_ttl_minutes", 10)
        )

    return _global_manager


def reset_global_manager():
    """
    重置全局管理器实例
    Reset global manager instance
    """
    global _global_manager
    _global_manager = None


def force_clear_all_caches():
    """
    强制清空所有缓存（包括重置全局实例）
    Force clear all caches (including resetting global instance)
    """
    global _global_manager
    if _global_manager is not None:
        _global_manager.clear_cache()
        _global_manager.reset_stats()

    # 重置全局实例
    _global_manager = None

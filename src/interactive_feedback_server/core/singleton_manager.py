# interactive_feedback_server/core/singleton_manager.py

"""
统一的单例管理器 - 优化版本
Unified Singleton Manager - Optimized Version

消除重复的全局实例模式，提供统一的单例管理。
Eliminates duplicate global instance patterns, provides unified singleton management.
"""

import threading
from typing import Dict, Any, Type, TypeVar, Callable, Optional
from functools import wraps

T = TypeVar("T")


class SingletonManager:
    """
    单例管理器
    Singleton Manager

    统一管理所有单例实例，避免重复的全局变量模式
    Unified management of all singleton instances, avoiding duplicate global variable patterns
    """

    def __init__(self):
        """初始化单例管理器"""
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._lock = threading.RLock()

    def register_factory(self, name: str, factory: Callable[[], T]) -> None:
        """
        注册单例工厂函数
        Register singleton factory function

        Args:
            name: 单例名称
            factory: 工厂函数
        """
        with self._lock:
            self._factories[name] = factory

    def get_instance(self, name: str) -> Any:
        """
        获取单例实例
        Get singleton instance

        Args:
            name: 单例名称

        Returns:
            Any: 单例实例
        """
        with self._lock:
            if name not in self._instances:
                if name not in self._factories:
                    raise ValueError(f"未注册的单例: {name}")

                self._instances[name] = self._factories[name]()

            return self._instances[name]

    def clear_instance(self, name: str) -> bool:
        """
        清除单例实例
        Clear singleton instance

        Args:
            name: 单例名称

        Returns:
            bool: 是否成功清除
        """
        with self._lock:
            if name in self._instances:
                del self._instances[name]
                return True
            return False

    def clear_all(self) -> None:
        """清除所有单例实例"""
        with self._lock:
            self._instances.clear()

    def get_registered_names(self) -> list:
        """获取已注册的单例名称列表"""
        with self._lock:
            return list(self._factories.keys())

    def get_active_instances(self) -> list:
        """获取已创建的实例名称列表"""
        with self._lock:
            return list(self._instances.keys())


# 全局单例管理器
_singleton_manager = SingletonManager()


def register_singleton(name: str):
    """
    单例注册装饰器
    Singleton registration decorator

    Args:
        name: 单例名称
    """

    def decorator(factory_func: Callable[[], T]) -> Callable[[], T]:
        _singleton_manager.register_factory(name, factory_func)

        @wraps(factory_func)
        def wrapper() -> T:
            return _singleton_manager.get_instance(name)

        return wrapper

    return decorator


def get_singleton(name: str) -> Any:
    """
    获取单例实例
    Get singleton instance

    Args:
        name: 单例名称

    Returns:
        Any: 单例实例
    """
    return _singleton_manager.get_instance(name)


def clear_singleton(name: str) -> bool:
    """
    清除单例实例
    Clear singleton instance

    Args:
        name: 单例名称

    Returns:
        bool: 是否成功清除
    """
    return _singleton_manager.clear_instance(name)


def get_singleton_manager() -> SingletonManager:
    """获取单例管理器实例"""
    return _singleton_manager


# 便捷的单例基类
class SingletonMeta(type):
    """单例元类"""

    _instances = {}
    _lock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class SingletonBase(metaclass=SingletonMeta):
    """单例基类"""

    pass

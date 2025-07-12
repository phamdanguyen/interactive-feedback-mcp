# feedback_ui/utils/resource_manager.py

"""
资源管理器
Resource Manager

提供统一的资源管理和上下文管理器，确保资源正确释放，
防止内存泄漏和资源泄漏。

Provides unified resource management and context managers to ensure
proper resource cleanup, preventing memory and resource leaks.
"""

import os
import tempfile
import threading
import time
import weakref
from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional, Callable, Union

try:
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QPixmap

    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from .object_pool import get_byte_array_pool, get_buffer_pool, PooledResource


class ResourceTracker:
    """
    资源跟踪器
    Resource Tracker

    跟踪和管理应用程序中的资源使用情况
    Tracks and manages resource usage in the application
    """

    def __init__(self):
        self._resources: Dict[str, Any] = {}
        self._temp_files: List[str] = []
        self._cleanup_callbacks: List[Callable] = []
        self._lock = threading.RLock()
        self._creation_time = time.time()

        # 统计信息
        self._resource_count = 0
        self._cleanup_count = 0
        self._error_count = 0

    def register_resource(
        self, name: str, resource: Any, cleanup_func: Optional[Callable] = None
    ) -> None:
        """
        注册资源
        Register resource

        Args:
            name: 资源名称
            resource: 资源对象
            cleanup_func: 清理函数
        """
        with self._lock:
            self._resources[name] = {
                "resource": resource,
                "cleanup_func": cleanup_func,
                "created_at": time.time(),
            }
            self._resource_count += 1

    def unregister_resource(self, name: str) -> bool:
        """
        注销资源
        Unregister resource

        Args:
            name: 资源名称

        Returns:
            bool: 是否成功注销
        """
        with self._lock:
            if name in self._resources:
                resource_info = self._resources[name]

                # 执行清理函数
                if resource_info["cleanup_func"]:
                    try:
                        resource_info["cleanup_func"](resource_info["resource"])
                        self._cleanup_count += 1
                    except Exception as e:
                        self._error_count += 1
                        print(f"资源清理失败 {name}: {e}")

                del self._resources[name]
                return True
            return False

    def register_temp_file(self, file_path: str) -> None:
        """注册临时文件"""
        with self._lock:
            if file_path not in self._temp_files:
                self._temp_files.append(file_path)

    def add_cleanup_callback(self, callback: Callable) -> None:
        """添加清理回调"""
        with self._lock:
            self._cleanup_callbacks.append(callback)

    def cleanup_all(self) -> None:
        """清理所有资源"""
        with self._lock:
            # 清理注册的资源
            for name in list(self._resources.keys()):
                self.unregister_resource(name)

            # 清理临时文件
            for file_path in self._temp_files[:]:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        self._temp_files.remove(file_path)
                        self._cleanup_count += 1
                except Exception as e:
                    self._error_count += 1
                    print(f"临时文件清理失败 {file_path}: {e}")

            # 执行清理回调
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                    self._cleanup_count += 1
                except Exception as e:
                    self._error_count += 1
                    print(f"清理回调失败: {e}")

            self._cleanup_callbacks.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "active_resources": len(self._resources),
                "temp_files": len(self._temp_files),
                "cleanup_callbacks": len(self._cleanup_callbacks),
                "total_created": self._resource_count,
                "total_cleaned": self._cleanup_count,
                "error_count": self._error_count,
                "uptime_seconds": time.time() - self._creation_time,
            }


# 全局资源跟踪器
_global_resource_tracker = ResourceTracker()


@contextmanager
def managed_resource(
    resource: Any, cleanup_func: Optional[Callable] = None, name: Optional[str] = None
) -> Generator[Any, None, None]:
    """
    托管资源上下文管理器
    Managed resource context manager

    Args:
        resource: 资源对象
        cleanup_func: 清理函数
        name: 资源名称

    Yields:
        Any: 资源对象
    """
    resource_name = name or f"resource_{id(resource)}"

    try:
        _global_resource_tracker.register_resource(
            resource_name, resource, cleanup_func
        )
        yield resource
    finally:
        _global_resource_tracker.unregister_resource(resource_name)


@contextmanager
def managed_temp_file(
    suffix: str = "", prefix: str = "tmp_", dir: Optional[str] = None
) -> Generator[str, None, None]:
    """
    托管临时文件上下文管理器
    Managed temporary file context manager

    Args:
        suffix: 文件后缀
        prefix: 文件前缀
        dir: 目录路径

    Yields:
        str: 临时文件路径
    """
    fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
    os.close(fd)  # 关闭文件描述符

    try:
        _global_resource_tracker.register_temp_file(temp_path)
        yield temp_path
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception as e:
            print(f"临时文件清理失败 {temp_path}: {e}")


if PYSIDE6_AVAILABLE:

    @contextmanager
    def managed_qbuffer() -> Generator[QBuffer, None, None]:
        """
        托管QBuffer上下文管理器
        Managed QBuffer context manager
        """
        buffer_pool = get_buffer_pool()

        if buffer_pool:
            # 使用对象池
            with PooledResource(buffer_pool) as buffer:
                yield buffer
        else:
            # 回退到直接创建
            buffer = QBuffer()
            try:
                yield buffer
            finally:
                if buffer.isOpen():
                    buffer.close()

    @contextmanager
    def managed_qbytearray() -> Generator[QByteArray, None, None]:
        """
        托管QByteArray上下文管理器
        Managed QByteArray context manager
        """
        byte_array_pool = get_byte_array_pool()

        if byte_array_pool:
            # 使用对象池
            with PooledResource(byte_array_pool) as byte_array:
                yield byte_array
        else:
            # 回退到直接创建
            byte_array = QByteArray()
            try:
                yield byte_array
            finally:
                byte_array.clear()

    @contextmanager
    def managed_image_processing() -> Generator[Dict[str, Any], None, None]:
        """
        托管图像处理资源上下文管理器
        Managed image processing resources context manager

        Yields:
            Dict[str, Any]: 包含图像处理所需资源的字典
        """
        resources = {}
        temp_files = []

        try:
            # 获取池化资源
            byte_array_pool = get_byte_array_pool()
            buffer_pool = get_buffer_pool()

            if byte_array_pool and buffer_pool:
                # 使用对象池
                byte_array = byte_array_pool.acquire()
                buffer = buffer_pool.acquire()

                resources.update(
                    {
                        "byte_array": byte_array,
                        "buffer": buffer,
                        "temp_files": temp_files,
                        "using_pools": True,
                    }
                )

                try:
                    yield resources
                finally:
                    # 归还到池中
                    buffer_pool.release(buffer)
                    byte_array_pool.release(byte_array)
            else:
                # 回退到直接创建
                byte_array = QByteArray()
                buffer = QBuffer()

                resources.update(
                    {
                        "byte_array": byte_array,
                        "buffer": buffer,
                        "temp_files": temp_files,
                        "using_pools": False,
                    }
                )

                try:
                    yield resources
                finally:
                    if buffer.isOpen():
                        buffer.close()
                    byte_array.clear()

        finally:
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"临时文件清理失败 {temp_file}: {e}")


class ResourceManager:
    """
    资源管理器类
    Resource Manager Class

    提供高级的资源管理功能
    Provides advanced resource management functionality
    """

    def __init__(self):
        self._tracker = ResourceTracker()
        self._weak_refs: List[weakref.ref] = []

    def track_object(self, obj: Any, cleanup_func: Optional[Callable] = None) -> None:
        """
        跟踪对象生命周期
        Track object lifecycle

        Args:
            obj: 要跟踪的对象
            cleanup_func: 清理函数
        """

        def cleanup_callback(ref):
            if cleanup_func:
                try:
                    cleanup_func()
                except Exception as e:
                    print(f"对象清理失败: {e}")

            # 从弱引用列表中移除
            if ref in self._weak_refs:
                self._weak_refs.remove(ref)

        weak_ref = weakref.ref(obj, cleanup_callback)
        self._weak_refs.append(weak_ref)

    def cleanup_dead_references(self) -> int:
        """
        清理死引用
        Cleanup dead references

        Returns:
            int: 清理的引用数量
        """
        initial_count = len(self._weak_refs)
        self._weak_refs = [ref for ref in self._weak_refs if ref() is not None]
        return initial_count - len(self._weak_refs)

    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        tracker_stats = self._tracker.get_stats()

        return {
            "tracker_stats": tracker_stats,
            "weak_references": len(self._weak_refs),
            "dead_references": self.cleanup_dead_references(),
        }

    def cleanup_all(self) -> None:
        """清理所有资源"""
        self._tracker.cleanup_all()
        self.cleanup_dead_references()


def get_global_resource_tracker() -> ResourceTracker:
    """获取全局资源跟踪器"""
    return _global_resource_tracker


def cleanup_global_resources() -> None:
    """清理全局资源"""
    _global_resource_tracker.cleanup_all()


def get_resource_stats() -> Dict[str, Any]:
    """获取全局资源统计信息"""
    return _global_resource_tracker.get_stats()

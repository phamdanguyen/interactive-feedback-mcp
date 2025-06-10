# feedback_ui/utils/object_pool.py

"""
对象池模式实现
Object Pool Pattern Implementation

提供高效的对象重用机制，减少对象创建和销毁的开销，
特别适用于重对象如QByteArray、QBuffer、QPixmap等。

Provides efficient object reuse mechanism to reduce object creation 
and destruction overhead, especially suitable for heavy objects 
like QByteArray, QBuffer, QPixmap, etc.
"""

import threading
from typing import TypeVar, Generic, List, Callable, Optional, Any, Dict

T = TypeVar("T")


class ObjectPool(Generic[T]):
    """
    通用对象池基类
    Generic Object Pool Base Class

    实现LRU淘汰策略、线程安全和对象重置功能
    Implements LRU eviction strategy, thread safety and object reset functionality
    """

    def __init__(
        self,
        factory: Callable[[], T],
        max_size: int = 50,
        reset_func: Optional[Callable[[T], None]] = None,
    ):
        """
        初始化对象池
        Initialize object pool

        Args:
            factory: 对象创建工厂函数
            max_size: 池最大大小
            reset_func: 对象重置函数
        """
        self._factory = factory
        self._max_size = max_size
        self._reset_func = reset_func
        self._pool: List[T] = []
        self._lock = threading.Lock()

        # 统计信息
        self._created_count = 0
        self._acquired_count = 0
        self._released_count = 0
        self._hit_count = 0
        self._miss_count = 0

    def acquire(self) -> T:
        """
        从池中获取对象
        Acquire object from pool

        Returns:
            T: 可用的对象实例
        """
        with self._lock:
            self._acquired_count += 1

            if self._pool:
                # 从池中获取（LRU：取最后一个）
                obj = self._pool.pop()
                self._hit_count += 1
                return obj
            else:
                # 池为空，创建新对象
                obj = self._factory()
                self._created_count += 1
                self._miss_count += 1
                return obj

    def release(self, obj: T) -> None:
        """
        将对象归还到池中
        Release object back to pool

        Args:
            obj: 要归还的对象
        """
        if obj is None:
            return

        with self._lock:
            self._released_count += 1

            if len(self._pool) < self._max_size:
                # 重置对象状态
                if self._reset_func:
                    try:
                        self._reset_func(obj)
                    except Exception as e:
                        # 重置失败，不放回池中
                        return

                # 放回池中（LRU：放在末尾）
                self._pool.append(obj)

    def clear(self) -> None:
        """
        清空对象池
        Clear object pool
        """
        with self._lock:
            self._pool.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取池统计信息
        Get pool statistics

        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            total_requests = self._hit_count + self._miss_count
            hit_rate = (
                (self._hit_count / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "pool_size": len(self._pool),
                "max_size": self._max_size,
                "created_count": self._created_count,
                "acquired_count": self._acquired_count,
                "released_count": self._released_count,
                "hit_count": self._hit_count,
                "miss_count": self._miss_count,
                "hit_rate_percent": round(hit_rate, 2),
                "utilization_percent": round(len(self._pool) / self._max_size * 100, 2),
            }


class PooledResource(Generic[T]):
    """
    池化资源上下文管理器
    Pooled Resource Context Manager

    确保资源正确归还到池中
    Ensures resources are properly returned to pool
    """

    def __init__(self, pool: ObjectPool[T]):
        self._pool = pool
        self._resource: Optional[T] = None

    def __enter__(self) -> T:
        self._resource = self._pool.acquire()
        return self._resource

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._resource is not None:
            self._pool.release(self._resource)
            self._resource = None


# Qt对象专用池实现
try:
    from PySide6.QtCore import QByteArray, QBuffer
    from PySide6.QtGui import QPixmap

    class QByteArrayPool(ObjectPool[QByteArray]):
        """QByteArray对象池"""

        def __init__(self, max_size: int = 20):
            super().__init__(
                factory=lambda: QByteArray(),
                max_size=max_size,
                reset_func=self._reset_byte_array,
            )

        @staticmethod
        def _reset_byte_array(byte_array: QByteArray) -> None:
            """重置QByteArray对象"""
            byte_array.clear()

    class QBufferPool(ObjectPool[QBuffer]):
        """QBuffer对象池"""

        def __init__(self, max_size: int = 10):
            super().__init__(
                factory=lambda: QBuffer(),
                max_size=max_size,
                reset_func=self._reset_buffer,
            )

        @staticmethod
        def _reset_buffer(buffer: QBuffer) -> None:
            """重置QBuffer对象"""
            if buffer.isOpen():
                buffer.close()
            buffer.setData(QByteArray())

    class QPixmapPool(ObjectPool[QPixmap]):
        """QPixmap对象池（用于临时缩放等操作）"""

        def __init__(self, max_size: int = 15):
            super().__init__(
                factory=lambda: QPixmap(),
                max_size=max_size,
                reset_func=self._reset_pixmap,
            )

        @staticmethod
        def _reset_pixmap(pixmap: QPixmap) -> None:
            """重置QPixmap对象"""
            # QPixmap没有clear方法，创建空的pixmap
            pixmap.swap(QPixmap())

except ImportError:
    # 如果PySide6不可用，提供空实现
    QByteArrayPool = None
    QBufferPool = None
    QPixmapPool = None


# 全局对象池实例
_byte_array_pool: Optional[QByteArrayPool] = None
_buffer_pool: Optional[QBufferPool] = None
_pixmap_pool: Optional[QPixmapPool] = None


def _get_or_create_pool(pool_class, pool_instance_var: str):
    """通用池获取函数，减少重复代码"""
    if pool_class is None:
        return None

    pool_instance = globals().get(pool_instance_var)
    if pool_instance is None:
        pool_instance = pool_class()
        globals()[pool_instance_var] = pool_instance
    return pool_instance


def get_byte_array_pool() -> Optional[QByteArrayPool]:
    """获取全局QByteArray池"""
    return _get_or_create_pool(QByteArrayPool, "_byte_array_pool")


def get_buffer_pool() -> Optional[QBufferPool]:
    """获取全局QBuffer池"""
    return _get_or_create_pool(QBufferPool, "_buffer_pool")


def get_pixmap_pool() -> Optional[QPixmapPool]:
    """获取全局QPixmap池"""
    return _get_or_create_pool(QPixmapPool, "_pixmap_pool")


def get_all_pool_stats() -> Dict[str, Dict[str, Any]]:
    """
    获取所有池的统计信息
    Get statistics for all pools

    Returns:
        Dict[str, Dict[str, Any]]: 所有池的统计信息
    """
    stats = {}

    if _byte_array_pool:
        stats["byte_array_pool"] = _byte_array_pool.get_stats()

    if _buffer_pool:
        stats["buffer_pool"] = _buffer_pool.get_stats()

    if _pixmap_pool:
        stats["pixmap_pool"] = _pixmap_pool.get_stats()

    return stats


def clear_all_pools() -> None:
    """清空所有全局池"""
    if _byte_array_pool:
        _byte_array_pool.clear()
    if _buffer_pool:
        _buffer_pool.clear()
    if _pixmap_pool:
        _pixmap_pool.clear()

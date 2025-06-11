# interactive_feedback_server/utils/list_optimizer.py

"""
列表操作优化工具
List Operation Optimization Tools

提供智能的列表操作函数，避免不必要的复制和内存分配，
优化列表合并、扩展等常见操作的性能。

Provides intelligent list operation functions to avoid unnecessary 
copying and memory allocation, optimizing performance of common 
operations like list merging and extension.
"""

from typing import List, Any, Optional, TypeVar, Callable

T = TypeVar("T")


def smart_extend(target: List[T], source: List[T], in_place: bool = False) -> List[T]:
    """
    智能列表扩展，避免不必要的复制
    Smart list extension, avoiding unnecessary copying

    Args:
        target: 目标列表
        source: 源列表
        in_place: 是否就地修改目标列表

    Returns:
        List[T]: 扩展后的列表
    """
    if not source:
        return target if in_place else target.copy()

    if not target:
        return source.copy()

    if in_place:
        target.extend(source)
        return target
    else:
        # 根据大小选择最优策略
        if len(source) == 1:
            # 单个元素，使用 + 操作符更高效
            return target + [source[0]]
        elif len(target) < len(source):
            # 目标较小，复制目标后扩展
            result = target.copy()
            result.extend(source)
            return result
        else:
            # 源较小，使用 + 操作符
            return target + source


def smart_merge(
    *lists: List[T], remove_duplicates: bool = False, preserve_order: bool = True
) -> List[T]:
    """
    智能列表合并，优化内存使用
    Smart list merging, optimizing memory usage

    Args:
        *lists: 要合并的列表
        remove_duplicates: 是否移除重复项
        preserve_order: 是否保持顺序

    Returns:
        List[T]: 合并后的列表
    """
    if not lists:
        return []

    # 过滤空列表
    non_empty_lists = [lst for lst in lists if lst]

    if not non_empty_lists:
        return []

    if len(non_empty_lists) == 1:
        result = non_empty_lists[0].copy()
    else:
        # 直接合并，避免不必要的长度计算
        result = []
        for lst in non_empty_lists:
            result.extend(lst)

    if remove_duplicates:
        if preserve_order:
            # 保持顺序的去重
            seen = set()
            unique_result = []
            for item in result:
                if item not in seen:
                    seen.add(item)
                    unique_result.append(item)
            return unique_result
        else:
            # 不保持顺序，使用set更高效
            return list(set(result))

    return result


def smart_filter(
    source: List[T], predicate: Callable[[T], bool], in_place: bool = False
) -> List[T]:
    """
    智能列表过滤，优化内存使用
    Smart list filtering, optimizing memory usage

    Args:
        source: 源列表
        predicate: 过滤条件函数
        in_place: 是否就地修改（仅当可能时）

    Returns:
        List[T]: 过滤后的列表
    """
    if not source:
        return []

    if in_place:
        # 就地过滤（从后往前删除以避免索引问题）
        for i in range(len(source) - 1, -1, -1):
            if not predicate(source[i]):
                del source[i]
        return source
    else:
        # 创建新列表
        return [item for item in source if predicate(item)]


def smart_deduplicate(
    source: List[T],
    key_func: Optional[Callable[[T], Any]] = None,
    preserve_order: bool = True,
) -> List[T]:
    """
    智能去重，支持自定义键函数
    Smart deduplication with custom key function support

    Args:
        source: 源列表
        key_func: 键提取函数
        preserve_order: 是否保持顺序

    Returns:
        List[T]: 去重后的列表
    """
    if not source:
        return []

    if len(source) == 1:
        return source.copy()

    if key_func is None:
        # 简单去重
        if preserve_order:
            seen = set()
            result = []
            for item in source:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        else:
            return list(set(source))
    else:
        # 基于键函数的去重
        seen_keys = set()
        result = []

        for item in source:
            key = key_func(item)
            if key not in seen_keys:
                seen_keys.add(key)
                result.append(item)

        return result


def smart_partition(
    source: List[T], predicate: Callable[[T], bool]
) -> tuple[List[T], List[T]]:
    """
    智能分区，将列表分为满足和不满足条件的两部分
    Smart partitioning, dividing list into matching and non-matching parts

    Args:
        source: 源列表
        predicate: 分区条件函数

    Returns:
        tuple[List[T], List[T]]: (满足条件的列表, 不满足条件的列表)
    """
    if not source:
        return [], []

    true_items = []
    false_items = []

    for item in source:
        if predicate(item):
            true_items.append(item)
        else:
            false_items.append(item)

    return true_items, false_items


def smart_chunk(source: List[T], chunk_size: int) -> List[List[T]]:
    """
    智能分块，将列表分割为指定大小的块
    Smart chunking, dividing list into chunks of specified size

    Args:
        source: 源列表
        chunk_size: 块大小

    Returns:
        List[List[T]]: 分块后的列表
    """
    if not source or chunk_size <= 0:
        return []

    if chunk_size >= len(source):
        return [source.copy()]

    chunks = []
    for i in range(0, len(source), chunk_size):
        chunks.append(source[i : i + chunk_size])

    return chunks


# V4.1 移除：LazyList类和create_lazy_list函数未在输入优化功能中使用


# V4.1 移除：性能跟踪装饰器未在输入优化功能中使用，简化代码

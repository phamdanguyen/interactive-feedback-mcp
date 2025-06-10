# src/interactive_feedback_server/utils/text_processor.py
"""
文本处理优化器
Text Processing Optimizer

V3.2 第一阶段性能优化 - Day 3: 字符串处理优化
V3.2 Phase 1 Performance Optimization - Day 3: String Processing Optimization

提供高性能的文本预处理和关键词匹配功能，显著提升文本处理速度。
Provides high-performance text preprocessing and keyword matching for significant speed improvement.

特性 Features:
- 预编译正则表达式 (Pre-compiled regex patterns)
- 智能文本标准化 (Intelligent text normalization)
- 高效关键词匹配 (Efficient keyword matching)
- 文本处理缓存 (Text processing cache)
"""

import re
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
import unicodedata


class TextProcessor:
    """
    高性能文本处理器
    High-Performance Text Processor

    优化文本预处理和关键词匹配性能。
    Optimizes text preprocessing and keyword matching performance.
    """

    def __init__(self):
        """初始化文本处理器"""
        # 预编译正则表达式模式
        self._whitespace_pattern = re.compile(r"\s+")
        self._punctuation_pattern = re.compile(r"[^\w\s]")
        self._number_pattern = re.compile(r"\d+")
        self._english_pattern = re.compile(r"[a-zA-Z]+")
        self._chinese_pattern = re.compile(r"[\u4e00-\u9fff]+")

        # 简化标点符号处理，避免复杂映射
        self._punctuation_map = None  # 暂时不使用复杂映射

        # 停用词集合（用于快速查找）
        self._stop_words = {
            "的",
            "了",
            "在",
            "是",
            "我",
            "有",
            "和",
            "就",
            "不",
            "人",
            "都",
            "一",
            "一个",
            "上",
            "也",
            "很",
            "到",
            "说",
            "要",
            "去",
            "你",
            "会",
            "着",
            "没有",
            "看",
            "好",
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
        }

        # 文本长度阈值
        self.MIN_TEXT_LENGTH = 2
        self.MAX_TEXT_LENGTH = 1000

    @lru_cache(maxsize=500)
    def normalize_text(self, text: str) -> str:
        """
        标准化文本（带缓存）
        Normalize text with caching

        Args:
            text: 原始文本

        Returns:
            str: 标准化后的文本
        """
        if not text or not isinstance(text, str):
            return ""

        # 长度检查
        if len(text) < self.MIN_TEXT_LENGTH:
            return ""
        if len(text) > self.MAX_TEXT_LENGTH:
            text = text[: self.MAX_TEXT_LENGTH]

        # 1. Unicode标准化
        text = unicodedata.normalize("NFKC", text)

        # 2. 转小写
        text = text.lower()

        # 3. 简化标点符号处理（移除或替换为空格）
        text = self._punctuation_pattern.sub(" ", text)

        # 4. 合并多个空白字符
        text = self._whitespace_pattern.sub(" ", text)

        # 5. 去除首尾空白
        text = text.strip()

        return text

    @lru_cache(maxsize=300)
    def extract_keywords(self, text: str) -> Tuple[str, ...]:
        """
        提取关键词（带缓存）
        Extract keywords with caching

        Args:
            text: 输入文本

        Returns:
            Tuple[str, ...]: 关键词元组（用于缓存）
        """
        normalized_text = self.normalize_text(text)
        if not normalized_text:
            return tuple()

        # 分词
        words = normalized_text.split()

        # 过滤停用词和短词
        keywords = []
        for word in words:
            if len(word) >= 2 and word not in self._stop_words and not word.isdigit():
                keywords.append(word)

        return tuple(keywords)

    def get_text_features(self, text: str) -> Dict[str, any]:
        """
        获取文本特征
        Get text features

        Args:
            text: 输入文本

        Returns:
            Dict[str, any]: 文本特征字典
        """
        normalized_text = self.normalize_text(text)

        if not normalized_text:
            return {
                "length": 0,
                "word_count": 0,
                "has_question": False,
                "has_chinese": False,
                "has_english": False,
                "keywords": tuple(),
            }

        # 基本特征
        word_count = len(normalized_text.split())
        has_question = "?" in text or "？" in text
        has_chinese = bool(self._chinese_pattern.search(text))
        has_english = bool(self._english_pattern.search(text))

        # 关键词
        keywords = self.extract_keywords(text)

        return {
            "length": len(normalized_text),
            "word_count": word_count,
            "has_question": has_question,
            "has_chinese": has_chinese,
            "has_english": has_english,
            "keywords": keywords,
        }


class OptimizedMatcher:
    """
    优化的关键词匹配器
    Optimized Keyword Matcher

    使用高效算法进行关键词匹配。
    Uses efficient algorithms for keyword matching.
    """

    def __init__(self, patterns: Dict[str, Dict[str, any]]):
        """
        初始化匹配器
        Initialize matcher

        Args:
            patterns: 模式字典，格式同CORE_PATTERNS
        """
        self.patterns = patterns
        self._build_optimized_structures()

    def _build_optimized_structures(self):
        """构建优化的数据结构"""
        # 按长度分组的触发词
        self._triggers_by_length: Dict[int, List[Tuple[str, str, int]]] = {}

        # 类别优先级
        self._category_priority = {
            "confirmation": 0,
            "choice": 1,
            "action": 2,
            "question": 3,
        }

        # 构建触发词索引
        for category, config in self.patterns.items():
            priority = self._category_priority.get(category, 999)

            for trigger in config["triggers"]:
                trigger_len = len(trigger)

                if trigger_len not in self._triggers_by_length:
                    self._triggers_by_length[trigger_len] = []

                self._triggers_by_length[trigger_len].append(
                    (trigger, category, priority)
                )

        # 按长度降序排序（长词优先）
        self._sorted_lengths = sorted(self._triggers_by_length.keys(), reverse=True)

        # 对每个长度组内按优先级排序
        for length in self._sorted_lengths:
            self._triggers_by_length[length].sort(key=lambda x: x[2])  # 按优先级排序

    @lru_cache(maxsize=200)
    def find_best_match(self, text: str) -> Optional[Tuple[str, str, List[str]]]:
        """
        查找最佳匹配（带缓存）
        Find best match with caching

        Args:
            text: 输入文本

        Returns:
            Optional[Tuple[str, str, List[str]]]: (触发词, 类别, 选项列表) 或 None
        """
        if not text:
            return None

        text_lower = text.lower()

        # 按长度优先级搜索
        for length in self._sorted_lengths:
            triggers = self._triggers_by_length[length]

            for trigger, category, _ in triggers:  # priority未使用
                if trigger in text_lower:
                    options = self.patterns[category]["options"]
                    return (trigger, category, options)

        return None

    def find_all_matches(self, text: str) -> List[Tuple[str, str, List[str]]]:
        """
        查找所有匹配
        Find all matches

        Args:
            text: 输入文本

        Returns:
            List[Tuple[str, str, List[str]]]: 所有匹配的列表
        """
        if not text:
            return []

        text_lower = text.lower()
        matches = []

        for category, config in self.patterns.items():
            for trigger in config["triggers"]:
                if trigger in text_lower:
                    matches.append((trigger, category, config["options"]))

        # 按触发词长度和优先级排序
        matches.sort(key=lambda x: (-len(x[0]), self._category_priority.get(x[1], 999)))

        return matches


# 全局实例
_text_processor = TextProcessor()
_optimized_matcher = None  # 延迟初始化


def get_text_processor() -> TextProcessor:
    """获取全局文本处理器实例"""
    return _text_processor


def get_optimized_matcher() -> OptimizedMatcher:
    """获取全局优化匹配器实例"""
    global _optimized_matcher

    if _optimized_matcher is None:
        # 延迟导入避免循环依赖
        from .rule_engine import CORE_PATTERNS

        _optimized_matcher = OptimizedMatcher(CORE_PATTERNS)

    return _optimized_matcher


def clear_text_processing_cache():
    """清空文本处理缓存"""
    _text_processor.normalize_text.cache_clear()
    _text_processor.extract_keywords.cache_clear()

    global _optimized_matcher
    if _optimized_matcher:
        _optimized_matcher.find_best_match.cache_clear()


def get_text_processing_stats() -> Dict[str, any]:
    """获取文本处理统计信息"""
    processor = get_text_processor()
    matcher = get_optimized_matcher()

    return {
        "normalize_cache_info": processor.normalize_text.cache_info()._asdict(),
        "keywords_cache_info": processor.extract_keywords.cache_info()._asdict(),
        "matcher_cache_info": matcher.find_best_match.cache_info()._asdict(),
        "total_patterns": len(matcher.patterns),
        "trigger_lengths": list(matcher._sorted_lengths),
    }


# 便捷函数
def fast_normalize_text(text: str) -> str:
    """快速文本标准化"""
    return _text_processor.normalize_text(text)


def fast_extract_keywords(text: str) -> Tuple[str, ...]:
    """快速关键词提取"""
    return _text_processor.extract_keywords(text)


def fast_find_match(text: str) -> Optional[Tuple[str, str, List[str]]]:
    """快速匹配查找"""
    return get_optimized_matcher().find_best_match(text)

# feedback_ui/utils/text_formatter.py

import re
from typing import Dict
from functools import lru_cache


class TextFormatter:
    """
    文本格式化工具类，将Markdown格式转换为更易读的纯文本格式
    Text formatter utility class that converts Markdown format to more readable plain text
    """

    def __init__(self):
        # 编译正则表达式模式以提高性能
        self._patterns = self._compile_patterns()
        # 缓存格式化结果以提高性能
        self._format_cache = {}

    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """编译所有正则表达式模式"""
        return {
            # 标题格式 (# ## ### 等)
            "headers": re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE),
            # 粗体格式 (**text** 或 __text__)
            "bold": re.compile(r"\*\*(.+?)\*\*|__(.+?)__"),
            # 斜体格式 (*text* 或 _text_)
            "italic": re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)|(?<!_)_([^_]+?)_(?!_)"),
            # 代码格式 (`code`)
            "inline_code": re.compile(r"`([^`]+?)`"),
            # 代码块格式 (```code```)
            "code_block": re.compile(r"```[\w]*\n?(.*?)\n?```", re.DOTALL),
            # 列表项格式 (- item 或 * item 或 + item)
            "unordered_list": re.compile(r"^[\s]*[-*+]\s+(.+)$", re.MULTILINE),
            # 有序列表格式 (1. item)
            "ordered_list": re.compile(r"^[\s]*\d+\.\s+(.+)$", re.MULTILINE),
            # 链接格式 [text](url)
            "links": re.compile(r"\[([^\]]+?)\]\([^)]+?\)"),
            # 引用格式 (> text)
            "blockquote": re.compile(r"^>\s+(.+)$", re.MULTILINE),
            # 水平分割线
            "horizontal_rule": re.compile(r"^[-*_]{3,}$", re.MULTILINE),
        }

    def format_text(self, text: str) -> str:
        """
        将包含Markdown格式的文本转换为更易读的纯文本
        Convert text with Markdown formatting to more readable plain text

        Args:
            text (str): 原始文本，可能包含Markdown格式

        Returns:
            str: 格式化后的纯文本
        """
        if not text or not isinstance(text, str):
            return text or ""

        # 检查缓存
        if text in self._format_cache:
            return self._format_cache[text]

        # 创建文本副本进行处理
        formatted_text = text

        # 1. 处理代码块（优先处理，避免内部格式被误处理）
        formatted_text = self._format_code_blocks(formatted_text)

        # 2. 处理标题
        formatted_text = self._format_headers(formatted_text)

        # 3. 处理粗体
        formatted_text = self._format_bold(formatted_text)

        # 4. 处理斜体
        formatted_text = self._format_italic(formatted_text)

        # 5. 处理内联代码
        formatted_text = self._format_inline_code(formatted_text)

        # 6. 处理列表
        formatted_text = self._format_lists(formatted_text)

        # 7. 处理链接
        formatted_text = self._format_links(formatted_text)

        # 8. 处理引用
        formatted_text = self._format_blockquotes(formatted_text)

        # 9. 处理水平分割线
        formatted_text = self._format_horizontal_rules(formatted_text)

        # 10. 清理多余的空行
        formatted_text = self._clean_extra_newlines(formatted_text)

        # 缓存结果（限制缓存大小避免内存泄漏）
        if len(self._format_cache) < 100:
            self._format_cache[text] = formatted_text

        return formatted_text

    def _format_headers(self, text: str) -> str:
        """格式化标题"""

        def replace_header(match):
            level = len(match.group(1))  # # 的数量
            title = match.group(2).strip()

            # 根据标题级别添加不同的装饰
            if level == 1:
                return f"【{title}】"
            elif level == 2:
                return f"■ {title}"
            elif level == 3:
                return f"▶ {title}"
            else:
                return f"• {title}"

        return self._patterns["headers"].sub(replace_header, text)

    def _apply_simple_format(
        self, text: str, pattern_name: str, format_func, group_index: int = 1
    ) -> str:
        """
        通用的简单格式化方法，减少代码重复
        Generic simple formatting method to reduce code duplication
        """

        def replace_match(match):
            if group_index == "multi":
                # 处理多组匹配（如粗体和斜体的多种语法）
                content = match.group(1) or match.group(2)
            else:
                content = match.group(group_index)
            return format_func(content)

        return self._patterns[pattern_name].sub(replace_match, text)

    def _format_bold(self, text: str) -> str:
        """格式化粗体文本"""
        return self._apply_simple_format(
            text, "bold", lambda content: f"【{content}】", "multi"
        )

    def _format_italic(self, text: str) -> str:
        """格式化斜体文本"""
        return self._apply_simple_format(
            text, "italic", lambda content: f"〈{content}〉", "multi"
        )

    def _format_inline_code(self, text: str) -> str:
        """格式化内联代码"""
        return self._apply_simple_format(
            text, "inline_code", lambda content: f"『{content}』"
        )

    def _format_code_blocks(self, text: str) -> str:
        """格式化代码块"""

        def replace_code_block(match):
            code = match.group(1).strip()
            lines = code.split("\n")

            # 为每行代码添加前缀
            formatted_lines = []
            for line in lines:
                formatted_lines.append(f"    {line}")

            return "\n".join(formatted_lines)

        return self._patterns["code_block"].sub(replace_code_block, text)

    def _format_lists(self, text: str) -> str:
        """格式化列表"""
        # 使用通用方法处理列表
        text = self._apply_simple_format(
            text, "unordered_list", lambda item: f"  • {item}"
        )
        text = self._apply_simple_format(
            text, "ordered_list", lambda item: f"  ① {item}"
        )
        return text

    def _format_links(self, text: str) -> str:
        """格式化链接"""
        return self._apply_simple_format(text, "links", lambda link_text: link_text)

    def _format_blockquotes(self, text: str) -> str:
        """格式化引用"""
        return self._apply_simple_format(
            text, "blockquote", lambda quote_text: f"  ▌{quote_text}"
        )

    def _format_horizontal_rules(self, text: str) -> str:
        """格式化水平分割线"""
        return self._patterns["horizontal_rule"].sub("─" * 40, text)

    def _clean_extra_newlines(self, text: str) -> str:
        """清理多余的空行"""
        # 将连续的多个换行符替换为最多两个换行符
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 只去除开头和结尾的换行符，保留空格缩进
        text = text.strip("\n")

        return text

    def is_formatted_text(self, text: str) -> bool:
        """
        检查文本是否包含Markdown格式标记
        Check if text contains Markdown formatting marks

        Args:
            text (str): 要检查的文本

        Returns:
            bool: 如果包含格式标记返回True
        """
        if not text:
            return False

        # 快速检查常见格式标记（避免复杂正则表达式）
        quick_markers = ["**", "*", "`", "#", "- ", "> ", "[", "```", "___", "__"]

        for marker in quick_markers:
            if marker in text:
                return True

        # 检查数字列表格式 (1. 2. 等)
        import re

        if re.search(r"^\s*\d+\.\s+", text, re.MULTILINE):
            return True

        return False

    def clear_cache(self):
        """
        清理格式化缓存
        Clear formatting cache
        """
        self._format_cache.clear()

    def get_cache_size(self) -> int:
        """
        获取当前缓存大小
        Get current cache size

        Returns:
            int: 缓存中的条目数量
        """
        return len(self._format_cache)


# 创建全局实例以供使用
text_formatter = TextFormatter()

# src/feedback_ui/utils/markdown_renderer.py
"""
Markdown到HTML渲染器 - V4.3 重构版本
Markdown to HTML renderer - V4.3 Refactored Version

使用成熟的Markdown库（mistune）将Markdown格式文本转换为Qt支持的HTML格式。
Uses mature Markdown library (mistune) to convert Markdown formatted text to Qt-supported HTML format.
"""

import re
from typing import Dict, Optional, Set

try:
    import mistune

    MISTUNE_AVAILABLE = True
except ImportError:
    MISTUNE_AVAILABLE = False
    print("Warning: mistune not available, falling back to basic renderer")

# 样式常量 - 避免重复定义和硬编码
COMMON_STYLES = {
    "code_font": "Consolas, Monaco, monospace",
    "line_height_normal": "1.4",
    "line_height_compact": "1.3",
    "line_height_tight": "1.2",
    "no_background": "background: none; border: none;",
    "inherit_color": "color: inherit;",
}


# 样式构建函数 - 消除重复代码
def _build_style(**kwargs) -> str:
    """构建CSS样式字符串，避免重复代码"""
    return (
        "; ".join(f'{k.replace("_", "-")}: {v}' for k, v in kwargs.items() if v) + ";"
    )


def _build_code_style(padding: str, display: str, font_size: str = None) -> str:
    """构建代码样式，消除重复"""
    style_parts = [
        COMMON_STYLES["no_background"],
        COMMON_STYLES["inherit_color"],
        f"padding: {padding}",
        f'font-family: {COMMON_STYLES["code_font"]}',
        f"display: {display}",
    ]
    if font_size:
        style_parts.append(f"font-size: {font_size}")
    return " ".join(style_parts) + ";"


# 预定义的完整样式模板 - 恢复到工作版本
STYLE_TEMPLATES = {
    "paragraph": _build_style(
        margin="2px 0", line_height=COMMON_STYLES["line_height_normal"]
    ),
    "list_item": _build_style(
        margin="0px 0", line_height=COMMON_STYLES["line_height_compact"]
    ),
    "list_container": _build_style(
        margin="3px 0 2px 0",
        padding_left="18px",
        line_height=COMMON_STYLES["line_height_compact"],
    ),
    "code_block": _build_code_style("4px 0", "block")
    + f' margin: 4px 0; white-space: pre-wrap; line-height: {COMMON_STYLES["line_height_compact"]};',
    "code_inline": _build_code_style("0", "inline", "0.9em"),
    "blockquote": _build_style(
        border_left="4px solid #ddd",
        margin="3px 0 2px 0",
        padding_left="10px",
        opacity="0.8",
        font_style="italic",
        line_height=COMMON_STYLES["line_height_compact"],
    )
    + f' {COMMON_STYLES["inherit_color"]}',
    "hr": _build_style(border="none", border_top="1px solid #ddd", margin="6px 0"),
}


# 标题样式配置 - 恢复到原始工作版本
def _create_heading_style(color: str, margin: str, font_size: str = None) -> str:
    """创建标题样式，确保CSS语法正确"""
    # 确保颜色属性以分号结尾
    if not color.endswith(";"):
        color += ";"
    base_style = f'{color} font-weight: bold; margin: {margin}; line-height: {COMMON_STYLES["line_height_tight"]};'
    return f"{base_style} font-size: {font_size};" if font_size else base_style


HEADING_STYLES = {
    # H1保持特殊颜色用于突出显示
    1: _create_heading_style("color: #1f4e79", "8px 0 3px 0"),
    # H2-H6使用继承颜色，通过字体大小区分层次
    2: _create_heading_style(COMMON_STYLES["inherit_color"], "6px 0 2px 0", "1.2em"),
    3: _create_heading_style(COMMON_STYLES["inherit_color"], "4px 0 1px 0", "1.1em"),
    4: _create_heading_style(COMMON_STYLES["inherit_color"], "3px 0 1px 0", "1.05em"),
    5: _create_heading_style(COMMON_STYLES["inherit_color"], "2px 0 0px 0", "1.0em"),
    6: _create_heading_style(COMMON_STYLES["inherit_color"], "1px 0 0px 0", "0.95em"),
}


class MarkdownRenderer:
    """
    Markdown到HTML渲染器 - V4.3 重构版本
    使用成熟的mistune库进行Markdown渲染，提供更好的兼容性和性能。
    """

    def __init__(self):
        self._mistune_renderer = None
        self._fallback_patterns = None
        self._render_cache = {}
        self._init_renderer()

    def _init_renderer(self):
        """初始化Markdown渲染器"""
        if MISTUNE_AVAILABLE:
            # 使用mistune创建自定义渲染器
            self._mistune_renderer = mistune.create_markdown(
                renderer=self._create_qt_renderer(),
                plugins=["strikethrough", "footnotes", "table"],
            )
        else:
            # 降级到基本渲染器
            self._fallback_patterns = self._compile_fallback_patterns()

    def _create_qt_renderer(self):
        """创建适合Qt显示的HTML渲染器"""
        if not MISTUNE_AVAILABLE:
            return None

        class QtHTMLRenderer(mistune.HTMLRenderer):
            """自定义HTML渲染器，优化Qt显示效果"""

            def paragraph(self, text):
                return f'<p style="{STYLE_TEMPLATES["paragraph"]}">{text}</p>\n'

            def heading(self, text, level):
                style = HEADING_STYLES.get(level, HEADING_STYLES[6])
                tag = f"h{min(level + 1, 6)}"  # Qt支持h1-h6
                return f'<{tag} style="{style}">{text}</{tag}>\n'

            def list_item(self, text):
                return f'<li style="{STYLE_TEMPLATES["list_item"]}">{text}</li>\n'

            def list(self, text, ordered, **attrs):
                tag = "ol" if ordered else "ul"
                return f'<{tag} style="{STYLE_TEMPLATES["list_container"]}">{text}</{tag}>\n'

            def block_code(self, code, info=None):
                return f'<pre style="{STYLE_TEMPLATES["code_block"]}">{mistune.escape(code)}</pre>\n'

            def codespan(self, text):
                return f'<code style="{STYLE_TEMPLATES["code_inline"]}">{mistune.escape(text)}</code>'

            def block_quote(self, text):
                return f'<blockquote style="{STYLE_TEMPLATES["blockquote"]}">{text}</blockquote>\n'

            def thematic_break(self):
                return f'<hr style="{STYLE_TEMPLATES["hr"]}">\n'

            def link(self, text, url, title=None):
                title_attr = f' title="{mistune.escape(title)}"' if title else ""
                # 链接保持适度的颜色区分，但更加柔和
                return f'<a href="{mistune.escape(url)}"{title_attr} style="color: #0066cc; text-decoration: underline; opacity: 0.9;">{text}</a>'

        return QtHTMLRenderer()

    def _compile_fallback_patterns(self) -> Dict[str, re.Pattern]:
        """编译降级模式的正则表达式模式"""
        return {
            # 基本格式检测
            "header": re.compile(r"^#{1,6}\s+.+$", re.MULTILINE),
            "bold": re.compile(r"\*\*(.+?)\*\*|__(.+?)__"),
            "italic": re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)|(?<!_)_([^_]+?)_(?!_)"),
            "code": re.compile(r"`([^`]+?)`"),
            "list": re.compile(r"^[-*+]\s+.+$|^\d+\.\s+.+$", re.MULTILINE),
            "link": re.compile(r"\[([^\]]+?)\]\(([^)]+?)\)"),
            "blockquote": re.compile(r"^>\s+.+$", re.MULTILINE),
        }

    def render_to_html(self, markdown_text: str) -> str:
        """
        将Markdown文本渲染为HTML - V4.3 重构版本
        Render Markdown text to HTML - V4.3 Refactored Version

        Args:
            markdown_text: Markdown格式的文本

        Returns:
            str: HTML格式的文本
        """
        if not self._validate_input(markdown_text):
            return markdown_text or ""

        # 检查缓存
        cached_result = self._get_cached_result(markdown_text)
        if cached_result is not None:
            return cached_result

        try:
            html_text = self._perform_rendering(markdown_text)
            self._cache_result(markdown_text, html_text)
            return html_text

        except Exception as e:
            print(f"Markdown渲染失败: {e}")
            return markdown_text

    def _validate_input(self, markdown_text: str) -> bool:
        """验证输入参数"""
        return markdown_text and isinstance(markdown_text, str)

    def _get_cached_result(self, markdown_text: str) -> Optional[str]:
        """获取缓存结果"""
        return self._render_cache.get(markdown_text)

    def _perform_rendering(self, markdown_text: str) -> str:
        """执行实际渲染"""
        if self._mistune_renderer:
            html_text = self._mistune_renderer(markdown_text)
            return self._clean_html_output(html_text)
        else:
            return self._fallback_render(markdown_text)

    def _clean_html_output(self, html_text: str) -> str:
        """清理HTML输出"""
        html_text = re.sub(r"\n\s*\n", "\n", html_text)
        return html_text.strip()

    def _cache_result(self, markdown_text: str, html_text: str) -> None:
        """缓存渲染结果"""
        self._render_cache[markdown_text] = html_text

    def _fallback_render(self, text: str) -> str:
        """降级渲染方法，当mistune不可用时使用"""
        html_text = self._escape_html(text)
        html_text = self._apply_basic_formatting(html_text)
        return f'<p style="{STYLE_TEMPLATES["paragraph"]}">{html_text}</p>'

    def _escape_html(self, text: str) -> str:
        """HTML转义"""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _apply_basic_formatting(self, text: str) -> str:
        """应用基本格式"""
        # 粗体处理
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

        # 斜体处理
        text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)

        # 代码处理，使用样式模板
        text = re.sub(
            r"`([^`]+?)`",
            rf'<code style="{STYLE_TEMPLATES["code_inline"]}">\1</code>',
            text,
        )

        return text

    def is_markdown_content(self, text: str) -> bool:
        """
        检查文本是否包含Markdown格式标记 - V4.3 优化版本
        Check if text contains Markdown formatting marks - V4.3 Optimized Version

        Args:
            text: 要检查的文本

        Returns:
            bool: 如果包含格式标记返回True
        """
        if not text:
            return False

        return (
            self._has_quick_markers(text)
            or self._has_numbered_lists(text)
            or self._has_table_format(text)
        )

    def _has_quick_markers(self, text: str) -> bool:
        """检查快速标记"""
        quick_markers: Set[str] = {
            "**",
            "*",
            "`",
            "#",
            "- ",
            "> ",
            "[",
            "```",
            "___",
            "__",
            "~~",
        }
        return any(marker in text for marker in quick_markers)

    def _has_numbered_lists(self, text: str) -> bool:
        """检查数字列表格式"""
        if not hasattr(self, "_list_pattern"):
            self._list_pattern = re.compile(r"^\s*\d+\.\s+", re.MULTILINE)
        return bool(self._list_pattern.search(text))

    def _has_table_format(self, text: str) -> bool:
        """检查表格格式"""
        if "|" not in text:
            return False

        if not hasattr(self, "_table_pattern"):
            self._table_pattern = re.compile(r"\|.*\|")
        return bool(self._table_pattern.search(text))

    def clear_cache(self):
        """清理渲染缓存"""
        self._render_cache.clear()

    def get_cache_size(self) -> int:
        """获取当前缓存大小"""
        return len(self._render_cache)


# 创建全局实例
markdown_renderer = MarkdownRenderer()

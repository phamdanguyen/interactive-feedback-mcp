import re
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QLabel

from ..utils.ui_helpers import set_selection_colors

# 预编译正则表达式，提高性能
_COLOR_STYLE_PATTERN = re.compile(r"color:\s*[^;]+;")
_BODY_TAG_PATTERN = re.compile(r"<body[^>]*>")

# 代码颜色常量
_CODE_COLOR = "#4A90E2"

# 预编译代码处理的正则表达式
_INLINE_CODE_PATTERN = re.compile(
    r'<span style="([^"]*font-family:\'Courier New\'[^"]*)"'
)
_CODE_BLOCK_PATTERN = re.compile(r'<pre style="([^"]*)"')
_CODE_BLOCK_SPAN_PATTERN = re.compile(
    r'(<pre[^>]*>.*?)<span style="([^"]*font-family:\'Courier New\'[^"]*)"([^>]*>.*?</span>.*?</pre>)',
    re.DOTALL,
)


class SelectableLabel(QLabel):
    """
    一个可以选择文本的标签，同时支持点击操作。
    A label that allows text selection while also supporting click operations.
    """

    clicked = Signal()

    def __init__(self, text: str = "", parent: QObject = None):
        super().__init__(parent)
        # 启用文本选择
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setMouseTracking(True)
        self.setWordWrap(True)

        # 设置选择文本时的高亮颜色为灰色
        set_selection_colors(self)

        # 跟踪鼠标按下的位置，用于判断是否为点击操作
        self._press_pos = None
        self._is_dragging = False

        # 初始化属性
        self._original_text = ""
        self._enable_formatting = False  # 默认禁用格式化

        # 设置初始文本（如果提供）
        if text:
            self.setText(text)

    def mousePressEvent(self, event: QEvent):
        """记录鼠标按下的位置，用于后续判断是点击还是拖拽选择文本"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
            self._is_dragging = False

        # 调用父类的事件处理，确保文本选择功能正常
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QEvent):
        """如果鼠标移动超过阈值，标记为拖拽操作"""
        if (
            self._press_pos
            and (event.position().toPoint() - self._press_pos).manhattanLength() > 5
        ):
            self._is_dragging = True

        # 调用父类的事件处理，确保文本选择功能正常
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QEvent):
        """根据是否为拖拽操作，决定是发送点击信号还是执行文本选择"""
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos:
            # 如果不是拖拽操作，并且鼠标释放在标签范围内，则发射点击信号
            if not self._is_dragging and self.rect().contains(
                event.position().toPoint()
            ):
                # 如果没有选中文本，才发射点击信号
                if not self.hasSelectedText():
                    self.clicked.emit()

        # 重置状态
        self._press_pos = None
        self._is_dragging = False

        # 调用父类的事件处理，确保文本选择功能正常
        super().mouseReleaseEvent(event)

    def hasSelectedText(self) -> bool:
        """检查是否有选中的文本"""
        # QLabel没有直接的方法检查选中文本，使用多种方法检查
        try:
            from PySide6.QtGui import QGuiApplication

            # 方法1：检查系统剪贴板
            clipboard = QGuiApplication.clipboard()
            if clipboard and clipboard.ownsSelection():
                return True

            # 方法2：检查是否有选择模式（更可靠的方法）
            if hasattr(self, "selectionStart") and hasattr(self, "selectionLength"):
                return self.selectionLength() > 0

        except Exception:
            # 如果检查失败，保守地返回False
            pass

        return False

    def setText(self, text: str):
        """
        设置文本内容，自动检测并渲染Markdown
        Set text content with automatic Markdown detection and rendering

        Args:
            text (str): 要设置的文本
        """
        # 存储原始文本
        self._original_text = text or ""

        # 检测是否为Markdown内容
        if self._is_markdown_content(text):
            # 设置为富文本格式并渲染Markdown
            self.setTextFormat(Qt.TextFormat.RichText)
            html_content = self._convert_markdown_to_html(text)
            super().setText(html_content)
        else:
            # 普通文本，保持原有逻辑
            self.setTextFormat(Qt.TextFormat.PlainText)
            super().setText(text or "")

    def setFormattingEnabled(self, enabled: bool):
        """
        启用或禁用文本格式化功能（当前已禁用格式化功能）
        Enable or disable text formatting feature (formatting is currently disabled)

        Args:
            enabled (bool): True启用格式化，False禁用
        """
        self._enable_formatting = enabled
        # 注意：当前版本已禁用格式化功能，此方法保留用于兼容性

    def getOriginalText(self) -> str:
        """
        获取原始未格式化的文本
        Get the original unformatted text

        Returns:
            str: 原始文本
        """
        return self._original_text

    def isFormattingEnabled(self) -> bool:
        """
        检查是否启用了文本格式化
        Check if text formatting is enabled

        Returns:
            bool: True表示启用格式化
        """
        return self._enable_formatting

    def _is_markdown_content(self, text: str) -> bool:
        """
        检测文本是否包含Markdown格式
        Detect if text contains Markdown formatting

        Args:
            text (str): 要检测的文本

        Returns:
            bool: True表示包含Markdown格式
        """
        if not text:
            return False

        # 复用现有的检测逻辑
        try:
            from ..utils.text_formatter import text_formatter

            return text_formatter.is_formatted_text(text)
        except (ImportError, AttributeError):
            # 如果导入失败，使用简单的检测逻辑
            # 使用元组而非列表，提高性能
            markdown_indicators = (
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
            )
            return any(indicator in text for indicator in markdown_indicators)

    def _convert_markdown_to_html(self, markdown_text: str) -> str:
        """
        将Markdown转换为HTML
        Convert Markdown to HTML

        Args:
            markdown_text (str): Markdown文本

        Returns:
            str: 转换后的HTML
        """
        try:
            # 使用QTextDocument的原生Markdown支持
            doc = QTextDocument()
            doc.setMarkdown(markdown_text)
            html = doc.toHtml()

            # 处理代码元素的颜色样式
            html = self._apply_code_colors(html)

            html = _BODY_TAG_PATTERN.sub("<body>", html)

            return html
        except (RuntimeError, AttributeError) as e:
            # 捕获具体的Qt相关异常
            print(f"Markdown转换失败: {e}")
            return markdown_text

    def _apply_code_colors(self, html: str) -> str:
        """
        为代码元素添加CSS类名和蓝色样式
        Add CSS classes and blue color styles to code elements

        Args:
            html (str): 原始HTML内容

        Returns:
            str: 处理后的HTML内容
        """
        # 1. 处理内联代码（span标签包含Courier New字体）
        html = _INLINE_CODE_PATTERN.sub(
            rf'<span class="code-inline" style="\1; color: {_CODE_COLOR};"', html
        )

        # 2. 处理代码块（pre标签）
        html = _CODE_BLOCK_PATTERN.sub(
            rf'<pre class="code-block" style="color: {_CODE_COLOR}; margin: 0; padding: 0; background: none; border: none; display: inline;"',
            html,
        )

        # 3. 处理代码块内的span元素
        html = _CODE_BLOCK_SPAN_PATTERN.sub(
            rf'\1<span style="\2; color: {_CODE_COLOR};"\3', html
        )

        # 4. 移除非代码元素的颜色样式（优化版本）
        return self._remove_non_code_colors(html)

    def _remove_non_code_colors(self, html: str) -> str:
        """
        移除非代码元素的颜色样式
        Remove color styles from non-code elements

        Args:
            html (str): HTML内容

        Returns:
            str: 处理后的HTML内容
        """
        # 定义代码相关标记（元组比列表更高效）
        code_markers = (
            "font-family:'Courier New'",
            "<pre",
            "code-inline",
            "code-block",
        )

        lines = html.split("\n")
        processed_lines = []

        for line in lines:
            # 如果这行不包含代码相关标记，移除颜色样式
            if not any(marker in line for marker in code_markers):
                line = _COLOR_STYLE_PATTERN.sub("", line)
            processed_lines.append(line)

        return "\n".join(processed_lines)

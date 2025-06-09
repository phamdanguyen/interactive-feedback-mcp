"""
ANSI转义序列解析器
ANSI Escape Sequence Parser

用于解析终端输出中的ANSI转义序列，将其转换为Qt富文本格式。
Parses ANSI escape sequences in terminal output and converts them to Qt rich text format.
"""

import re
from typing import List, Tuple
from PySide6.QtGui import QColor, QTextCharFormat, QFont


class ANSIParser:
    """ANSI转义序列解析器"""

    # ANSI颜色映射表
    ANSI_COLORS = {
        # 标准颜色 (30-37, 40-47)
        30: QColor(0, 0, 0),  # 黑色
        31: QColor(205, 49, 49),  # 红色
        32: QColor(13, 188, 121),  # 绿色
        33: QColor(229, 229, 16),  # 黄色
        34: QColor(36, 114, 200),  # 蓝色
        35: QColor(188, 63, 188),  # 洋红
        36: QColor(17, 168, 205),  # 青色
        37: QColor(229, 229, 229),  # 白色
        # 亮色 (90-97, 100-107)
        90: QColor(102, 102, 102),  # 亮黑色（灰色）
        91: QColor(241, 76, 76),  # 亮红色
        92: QColor(35, 209, 139),  # 亮绿色
        93: QColor(245, 245, 67),  # 亮黄色
        94: QColor(59, 142, 234),  # 亮蓝色
        95: QColor(214, 112, 214),  # 亮洋红
        96: QColor(41, 184, 219),  # 亮青色
        97: QColor(255, 255, 255),  # 亮白色
    }

    def __init__(self):
        # ANSI转义序列正则表达式（更全面的匹配）
        self.ansi_escape = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07)"
        )

        # SGR (Select Graphic Rendition) 参数正则表达式
        self.sgr_pattern = re.compile(r"\x1B\[([0-9;]*)m")

        # OSC (Operating System Command) 序列正则表达式
        self.osc_pattern = re.compile(r"\x1B\]([0-9]+);([^\x07]*)\x07")

        # 损坏的ANSI序列修复模式（处理转义字符丢失的情况）
        self.broken_ansi_pattern = re.compile(r"\[\]([0-9;]*)m")

        # 当前文本格式状态
        self.reset_format()

    def reset_format(self):
        """重置格式状态"""
        self.current_format = QTextCharFormat()
        self.current_format.setForeground(QColor(255, 255, 255))  # 默认白色文字
        self.current_format.setBackground(QColor(30, 30, 30))  # 默认深色背景

    def parse_sgr_codes(self, codes_str: str) -> QTextCharFormat:
        """解析SGR代码并返回对应的文本格式"""
        if not codes_str:
            codes = [0]  # 默认重置
        else:
            try:
                codes = [int(code) for code in codes_str.split(";") if code]
            except ValueError:
                codes = [0]

        format_copy = QTextCharFormat(self.current_format)

        i = 0
        while i < len(codes):
            code = codes[i]

            if code == 0:  # 重置所有格式
                format_copy = QTextCharFormat()
                format_copy.setForeground(QColor(255, 255, 255))
                format_copy.setBackground(QColor(30, 30, 30))

            elif code == 1:  # 粗体
                format_copy.setFontWeight(QFont.Weight.Bold)

            elif code == 2:  # 暗淡
                format_copy.setFontWeight(QFont.Weight.Light)

            elif code == 3:  # 斜体
                format_copy.setFontItalic(True)

            elif code == 4:  # 下划线
                format_copy.setFontUnderline(True)

            elif code == 7:  # 反转颜色
                fg = format_copy.foreground().color()
                bg = format_copy.background().color()
                format_copy.setForeground(bg)
                format_copy.setBackground(fg)

            elif code == 22:  # 正常强度（取消粗体/暗淡）
                format_copy.setFontWeight(QFont.Weight.Normal)

            elif code == 23:  # 取消斜体
                format_copy.setFontItalic(False)

            elif code == 24:  # 取消下划线
                format_copy.setFontUnderline(False)

            elif code == 27:  # 取消反转
                # 这里需要恢复到默认颜色，简化处理
                format_copy.setForeground(QColor(255, 255, 255))
                format_copy.setBackground(QColor(30, 30, 30))

            elif 30 <= code <= 37:  # 前景色
                if code in self.ANSI_COLORS:
                    format_copy.setForeground(self.ANSI_COLORS[code])

            elif code == 39:  # 默认前景色
                format_copy.setForeground(QColor(255, 255, 255))

            elif 40 <= code <= 47:  # 背景色
                bg_code = code - 10  # 转换为前景色代码
                if bg_code in self.ANSI_COLORS:
                    format_copy.setBackground(self.ANSI_COLORS[bg_code])

            elif code == 49:  # 默认背景色
                format_copy.setBackground(QColor(30, 30, 30))

            elif 90 <= code <= 97:  # 亮前景色
                if code in self.ANSI_COLORS:
                    format_copy.setForeground(self.ANSI_COLORS[code])

            elif 100 <= code <= 107:  # 亮背景色
                bg_code = code - 10  # 转换为前景色代码
                if bg_code in self.ANSI_COLORS:
                    format_copy.setBackground(self.ANSI_COLORS[bg_code])

            i += 1

        self.current_format = format_copy
        return format_copy

    def parse_text(self, text: str) -> List[Tuple[str, QTextCharFormat]]:
        """
        解析包含ANSI转义序列的文本
        返回 (文本片段, 格式) 的列表
        """
        # 首先修复损坏的ANSI序列（将 []32m 转换为 \x1b[32m）
        text = self.broken_ansi_pattern.sub(lambda m: f"\x1b[{m.group(1)}m", text)

        # 移除OSC序列（如窗口标题设置）
        text = self.osc_pattern.sub("", text)

        result = []
        last_end = 0

        # 查找所有SGR序列
        for match in self.sgr_pattern.finditer(text):
            start, end = match.span()

            # 添加SGR序列之前的文本（使用当前格式）
            if start > last_end:
                plain_text = text[last_end:start]
                if plain_text:
                    result.append((plain_text, QTextCharFormat(self.current_format)))

            # 解析SGR代码并更新格式
            codes_str = match.group(1)
            self.parse_sgr_codes(codes_str)

            last_end = end

        # 添加剩余的文本
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                result.append((remaining_text, QTextCharFormat(self.current_format)))

        return result

    def strip_ansi(self, text: str) -> str:
        """移除文本中的所有ANSI转义序列"""
        # 先修复损坏的ANSI序列
        text = self.broken_ansi_pattern.sub(lambda m: f"\x1b[{m.group(1)}m", text)
        # 移除OSC序列
        text = self.osc_pattern.sub("", text)
        # 移除其他ANSI序列
        return self.ansi_escape.sub("", text)

    def has_ansi(self, text: str) -> bool:
        """检查文本是否包含ANSI转义序列"""
        return bool(
            self.ansi_escape.search(text) or self.broken_ansi_pattern.search(text)
        )


class ANSITextProcessor:
    """ANSI文本处理器，用于与QTextEdit集成"""

    def __init__(self):
        self.parser = ANSIParser()

    def process_text(self, text: str) -> List[Tuple[str, QTextCharFormat]]:
        """处理文本并返回格式化的片段"""
        return self.parser.parse_text(text)

    def reset(self):
        """重置解析器状态"""
        self.parser.reset_format()

    def strip_ansi(self, text: str) -> str:
        """移除ANSI转义序列"""
        return self.parser.strip_ansi(text)

    def has_ansi(self, text: str) -> bool:
        """检查是否包含ANSI转义序列"""
        return self.parser.has_ansi(text)

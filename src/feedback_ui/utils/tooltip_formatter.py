# feedback_ui/utils/tooltip_formatter.py


class TooltipFormatter:
    """
    工具提示格式化工具类
    Utility class for formatting tooltip text
    """

    @staticmethod
    def format_text(text: str, max_chars_per_line: int = 40) -> str:
        """
        格式化工具提示文本，确保长文本能够正确换行显示
        Format tooltip text to ensure proper line wrapping for long text

        Args:
            text (str): 原始文本
            max_chars_per_line (int): 每行最大字符数，默认40

        Returns:
            str: 格式化后的文本，包含适当的换行符
        """
        if not text or not isinstance(text, str):
            return text or ""

        # 如果文本长度小于等于最大字符数，直接返回
        if len(text) <= max_chars_per_line:
            return text

        # 将长文本分割成多行
        lines = []
        current_line = ""

        # 定义断行符号（优先在这些位置断行）
        break_chars = [
            " ",
            "，",
            "。",
            "！",
            "？",
            ",",
            ".",
            "!",
            "?",
            ";",
            "；",
            ":",
            "：",
        ]

        i = 0
        while i < len(text):
            char = text[i]
            current_line += char

            # 检查当前行长度
            if len(current_line) >= max_chars_per_line:
                # 尝试在合适的位置断行
                if char in break_chars:
                    lines.append(current_line.strip())
                    current_line = ""
                else:
                    # 向前查找最近的断行符
                    break_pos = -1
                    for j in range(
                        len(current_line) - 1, max(0, len(current_line) - 10), -1
                    ):
                        if current_line[j] in break_chars:
                            break_pos = j
                            break

                    if break_pos > 0:
                        # 在找到的位置断行
                        lines.append(current_line[: break_pos + 1].strip())
                        current_line = current_line[break_pos + 1 :]
                    elif len(current_line) > max_chars_per_line + 8:
                        # 强制断行（避免行过长）
                        lines.append(current_line.strip())
                        current_line = ""

            i += 1

        # 添加剩余的文本
        if current_line.strip():
            lines.append(current_line.strip())

        # 用换行符连接所有行，并移除空行
        result_lines = [line for line in lines if line]
        return "\n".join(result_lines)

    @staticmethod
    def format_for_canned_response(text: str) -> str:
        """
        专门为常用语格式化工具提示文本
        Format tooltip text specifically for canned responses

        Args:
            text (str): 常用语文本

        Returns:
            str: 格式化后的工具提示文本
        """
        # 常用语使用稍微宽松一点的行长度
        return TooltipFormatter.format_text(text, max_chars_per_line=45)

    @staticmethod
    def set_tooltip_for_widget(widget, text: str):
        """
        为widget设置格式化的工具提示
        Set formatted tooltip for a widget

        Args:
            widget: 要设置工具提示的widget
            text (str): 工具提示文本
        """
        if widget and text:
            formatted_text = TooltipFormatter.format_for_canned_response(text)
            widget.setToolTip(formatted_text)

"""
PowerShell输出格式化器
PowerShell Output Formatter

优化PowerShell命令输出的显示格式，提供更友好的文件大小显示。
"""

import re
from typing import List, Tuple


class PowerShellFormatter:
    """PowerShell输出格式化器"""

    def __init__(self):
        # 文件列表输出的正则表达式
        self.file_list_pattern = re.compile(
            r"^([d\-][a-z\-]{4})\s+(\d{4}/\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})\s+(\d+)?\s+(.+)$"
        )

    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小为人类可读格式"""
        if size_bytes == 0:
            return "0 B"

        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0

        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1

        if unit_index == 0:
            return f"{int(size)} {units[unit_index]}"
        else:
            return f"{size:.1f} {units[unit_index]}"

    def format_file_list_line(self, line: str) -> str:
        """格式化文件列表行"""
        match = self.file_list_pattern.match(line.strip())
        if not match:
            return line  # 不匹配的行保持原样

        mode, date, time, size_str, name = match.groups()

        # 格式化文件大小
        if size_str:
            size_bytes = int(size_str)
            formatted_size = self.format_file_size(size_bytes)
            # 右对齐文件大小，固定宽度
            size_display = f"{formatted_size:>8}"
        else:
            # 目录没有大小
            size_display = "        "  # 8个空格

        # 重新组装行
        return f"{mode}  {date}  {time}  {size_display}  {name}"

    def format_output(self, text: str) -> str:
        """格式化整个输出文本"""
        lines = text.split("\n")
        formatted_lines = []

        for line in lines:
            if line.strip():
                formatted_line = self.format_file_list_line(line)
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def should_format_output(self, text: str) -> bool:
        """判断是否应该格式化输出（检测是否为文件列表）"""
        lines = text.strip().split("\n")

        # 检查是否包含典型的PowerShell文件列表标题
        header_patterns = [
            r"Mode\s+LastWriteTime\s+Length\s+Name",
            r"----\s+-------------\s+------\s+----",
        ]

        for line in lines[:5]:  # 只检查前5行
            for pattern in header_patterns:
                if re.search(pattern, line):
                    return True

        return False


# 全局格式化器实例
_formatter = PowerShellFormatter()


def format_powershell_output(text: str) -> str:
    """格式化PowerShell输出的便捷函数"""
    if _formatter.should_format_output(text):
        return _formatter.format_output(text)
    return text


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小的便捷函数"""
    return _formatter.format_file_size(size_bytes)


# 测试函数
def test_formatter():
    """测试格式化器"""
    test_input = """Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----            2025/6/6    14:02                .cursor
-a---            2025/6/8     2:25          14505 安装与配置指南.md
-a---            2025/6/8     2:25          12578 功能说明.md
-a---            2025/6/9    21:58         178152 uv.lock"""

    print("原始输出:")
    print(test_input)
    print("\n格式化后:")
    print(format_powershell_output(test_input))


if __name__ == "__main__":
    test_formatter()

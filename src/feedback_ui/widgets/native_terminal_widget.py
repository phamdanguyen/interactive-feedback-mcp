"""
原生终端组件
Native Terminal Widget

提供类似原生终端的交互体验，支持直接在输出区域内输入命令。
Provides native terminal-like interaction experience with direct input in output area.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor, QKeyEvent, QKeySequence
from PySide6.QtWidgets import QTextEdit

from ..utils.ansi_parser import ANSITextProcessor
from ..utils.terminal_styles import apply_terminal_style


class NativeTerminalWidget(QTextEdit):
    """原生终端组件，支持直接在输出区域内输入"""

    command_entered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        # 基本设置
        self.setAcceptRichText(True)  # 启用富文本支持ANSI解析

        # 初始化ANSI处理器
        self.ansi_processor = ANSITextProcessor()

        # 应用统一的终端样式
        apply_terminal_style(self)

        # 命令历史
        self.command_history = []
        self.history_index = -1

        # 当前命令行状态
        self.current_line_start = 0  # 当前输入行的开始位置
        self.prompt_length = 0  # 提示符长度
        self.is_input_mode = False  # 是否处于输入模式

    def append_ansi_text(self, text: str):
        """添加支持ANSI转义序列的文本"""
        if not text:
            return

        # 暂时禁用输入模式
        was_input_mode = self.is_input_mode
        self.is_input_mode = False

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 检查是否包含ANSI序列
        if self.ansi_processor.has_ansi(text):
            # 解析ANSI序列并应用格式
            segments = self.ansi_processor.process_text(text)

            for text_segment, format_obj in segments:
                if text_segment:  # 只插入非空文本
                    cursor.insertText(text_segment, format_obj)
        else:
            # 普通文本，使用默认格式
            cursor.insertText(text)

        self.setTextCursor(cursor)
        self.ensureCursorVisible()

        # 检查是否包含提示符，如果是则进入输入模式
        # 支持更多提示符格式
        prompt_patterns = ["$ ", "> ", "PS> ", "PS ", "# ", "C:\\", "D:\\"]
        has_prompt = any(pattern in text for pattern in prompt_patterns)

        if has_prompt and not text.strip().endswith("\n"):
            self._enter_input_mode()
        else:
            self.is_input_mode = was_input_mode

    def _enter_input_mode(self):
        """进入输入模式"""
        self.is_input_mode = True
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 记录当前行的开始位置和提示符长度
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        line_start = cursor.position()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 查找提示符的结束位置
        line_text = cursor.block().text()
        prompt_end = -1

        # 支持更多提示符格式
        prompt_patterns = ["PS> ", "PS ", "$ ", "> ", "# "]

        # 特殊处理Windows路径提示符（如 C:\> 或 D:\>）
        import re

        windows_prompt = re.search(r"[A-Z]:\\[^>]*>", line_text)
        if windows_prompt:
            prompt_end = windows_prompt.end()
        else:
            # 查找标准提示符
            for prompt in prompt_patterns:
                pos = line_text.rfind(prompt)
                if pos >= 0:
                    prompt_end = pos + len(prompt)
                    break

        if prompt_end >= 0:
            self.current_line_start = line_start + prompt_end
            self.prompt_length = prompt_end
        else:
            self.current_line_start = cursor.position()
            self.prompt_length = 0

        # 将光标移动到输入位置
        cursor.setPosition(self.current_line_start)
        self.setTextCursor(cursor)

        # 激活光标并确保可见
        self._activate_cursor()

    def keyPressEvent(self, event: QKeyEvent):
        """处理键盘事件"""
        if not self.is_input_mode:
            # 非输入模式，只允许滚动和复制
            if event.key() in [
                Qt.Key.Key_Up,
                Qt.Key.Key_Down,
                Qt.Key.Key_PageUp,
                Qt.Key.Key_PageDown,
            ]:
                super().keyPressEvent(event)
            elif event.matches(QKeySequence.StandardKey.Copy):
                super().keyPressEvent(event)
            return

        cursor = self.textCursor()

        # 处理特殊按键
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # 回车键：执行命令
            self._execute_current_command()
            return

        elif event.key() == Qt.Key.Key_Up:
            # 上箭头：历史命令（上一个）
            self._navigate_history(-1)
            return

        elif event.key() == Qt.Key.Key_Down:
            # 下箭头：历史命令（下一个）
            self._navigate_history(1)
            return

        elif event.key() == Qt.Key.Key_Left:
            # 左箭头：限制在输入区域内
            if cursor.position() > self.current_line_start:
                super().keyPressEvent(event)
            return

        elif event.key() == Qt.Key.Key_Home:
            # Home键：移动到输入区域开始
            cursor.setPosition(self.current_line_start)
            self.setTextCursor(cursor)
            return

        elif event.key() == Qt.Key.Key_Backspace:
            # 退格键：限制在输入区域内
            if cursor.position() > self.current_line_start:
                super().keyPressEvent(event)
            return

        elif event.key() == Qt.Key.Key_Delete:
            # 删除键：只在输入区域内有效
            if cursor.position() >= self.current_line_start:
                super().keyPressEvent(event)
            return

        # 其他可打印字符
        elif event.text() and event.text().isprintable():
            # 确保光标在输入区域内
            if cursor.position() < self.current_line_start:
                cursor.setPosition(self.current_line_start)
                self.setTextCursor(cursor)
            super().keyPressEvent(event)

        # Ctrl+C 等组合键
        elif event.matches(QKeySequence.StandardKey.Copy) or event.matches(
            QKeySequence.StandardKey.Paste
        ):
            super().keyPressEvent(event)

    def _execute_current_command(self):
        """执行当前命令"""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 获取当前行的命令部分
        line_text = cursor.block().text()
        if self.prompt_length < len(line_text):
            command = line_text[self.prompt_length :].strip()
        else:
            command = ""

        # 添加到历史记录
        if command and (
            not self.command_history or self.command_history[-1] != command
        ):
            self.command_history.append(command)
        self.history_index = len(self.command_history)

        # 添加换行
        cursor.insertText("\n")
        self.setTextCursor(cursor)

        # 退出输入模式
        self.is_input_mode = False

        # 发送命令（包括空命令，因为空回车在终端中也是有意义的）
        self.command_entered.emit(command)

    def _navigate_history(self, direction: int):
        """浏览命令历史"""
        if not self.command_history:
            return

        # 更新历史索引
        new_index = self.history_index + direction
        if new_index < 0:
            new_index = 0
        elif new_index >= len(self.command_history):
            new_index = len(self.command_history)

        self.history_index = new_index

        # 获取历史命令
        if self.history_index < len(self.command_history):
            command = self.command_history[self.history_index]
        else:
            command = ""

        # 替换当前输入
        cursor = self.textCursor()
        cursor.setPosition(self.current_line_start)
        cursor.movePosition(
            QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor
        )
        cursor.removeSelectedText()
        cursor.insertText(command)
        self.setTextCursor(cursor)

    def _activate_cursor(self):
        """激活光标，使其可见并闪动"""
        # 确保组件获得焦点
        self.setFocus(Qt.FocusReason.OtherFocusReason)

        # 确保光标可见
        self.ensureCursorVisible()

        # 强制刷新显示
        self.update()

        # 确保光标闪动
        self.setCursorWidth(2)  # 设置光标宽度，使其更明显

    def reset_ansi_state(self):
        """重置ANSI解析器状态"""
        self.ansi_processor.reset()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        super().mousePressEvent(event)

        # 如果在输入模式下点击了非输入区域，将光标移回输入区域
        if self.is_input_mode:
            cursor = self.textCursor()
            if cursor.position() < self.current_line_start:
                cursor.setPosition(self.current_line_start)
                self.setTextCursor(cursor)

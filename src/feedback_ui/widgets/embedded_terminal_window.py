"""
嵌入式终端窗口组件
Embedded Terminal Window Component

提供一个独立的置顶终端窗口，支持PowerShell交互和命令执行。
Provides an independent topmost terminal window with PowerShell interaction and command execution.
"""

import os
from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QTextCursor, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QToolBar,
    QApplication,
)

from ..utils.settings_manager import SettingsManager
from ..utils.terminal_manager import TerminalManager
from ..utils.terminal_styles import apply_terminal_window_style
from .native_terminal_widget import NativeTerminalWidget


# 传统模式组件已移除，现在只使用NativeTerminalWidget


class EmbeddedTerminalWindow(QMainWindow):
    """嵌入式终端窗口"""

    def __init__(
        self, working_directory: str = None, terminal_type: str = None, parent=None
    ):
        super().__init__(parent)
        self.working_directory = working_directory or os.getcwd()
        self.terminal_type = terminal_type or "powershell"  # 默认使用PowerShell
        self.process = None
        self.settings_manager = SettingsManager(self)
        self.terminal_manager = TerminalManager()

        self._setup_window()
        self._create_ui()
        self._setup_process()
        self._load_settings()

    def _setup_window(self):
        """设置窗口属性"""
        # 根据终端类型设置窗口标题
        terminal_names = {
            "powershell": "PowerShell",
            "gitbash": "Git Bash",
            "cmd": "Command Prompt",
        }
        terminal_name = terminal_names.get(self.terminal_type, "Terminal")
        self.setWindowTitle(f"嵌入式终端 - {terminal_name} - Interactive Feedback MCP")
        self.setMinimumSize(800, 600)

        # 设置窗口置顶，并防止跟随父窗口最小化
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

        # 设置窗口属性，使其独立于父窗口状态
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)

        # 应用原生终端窗口样式
        apply_terminal_window_style(self)

        # 设置窗口图标（如果有的话）
        try:
            from ..main_window import FeedbackUI

            if hasattr(FeedbackUI, "_setup_window_icon"):
                # 复用主窗口的图标设置逻辑
                pass
        except:
            pass

    def _create_ui(self):
        """创建用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 创建工具栏
        self._create_toolbar()

        # 原生终端模式：只有一个输出/输入区域
        self.output_widget = NativeTerminalWidget()
        self.output_widget.command_entered.connect(self._execute_command)
        main_layout.addWidget(self.output_widget)

        # 原生模式下不需要传统的输入框和提示符
        self.input_widget = None
        self.prompt_label = None

        # 自动聚焦到输出区域
        self.output_widget.setFocus()

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # 清屏按钮
        clear_action = QAction("清屏", self)
        clear_action.triggered.connect(self._clear_output)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        # 复制输出按钮
        copy_action = QAction("复制输出", self)
        copy_action.triggered.connect(self._copy_output)
        toolbar.addAction(copy_action)

        toolbar.addSeparator()

        # 重启终端按钮
        restart_action = QAction("重启终端", self)
        restart_action.triggered.connect(self._restart_terminal)
        toolbar.addAction(restart_action)

    def _setup_process(self):
        """设置QProcess"""
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.readyReadStandardError.connect(self._read_error)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)

        # 启动终端
        self._start_terminal()

    def _start_terminal(self):
        """根据终端类型启动对应的终端进程"""
        try:
            # 获取终端管理器
            from ..utils.terminal_manager import get_terminal_manager

            terminal_manager = get_terminal_manager()

            # 获取终端命令
            terminal_command = terminal_manager.get_terminal_command(self.terminal_type)
            if not terminal_command:
                self._append_output(
                    f"错误：未找到可用的{self.terminal_type}程序\n", is_error=True
                )
                return

            # 设置工作目录
            self.process.setWorkingDirectory(self.working_directory)

            # 获取启动参数并根据终端类型优化
            args = terminal_manager.get_terminal_args(self.terminal_type)

            # 为不同终端设置最佳编码和显示参数
            if self.terminal_type == "powershell":
                # PowerShell: 设置UTF-8编码
                args = [
                    "-NoLogo",
                    "-NoExit",
                    "-Command",
                    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                    + "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
                    + "chcp 65001 | Out-Null",
                ]
            elif self.terminal_type == "gitbash":
                # Git Bash: 简化启动，使用环境变量设置
                args = ["--login", "-i"]
            elif self.terminal_type == "cmd":
                # CMD: 设置UTF-8编码页
                args = ["/k", "chcp 65001 >nul"]

            # 启动终端
            self.process.start(terminal_command, args)

            if self.process.waitForStarted(3000):
                terminal_names = {
                    "powershell": "PowerShell",
                    "gitbash": "Git Bash",
                    "cmd": "Command Prompt",
                }
                terminal_name = terminal_names.get(self.terminal_type, "Terminal")
                self._append_output(
                    f"{terminal_name}已启动 - 工作目录: {self.working_directory}\n"
                )

                # 设置初始目录和环境（根据终端类型使用不同命令）
                cd_command = terminal_manager.get_working_directory_command(
                    self.terminal_type, self.working_directory
                )

                # 为Git Bash批量设置环境，减少显示的命令数量
                if self.terminal_type == "gitbash":
                    # 将所有设置命令合并为一个，用分号分隔
                    batch_command = (
                        f"{cd_command}; "
                        "export FORCE_COLOR=1; "
                        "export CLICOLOR=1; "
                        "export TERM=xterm-256color; "
                        "export LS_COLORS='di=1;34:ln=1;36:so=1;35:pi=1;33:ex=1;32:bd=1;33:cd=1;33:su=1;31:sg=1;31:tw=1;34:ow=1;34'; "
                        "alias ls='ls --color=always'; "
                        "alias ll='ls -la --color=always'; "
                        "alias dir='ls --color=always'; "
                        "clear"  # 清屏，只显示最终的提示符
                    )
                    self._execute_command(batch_command)
                else:
                    # 其他终端使用原来的方式
                    self._execute_command(cd_command)
            else:
                self._append_output(
                    f"错误：无法启动{self.terminal_type}进程\n", is_error=True
                )

        except Exception as e:
            self._append_output(f"启动终端时发生错误: {e}\n", is_error=True)

    # 移除重复的检测逻辑，使用TerminalManager统一管理

    def _execute_command(self, command: str):
        """执行命令"""
        if not self.process or self.process.state() != QProcess.ProcessState.Running:
            self._append_output("错误：终端进程未运行\n", is_error=True)
            return

        # 发送命令到终端
        command_with_newline = command + "\n"
        self.process.write(command_with_newline.encode("utf-8"))

    def _decode_terminal_output(self, data_bytes: bytes) -> str:
        """智能解码终端输出，尝试多种编码，保护ANSI转义序列"""
        # 首先尝试UTF-8解码，这对ANSI序列最友好
        try:
            text = data_bytes.decode("utf-8", errors="replace")
            # 检查是否包含ANSI转义序列的标志
            if b"\x1b" in data_bytes or b"\033" in data_bytes:
                # 包含转义序列，优先使用UTF-8
                return text
        except:
            pass

        # 尝试其他编码
        encodings = ["utf-8", "gbk", "cp936", "cp1252", "latin1"]

        for encoding in encodings:
            try:
                text = data_bytes.decode(encoding, errors="replace")
                # 检查解码结果是否合理（没有太多替换字符）
                if text.count("\ufffd") / max(len(text), 1) < 0.1:  # 替换字符少于10%
                    return text
            except UnicodeDecodeError:
                continue

        # 如果所有编码都失败，使用utf-8并保留错误字符
        return data_bytes.decode("utf-8", errors="replace")

    def _read_output(self):
        """读取标准输出"""
        data = self.process.readAllStandardOutput()
        text = self._decode_terminal_output(data.data())
        self._append_output(text)

    def _read_error(self):
        """读取错误输出"""
        data = self.process.readAllStandardError()
        text = self._decode_terminal_output(data.data())
        self._append_output(text, is_error=True)

    def _append_output(
        self, text: str, is_error: bool = False, is_command: bool = False
    ):
        """添加输出到显示区域，支持ANSI转义序列"""
        if not text:
            return

        # 检查是否包含ANSI转义序列
        has_ansi = self.output_widget.ansi_processor.has_ansi(text)

        # 如果包含ANSI序列，优先使用ANSI解析器（即使是错误输出）
        if has_ansi:
            self.output_widget.append_ansi_text(text)
        elif is_error or is_command:
            # 对于不含ANSI的错误和命令文本，使用传统的颜色处理
            cursor = self.output_widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            # 设置文本颜色
            if is_error:
                self.output_widget.setTextColor(Qt.GlobalColor.red)
            elif is_command:
                self.output_widget.setTextColor(Qt.GlobalColor.yellow)

            cursor.insertText(text)
            self.output_widget.setTextCursor(cursor)
            self.output_widget.ensureCursorVisible()
        else:
            # 对于普通输出，使用ANSI解析
            self.output_widget.append_ansi_text(text)

        # 如果输出包含提示符，自动激活光标
        if (
            hasattr(self.output_widget, "_activate_cursor")
            and hasattr(self.output_widget, "is_input_mode")
            and self.output_widget.is_input_mode
        ):
            # 延迟激活光标，确保文本已完全显示
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, self.output_widget._activate_cursor)

    def _process_finished(self, exit_code):
        """进程结束处理"""
        self._append_output(f"\n进程已结束 (退出代码: {exit_code})\n", is_error=True)

    def _process_error(self, error):
        """进程错误处理"""
        self._append_output(f"进程错误: {error}\n", is_error=True)

    def _clear_output(self):
        """清屏"""
        self.output_widget.clear()
        # 重置ANSI解析器状态
        self.output_widget.reset_ansi_state()

    def _copy_output(self):
        """复制输出到剪贴板"""
        text = self.output_widget.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self._append_output("输出已复制到剪贴板\n")

    def _restart_terminal(self):
        """重启终端"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(3000)

        self._clear_output()
        self._start_terminal()

    def _load_settings(self):
        """加载设置"""
        # 加载窗口大小和位置
        geometry = self.settings_manager.get_terminal_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)

    def _save_settings(self):
        """保存设置"""
        # 保存窗口大小和位置
        self.settings_manager.set_terminal_window_geometry(self.saveGeometry())

    def closeEvent(self, event):
        """窗口关闭事件"""
        self._save_settings()

        # 终止进程
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(3000)

        super().closeEvent(event)

    def show_and_focus(self):
        """显示窗口并获取焦点"""
        self.show()
        self.raise_()
        self.activateWindow()
        # 聚焦到原生终端区域并激活光标
        self.output_widget.setFocus()
        if hasattr(self.output_widget, "_activate_cursor"):
            self.output_widget._activate_cursor()

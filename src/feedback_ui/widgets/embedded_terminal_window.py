"""
嵌入式终端窗口组件
Embedded Terminal Window Component

提供一个独立的置顶终端窗口，支持PowerShell交互和命令执行。
Provides an independent topmost terminal window with PowerShell interaction and command execution.
"""

import os
import sys
from typing import Optional

from PySide6.QtCore import QProcess, QTimer, Qt, Signal, QIODevice
from PySide6.QtGui import QFont, QTextCursor, QKeySequence, QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QToolBar,
    QApplication,
    QMessageBox,
    QSplitter,
)

from ..utils.settings_manager import SettingsManager


class TerminalOutputWidget(QTextEdit):
    """终端输出显示组件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(False)

        # 设置终端字体
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # 设置样式
        self.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                selection-background-color: #264f78;
            }
        """
        )


class TerminalInputWidget(QLineEdit):
    """终端输入组件"""

    command_entered = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.command_history = []
        self.history_index = -1

        # 设置终端字体
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # 设置样式
        self.setStyleSheet(
            """
            QLineEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3c3c3c;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
        """
        )

        self.returnPressed.connect(self._on_return_pressed)

    def _on_return_pressed(self):
        """处理回车键按下"""
        command = self.text().strip()
        if command:
            self.command_history.append(command)
            self.history_index = len(self.command_history)
            self.command_entered.emit(command)
        self.clear()

    def keyPressEvent(self, event):
        """处理特殊按键"""
        if event.key() == Qt.Key.Key_Up:
            self._navigate_history(-1)
        elif event.key() == Qt.Key.Key_Down:
            self._navigate_history(1)
        else:
            super().keyPressEvent(event)

    def _navigate_history(self, direction):
        """导航命令历史"""
        if not self.command_history:
            return

        self.history_index += direction
        self.history_index = max(0, min(self.history_index, len(self.command_history)))

        if self.history_index < len(self.command_history):
            self.setText(self.command_history[self.history_index])
        else:
            self.clear()


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

        # 设置窗口置顶
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowCloseButtonHint
        )

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

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 输出区域
        self.output_widget = TerminalOutputWidget()
        splitter.addWidget(self.output_widget)

        # 输入区域容器
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)

        # 提示符标签 - 根据终端类型设置
        prompt_text = {"powershell": "PS>", "gitbash": "$", "cmd": ">"}.get(
            self.terminal_type, "PS>"
        )

        self.prompt_label = QPushButton(prompt_text)
        self.prompt_label.setEnabled(False)
        self.prompt_label.setMaximumWidth(40)
        self.prompt_label.setStyleSheet(
            """
            QPushButton {
                background-color: #1e1e1e;
                color: #00ff00;
                border: 1px solid #3c3c3c;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 10pt;
            }
        """
        )

        # 输入框
        self.input_widget = TerminalInputWidget()
        self.input_widget.command_entered.connect(self._execute_command)

        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.input_widget)

        splitter.addWidget(input_container)

        # 设置分割器比例
        splitter.setSizes([500, 100])
        splitter.setChildrenCollapsible(False)

        main_layout.addWidget(splitter)

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

            # 获取启动参数
            args = terminal_manager.get_terminal_args(self.terminal_type)

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

                # 设置初始目录（根据终端类型使用不同命令）
                cd_command = terminal_manager.get_working_directory_command(
                    self.terminal_type, self.working_directory
                )
                self._execute_command(cd_command, add_to_history=False)
            else:
                self._append_output(
                    f"错误：无法启动{self.terminal_type}进程\n", is_error=True
                )

        except Exception as e:
            self._append_output(f"启动终端时发生错误: {e}\n", is_error=True)

    def _detect_terminal_command(self) -> str:
        """检测可用的PowerShell命令，优先使用高版本"""
        if os.name == "nt":  # Windows
            # 按优先级顺序检测PowerShell
            powershell_candidates = [
                # PowerShell 7+ 常见安装路径
                r"C:\Program Files\PowerShell\7\pwsh.exe",
                r"C:\Program Files\PowerShell\6\pwsh.exe",
                # 通过PATH查找pwsh
                "pwsh.exe",
                # Windows PowerShell 5.1
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                # 通过PATH查找powershell
                "powershell.exe",
            ]

            for candidate in powershell_candidates:
                try:
                    if os.path.isabs(candidate):
                        # 绝对路径，直接检查文件是否存在
                        if os.path.isfile(candidate):
                            version_info = self._get_powershell_version(candidate)
                            print(
                                f"DEBUG: 找到PowerShell: {candidate}, 版本: {version_info}",
                                file=sys.stderr,
                            )
                            return candidate
                    else:
                        # 相对路径，通过where命令查找
                        import subprocess

                        result = subprocess.run(
                            ["where", candidate],
                            capture_output=True,
                            text=True,
                            shell=True,
                        )
                        if result.returncode == 0:
                            found_path = result.stdout.strip().split("\n")[
                                0
                            ]  # 取第一个结果
                            version_info = self._get_powershell_version(found_path)
                            print(
                                f"DEBUG: 找到PowerShell: {found_path}, 版本: {version_info}",
                                file=sys.stderr,
                            )
                            return found_path
                except Exception as e:
                    print(f"DEBUG: 检测 {candidate} 时出错: {e}", file=sys.stderr)
                    continue

        print("DEBUG: 未找到任何可用的PowerShell程序", file=sys.stderr)
        return ""

    def _get_powershell_version(self, powershell_path: str) -> str:
        """获取PowerShell版本信息"""
        try:
            import subprocess

            result = subprocess.run(
                [powershell_path, "-Command", "$PSVersionTable.PSVersion.ToString()"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return "未知版本"
        except Exception:
            return "版本检测失败"

    def _execute_command(self, command: str, add_to_history: bool = True):
        """执行命令"""
        if not self.process or self.process.state() != QProcess.ProcessState.Running:
            self._append_output("错误：终端进程未运行\n", is_error=True)
            return

        if add_to_history:
            self._append_output(f"PS> {command}\n", is_command=True)

        # 发送命令到PowerShell
        command_with_newline = command + "\n"
        self.process.write(command_with_newline.encode("utf-8"))

    def _read_output(self):
        """读取标准输出"""
        data = self.process.readAllStandardOutput()
        text = data.data().decode("utf-8", errors="ignore")
        self._append_output(text)

    def _read_error(self):
        """读取错误输出"""
        data = self.process.readAllStandardError()
        text = data.data().decode("utf-8", errors="ignore")
        self._append_output(text, is_error=True)

    def _append_output(
        self, text: str, is_error: bool = False, is_command: bool = False
    ):
        """添加输出到显示区域"""
        cursor = self.output_widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # 设置文本颜色
        if is_error:
            self.output_widget.setTextColor(Qt.GlobalColor.red)
        elif is_command:
            self.output_widget.setTextColor(Qt.GlobalColor.yellow)
        else:
            self.output_widget.setTextColor(Qt.GlobalColor.white)

        cursor.insertText(text)
        self.output_widget.setTextCursor(cursor)
        self.output_widget.ensureCursorVisible()

    def _process_finished(self, exit_code, exit_status):
        """进程结束处理"""
        self._append_output(f"\n进程已结束 (退出代码: {exit_code})\n", is_error=True)

    def _process_error(self, error):
        """进程错误处理"""
        self._append_output(f"进程错误: {error}\n", is_error=True)

    def _clear_output(self):
        """清屏"""
        self.output_widget.clear()

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
        self._start_powershell()

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
        self.input_widget.setFocus()

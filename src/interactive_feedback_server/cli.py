# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by pawa (https://github.com/pawaovo) with ideas from https://github.com/noopstudios/interactive-feedback-mcp
import os
import sys
import json
import tempfile
import subprocess
import base64
import uuid
import argparse
import threading
import atexit

# from typing import Annotated # Annotated 未在此文件中直接使用 (Annotated not directly used in this file)
from typing import (
    Dict,
    List,
    Any,
    Optional,
    Tuple,
    Union,
)  # 简化导入 (Simplified imports)

from fastmcp import FastMCP, Image
from pydantic import (
    Field,
)  # Field 由 FastMCP 内部使用 (Field is used internally by FastMCP)
from PySide6.QtCore import QEventLoop, QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QApplication, QPushButton, QMessageBox

# --- 关键修复：动态调整Python路径以支持绝对导入 ---
# 将项目根目录添加到sys.path，以解决相对导入问题
# This is a crucial fix to resolve relative import issues by adjusting the Python path
try:
    # 尝试正常的包内导入
    from . import constants
except ImportError:
    # 如果作为脚本运行，则动态添加父级目录
    # Fallback for when the script is run directly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../"))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# --- 现在使用绝对路径导入 ---
from src.managers.window_manager import WindowManager
from src.feedback_ui.main_window import FeedbackUI
from src.feedback_ui.utils.constants import FeedbackResult
from src.workers.feedback_worker import FeedbackWorker

# 全局变量，用于在主函数和工具函数之间共享核心组件
# Global variables to share core components between the main function and tool functions
window_manager: Optional[WindowManager] = None
mcp_instance: Optional[FastMCP] = None

# 服务启动时的基本信息打印可以保留，用于基本诊断
# Basic info print on server start can be kept for diagnostics
print(f"Server.py 启动 - Python解释器路径: {sys.executable}")
print(f"Server.py 当前工作目录: {os.getcwd()}")


mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")


def launch_feedback_ui(
    summary: str, predefined_options_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Launches the feedback UI as a separate process using its command-line entry point.
    Collects user input and returns it as a structured dictionary.

    通过命令行入口点将反馈UI作为独立进程启动。
    收集用户输入并将其作为结构化字典返回。
    """
    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp_file_path = tmp.name

        options_str = (
            "|||".join(predefined_options_list) if predefined_options_list else ""
        )

        # Build the argument list for the 'feedback-ui' command
        # This command is available after installing the package in editable mode.
        args_list = [
            "feedback-ui",
            "--prompt",
            summary,
            "--output-file",
            tmp_file_path,
            "--predefined-options",
            options_str,
        ]

        # Run the feedback-ui command
        process_result = subprocess.run(
            args_list,
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            close_fds=(
                os.name != "nt"
            ),  # close_fds is not supported on Windows when shell=False
            text=True,
            errors="ignore",
        )

        if process_result.returncode != 0:
            print(
                f"错误: 启动反馈UI (feedback-ui) 失败。返回码: {process_result.returncode}",
                file=sys.stderr,
            )
            print(
                f"(Error: Failed to launch feedback UI (feedback-ui). Return code: {process_result.returncode})",
                file=sys.stderr,
            )
            if process_result.stdout:
                print(f"UI STDOUT:\n{process_result.stdout}", file=sys.stderr)
            if process_result.stderr:
                print(f"UI STDERR:\n{process_result.stderr}", file=sys.stderr)
            raise Exception(
                f"启动反馈UI失败 (Failed to launch feedback UI): {process_result.returncode}. 详细信息请查看服务器日志 (Check server logs for details)."
            )

        with open(tmp_file_path, "r", encoding="utf-8") as f:
            ui_result_data = json.load(f)

        return ui_result_data

    except FileNotFoundError:
        print("错误: 'feedback-ui' 命令未找到。", file=sys.stderr)
        print("请确保项目已在可编辑模式下安装 (pip install -e .)", file=sys.stderr)
        print("(Error: 'feedback-ui' command not found.)", file=sys.stderr)
        print(
            "(Please ensure the project is installed in editable mode: pip install -e .)",
            file=sys.stderr,
        )
        raise
    except Exception as e:
        print(f"错误: 在 launch_feedback_ui 中发生异常: {e}", file=sys.stderr)
        print(f"(Error: Exception in launch_feedback_ui: {e})", file=sys.stderr)
        raise  # 重新抛出异常，让上层调用者知道发生了错误 (Re-throw exception for caller awareness)
    finally:
        # 确保临时文件在完成后被删除
        # Ensure the temporary file is deleted after completion
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError as e_unlink:
                print(
                    f"警告: 删除临时文件失败 '{tmp_file_path}': {e_unlink}",
                    file=sys.stderr,
                )
                print(
                    f"(Warning: Failed to delete temporary file '{tmp_file_path}': {e_unlink})",
                    file=sys.stderr,
                )


class McpServiceWorker(QObject):
    """后台运行 FastMCP 服务的 Worker"""

    def __init__(self, mcp_instance):
        super().__init__()
        self.mcp = mcp_instance

    def run_mcp(self):
        """启动 MCP 服务"""
        print("FastMCP 服务正在后台线程中启动...")
        try:
            self.mcp.run(transport="stdio")
            print("FastMCP 服务已停止。")
        except Exception as e:
            print(f"后台 MCP 服务出错: {e}", file=sys.stderr)


@mcp.tool()
def interactive_feedback(
    message: str = Field(
        description="The specific question for the user (给用户的具体问题)"
    ),
    predefined_options: Optional[List[str]] = Field(
        default=None, description="Predefined options for the user (用户的预定义选项)"
    ),
) -> Tuple[Union[str, Image], ...]:  # 返回字符串和/或 fastmcp.Image 对象的元组
    """
    通过应用内GUI请求用户的交互式反馈，并同步等待结果。
    此函数现在使用QEventLoop和后台工作线程来管理UI，而不是启动子进程。
    """
    global window_manager
    # --- 诊断代码 ---
    print("--- interactive_feedback 函数入口 ---")
    app_instance = QApplication.instance()
    print(f"QApplication.instance(): {app_instance}")
    print(f"window_manager 全局变量: {window_manager}")
    # --- 诊断代码结束 ---

    if app_instance is None or window_manager is None:
        # 如果Qt应用未运行或管理器不存在，则回退到旧的阻塞方法
        # Fallback to the old blocking method if Qt app is not running or manager is absent
        print("警告: Qt事件循环或WindowManager不可用，回退到旧的子进程模式。")
        ui_output_dict = launch_feedback_ui(message, predefined_options)
    else:
        # --- 新的、基于 threading.Event 的并发流程 ---
        task_id = str(uuid.uuid4())

        # 使用 Python 原生的 threading.Event 来实现跨线程的阻塞和唤醒
        # 这比在非GUI线程中使用嵌套的QEventLoop更健壮
        result_container = {}
        wake_up_event = threading.Event()

        # 1. 定义一个在UI提供反馈时被调用的槽函数
        #    这个槽函数将在GUI线程中被调用
        @Slot(str, dict)
        def on_feedback(feedback_task_id, data):
            if feedback_task_id == task_id:
                result_container["data"] = data
                wake_up_event.set()  # 唤醒被阻塞的MCP线程

        # 2. 连接信号和槽
        #    注意：我们需要在函数退出时断开连接，防止内存泄漏
        window_manager.feedback_received.connect(on_feedback)

        # 3. 直接调用 window_manager 的方法来创建UI
        #    因为 window_manager 属于GUI线程，Qt会自动处理跨线程调用
        initial_ui_data = {"prompt": message, "options": predefined_options}
        initial_ui_data_json = json.dumps(initial_ui_data)
        print(f"调用 window_manager.create_window 为任务 {task_id} 创建UI窗口...")
        window_manager.create_window(task_id, initial_ui_data_json)

        # 关键点：确保Qt事件循环立即处理待处理事件
        print("正在处理Qt事件队列，确保窗口创建命令被执行...")
        QApplication.processEvents()
        print("Qt事件处理完成。窗口应当已创建。")

        # 4. 阻塞MCP线程，等待UI反馈
        #    设置一个超时以防止无限期等待
        print("MCP线程正在等待UI反馈...")
        wake_up_event.wait(timeout=300)  # 5分钟超时
        print("MCP线程已唤醒或超时。")

        # 5. 清理：断开信号连接
        window_manager.feedback_received.disconnect(on_feedback)

        ui_output_dict = result_container.get("data", {})

    # --- 从这里开始，代码与旧版本相同，处理来自UI的结果 ---
    processed_mcp_content: List[Union[str, Image]] = []

    if (
        ui_output_dict
        and "content" in ui_output_dict
        and isinstance(ui_output_dict["content"], list)
    ):
        ui_content_list = ui_output_dict.get("content", [])
        for item in ui_content_list:
            if not isinstance(item, dict):  # 跳过无效的项目 (Skip invalid items)
                print(f"警告: 无效的内容项格式: {item}", file=sys.stderr)
                print(
                    f"(Warning: Invalid content item format: {item})", file=sys.stderr
                )
                continue

            item_type = item.get("type")
            if item_type == "text":
                text_content = item.get("text", "")
                if text_content:  # 仅添加非空文本 (Only add non-empty text)
                    processed_mcp_content.append(text_content)
            elif item_type == "image":
                base64_data = item.get("data")
                mime_type = item.get("mimeType")
                if base64_data and mime_type:
                    try:
                        image_format_str = mime_type.split("/")[
                            -1
                        ].lower()  # 清晰的变量名并转小写
                        if image_format_str == "jpeg":
                            image_format_str = "jpg"  # fastmcp.Image 期望 'jpg'

                        image_bytes = base64.b64decode(base64_data)
                        mcp_image = Image(data=image_bytes, format=image_format_str)
                        processed_mcp_content.append(mcp_image)
                    except Exception as e:
                        print(f"错误 server.py: 处理图像失败: {e}", file=sys.stderr)
                        print(
                            f"(Error server.py: Failed to process image: {e})",
                            file=sys.stderr,
                        )
                        # 提供用户可见的失败消息 (Provide a user-facing message about the failure)
                        processed_mcp_content.append(
                            f"[图像处理失败 (Image processing failed): {mime_type or 'unknown type'}]"
                        )
            elif item_type == "file_reference":
                display_name = item.get("display_name", "")
                file_path = item.get("path", "")
                if display_name and file_path:
                    # 为MCP格式化文件引用信息 (Format file reference info for MCP)
                    file_info = f"引用文件 (Referenced File): {display_name} [路径 (Path): {file_path}]"
                    processed_mcp_content.append(file_info)
            else:
                print(f"警告: 未知的内容项类型: {item_type}", file=sys.stderr)
                print(
                    f"(Warning: Unknown content item type: {item_type})",
                    file=sys.stderr,
                )

    if not processed_mcp_content:
        # 如果没有提供或处理任何反馈，则返回清晰的消息 (Return a clear message if no feedback was provided or processed)
        return ("[用户未提供反馈 (User provided no feedback)]",)

    # 返回所有已处理内容项（文本和图像）的元组
    # Return a tuple of all processed content items (text and images)
    return tuple(processed_mcp_content)


def main():
    """主入口点：初始化并运行服务"""
    global window_manager, mcp_instance
    mcp_instance = mcp  # 将mcp实例赋给全局变量

    # 创建Qt应用程序实例
    app = QApplication(sys.argv)

    # === 添加测试窗口 ===
    test_button = QPushButton("测试UI (Test UI)")
    test_button.resize(200, 50)
    test_button.show()

    def on_test_button_clicked():
        print("测试按钮被点击")
        QMessageBox.information(None, "测试成功", "UI系统工作正常！")
        # 测试创建一个模拟的反馈窗口
        if window_manager:
            test_data = {"prompt": "这是一个测试提示", "options": ["选项1", "选项2"]}
            test_data_json = json.dumps(test_data)
            window_manager.create_window("test_task_id", test_data_json)

    test_button.clicked.connect(on_test_button_clicked)
    print("测试按钮已创建 - 如果您能看到一个按钮，说明Qt GUI环境正常工作")
    # === 测试窗口添加完成 ===

    # 创建并初始化窗口管理器
    window_manager = WindowManager()

    # 创建并启动后台MCP服务线程
    mcp_thread = QThread()
    mcp_worker = McpServiceWorker(mcp_instance)
    mcp_worker.moveToThread(mcp_thread)
    mcp_thread.started.connect(mcp_worker.run_mcp)
    mcp_thread.start()

    # 启动Qt事件循环
    # 注意：这将是一个阻塞调用，直到应用程序退出
    print("Qt事件循环已启动。MCP服务在后台运行。")
    app.exec()

    # 清理
    mcp_thread.quit()
    mcp_thread.wait()
    print("服务已关闭。")


if __name__ == "__main__":
    main()

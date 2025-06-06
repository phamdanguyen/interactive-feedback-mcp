"""
端到端测试脚本，用于验证重构后的并发UI架构。
此脚本将启动主服务，并模拟多个客户端并发调用 `interactive_feedback` 工具。
"""

import sys
import os
import threading
import time
import uuid
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, Slot, QObject, Signal, Qt

# --- 解决模块导入问题的关键代码 ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- 结束 ---

# 导入重构后的工具和主服务入口点
# 注意：我们需要确保在导入 `cli` 之前，PySide6 已被安装
from src.interactive_feedback_server.cli import (
    main as server_main,
    interactive_feedback,
)
from src.managers.window_manager import WindowManager


class WindowRequester(QObject):
    """一个简单的QObject，用于从工作线程发出信号，以线程安全的方式请求窗口创建。"""

    window_requested = Signal(dict, str)


# 全局变量
# Global variables
window_manager_instance: Optional[WindowManager] = None
app_instance: Optional[QApplication] = None
server_thread_instance: Optional[threading.Thread] = None


# --- 新的测试客户端 ---
# --- New Test Client ---
def client_thread_function(client_id: int, prompt: str, results: list):
    """
    模拟客户端调用，直接与 WindowManager 交互。
    Simulates a client call that interacts directly with the WindowManager.
    """
    global window_manager_instance
    print(f"[客户端线程-{client_id}] 正在准备调用...")

    if not window_manager_instance:
        print(f"[客户端线程-{client_id}] 错误: WindowManager 未初始化。")
        results[client_id] = {"error": "WindowManager not initialized"}
        return

    task_id = f"test_task_{client_id}_{uuid.uuid4()}"
    result = {}
    loop = QEventLoop()

    # 当此任务的反馈到达时，退出循环
    # This slot will exit the loop when feedback for this task arrives
    @Slot(str, dict)
    def on_feedback_received(received_task_id, data):
        nonlocal result
        if received_task_id == task_id:
            print(f"[客户端线程-{client_id}] 接收到反馈: {data}")
            result = data
            loop.quit()

    # 连接到 window_manager 的信号
    # Connect to the window_manager's signal
    window_manager_instance.feedback_received.connect(on_feedback_received)

    # 使用信号/槽机制来线程安全地请求窗口
    # Use a signal/slot mechanism to request window creation thread-safely
    requester = WindowRequester()
    # 必须使用 QueuedConnection，以确保 create_window 在 WindowManager 的线程中执行
    requester.window_requested.connect(
        window_manager_instance.create_window, Qt.ConnectionType.QueuedConnection
    )

    print(f"[客户端线程-{client_id}] 正在请求反馈 (任务ID: {task_id})...")
    initial_data = {"prompt": prompt, "options": []}

    # 发射信号来请求窗口创建
    requester.window_requested.emit(initial_data, task_id)

    # 等待反馈
    # Wait for feedback
    loop.exec()

    # 断开连接以避免重复处理
    # Disconnect to avoid handling signals multiple times
    try:
        window_manager_instance.feedback_received.disconnect(on_feedback_received)
    except (TypeError, RuntimeError) as e:
        # 在多线程环境中，信号可能已经断开，忽略此错误
        # In a multi-threaded environment, the signal might already be disconnected, ignore this error
        print(f"[客户端线程-{client_id}] 断开信号时发生非致命错误: {e}")

    results[client_id] = result
    print(f"[客户端线程-{client_id}] 完成。")


def start_server_in_background():
    """在后台线程中启动主服务器逻辑。"""
    global server_thread_instance
    server_thread_instance = threading.Thread(target=server_main, daemon=True)
    server_thread_instance.start()
    print("服务器线程已启动。等待其初始化...")
    # 给服务器一些时间来完全启动Qt应用和WindowManager
    # Give the server some time to fully initialize the Qt app and WindowManager
    time.sleep(3)

    # 从主线程的 cli 模块获取全局实例
    # Get the global instances from the main thread's cli module
    global window_manager_instance, app_instance
    # 需要从运行中的模块获取
    # We need to get it from the running module
    import src.interactive_feedback_server.cli as cli_module

    window_manager_instance = cli_module.window_manager
    app_instance = QApplication.instance()

    if not window_manager_instance:
        print("错误: 无法在主线程中获取 WindowManager 实例。测试中止。")
        sys.exit(1)
    if not app_instance:
        print("错误: 无法获取 QApplication 实例。测试中止。")
        sys.exit(1)


def run_test_suite():
    """运行完整的测试套件。"""
    start_server_in_background()

    num_clients = 3
    threads = []
    results = [None] * num_clients

    print("\n" + "=" * 50)
    print("--- 开始并发调用 interactive_feedback ---")
    print("=" * 50 + "\n")

    prompts = [
        "客户端1: 请提供您的名字。",
        "客户端2: 请提供您的年龄。",
        "客户端3: 请提供您的职业。",
    ]

    for i in range(num_clients):
        thread = threading.Thread(
            target=client_thread_function, args=(i, prompts[i], results)
        )
        threads.append(thread)
        thread.start()
        time.sleep(0.5)  # 错开UI请求

    for thread in threads:
        thread.join()

    print("\n" + "=" * 50)
    print("--- 所有客户端线程已完成 ---")
    print("=" * 50 + "\n")

    successful_calls = 0
    for i, res in enumerate(results):
        print(f"正在验证 客户端线程-{i} 的结果: {res}")
        if isinstance(res, dict) and "content" in res:
            print(f"  [成功] 客户端线程-{i} 返回了有效的结果。")
            successful_calls += 1
        else:
            print(f"  [失败] 客户端线程-{i} 返回了无效或错误的结果: {res}")

    # 测试后关闭Qt应用
    if app_instance:
        print("\n正在关闭Qt应用程序...")
        app_instance.quit()

    time.sleep(1)  # 等待线程清理

    assert (
        successful_calls == num_clients
    ), f"测试失败！预期 {num_clients} 次成功调用，实际只有 {successful_calls} 次。"
    print(f"\n测试成功！所有 {num_clients} 个并发调用均已成功完成。")


if __name__ == "__main__":
    run_test_suite()

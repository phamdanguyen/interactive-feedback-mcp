"""
此模块包含 WindowManager 类，负责管理应用的并发UI窗口。
"""

import sys
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication
import json

# 这是一个临时的、骨架版本的 InteractiveUI，仅用于类型提示和早期开发。
# 完整的实现将在第二阶段完成。
# This is a temporary, skeleton version of InteractiveUI for type hinting and early development.
# The full implementation will be done in Phase 2.
from ..feedback_ui.main_window import FeedbackUI


class WindowManager(QObject):
    """
    管理所有交互式UI窗口的中央调度器。
    负责UI窗口的创建、追踪和销毁，确保线程安全。
    """

    # 当从UI接收到最终反馈时，此信号被发射，并携带任务ID和结果数据。
    # This signal is emitted when final feedback is received from a UI, carrying the task ID and result data.
    feedback_received = Signal(str, dict)

    def __init__(self):
        super().__init__()
        self.active_windows = {}  # 使用字典通过 task_id 追踪活跃窗口

    @Slot(str, str)
    def create_window(self, task_id: str, initial_data_json: str):
        """创建一个新的反馈窗口实例。"""
        # 从JSON字符串中安全地加载数据
        try:
            initial_data = json.loads(initial_data_json)
        except json.JSONDecodeError:
            print(f"错误: 无法解析来自 task_id {task_id} 的JSON数据")
            return

        prompt = initial_data.get("prompt", "没有提供提示信息。")
        options = initial_data.get("options", [])

        print(f"WindowManager 正在为 task_id 创建窗口: {task_id}")

        # 确保在主线程中创建UI组件
        # Make sure to create UI components in the main thread
        window = FeedbackUI(task_id=task_id, prompt=prompt, predefined_options=options)

        window.feedback_provided.connect(self.on_feedback_provided)
        window.closed.connect(self.on_window_closed)
        self.active_windows[task_id] = window

        # 确保窗口被正确显示和激活
        print(f"WindowManager: 正在显示并激活窗口 {task_id}")
        window.show()
        window.raise_()
        window.activateWindow()

        # 手动处理事件队列，确保显示命令被执行
        QApplication.processEvents()

        print(f"WindowManager: 窗口 {task_id} 应已显示")

    @Slot(str, dict)
    def on_feedback_provided(self, task_id: str, data: dict):
        """
        接收来自UI窗口的反馈。
        发射 feedback_received 信号，以供主业务逻辑捕获。
        """
        if task_id in self.active_windows:
            self.feedback_received.emit(task_id, data)
            # 在收到反馈后，可以安全地关闭窗口
            # The window can be safely closed after receiving feedback.
            self.active_windows[task_id].close()

    @Slot(str)
    def on_window_closed(self, task_id: str):
        """
        当窗口关闭时进行清理。
        从追踪字典中移除窗口引用，并安全地删除Qt对象。
        """
        if task_id in self.active_windows:
            window = self.active_windows.pop(task_id)
            window.deleteLater()
            print(f"窗口 {task_id} 已关闭并清理。")

    def get_active_window_count(self):
        """返回当前活跃窗口的数量。"""
        return len(self.active_windows)

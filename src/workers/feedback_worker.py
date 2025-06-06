# src/workers/feedback_worker.py
from PySide6.QtCore import QObject, Signal


class FeedbackWorker(QObject):
    """
    一个在后台线程中运行的Worker，用于处理请求UI的业务逻辑。
    """

    # 信号定义
    # request_ui: 当需要显示UI时发射，携带task_id和初始化数据
    # finished: 当worker完成其任务时发射
    request_ui = Signal(str, dict)
    finished = Signal()

    def __init__(self, task_id: str, data: dict):
        """
        初始化 FeedbackWorker。

        Args:
            task_id (str): 与此任务关联的唯一ID。
            data (dict): 需要传递给UI的初始化数据 (例如, 提示信息)。
        """
        super().__init__()
        self.task_id = task_id
        self.data = data
        self._is_running = True

    def run(self):
        """
        Worker的核心执行逻辑。
        此方法被设计为在后台QThread中调用。
        """
        if self._is_running:
            print(f"FeedbackWorker ({self.task_id}): 正在请求UI...")
            # 发射信号，请求WindowManager创建并显示UI
            self.request_ui.emit(self.task_id, self.data)

    def stop(self):
        """停止worker的执行。"""
        self._is_running = False
        self.finished.emit()

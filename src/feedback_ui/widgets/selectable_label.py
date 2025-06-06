from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import QLabel

from ..utils.ui_helpers import set_selection_colors


class SelectableLabel(QLabel):
    """
    一个可以选择文本的标签，同时支持点击操作。
    A label that allows text selection while also supporting click operations.
    """

    clicked = Signal()

    def __init__(self, text: str = "", parent: QObject = None):
        super().__init__(text, parent)
        # 启用文本选择
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setMouseTracking(True)
        self.setWordWrap(True)

        # 设置选择文本时的高亮颜色为灰色
        set_selection_colors(self)

        # 跟踪鼠标按下的位置，用于判断是否为点击操作
        self._press_pos = None
        self._is_dragging = False

    def mousePressEvent(self, event: QEvent):
        """记录鼠标按下的位置，用于后续判断是点击还是拖拽选择文本"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
            self._is_dragging = False

        # 调用父类的事件处理，确保文本选择功能正常
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QEvent):
        """如果鼠标移动超过阈值，标记为拖拽操作"""
        if (
            self._press_pos
            and (event.position().toPoint() - self._press_pos).manhattanLength() > 5
        ):
            self._is_dragging = True

        # 调用父类的事件处理，确保文本选择功能正常
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QEvent):
        """根据是否为拖拽操作，决定是发送点击信号还是执行文本选择"""
        if event.button() == Qt.MouseButton.LeftButton and self._press_pos:
            # 如果不是拖拽操作，并且鼠标释放在标签范围内，则发射点击信号
            if not self._is_dragging and self.rect().contains(
                event.position().toPoint()
            ):
                # 如果没有选中文本，才发射点击信号
                if not self.hasSelectedText():
                    self.clicked.emit()

        # 重置状态
        self._press_pos = None
        self._is_dragging = False

        # 调用父类的事件处理，确保文本选择功能正常
        super().mouseReleaseEvent(event)

    def hasSelectedText(self) -> bool:
        """检查是否有选中的文本"""
        # QLabel没有直接的方法检查选中文本，使用系统剪贴板检查
        from PySide6.QtGui import QGuiApplication

        clipboard = QGuiApplication.clipboard()
        if clipboard and clipboard.ownsSelection():
            return True
        return False

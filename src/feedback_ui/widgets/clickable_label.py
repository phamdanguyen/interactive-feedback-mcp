# feedback_ui/widgets/clickable_label.py
from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtWidgets import QLabel


class CursorOverrideFilter(QObject):
    """
    An event filter to override the cursor shape for a widget.
    一个事件过滤器，用于覆盖小部件的光标形状。
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # This filter seems to intend to force ArrowCursor on certain interactions.
        # However, ClickableLabel sets PointingHandCursor. This might create conflicts
        # or have a specific desired interaction order.
        # For now, keeping original logic.
        # 此过滤器似乎打算在某些交互上强制使用 ArrowCursor。
        # 然而，ClickableLabel 设置了 PointingHandCursor。这可能会产生冲突
        # 或具有特定的期望交互顺序。
        # 目前，保留原始逻辑。
        if event.type() in (
            QEvent.Type.Enter,
            QEvent.Type.HoverEnter,
            QEvent.Type.HoverMove,
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
        ):
            if hasattr(obj, "setCursor"):  # Check if object has setCursor method
                obj.setCursor(Qt.CursorShape.ArrowCursor)  # Use enum member
            return False  # Event not handled here, just cursor override
        return super().eventFilter(obj, event)


class ClickableLabel(QLabel):
    """
    A QLabel that emits a 'clicked' signal when pressed.
    一个在按下时发出 'clicked' 信号的 QLabel。
    """

    clicked = Signal()

    def __init__(self, text: str = "", parent: QObject = None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        # The CursorOverrideFilter might conflict with PointingHandCursor.
        # Consider if this filter is truly needed for ClickableLabel or if PointingHandCursor is sufficient.
        # self._cursor_filter = CursorOverrideFilter(self) # Temporarily commented for review
        # self.installEventFilter(self._cursor_filter)      # Temporarily commented for review

    def mouseMoveEvent(self, event: QEvent):  # Parameter type QMouseEvent expected
        # QApplication.restoreOverrideCursor() # Overriding global cursor can be problematic
        # QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
        super().mouseMoveEvent(event)

    def enterEvent(self, event: QEvent):  # Parameter type QEnterEvent expected
        # QApplication.setOverrideCursor(Qt.CursorShape.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        # QApplication.restoreOverrideCursor()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QEvent):  # Parameter type QMouseEvent expected
        if event.button() == Qt.MouseButton.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QEvent):  # Parameter type QMouseEvent expected
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if the mouse release is within the label's bounds
            if self.rect().contains(
                event.position().toPoint()
            ):  # event.pos() in PySide6 is QPointF
                self.clicked.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

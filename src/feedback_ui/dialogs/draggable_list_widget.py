# feedback_ui/dialogs/draggable_list_widget.py
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import (
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QShowEvent,
)  # Added missing imports
from PySide6.QtWidgets import QLabel, QListWidget, QWidget


class DraggableListWidget(QListWidget):
    """
    A QListWidget that supports internal drag-and-drop to reorder items.
    It also emits a signal when an item is double-clicked.

    一个支持内部拖放以重新排序项目的 QListWidget。
    它还在项目被双击时发出信号。
    """

    drag_completed = Signal()  # Emitted after a drag-and-drop operation is completed
    # 拖放操作完成后发出
    item_double_clicked = Signal(
        str
    )  # Emitted with the text of the double-clicked item
    # 发出双击项目的文本

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(
            QListWidget.DragDropMode.InternalMove
        )  # Items can be moved within the list
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAlternatingRowColors(True)  # Improves readability
        self.setCurrentRow(-1)  # No item selected by default
        self.setIconSize(QSize(32, 32))  # Default icon size, can be overridden

        self._drag_start_position = None

    def showEvent(self, event: QShowEvent):  # Corrected type hint
        """Clears selection when the widget is shown."""
        super().showEvent(event)
        self.clearSelection()
        self.setCurrentItem(None)

    def mouseDoubleClickEvent(self, event: QMouseEvent):  # Corrected type hint
        """Handles double-click events on list items."""
        item = self.itemAt(event.position().toPoint())  # event.pos() is QPointF
        if item:
            item_widget = self.itemWidget(
                item
            )  # Assuming custom widgets are set for items
            if item_widget:
                # Attempt to find a QLabel within the item_widget to get its text
                # 尝试在 item_widget 中找到 QLabel 以获取其文本
                # This assumes a specific structure for item widgets.
                # 这假定项目小部件具有特定结构。
                text_label = item_widget.findChild(QLabel)
                if text_label:
                    self.item_double_clicked.emit(text_label.text())
                    event.accept()
                    return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent):  # Corrected type hint
        """Stores the starting position of a potential drag operation."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_position = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):  # Corrected type hint
        """
        Initiates a drag operation if the mouse moves beyond a certain threshold
        while the left button is pressed. Qt's default drag initiation handles this
        when setDragEnabled(True) is used. This method can be simplified or removed
        if default behavior is sufficient.

        如果鼠标在按下左键的情况下移动超过某个阈值，则启动拖动操作。
        当使用 setDragEnabled(True) 时，Qt 的默认拖动启动会处理此问题。
        如果默认行为足够，则可以简化或删除此方法。
        """
        # Qt's default drag handling with setDragEnabled(True) is usually sufficient.
        # This explicit check might be redundant unless custom drag data is needed.
        # if not (event.buttons() & Qt.MouseButton.LeftButton):
        #     return super().mouseMoveEvent(event)
        # if not self._drag_start_position:
        #     return super().mouseMoveEvent(event)

        # manhattan_length = (event.position().toPoint() - self._drag_start_position).manhattanLength()
        # if manhattan_length < QApplication.startDragDistance():
        #     return super().mouseMoveEvent(event)

        # If we reach here, a drag should start. Qt handles this internally.
        # Calling super() is important for the default drag to begin.
        super().mouseMoveEvent(event)

    def dropEvent(self, event: QDropEvent):  # Corrected type hint
        """Handles the drop event, clears selection, and emits drag_completed signal."""
        super().dropEvent(event)  # Allow Qt to handle the internal move
        # Clear selection after the drop to avoid a lingering selected item
        # QTimer.singleShot(0, self.clearSelection) # Clear selection in the next event loop cycle
        self.setCurrentRow(-1)  # More direct way to clear selection focus
        self.drag_completed.emit()
        event.acceptProposedAction()

    def keyPressEvent(self, event: QKeyEvent):  # Added keyPressEvent
        """Handle key presses, e.g., Enter to trigger double click action."""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_item = self.currentItem()
            if current_item:
                item_widget = self.itemWidget(current_item)
                if item_widget:
                    text_label = item_widget.findChild(QLabel)
                    if text_label:
                        self.item_double_clicked.emit(text_label.text())
                        event.accept()
                        return
        super().keyPressEvent(event)

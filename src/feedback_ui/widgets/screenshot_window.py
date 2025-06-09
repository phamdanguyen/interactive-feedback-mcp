"""
截图窗口模块
提供全屏截图选择功能
"""

import sys
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QPixmap, QCursor
from PySide6.QtWidgets import QWidget, QApplication

from ..utils.constants import (
    SCREENSHOT_MIN_SIZE,
    SCREENSHOT_OVERLAY_OPACITY,
    SCREENSHOT_BORDER_COLOR,
    SCREENSHOT_BORDER_WIDTH,
    SCREENSHOT_TEXT_COLOR,
)


class ScreenshotWindow(QWidget):
    """
    全屏截图选择窗口
    用户可以通过拖拽鼠标选择矩形区域进行截图
    """

    # 信号：截图完成，传递QPixmap对象
    screenshot_taken = Signal(QPixmap)
    # 信号：截图取消
    screenshot_cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_window()
        self.init_variables()
        # 先捕获屏幕，再显示窗口，减少闪烁
        self.capture_screen()

    def setup_window(self):
        """设置窗口属性"""
        # 设置为无边框、置顶、全屏窗口
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        # 设置窗口透明背景
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 设置鼠标追踪
        self.setMouseTracking(True)

        # 设置光标为十字形
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        # 设置窗口几何但不显示
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

    def init_variables(self):
        """初始化变量"""
        self.start_point = QPoint()  # 拖拽起始点
        self.end_point = QPoint()  # 拖拽结束点
        self.is_dragging = False  # 是否正在拖拽
        self.screen_pixmap = None  # 屏幕截图

    def capture_screen(self):
        """捕获当前屏幕内容"""
        try:
            # 直接捕获屏幕，不显示窗口
            screen = QApplication.primaryScreen()
            if not screen:
                raise RuntimeError("无法获取主屏幕")

            self.screen_pixmap = screen.grabWindow(0)
            if self.screen_pixmap.isNull():
                raise RuntimeError("屏幕截图为空")

            # 捕获完成后再显示窗口
            self.showFullScreen()
        except (RuntimeError, AttributeError) as e:
            print(f"ERROR: 捕获屏幕失败: {e}", file=sys.stderr)
            self.screenshot_cancelled.emit()
            self.close()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_dragging = True
            self.update()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_dragging:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.capture_selected_area()
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键取消截图
            self.screenshot_cancelled.emit()
            self.close()

    def keyPressEvent(self, event):
        """键盘按下事件"""
        if event.key() == Qt.Key.Key_Escape:
            # ESC键取消截图
            self.screenshot_cancelled.emit()
            self.close()
        super().keyPressEvent(event)

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        painter = QPainter(self)

        # 绘制屏幕背景（半透明遮罩）
        if self.screen_pixmap:
            painter.drawPixmap(0, 0, self.screen_pixmap)

        # 绘制半透明遮罩
        overlay = QBrush(QColor(0, 0, 0, SCREENSHOT_OVERLAY_OPACITY))  # 黑色半透明
        painter.fillRect(self.rect(), overlay)

        # 如果正在选择，绘制选择区域
        if self.is_dragging or (self.start_point != self.end_point):
            selection_rect = self.get_selection_rect()

            # 清除选择区域的遮罩（显示原始屏幕内容）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(selection_rect, QBrush(QColor(0, 0, 0, 0)))

            # 重新绘制选择区域的原始内容
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            if self.screen_pixmap:
                painter.drawPixmap(selection_rect, self.screen_pixmap, selection_rect)

            # 绘制选择框边框
            pen = QPen(
                QColor(*SCREENSHOT_BORDER_COLOR), SCREENSHOT_BORDER_WIDTH
            )  # 蓝色边框
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawRect(selection_rect)

            # 绘制尺寸信息
            self.draw_size_info(painter, selection_rect)

    def get_selection_rect(self):
        """获取选择矩形"""
        return QRect(
            min(self.start_point.x(), self.end_point.x()),
            min(self.start_point.y(), self.end_point.y()),
            abs(self.end_point.x() - self.start_point.x()),
            abs(self.end_point.y() - self.start_point.y()),
        )

    def draw_size_info(self, painter, rect):
        """绘制尺寸信息"""
        if rect.width() > 0 and rect.height() > 0:
            # 设置文本样式
            painter.setPen(QPen(QColor(*SCREENSHOT_TEXT_COLOR), 1))

            # 尺寸文本
            size_text = f"{rect.width()} × {rect.height()}"

            # 计算文本位置（在选择框上方）
            text_x = rect.x() + 5
            text_y = rect.y() - 5

            # 确保文本不超出屏幕
            if text_y < 20:
                text_y = rect.y() + 20

            painter.drawText(text_x, text_y, size_text)

    def capture_selected_area(self):
        """捕获选择的区域"""
        selection_rect = self.get_selection_rect()

        # 检查选择区域是否有效
        if (
            selection_rect.width() < SCREENSHOT_MIN_SIZE
            or selection_rect.height() < SCREENSHOT_MIN_SIZE
        ):
            self.screenshot_cancelled.emit()
            self.close()
            return

        # 从屏幕截图中提取选择区域
        if self.screen_pixmap and not self.screen_pixmap.isNull():
            selected_pixmap = self.screen_pixmap.copy(selection_rect)
            if not selected_pixmap.isNull():
                self.screenshot_taken.emit(selected_pixmap)
            else:
                self.screenshot_cancelled.emit()
        else:
            self.screenshot_cancelled.emit()

        self.close()

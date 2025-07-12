"""
Loading Overlay Widget
加载覆盖层组件

提供一个半透明的加载覆盖层，显示在父窗口中央，用于表示正在进行的操作。
Provides a semi-transparent loading overlay that displays in the center of the parent window
to indicate ongoing operations.
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtGui import QPainter, QColor

# 常量定义
DEFAULT_AUTO_HIDE_DELAY = 500  # 默认自动隐藏延迟（毫秒）
CONTAINER_WIDTH = 260  # 容器宽度
ICON_SIZE = 60  # 图标尺寸
FADE_IN_DURATION = 300  # 淡入动画时长
FADE_OUT_DURATION = 200  # 淡出动画时长


class LoadingOverlay(QWidget):
    """
    加载覆盖层组件
    Loading Overlay Component

    在父窗口上显示半透明的加载指示器，包含旋转的进度条和提示文本。
    Displays a semi-transparent loading indicator over the parent window with
    a spinning progress bar and hint text.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_animations()
        self._apply_styles()

        # 初始隐藏
        self.hide()

    def _setup_ui(self):
        """设置UI布局"""
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建中央容器
        self.central_container = QWidget()
        self.central_container.setObjectName("loadingContainer")

        # 中央容器布局
        container_layout = QVBoxLayout(self.central_container)
        container_layout.setContentsMargins(30, 25, 30, 25)
        container_layout.setSpacing(15)

        # 静态加载图标（替代动态进度条）
        self.loading_icon = QLabel("⏳")
        self.loading_icon.setObjectName("loadingIcon")
        self.loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_icon.setStyleSheet("font-size: 32px; margin: 10px;")
        self.loading_icon.setFixedSize(ICON_SIZE, ICON_SIZE)

        # 加载文本
        self.loading_label = QLabel("🔄 正在优化文本，请稍候...")
        self.loading_label.setObjectName("loadingLabel")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 添加到容器布局
        container_layout.addWidget(self.loading_icon, 0, Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.loading_label, 0, Qt.AlignmentFlag.AlignCenter)

        # 添加到主布局（居中）
        main_layout.addWidget(self.central_container, 0, Qt.AlignmentFlag.AlignCenter)

    def _setup_animations(self):
        """设置动画效果"""
        # 透明度效果
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)

        # 淡入动画
        self.fade_in_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in_animation.setDuration(FADE_IN_DURATION)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # 淡出动画
        self.fade_out_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out_animation.setDuration(FADE_OUT_DURATION)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.setEasingCurve(QEasingCurve.Type.InCubic)
        self.fade_out_animation.finished.connect(self.hide)

    def _apply_styles(self):
        """应用样式 - 优化版本"""
        # 检测主题（简单的检测方法）
        is_dark_theme = True  # 默认深色主题
        if self.parent():
            # 尝试从父窗口获取主题信息
            parent_bg = self.parent().palette().color(self.parent().backgroundRole())
            is_dark_theme = parent_bg.lightness() < 128

        self._apply_theme_styles(is_dark_theme)

    def _apply_theme_styles(self, is_dark_theme: bool):
        """应用主题样式 - 优化版本"""
        if is_dark_theme:
            bg_color = "rgba(45, 45, 45, 1.0)"
            border_color = "rgba(100, 100, 100, 0.6)"
            text_color = "#ffffff"
            icon_color = "#4A90E2"
        else:
            bg_color = "rgba(255, 255, 255, 1.0)"
            border_color = "rgba(200, 200, 200, 0.8)"
            text_color = "#333333"
            icon_color = "#1565c0"

        # 统一的样式模板
        style_template = f"""
            QWidget#loadingContainer {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                min-width: {CONTAINER_WIDTH}px;
                max-width: {CONTAINER_WIDTH}px;
            }}

            QLabel#loadingLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 500;
                padding: 5px;
                background-color: transparent;
            }}

            QLabel#loadingIcon {{
                color: {icon_color};
                background-color: transparent;
                border: none;
            }}
        """
        self.setStyleSheet(style_template)

    def show_loading(self, message: str = "🔄 正在优化文本，请稍候..."):
        """
        显示加载覆盖层
        Show loading overlay

        Args:
            message: 加载提示文本
        """
        # 重置为加载状态
        self.loading_icon.setText("⏳")
        self.loading_label.setText(message)
        self._update_position()

        # 确保完全不透明显示
        self.opacity_effect.setOpacity(1.0)
        self.show()
        self.raise_()

    def hide_loading(self):
        """
        隐藏加载覆盖层
        Hide loading overlay
        """
        self.fade_out_animation.start()

    def show_success(
        self, message: str = "✅ 完成！", auto_hide_delay: int = DEFAULT_AUTO_HIDE_DELAY
    ):
        """
        显示成功状态并自动隐藏
        Show success status and auto hide

        Args:
            message: 成功提示文本
            auto_hide_delay: 自动隐藏延迟（毫秒）
        """
        # 更新为成功状态
        self.loading_icon.setText("✅")  # 更改图标为成功标志
        self.loading_label.setText(message)

        # 确保完全不透明显示
        self.opacity_effect.setOpacity(1.0)

        # 如果当前未显示，则显示
        if not self.isVisible():
            self.show()
            self.raise_()
            # 成功状态直接显示，无需动画

        # 自动隐藏
        QTimer.singleShot(auto_hide_delay, self.hide_loading)

    def _update_position(self):
        """更新位置，确保居中显示"""
        if self.parent():
            parent_rect = self.parent().rect()
            self.setGeometry(parent_rect)

    def resizeEvent(self, event):
        """窗口大小变化时重新定位"""
        super().resizeEvent(event)
        self._update_position()

    def paintEvent(self, event):
        """绘制半透明背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制半透明背景
        overlay_color = QColor(0, 0, 0, 80)  # 半透明黑色
        painter.fillRect(self.rect(), overlay_color)

        super().paintEvent(event)

    def set_theme(self, is_dark_theme: bool):
        """
        设置主题 - 优化版本
        Set theme

        Args:
            is_dark_theme: 是否为深色主题
        """
        self._apply_theme_styles(is_dark_theme)

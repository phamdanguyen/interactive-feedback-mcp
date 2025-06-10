# feedback_ui/widgets/image_preview.py

from PySide6.QtCore import QEvent, Qt, Signal  # Added QObject
from PySide6.QtGui import QColor, QCursor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ..utils.object_pool import get_pixmap_pool, PooledResource


class ImagePreviewWidget(QWidget):
    """
    A widget to display a small thumbnail of an image.
    Shows a larger preview on hover and allows deletion on click.

    用于显示图像小缩略图的小部件。
    悬停时显示较大的预览，并允许单击删除。
    """

    image_deleted = Signal(
        int
    )  # Emits the image_id when deleted (发出删除图像的 image_id)

    def __init__(
        self, image_pixmap: QPixmap, image_id: int, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.image_pixmap = (
            image_pixmap  # This is the thumbnail, original_pixmap is full res
        )
        self.image_id = image_id
        self.original_pixmap = (
            image_pixmap  # Store the full resolution pixmap for preview
        )
        self.is_hovering = False

        self.setFixedSize(48, 48)  # Fixed size for the thumbnail widget

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)  # Small margins around the thumbnail
        layout.setSpacing(0)

        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create scaled thumbnail for display (using object pool if available)
        self.display_thumbnail = self._create_scaled_pixmap(44, 44)
        self.hover_thumbnail = self._create_hover_thumbnail(
            self.display_thumbnail
        )  # Thumbnail for hover state

        self.thumbnail_label.setPixmap(self.display_thumbnail)
        layout.addWidget(self.thumbnail_label)

        self.setToolTip(
            "悬停查看大图，点击图标删除图片 (Hover to see larger image, click to delete)"
        )
        self.setMouseTracking(
            True
        )  # Needed for enterEvent/leaveEvent without mouse button press
        self.preview_window: QMainWindow | None = None  # To hold the preview pop-up

    def _create_hover_thumbnail(self, base_thumbnail: QPixmap) -> QPixmap:
        """Creates a version of the thumbnail with a red tint for hover effect."""
        if base_thumbnail.isNull():
            return base_thumbnail

        hover_pixmap = QPixmap(base_thumbnail.size())
        hover_pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background

        painter = QPainter(hover_pixmap)
        painter.drawPixmap(0, 0, base_thumbnail)  # Draw original thumbnail
        # Apply a semi-transparent red overlay
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        painter.fillRect(
            hover_pixmap.rect(), QColor(255, 100, 100, 160)
        )  # Reddish tint
        painter.end()
        return hover_pixmap

    def enterEvent(self, event: QEvent):  # QEnterEvent
        self.is_hovering = True
        self.thumbnail_label.setPixmap(self.hover_thumbnail)  # Change to hover version
        self._show_full_image_preview()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent):
        self.is_hovering = False
        self.thumbnail_label.setPixmap(
            self.display_thumbnail
        )  # Revert to default thumbnail
        if self.preview_window and self.preview_window.isVisible():
            self.preview_window.close()  # Close the pop-up preview
            self.preview_window = None
        QToolTip.hideText()  # Ensure any native tooltip is hidden
        super().leaveEvent(event)

    def mousePressEvent(self, event: QEvent):  # QMouseEvent
        if event.button() == Qt.MouseButton.LeftButton:
            self._delete_image()  # Trigger deletion on left click
            event.accept()  # Event handled
            return
        super().mousePressEvent(event)

    def _show_full_image_preview(self):
        """Displays a larger, non-modal preview of the image near the cursor."""
        if not self.is_hovering or self.original_pixmap.isNull():
            return

        if (
            self.preview_window and self.preview_window.isVisible()
        ):  # Close existing first
            self.preview_window.close()
            self.preview_window = None

        max_preview_width = 400
        max_preview_height = 300

        # 使用优化的缩放方法
        preview_pixmap = self._create_scaled_pixmap(
            max_preview_width, max_preview_height
        )

        cursor_pos = QCursor.pos()  # Global cursor position

        # Create a frameless window that stays on top
        self.preview_window = QMainWindow(None)  # Parent to None or self.window()
        self.preview_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool  # Behaves like a tooltip window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.preview_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.preview_window.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )  # For rounded corners if QSS is used

        preview_widget_container = QWidget()
        preview_widget_container.setObjectName("ImagePreviewPopupContainer")
        preview_widget_container.setStyleSheet(
            "#ImagePreviewPopupContainer { background-color: #2b2b2b; border: 1px solid #444; border-radius: 5px; padding: 5px; }"
            "QLabel#PreviewImageLabel { background-color: transparent; }"
            "QLabel#PreviewInfoLabel { color: #ccc; font-size: 9pt; background-color: transparent; padding-top: 3px; }"
        )

        layout = QVBoxLayout(preview_widget_container)
        layout.setContentsMargins(5, 5, 5, 5)  # Margins within the popup

        image_label = QLabel()
        image_label.setObjectName("PreviewImageLabel")
        image_label.setPixmap(preview_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        info_text = f"尺寸 (Size): {self.original_pixmap.width()} x {self.original_pixmap.height()}"
        info_label = QLabel(info_text)
        info_label.setObjectName("PreviewInfoLabel")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        self.preview_window.setCentralWidget(preview_widget_container)
        self.preview_window.adjustSize()  # Adjust size to content

        # Position the preview window near the cursor, avoiding screen edges
        popup_x = cursor_pos.x() + 20
        popup_y = cursor_pos.y() + 20

        screen_geometry = QApplication.primaryScreen().availableGeometry()
        if popup_x + self.preview_window.width() > screen_geometry.right():
            popup_x = cursor_pos.x() - self.preview_window.width() - 10
        if popup_y + self.preview_window.height() > screen_geometry.bottom():
            popup_y = cursor_pos.y() - self.preview_window.height() - 10

        # Ensure it's not off-screen to the top/left either
        popup_x = max(screen_geometry.left(), popup_x)
        popup_y = max(screen_geometry.top(), popup_y)

        self.preview_window.move(popup_x, popup_y)
        self.preview_window.show()

    def _delete_image(self):
        """Emits the signal for image deletion and prepares for self-destruction."""
        if self.preview_window and self.preview_window.isVisible():
            self.preview_window.close()  # Close preview if open
        self.image_deleted.emit(self.image_id)
        # The parent (FeedbackUI) will handle self.deleteLater()

    def _create_scaled_pixmap(self, max_width: int, max_height: int) -> QPixmap:
        """
        创建缩放后的QPixmap，优先使用对象池
        Create scaled QPixmap, preferring object pool
        """
        # 检查是否需要缩放
        if (
            self.original_pixmap.width() <= max_width
            and self.original_pixmap.height() <= max_height
        ):
            return self.original_pixmap

        # 尝试使用对象池
        pixmap_pool = get_pixmap_pool()
        if pixmap_pool is not None:
            with PooledResource(pixmap_pool) as temp_pixmap:
                # 使用池化的pixmap进行缩放
                scaled = self.original_pixmap.scaled(
                    max_width,
                    max_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                # 复制结果到新的pixmap（因为池化对象会被回收）
                result = QPixmap(scaled)
                return result
        else:
            # 回退到直接创建
            return self.original_pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

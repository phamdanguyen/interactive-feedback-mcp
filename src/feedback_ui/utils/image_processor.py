# feedback_ui/utils/image_processor.py
import base64
from typing import Any

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QPixmap, Qt  # Qt 已在之前添加
from PySide6.QtWidgets import QMessageBox

from .constants import (
    MAX_IMAGE_BYTES,
    MAX_IMAGE_HEIGHT,
    MAX_IMAGE_WIDTH,
    IMAGE_QUALITY,
    IMAGE_SCALE_FACTOR,
    ContentItem,
)
from .resource_manager import managed_image_processing


def process_single_image(pixmap_to_save: QPixmap) -> dict[str, Any] | None:
    """
    Processes a QPixmap into a dictionary containing Base64 encoded image data and its metadata.
    The image is resized and compressed if necessary to meet defined limits.
    Uses object pools to reduce memory allocation overhead.

    将 QPixmap 处理为包含 Base64 编码图像数据及其元数据的字典。
    如有必要，图像将被调整大小和压缩以满足定义的限制。
    使用对象池减少内存分配开销。

    Returns:
        dict[str, Any] | None: 处理结果或None（如果失败）
    """
    if pixmap_to_save is None or pixmap_to_save.isNull():
        return None

    # 图像缩放处理
    current_pixmap = pixmap_to_save
    if (
        current_pixmap.width() > MAX_IMAGE_WIDTH
        or current_pixmap.height() > MAX_IMAGE_HEIGHT
    ):
        current_pixmap = current_pixmap.scaled(
            MAX_IMAGE_WIDTH,
            MAX_IMAGE_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    # 使用托管资源处理图像 (V3.2 资源管理优化)
    try:
        with managed_image_processing() as resources:
            return _process_image_with_managed_resources(current_pixmap, resources)
    except Exception as e:
        print(f"托管资源处理失败，使用回退方法: {e}")
        return _process_image_fallback(current_pixmap)


def _process_image_with_managed_resources(
    pixmap: QPixmap, resources: dict
) -> dict[str, Any] | None:
    """
    使用托管资源处理图像 (简化版本 - 100%质量，超过2MB时缩小尺寸)
    Process image using managed resources (Simplified - 100% quality, scale down if > 2MB)
    """
    save_format = "JPEG"
    mime_type = "image/jpeg"
    current_pixmap = pixmap
    byte_array = resources["byte_array"]

    # 最多尝试10次缩放（防止无限循环）
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        # 重置资源状态
        byte_array.clear()

        # 正确创建QBuffer - 直接关联byte_array
        buffer = QBuffer(byte_array)

        # 尝试保存图像
        if buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            try:
                if current_pixmap.save(buffer, save_format, IMAGE_QUALITY):
                    buffer.close()

                    # 检查大小是否符合要求
                    if byte_array.size() <= MAX_IMAGE_BYTES:
                        return _create_image_result(
                            current_pixmap,
                            byte_array,
                            save_format,
                            mime_type,
                            IMAGE_QUALITY,
                        )
                    else:
                        # 超过大小限制，缩小图片
                        new_width = int(current_pixmap.width() * IMAGE_SCALE_FACTOR)
                        new_height = int(current_pixmap.height() * IMAGE_SCALE_FACTOR)

                        # 防止图片过小
                        if new_width < 32 or new_height < 32:
                            break

                        current_pixmap = current_pixmap.scaled(
                            new_width,
                            new_height,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        attempt += 1
                        continue
            except Exception:
                pass
            finally:
                if buffer.isOpen():
                    buffer.close()

        break

    # 无法满足大小要求
    _show_image_error("无法将图像压缩到合适的大小")
    return None


def _process_image_fallback(pixmap: QPixmap) -> dict[str, Any] | None:
    """
    回退处理方法（不使用对象池，简化版本）
    Fallback processing method (without object pools, simplified)
    """
    save_format = "JPEG"
    mime_type = "image/jpeg"
    current_pixmap = pixmap

    # 最多尝试10次缩放（防止无限循环）
    max_attempts = 10
    attempt = 0

    while attempt < max_attempts:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)

        if buffer.open(QIODevice.OpenModeFlag.WriteOnly):
            try:
                if current_pixmap.save(buffer, save_format, IMAGE_QUALITY):
                    buffer.close()

                    if byte_array.size() <= MAX_IMAGE_BYTES:
                        return _create_image_result(
                            current_pixmap,
                            byte_array,
                            save_format,
                            mime_type,
                            IMAGE_QUALITY,
                        )
                    else:
                        # 超过大小限制，缩小图片
                        new_width = int(current_pixmap.width() * IMAGE_SCALE_FACTOR)
                        new_height = int(current_pixmap.height() * IMAGE_SCALE_FACTOR)

                        # 防止图片过小
                        if new_width < 32 or new_height < 32:
                            break

                        current_pixmap = current_pixmap.scaled(
                            new_width,
                            new_height,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        attempt += 1
                        continue
            except Exception:
                pass
            finally:
                if buffer.isOpen():
                    buffer.close()

        break

    _show_image_error("无法将图像压缩到合适的大小")
    return None


def _create_image_result(
    pixmap: QPixmap,
    byte_array: QByteArray,
    save_format: str,
    mime_type: str,
    quality: int,
) -> dict[str, Any]:
    """
    创建图像处理结果
    Create image processing result
    """
    image_data_bytes = byte_array.data()
    if not image_data_bytes:
        _show_image_error("无法获取图像数据")
        return None

    try:
        base64_encoded_data = base64.b64encode(image_data_bytes).decode("utf-8")

        metadata = {
            "width": pixmap.width(),
            "height": pixmap.height(),
            "format": save_format.lower(),
            "size": byte_array.size(),
            "compression_quality_used": quality,
        }

        image_data_dict: ContentItem = {
            "type": "image",
            "text": None,
            "data": base64_encoded_data,
            "mimeType": mime_type,
            "display_name": None,
            "path": None,
        }

        return {
            "image_data": image_data_dict,
            "metadata": metadata,
        }

    except Exception as e:
        _show_image_error(f"图像数据编码失败: {e}")
        return None


def _show_image_error(message: str) -> None:
    """
    显示图像处理错误消息
    Show image processing error message
    """
    QMessageBox.critical(None, "图像处理错误 (Image Processing Error)", message)


def get_image_items_from_widgets(image_widgets: dict[int, Any]) -> list[ContentItem]:
    """
    Collects processed image data (as ContentItem) for all image widgets.
    The 'Any' for image_widgets value should ideally be ImagePreviewWidget.

    收集所有图像小部件已处理的图像数据（作为 ContentItem）。
    image_widgets 值的 'Any' 类型理想情况下应为 ImagePreviewWidget。
    """
    processed_image_items: list[ContentItem] = []
    # 使用 list(image_widgets.keys()) 以防在迭代时修改字典 (Use list() in case dict is modified during iteration)
    for image_id in list(image_widgets.keys()):
        widget = image_widgets.get(image_id)
        if widget and hasattr(
            widget, "original_pixmap"
        ):  # 确保 widget 是 ImagePreviewWidget 的实例 (Ensure widget is instance of ImagePreviewWidget)
            pixmap = (
                widget.original_pixmap
            )  # original_pixmap 应该是高分辨率版本 (should be full-res version)
            processed_data = process_single_image(pixmap)
            if processed_data and "image_data" in processed_data:
                # 确保项目符合 ContentItem (Ensure the item conforms to ContentItem)
                img_item: ContentItem = processed_data["image_data"]
                processed_image_items.append(img_item)
    return processed_image_items

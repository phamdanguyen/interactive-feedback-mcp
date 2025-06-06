# feedback_ui/utils/image_processor.py
import base64
from typing import Any

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QPixmap, Qt  # Qt 已在之前添加
from PySide6.QtWidgets import QMessageBox

from .constants import MAX_IMAGE_BYTES, MAX_IMAGE_HEIGHT, MAX_IMAGE_WIDTH, ContentItem


def process_single_image(pixmap_to_save: QPixmap) -> dict[str, Any] | None:
    """
    Processes a QPixmap into a dictionary containing Base64 encoded image data and its metadata.
    The image is resized and compressed if necessary to meet defined limits.
    Output structure: {"image_data": {"type": "image", "data": "base64...", "mimeType": "image/jpeg"},
                       "metadata": {"width": ..., "height": ..., "format": ..., "size": ...}}
    Returns None if processing fails.

    将 QPixmap 处理为包含 Base64 编码图像数据及其元数据的字典。
    如有必要，图像将被调整大小和压缩以满足定义的限制。
    输出结构: {"image_data": {"type": "image", "data": "base64...", "mimeType": "image/jpeg"},
               "metadata": {"width": ..., "height": ..., "format": ..., "size": ...}}
    如果处理失败，则返回 None。
    """
    if pixmap_to_save is None or pixmap_to_save.isNull():
        return None

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

    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    save_format = "JPEG"
    mime_type = "image/jpeg"
    saved_successfully = False
    quality = 80  # 初始压缩质量 (Initial compression quality)

    qualities_to_try = [quality, 70, 60, 50, 40]

    for q_val in qualities_to_try:
        byte_array.clear()  # 为新尝试清空 (Clear for new attempt)
        # buffer.setData(QByteArray()) # 为新尝试重置缓冲区 (Reset buffer for new attempt) - QBuffer(byte_array) 构造已关联
        if buffer.open(QIODevice.OpenModeFlag.WriteOnly):  # 使用 OpenModeFlag
            if current_pixmap.save(buffer, save_format, q_val):
                saved_successfully = True
            buffer.close()  # 确保在每次尝试后关闭 (Ensure close after each attempt)

        if saved_successfully and byte_array.size() <= MAX_IMAGE_BYTES:
            quality = q_val  # 保存实际使用的质量 (Store the quality that worked)
            break  # 如果成功且在大小限制内，则退出循环 (Exit loop if successful and within size limits)
        elif saved_successfully and byte_array.size() > MAX_IMAGE_BYTES:
            # 如果太大，则标记为本次迭代不成功 (Too large, mark as unsuccessful for this quality)
            saved_successfully = False
        # 如果保存本身失败，则循环继续尝试下一个质量 (If save itself failed, loop continues to try next quality)

    if (
        not saved_successfully or byte_array.isEmpty()
    ):  # 检查 byte_array 是否为空 (Check if byte_array is empty)
        QMessageBox.critical(
            None,
            "图像处理错误 (Image Processing Error)",
            "无法将图像保存为 JPEG 格式。(Could not save image as JPEG.)",
        )
        return None

    if (
        byte_array.size() > MAX_IMAGE_BYTES
    ):  # 所有尝试后的最终检查 (Final check after all attempts)
        QMessageBox.critical(
            None,
            "图像过大 (Image Too Large)",
            f"图像大小 ({byte_array.size() // 1024} KB) 超过了限制 ({MAX_IMAGE_BYTES // 1024} KB)。\n"
            "请使用更小的图像或进一步压缩。(Image size exceeds the limit. Please use a smaller or more compressed image.)",
        )
        return None

    image_data_bytes = byte_array.data()  # 获取字节数据 (Get byte data)
    if not image_data_bytes:  # 确保字节数据非空 (Ensure byte data is not empty)
        QMessageBox.critical(
            None,
            "图像处理错误 (Image Processing Error)",
            "无法获取图像数据。(Could not get image data.)",
        )
        return None

    try:
        base64_encoded_data = base64.b64encode(image_data_bytes).decode("utf-8")

        metadata = {
            "width": current_pixmap.width(),
            "height": current_pixmap.height(),
            "format": save_format.lower(),
            "size": byte_array.size(),
            "compression_quality_used": quality,  # (可选) 包含使用的压缩质量 (Optionally include compression quality used)
        }
        # 根据 ContentItem 结构明确类型提示 (Explicitly type hint according to ContentItem structure)
        image_data_dict: ContentItem = {
            "type": "image",
            "text": None,  # (图像类型不使用) (Not used for image type)
            "data": base64_encoded_data,
            "mimeType": mime_type,
            "display_name": None,  # (图像类型不使用)
            "path": None,  # (图像类型不使用)
        }

        return {
            "image_data": image_data_dict,  # 这是 ContentItem
            "metadata": metadata,  # 这是关于 ContentItem 的额外信息 (This is additional info about the ContentItem)
        }

    except Exception as e:
        QMessageBox.critical(
            None,
            "图像处理错误 (Image Processing Error)",
            f"图像数据编码失败 (Image data encoding failed): {e}",
        )
        return None


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

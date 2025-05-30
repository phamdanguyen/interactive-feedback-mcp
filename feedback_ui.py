# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import argparse
import base64  # 确保导入 base64 模块
from typing import Optional, TypedDict, List, Dict, Any, Union, Tuple
from io import BytesIO  # 导入 BytesIO 用于处理二进制数据
import time  # 添加时间模块
import traceback
from datetime import datetime
import functools # 添加导入

# 添加pyperclip模块，用于剪贴板操作
try:
    import pyperclip
except ImportError:
    print("警告: 无法导入pyperclip模块，部分剪贴板功能可能无法正常工作", file=sys.stderr)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame, QSizePolicy, QScrollArea, QToolTip, QDialog, QListWidget,
    QMessageBox, QListWidgetItem, QComboBox, QGridLayout, QSpacerItem, QLayout,
    QDialogButtonBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSettings, QEvent, QSize, QStringListModel, QByteArray, QBuffer, QIODevice, QMimeData, QPoint, QRect, QRectF
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QPixmap, QCursor, QPainter, QClipboard, QImage, QFont, QKeySequence, QShortcut, QDrag, QPen, QAction, QFontMetrics

# 添加自定义ClickableLabel类
class ClickableLabel(QLabel):
    """自定义标签类，允许文本选择但禁止光标变化"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # 设置文本可选标志 - 只读
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # 使用更强的方式设置标签样式
        self.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                selection-background-color: #2a82da;
                selection-color: white;
            }
        """)
        
        # 禁用光标重设 - 关键设置
        self.setCursor(Qt.ArrowCursor)
        self.setMouseTracking(True)  # 启用鼠标跟踪以便处理所有鼠标移动事件
        
        # 创建事件过滤器对象，并安装到自身
        self._cursor_filter = CursorOverrideFilter(self)
        self.installEventFilter(self._cursor_filter)
    
    # 重写mouseMoveEvent确保光标不变
    def mouseMoveEvent(self, event):
        QApplication.restoreOverrideCursor()  # 先清除可能的光标堆栈
        QApplication.setOverrideCursor(Qt.ArrowCursor)  # 强制设置为箭头光标
        super().mouseMoveEvent(event)
    
    # 重写以下事件来确保光标始终为箭头
    def enterEvent(self, event):
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

# 添加一个专用的事件过滤器类用于光标控制
class CursorOverrideFilter(QObject):
    """确保特定控件永远使用箭头光标的事件过滤器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def eventFilter(self, obj, event):
        # 捕获所有可能导致光标变化的事件
        if event.type() in (QEvent.Enter, QEvent.HoverEnter, QEvent.HoverMove, 
                           QEvent.MouseMove, QEvent.MouseButtonPress, 
                           QEvent.MouseButtonRelease):
            # 确保使用箭头光标
            obj.setCursor(Qt.ArrowCursor)
            return False  # 继续处理事件
        return False  # 让所有其他事件继续传递

# 添加图片处理相关常量
MAX_IMAGE_WIDTH = 512  # 最大图片宽度 - 从1280降低到512，优化LLM处理
MAX_IMAGE_HEIGHT = 512  # 最大图片高度 - 从720降低到512，优化LLM处理
MAX_IMAGE_BYTES = 1048576  # 最大文件大小 (1MB) - 从2MB降低到1MB

# 修改 FeedbackResult 类型定义，使其与 MCP 格式一致
class ContentItem(TypedDict):
    type: str
    text: Optional[str]  # 文本类型时使用
    data: Optional[str]  # 图片类型时使用
    mimeType: Optional[str]  # 图片类型时使用

class FeedbackResult(TypedDict):
    content: List[ContentItem]

def get_dark_mode_palette(app: QApplication):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    return darkPalette

class FeedbackTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置接受纯文本模式
        self.setAcceptRichText(False)
        # 禁用自动格式化
        document = self.document()
        document.setDefaultStyleSheet("")
        # 确保没有HTML格式处理
        self.setAutoFormatting(QTextEdit.AutoNone)
        # 设置纯文本编辑模式
        self.setPlainText("")
        
        # 创建图片预览容器（重叠在文本编辑框上）
        self.images_container = QWidget(self)
        self.images_layout = QHBoxLayout(self.images_container)
        self.images_layout.setContentsMargins(5, 5, 5, 5)
        self.images_layout.setSpacing(5)
        self.images_layout.setAlignment(Qt.AlignLeft)
        
        # 设置图片容器的背景和样式
        self.images_container.setStyleSheet("""
            background-color: rgba(40, 40, 40, 180);
            border-top: 1px solid #444;
            border-radius: 0px;
            padding: 3px;
        """)
        
        # 默认隐藏图片预览区域
        self.images_container.setVisible(False)
        
        # 直接设置文本颜色和字体大小
        self.setStyleSheet("""
            QTextEdit {
                color: #ffffff;
                font-size: 11pt;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
    def resizeEvent(self, event):
        """当文本框大小改变时，调整图片预览容器的位置和大小"""
        super().resizeEvent(event)
        # 设置图片容器位置在底部
        container_height = 60
        self.images_container.setGeometry(0, self.height() - container_height, self.width(), container_height)
        
        # 如果图片预览区域可见，为文本区域设置底部边距
        if self.images_container.isVisible():
            self.setViewportMargins(0, 0, 0, container_height)
        else:
            self.setViewportMargins(0, 0, 0, 0)
            
    def showEvent(self, event):
        """当控件显示时，调整图片预览容器位置"""
        super().showEvent(event)
        container_height = 60
        self.images_container.setGeometry(0, self.height() - container_height, self.width(), container_height)
        
        # 根据图片预览区域可见性设置边距
        if self.images_container.isVisible():
            self.setViewportMargins(0, 0, 0, container_height)

    def keyPressEvent(self, event: QKeyEvent):
        # 添加对BackSpace键的特殊处理，提高删除文字时的响应速度
        if event.key() == Qt.Key_Backspace:
            # 获取当前光标位置
            cursor = self.textCursor()
            # 直接调用标准删除操作，而不触发额外的处理
            if not cursor.hasSelection():
                # 如果没有选择文本，则简单地删除前一个字符
                cursor.deletePreviousChar()
            else:
                # 如果有选择文本，则删除选定内容
                cursor.removeSelectedText()
            # 不调用父类方法，避免额外处理
            return
            
        # 按Enter键发送消息，按Shift+Enter换行
        elif event.key() == Qt.Key_Return:
            # 如果按下Shift+Enter，则执行换行操作
            if event.modifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event)
            # 如果按下Ctrl+Enter或单独按Enter，则发送消息
            elif event.modifiers() == Qt.ControlModifier or event.modifiers() == Qt.NoModifier:
                # 查找父FeedbackUI实例并调用提交方法
                parent = self.parent()
                while parent and not isinstance(parent, FeedbackUI):
                    parent = parent.parent()
                if parent:
                    # 调用父窗口的提交方法（已优化为使用按键序列）
                    parent._submit_feedback()
            else:
                super().keyPressEvent(event)
        # 处理Ctrl+V粘贴图片
        elif event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            # 查找剪贴板是否有图片
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            # 如果剪贴板有图片且有父FeedbackUI实例，则调用粘贴图片方法
            if mime_data.hasImage():
                parent = self.parent()
                while parent and not isinstance(parent, FeedbackUI):
                    parent = parent.parent()
                if parent:
                    # 如果成功处理了图片粘贴，则不执行默认粘贴行为
                    if parent.handle_paste_image():
                        return
            
            # 如果没有图片或没找到父FeedbackUI实例，则执行默认粘贴行为
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
            
    def insertFromMimeData(self, source):
        # 处理粘贴内容，包括图片和文本
        handled = False
        
        # 如果有图片，先尝试处理图片
        if source.hasImage():
            # 寻找父FeedbackUI实例
            parent = self.parent()
            while parent and not isinstance(parent, FeedbackUI):
                parent = parent.parent()
                
            # 如果找到父实例，使用其处理图片
            if parent:
                image = source.imageData()
                if image and not image.isNull():
                    pixmap = QPixmap.fromImage(QImage(image))
                    if not pixmap.isNull():
                        parent.add_image_preview(pixmap)
                        handled = True
                        print("DEBUG: insertFromMimeData处理了图片内容", file=sys.stderr)
        
        # 处理文本内容（即使已处理了图片）
        if source.hasText():
            text = source.text().strip()
            if text:
                # 确保只插入纯文本，忽略所有格式
                self.insertPlainText(text)
                handled = True
                print("DEBUG: insertFromMimeData处理了文本内容", file=sys.stderr)
        
        # 如果没有处理任何内容，调用父类方法
        if not handled:
            super().insertFromMimeData(source)

    def show_images_container(self, visible):
        """显示或隐藏图片预览容器"""
        self.images_container.setVisible(visible)
        container_height = 60 if visible else 0
        self.setViewportMargins(0, 0, 0, container_height)
        # 强制重新绘制
        self.viewport().update()

class ImagePreviewWidget(QWidget):
    """图片预览小部件，鼠标悬停时放大，支持删除功能"""
    
    image_deleted = Signal(int)  # 图片删除信号，参数为图片ID
    
    def __init__(self, image_pixmap, image_id, parent=None):
        super().__init__(parent)
        self.image_pixmap = image_pixmap
        self.image_id = image_id
        self.original_pixmap = image_pixmap  # 保存原始图片
        self.is_hovering = False
        self.hover_color = False  # 控制悬停时的颜色变化
        
        # 设置固定大小，让图片预览图标更小，适合显示在输入框底部
        self.setFixedSize(48, 48)
        
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        # 图片缩略图标签
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        # 缩放图片创建缩略图
        thumbnail = image_pixmap.scaled(
            44, 44, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.original_thumbnail = thumbnail  # 保存原始缩略图
        self.red_thumbnail = self._create_red_thumbnail(thumbnail)  # 创建浅红色缩略图
        self.thumbnail_label.setPixmap(thumbnail)
        
        # 删除按钮放在右上角
        layout.addWidget(self.thumbnail_label)
        
        # 设置小部件样式
        self.setStyleSheet("""
            ImagePreviewWidget {
                background-color: rgba(51, 51, 51, 200);
                border: 1px solid #555;
                border-radius: 4px;
                margin: 2px;
            }
            ImagePreviewWidget:hover {
                border: 1px solid #2a82da;
            }
        """)
        
        # 设置工具提示
        self.setToolTip("悬停查看大图，点击图标删除图片")
        
        # 确保鼠标跟踪，以便接收鼠标悬停事件
        self.setMouseTracking(True)
    
    def _create_red_thumbnail(self, pixmap):
        """创建浅红色版本的缩略图"""
        if pixmap.isNull():
            return pixmap
            
        # 创建一个新的pixmap
        red_pixmap = QPixmap(pixmap.size())
        red_pixmap.fill(Qt.transparent)
        
        # 创建QPainter来绘制红色效果
        painter = QPainter(red_pixmap)
        
        # 先绘制原始图片
        painter.drawPixmap(0, 0, pixmap)
        
        # 添加一个红色半透明层
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        painter.fillRect(red_pixmap.rect(), QColor(255, 100, 100, 160))
        
        # 结束绘制
        painter.end()
        
        return red_pixmap
    
    def enterEvent(self, event):
        """鼠标进入事件，显示大图预览并变为浅红色"""
        self.is_hovering = True
        self.hover_color = True
        
        # 更新缩略图为红色
        self.thumbnail_label.setPixmap(self.red_thumbnail)
        
        # 显示大图预览
        self._show_full_image()
        return super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件，隐藏大图预览并恢复颜色"""
        self.is_hovering = False
        self.hover_color = False
        
        # 恢复原始缩略图
        self.thumbnail_label.setPixmap(self.original_thumbnail)
        
        QToolTip.hideText()
        
        # 关闭预览窗口
        if hasattr(self, 'preview_window') and self.preview_window:
            self.preview_window.close()
            
        return super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """处理鼠标点击事件，点击图标直接删除"""
        if event.button() == Qt.LeftButton:
            # 点击图标任何位置都删除图片
            self._delete_image()
            return
        return super().mousePressEvent(event)
        
    def _show_full_image(self):
        """显示大图预览"""
        if self.is_hovering and not self.original_pixmap.isNull():
            # 限制预览图最大尺寸
            max_width = 400
            max_height = 300
            
            # 调整图片大小，保持纵横比
            preview_pixmap = self.original_pixmap
            if preview_pixmap.width() > max_width or preview_pixmap.height() > max_height:
                preview_pixmap = preview_pixmap.scaled(
                    max_width, max_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            
            # 创建一个QLabel来显示图片
            preview_label = QLabel()
            preview_label.setPixmap(preview_pixmap)
            preview_label.setStyleSheet("background-color: #333; padding: 5px; border: 1px solid #666;")
            
            # 获取当前鼠标位置
            cursor_pos = QCursor.pos()
            
            # 显示工具提示
            QToolTip.showText(
                cursor_pos,
                f"<div style='background-color: #333; padding: 10px; border: 1px solid #666;'>"
                f"<div style='color: white; margin-bottom: 5px;'>图片预览 ({self.original_pixmap.width()}x{self.original_pixmap.height()})</div>"
                f"</div>",
                self
            )
            
            # 创建一个无模态对话框显示图片预览
            self.preview_window = QMainWindow(self)
            self.preview_window.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
            self.preview_window.setAttribute(Qt.WA_DeleteOnClose)
            self.preview_window.setAttribute(Qt.WA_TranslucentBackground)
            
            # 创建中央部件
            preview_widget = QWidget()
            preview_layout = QVBoxLayout(preview_widget)
            preview_layout.setContentsMargins(10, 10, 10, 10)
            
            # 添加图片标签
            preview_image_label = QLabel()
            preview_image_label.setPixmap(preview_pixmap)
            preview_image_label.setAlignment(Qt.AlignCenter)
            preview_image_label.setStyleSheet("background-color: #333; padding: 5px; border: 1px solid #666; border-radius: 4px;")
            preview_layout.addWidget(preview_image_label)
            
            # 添加图片信息标签
            info_label = QLabel(f"尺寸: {self.original_pixmap.width()} x {self.original_pixmap.height()} 像素")
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet("color: white; background-color: #333; padding: 5px;")
            preview_layout.addWidget(info_label)
            
            self.preview_window.setCentralWidget(preview_widget)
            
            # 调整大小
            self.preview_window.resize(preview_pixmap.width() + 30, preview_pixmap.height() + 70)
            
            # 移动到合适位置
            cursor_pos = QCursor.pos()
            preview_window_x = cursor_pos.x() + 20
            preview_window_y = cursor_pos.y() + 20
            
            # 确保预览窗口不会超出屏幕边界
            screen = QApplication.primaryScreen().geometry()
            if preview_window_x + self.preview_window.width() > screen.width():
                preview_window_x = screen.width() - self.preview_window.width()
            if preview_window_y + self.preview_window.height() > screen.height():
                preview_window_y = screen.height() - self.preview_window.height()
                
            self.preview_window.move(preview_window_x, preview_window_y)
            
            # 显示预览窗口
            self.preview_window.show()
    
    def _delete_image(self):
        """删除图片"""
        self.image_deleted.emit(self.image_id)
        self.deleteLater()  # 从UI中移除此部件

class FeedbackUI(QMainWindow):
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None):
        """初始化交互式反馈UI
        
        Args:
            prompt (str): 要显示的提示
            predefined_options (Optional[List[str]], optional): 预定义选项列表. Defaults to None.
        """
        super().__init__()
        
        print("初始化FeedbackUI...", file=sys.stderr)
        self.prompt = prompt
        
        # 添加调试信息，查看收到的选项
        print(f"DEBUG: 收到的预定义选项: {predefined_options}", file=sys.stderr)
        self.predefined_options = predefined_options or []
        print(f"DEBUG: 初始化使用的预定义选项: {self.predefined_options}", file=sys.stderr)

        self.result = None  # 使用统一的属性名 result
        self.image_pixmap = None  # 存储粘贴的图片
        self.next_image_id = 0  # 用于生成唯一的图片ID
        self.image_widgets = {}  # 存储图片预览部件 {id: widget}
        
        # 用于控制是否自动最小化的标志
        self.disable_auto_minimize = False
        
        # 用于记录是否已尝试过直接对话模式
        self.attempted_direct_dialog = False
        
        # 设置窗口标题和窗口最小宽度
        self.setWindowTitle("Interactive Feedback MCP")
        self.setMinimumWidth(1000)  # 明确设置最小宽度为1000
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "images", "feedback.png")
        
        # 尝试加载图标，如果不存在则创建一个空目录确保后续程序正确运行
        try:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # 如果图标文件不存在，确保images目录存在
                images_dir = os.path.join(script_dir, "images")
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir, exist_ok=True)
                print(f"警告: 图标文件不存在: {icon_path}", file=sys.stderr)
        except Exception as e:
            print(f"警告: 无法加载图标文件: {e}", file=sys.stderr)
        
        # 移除窗口总在最前的行为，但保留标准窗口按钮
        # 设置新的窗口标志，明确包含标准窗口按钮
        self.setWindowFlags(Qt.Window)  # 使用标准窗口类型，包含所有标准按钮
        
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # 首先设置我们想要的默认窗口大小，这样即使恢复几何失败也能保持这个尺寸
        self.resize(1000, 750)  # 将高度从600增加到750
        self.setMinimumHeight(700)  # 设置最小高度
        
        # 窗口居中显示
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - 1000) // 2
        y = (screen.height() - 750) // 2
        self.move(x, y)
        
        # 然后尝试加载保存的布局设置，但确保窗口宽度至少为1000
        self.settings.beginGroup("MainWindow_General")
        geometry = self.settings.value("geometry")
        if geometry:
            # 先恢复几何
            self.restoreGeometry(geometry)
            # 然后检查窗口宽度是否满足最小要求
            if self.width() < 1000:
                self.setMinimumWidth(1000)
                self.resize(1000, self.height())
                print(f"DEBUG: 应用最小宽度1000 (恢复的宽度为 {self.width()})", file=sys.stderr)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        self.settings.endGroup() # End "MainWindow_General" group

        print("开始创建UI...", file=sys.stderr)
        self._create_ui()
        print("UI创建完成", file=sys.stderr)

    def _create_ui(self):
        print("创建中央窗口部件...", file=sys.stderr)
        # 创建中央窗口部件
        central_widget = QWidget()
        central_widget.setMinimumWidth(1000)  # 确保中央部件也足够宽
        self.setCentralWidget(central_widget)
        
        # 主布局 - 垂直布局，减小边距使界面更紧凑
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        print("创建反馈分组框...", file=sys.stderr)
        # 创建反馈分组框
        self.feedback_group = QGroupBox("Feedback")
        self.feedback_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feedback_group.setMinimumWidth(980)  # 留出一些边距
        
        # 反馈区域布局 - 垂直布局
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setContentsMargins(12, 15, 12, 15)  # 增加内边距
        feedback_layout.setSpacing(15)  # 增加元素间距
        
        # 创建提示文字的滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内部控件调整大小
        scroll_area.setFrameShape(QFrame.NoFrame)  # 无边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示垂直滚动条
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 设置滚动区域的最大高度，确保不会占用太多空间
        scroll_area.setMaximumHeight(200)  # 从140增加到200，以显示更多提示文本
        
        # 创建容器小部件用于放置描述标签
        description_container = QWidget()
        description_layout = QVBoxLayout(description_container)
        description_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加描述标签
        self.description_label = QLabel(self.prompt)
        self.description_label.setWordWrap(True)
        self.description_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.description_label.setStyleSheet("font-weight: bold; margin-bottom: 8px;")  # 添加粗体和底部间距
        # 启用文本选择
        self.description_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        description_layout.addWidget(self.description_label)
        
        # 添加图片处理说明
        self.image_usage_label = QLabel("提示: 当您添加图片后，点击提交按钮将直接激活Cursor对话框，并自动填充内容。")
        self.image_usage_label.setWordWrap(True)
        self.image_usage_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.image_usage_label.setStyleSheet("color: #ff8c00; font-style: italic; font-size: 10pt; margin-top: 5px;")
        # 启用文本选择
        self.image_usage_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.image_usage_label.setVisible(False)  # 初始隐藏，只有添加图片后才显示
        description_layout.addWidget(self.image_usage_label)
        
        # 粘贴优化提示（仅在首次启动时显示，现在默认不显示）
        self.paste_optimization_label = QLabel("新功能: 已优化粘贴后的发送逻辑，图片和文本会一次性完整发送到Cursor。使用Ctrl+V粘贴内容。")
        self.paste_optimization_label.setWordWrap(True)
        self.paste_optimization_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paste_optimization_label.setStyleSheet("color: #4caf50; font-style: italic; font-size: 10pt; margin-top: 5px;")
        # 启用文本选择
        self.paste_optimization_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # 默认隐藏粘贴优化提示
        self.paste_optimization_label.setVisible(False)
        description_layout.addWidget(self.paste_optimization_label)
        
        # 创建状态标签
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_label.setAlignment(Qt.AlignLeft)
        # 启用文本选择
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_label.setVisible(False)  # 初始不可见
        description_layout.addWidget(self.status_label)

        # 将容器设置为滚动区域的小部件
        scroll_area.setWidget(description_container)
        
        # 将滚动区域添加到反馈布局
        feedback_layout.addWidget(scroll_area)

        # 添加预定义选项（如果有）
        self.option_checkboxes = [] # 存储 QCheckBox 实例
        self.option_labels = [] # 存储 QLabel 实例
        
        # 创建选项框架，无论是否有预定义选项都创建
        options_frame = QFrame()
        options_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        options_frame.setMinimumWidth(950)  # 确保选项区域足够宽
        
        # 选项布局 - 垂直或网格布局，优化间距和边距
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(2, 2, 2, 2)  # 减少所有边距，使元素更紧凑
        options_layout.setSpacing(2)  # 进一步减小间距

        # 不添加常用语按钮，因为已经在顶部添加了
        
        # 如果有预定义选项时，创建复选框和标签
        if self.predefined_options and len(self.predefined_options) > 0:
            for option_text in self.predefined_options:
                option_row_layout = QHBoxLayout()
                option_row_layout.setContentsMargins(0, 0, 0, 0)
                option_row_layout.setSpacing(5)  # 减小间距
                
                # 创建复选框 - 不再包含文本
                checkbox = QCheckBox()
                checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 固定大小
                self.option_checkboxes.append(checkbox)
                
                # 直接将复选框添加到行布局，不再使用额外的容器布局
                option_row_layout.addWidget(checkbox)
                
                # 创建文本标签 - 使用ClickableLabel，仅用于显示和文本选择
                label = ClickableLabel(option_text)
                label.setWordWrap(True)
                self.option_labels.append(label)
                
                # 将标签添加到行布局，调整权重
                option_row_layout.addWidget(label)
                
                # 确保标签获取所有额外空间
                option_row_layout.setStretchFactor(checkbox, 0)  # 复选框不伸缩
                option_row_layout.setStretchFactor(label, 1)     # 标签获取所有额外空间
                
                # 将行布局添加到选项布局
                options_layout.addLayout(option_row_layout)
        
        # 添加选项框架和常用语按钮容器到布局
        feedback_layout.addWidget(options_frame)
        #feedback_layout.addWidget(canned_responses_container)  # 已经添加到options_layout中，不需要再次添加
            
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        feedback_layout.addWidget(separator)

        # 自由文本反馈区
        # 创建文本编辑区和提交按钮的容器
        text_input_container = QWidget()
        text_input_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_input_container.setMinimumWidth(950)  # 确保文本输入区域足够宽
        text_input_layout = QVBoxLayout(text_input_container)
        text_input_layout.setContentsMargins(0, 0, 0, 0)
        text_input_layout.setSpacing(8)
        
        # 文本编辑框
        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feedback_text.setMinimumWidth(950)  # 确保文本编辑框足够宽
        self.feedback_text.setMinimumHeight(220)  # 设置最小高度为220，增加可见行数
        self.feedback_text.setPlaceholderText("在此输入反馈内容 (纯文本格式，按Enter发送，Shift+Enter换行，Ctrl+V粘贴图片)")
        

        
        # 连接文本变化信号，更新提交按钮文本
        self.feedback_text.textChanged.connect(self._update_submit_button_text)
        
        # 功能按钮区域 - 总是创建，确保界面完整
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        # 添加常用语按钮到左下角
        self.bottom_canned_responses_button = QPushButton("常用语")
        self.bottom_canned_responses_button.setFixedSize(100, 30)  # 调整大小
        self.bottom_canned_responses_button.setToolTip("选择或管理常用反馈短语")
        # 直接连接到_show_canned_responses方法
        self.bottom_canned_responses_button.clicked.connect(self._show_canned_responses)
        self.bottom_canned_responses_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """)
        buttons_layout.addWidget(self.bottom_canned_responses_button)
        
        # 添加弹性空间，将后续按钮推到右侧
        buttons_layout.addStretch(1)
        
        # 按顺序添加所有控件到文本输入布局
        text_input_layout.addWidget(self.feedback_text, 1)  # 设置拉伸因子为1，允许垂直拉伸
        text_input_layout.addWidget(buttons_container)  # 添加功能按钮区域
        
        # 提交按钮 - 修改为占据整行，使其更明显
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.submit_button.setMinimumHeight(50)  # 增加按钮高度
        self.submit_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """)
        self.submit_button.clicked.connect(self._submit_feedback)
        text_input_layout.addWidget(self.submit_button)  # 直接添加到主布局，占据整行
        
        # 将文本输入容器添加到反馈布局
        feedback_layout.addWidget(text_input_container, 1)  # 设置拉伸因子为1，允许垂直拉伸
        
        # 将反馈分组框添加到主布局
        main_layout.addWidget(self.feedback_group)
        
        # 初始更新一次提交按钮文本
        self._update_submit_button_text()
        
        print(f"UI创建完成，包含 {len(self.option_checkboxes)} 个选项复选框", file=sys.stderr)

    def get_image_content_data(self, image_id=None):
        """
        获取指定ID或最后一个图片的 Base64 编码数据和 MIME 类型，以及图片元数据。
        返回一个包含图片元数据和Base64编码数据的字典。
        如果无有效图片或处理失败，则返回 None。
        
        Args:
            image_id: 指定图片ID，如果为None则使用最后添加的图片
        
        Returns:
            dict: 包含以下键的字典:
                - image_data: 包含type, data, mimeType的图片数据字典
                - metadata: 包含width, height, format, size的元数据字典
                如果处理失败则返回None
        """
        print(f"DEBUG: 开始处理图片 ID: {image_id}", file=sys.stderr)
        
        # 如果指定了ID，使用该ID的图片，否则使用最后一个图片
        if image_id is not None and image_id in self.image_widgets:
            pixmap_to_save = self.image_widgets[image_id].original_pixmap
            print(f"DEBUG: 使用指定图片 ID: {image_id}", file=sys.stderr)
        elif self.image_widgets:
            # 使用最后一个图片ID
            last_id = max(self.image_widgets.keys())
            pixmap_to_save = self.image_widgets[last_id].original_pixmap
            print(f"DEBUG: 使用最后一个图片 ID: {last_id}", file=sys.stderr)
        else:
            # 没有图片
            print("DEBUG: 没有找到有效图片", file=sys.stderr)
            return None
            
        # 检查图片是否有效
        if pixmap_to_save is None or pixmap_to_save.isNull():
            print("DEBUG: 图片无效 (None 或 isNull)", file=sys.stderr)
            return None
            
        # 记录原始图片信息
        original_width = pixmap_to_save.width()
        original_height = pixmap_to_save.height()
        print(f"DEBUG: 原始图片尺寸: {original_width}x{original_height}", file=sys.stderr)
        
        # 检查并缩放图片，确保不超过最大尺寸限制
        if original_width > MAX_IMAGE_WIDTH or original_height > MAX_IMAGE_HEIGHT:
            print(f"DEBUG: 图片尺寸超过限制，进行缩放", file=sys.stderr)
            # 保持长宽比例缩放
            pixmap_to_save = pixmap_to_save.scaled(
                MAX_IMAGE_WIDTH, 
                MAX_IMAGE_HEIGHT,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            print(f"DEBUG: 缩放后图片尺寸: {pixmap_to_save.width()}x{pixmap_to_save.height()}", file=sys.stderr)
        
        # 将 QPixmap 保存为字节数据
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        
        # 默认使用 JPEG 格式，固定质量为80
        save_format = "JPEG"
        mime_type = "image/jpeg"
        saved_successfully = False
        quality = 80  # 固定JPEG质量为80
        
        if buffer.open(QIODevice.WriteOnly):
            if pixmap_to_save.save(buffer, save_format, quality):
                saved_successfully = True
                print(f"DEBUG: 成功保存为 JPEG 格式, 质量: {quality}%, 大小: {byte_array.size()} 字节", file=sys.stderr)
            else:
                print(f"DEBUG: JPEG 格式保存失败 (质量: {quality}%)", file=sys.stderr)
            buffer.close()
        
        # 如果 JPEG 保存失败或文件仍然过大，尝试降低质量
        if (not saved_successfully or byte_array.isEmpty() or 
            (byte_array.size() > MAX_IMAGE_BYTES)):
                
            print(f"DEBUG: JPEG 质量 {quality}% 后文件仍然过大 ({byte_array.size()} 字节)，尝试降低质量", file=sys.stderr)
            
            # 尝试不同的质量级别，以找到适合的大小
            quality_levels = [70, 60, 50, 40]
            
            for lower_quality in quality_levels:
                byte_array.clear()
                buffer = QBuffer(byte_array)
                
                if buffer.open(QIODevice.WriteOnly):
                    if pixmap_to_save.save(buffer, save_format, lower_quality):
                        saved_successfully = True
                        print(f"DEBUG: 成功保存为 JPEG 格式，降低质量至: {lower_quality}%, 大小: {byte_array.size()} 字节", file=sys.stderr)
                        buffer.close()
                        
                        # 如果文件大小满足要求，跳出循环
                        if byte_array.size() <= MAX_IMAGE_BYTES:
                            quality = lower_quality  # 更新使用的质量值
                            break
                    else:
                        print(f"DEBUG: JPEG 格式保存失败 (质量: {lower_quality}%)", file=sys.stderr)
                        buffer.close()
        
        if not saved_successfully or byte_array.isEmpty():
            print("ERROR: 无法将图片保存为 JPEG 格式", file=sys.stderr)
            QMessageBox.critical(self, "图像处理错误", "无法将图像保存为 JPEG 格式。")
            return None
            
        # 检查图片大小是否超过限制
        if byte_array.size() > MAX_IMAGE_BYTES:
            print(f"ERROR: 图片大小 ({byte_array.size()} 字节) 超过限制 ({MAX_IMAGE_BYTES} 字节)", file=sys.stderr)
            QMessageBox.critical(self, "图像过大", 
                              f"图像大小 ({byte_array.size() // 1024} KB) 超过了限制 ({MAX_IMAGE_BYTES // 1024} KB)。\n"
                              "请使用更小的图像或进一步压缩。")
            return None
            
        # 获取图片数据字节
        image_data = byte_array.data()
        if not image_data:
            print("ERROR: 保存操作后没有图片数据", file=sys.stderr)
            return None
        
        try:
            # 使用 Base64 编码图片数据
            base64_encoded_data = base64.b64encode(image_data).decode('utf-8')
            print(f"DEBUG: Base64编码成功, 编码后长度: {len(base64_encoded_data)}", file=sys.stderr)
            print(f"DEBUG: Base64编码前10个字符: {base64_encoded_data[:10]}...", file=sys.stderr)
            
            # 检查 Base64 编码是否有效
            try:
                # 尝试解码 Base64 字符串，验证其有效性
                decoded = base64.b64decode(base64_encoded_data)
                if len(decoded) != len(image_data):
                    print(f"WARNING: Base64解码后数据长度不匹配: {len(decoded)} vs 原始 {len(image_data)}", file=sys.stderr)
            except Exception as e:
                print(f"WARNING: Base64验证失败: {e}", file=sys.stderr)
                # 继续使用编码后的数据，不中断流程
            
            # 收集图片元数据
            processed_width = pixmap_to_save.width()
            processed_height = pixmap_to_save.height()
            format_type = save_format.lower()  # 如 'jpeg', 'png'
            byte_size = byte_array.size()
            
            # 构建元数据字典
            metadata = {
                "width": processed_width,
                "height": processed_height,
                "format": format_type,
                "size": byte_size
            }
            
            # 构建图片数据字典
            image_data_dict = {
                "type": "image",
                "data": base64_encoded_data,
                "mimeType": mime_type  # 确保 MIME 类型与实际保存的格式匹配
            }
            
            # 验证数据格式是否符合MCP要求
            if "type" not in image_data_dict or "data" not in image_data_dict or "mimeType" not in image_data_dict:
                print("WARNING: 返回的图片数据结构缺少必要字段", file=sys.stderr)
            
            print(f"DEBUG: 返回图片数据结构: type={image_data_dict['type']}, mimeType={image_data_dict['mimeType']}", file=sys.stderr)
            print(f"DEBUG: 返回图片元数据: {json.dumps(metadata)}", file=sys.stderr)
            
            # 返回包含图片数据和元数据的字典
            return {
                "image_data": image_data_dict,
                "metadata": metadata
            }
            
        except Exception as e:
            print(f"ERROR: Base64编码或元数据处理失败: {e}", file=sys.stderr)
            QMessageBox.critical(self, "图像处理错误", f"图像数据编码失败: {e}")
            return None
    
    def get_all_images_content_data(self):
        """
        获取所有图片的内容数据列表
        
        Returns:
            List[Dict]: 包含每张图片的元数据和图片数据的列表
                每个元素是一个字典，包含两个键：
                - metadata_item: 包含图片元数据的ContentItem字典
                - image_item: 包含图片数据的ContentItem字典
        """
        result = []
        print(f"DEBUG: 开始处理所有图片, 共 {len(self.image_widgets)} 张", file=sys.stderr)
        
        for image_id in self.image_widgets.keys():
            print(f"DEBUG: 处理图片 ID: {image_id}", file=sys.stderr)
            processed_data = self.get_image_content_data(image_id)
            if processed_data:
                # 从处理结果中提取元数据和图片数据
                metadata = processed_data["metadata"]
                image_data_dict = processed_data["image_data"]
                
                # 创建元数据文本项
                metadata_item = {
                    "type": "text",
                    "text": json.dumps(metadata)
                }
                
                # 图片数据项已经是正确格式
                image_item = image_data_dict
                
                # 将元数据和图片数据作为一对添加到结果列表
                result.append({
                    "metadata_item": metadata_item,
                    "image_item": image_item
                })
                print(f"DEBUG: 成功处理图片 ID: {image_id}", file=sys.stderr)
            else:
                print(f"DEBUG: 图片处理失败 ID: {image_id}", file=sys.stderr)
                
        print(f"DEBUG: 总共成功处理 {len(result)}/{len(self.image_widgets)} 张图片", file=sys.stderr)
        return result

    def _submit_feedback(self):
        # 获取纯文本反馈，确保使用toPlainText()
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []
        
        print("DEBUG: 开始提交反馈", file=sys.stderr)
        print(f"DEBUG: 反馈文本长度: {len(feedback_text)}", file=sys.stderr)
        
        # 获取所选择的预定义选项
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    # 确保选项文本是纯文本
                    selected_options.append(self.predefined_options[i].strip())
        
        print(f"DEBUG: 选定的选项数量: {len(selected_options)}", file=sys.stderr)
        if selected_options:
            print(f"DEBUG: 选定的选项: {selected_options}", file=sys.stderr)
        
        # 组合所有文本部分
        final_text_parts = []
        
        # 添加选定的选项
        if selected_options:
            final_text_parts.append("; ".join(selected_options))
        
        # 添加用户的文本反馈
        if feedback_text:
            final_text_parts.append(feedback_text)
        
        # 组合所有文本部分
        combined_text = "\n\n".join(final_text_parts)
        
        # 检查是否有图片
        has_images = bool(self.image_widgets)
        print(f"DEBUG: 检测到图片: {has_images}, 图片数量: {len(self.image_widgets) if has_images else 0}", file=sys.stderr)
        
        # 如果有图片，优先使用优化的按键序列
        if has_images:
            # 收集所有图片数据
            image_pixmaps = []
            for image_id in sorted(self.image_widgets.keys()):
                widget = self.image_widgets[image_id]
                if widget and hasattr(widget, 'original_pixmap'):
                    image_pixmaps.append(widget.original_pixmap)
            
            print(f"DEBUG: 准备使用优化按键序列发送 {len(image_pixmaps)} 张图片", file=sys.stderr)
            
            # 动态导入直接输入模块
            try:
                # 尝试导入优化的按键序列函数
                try:
                    from cursor_direct_input import send_to_cursor_with_sequence
                    use_optimized_sequence = True
                    print("DEBUG: 成功导入优化按键序列函数", file=sys.stderr)
                except (ImportError, AttributeError) as seq_error:
                    print(f"WARNING: 无法导入优化按键序列函数: {seq_error}, 将使用标准函数", file=sys.stderr)
                    use_optimized_sequence = False
                
                # 总是导入标准函数作为备用
                from cursor_direct_input import send_to_cursor_input
            except ImportError as e:
                print(f"ERROR: 无法导入cursor_direct_input模块: {e}", file=sys.stderr)
                QMessageBox.critical(
                    self,
                    "模块导入错误",
                    f"无法导入cursor_direct_input模块: {e}\n请确保已安装所需的依赖。"
                )
            else:
                # 模块导入成功后执行的代码
                # 隐藏窗口
                self.hide()
                
                # 先处理一下剩余的事件，确保窗口完全隐藏
                QApplication.processEvents()
                
                # 显示等待消息
                print("DEBUG: 即将激活Cursor对话框...", file=sys.stderr)
        
                # 尝试发送到Cursor对话框
                try:
                    # 尝试使用优化的按键序列发送内容
                    if use_optimized_sequence:
                        print("DEBUG: 使用优化按键序列发送内容...", file=sys.stderr)
                        success = send_to_cursor_with_sequence(combined_text, image_pixmaps)
                    else:
                        print("DEBUG: 使用标准方法发送内容...", file=sys.stderr)
                        success = send_to_cursor_input(combined_text, image_pixmaps)
                    
                    if success:
                        print("DEBUG: 成功发送到Cursor对话框，完全关闭MCP服务", file=sys.stderr)
                        # 设置空结果，表示已成功完成
                        self.result = {"content": []}
                        # 关闭窗口
                        self.close()
                        # 直接终止进程，确保MCP服务完全关闭
                        print("DEBUG: MCP服务已完成，即将退出进程", file=sys.stderr)
                        # 在应用程序退出前确保剩余事件被处理
                        QApplication.processEvents()
                        # 完全退出程序
                        sys.exit(0)
                        return
                    else:
                        # 发送失败，切换到标准MCP模式
                        print("DEBUG: 直接对话发送失败，使用标准MCP模式", file=sys.stderr)
                        # 重新显示窗口用于标准模式
                        self.show()
                except Exception as e:
                    print(f"ERROR: 直接对话模式错误: {e}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    
                    # 发生异常，重新显示窗口
                    self.show()
        
        # 纯文本模式或直接对话模式失败时使用标准MCP模式
        # 构建最终的 MCP 响应结构
        content_list = []
        
        # 添加文本内容
        if combined_text:
            content_list.append({
                "type": "text",
                "text": combined_text
            })
            print(f"DEBUG: 添加文本内容, 长度: {len(combined_text)}", file=sys.stderr)
        
        # 检查是否有内容可提交
        if not content_list:
            print("DEBUG: 没有内容可提交，直接关闭窗口", file=sys.stderr)
            # 设置空结果并关闭窗口，等同于用户直接关闭窗口
            self.close()
            return
        
        # 设置结果并关闭窗口
        self.result = {"content": content_list}
        print("DEBUG: 反馈结果设置完成，关闭窗口", file=sys.stderr)
        self.close()

    def closeEvent(self, event):
        # Save general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()

        super().closeEvent(event)

    def run(self) -> FeedbackResult:
        print("开始运行UI...", file=sys.stderr)
        self.show()
        print("UI窗口已显示，准备进入事件循环...", file=sys.stderr)
        
        # 添加一个单次定时器，在窗口显示后强制应用宽度
        # 这是处理某些系统上可能出现的窗口尺寸设置不正确的问题的方法
        QTimer.singleShot(100, self._enforce_window_size)
        
        QApplication.instance().exec()
        print("事件循环结束，窗口关闭...", file=sys.stderr)

        if not self.result:
            # 返回空的内容列表而不是空字符串
            print("未获得反馈结果，返回空内容列表", file=sys.stderr)
            return FeedbackResult(content=[])

        print(f"返回反馈结果: {self.result}", file=sys.stderr)
        return self.result
        
    def _enforce_window_size(self):
        """强制应用窗口尺寸，确保宽度为1000，高度至少为750"""
        needs_resize = False
        
        # 检查宽度
        if self.width() < 1000:
            print(f"DEBUG: 强制应用窗口宽度，当前宽度为 {self.width()}, 调整到 1000", file=sys.stderr)
            needs_resize = True
            
        # 检查高度
        if self.height() < 750:
            print(f"DEBUG: 强制应用窗口高度，当前高度为 {self.height()}, 调整到 750", file=sys.stderr)
            needs_resize = True
            
        # 如果需要调整大小
        if needs_resize:
            self.resize(1000, 750)
            # 居中显示
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 1000) // 2
            y = (screen.height() - 750) // 2
            self.move(x, y)

    def event(self, event):
        # 检测窗口失活事件
        if event.type() == QEvent.WindowDeactivate:
            # 如果窗口当前可见且未最小化，且未禁用自动最小化功能
            if self.isVisible() and not self.isMinimized() and not self.disable_auto_minimize:
                # 使用短延迟以避免立即最小化可能导致的焦点问题
                QTimer.singleShot(100, self.showMinimized)
        
        # 调用父类的event处理，确保其他事件正常处理
        return super().event(event)
        
    def handle_paste_image(self):
        """处理粘贴图片操作，支持同时处理文本和图片"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        handled_content = False
        
        # 检查是否有图片内容
        if mime_data.hasImage():
            # 从剪贴板获取图片
            image = clipboard.image()
            if not image.isNull():
                # 将QImage转换为QPixmap并保存
                pixmap = QPixmap.fromImage(image)
                self.add_image_preview(pixmap)
                handled_content = True
                print("DEBUG: 从剪贴板处理了图片内容", file=sys.stderr)
        
        # 检查是否有文本内容 (即使已处理了图片也检查文本)
        if mime_data.hasText():
            text = mime_data.text().strip()
            if text:
                # 只有当文本编辑框为空或当前没有选中文本时，才直接替换整个内容
                # 否则将文本插入到当前光标位置
                cursor = self.feedback_text.textCursor()
                if self.feedback_text.toPlainText().strip() == "" or cursor.hasSelection():
                    self.feedback_text.setPlainText(text)
                else:
                    # 在当前光标位置插入文本
                    self.feedback_text.insertPlainText(text)
                handled_content = True
                print("DEBUG: 从剪贴板处理了文本内容", file=sys.stderr)
        
        # 如果有URLs（可能是图片文件）且尚未处理图片，尝试处理
        if mime_data.hasUrls() and not handled_content:
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # 检查是否是图片文件
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            self.add_image_preview(pixmap)
                            handled_content = True
                            print(f"DEBUG: 从剪贴板URL处理了图片: {file_path}", file=sys.stderr)
                            break  # 只处理第一个有效图片文件
        
        # 更新提交按钮文本
        self._update_submit_button_text()
        
        return handled_content
    
    def add_image_preview(self, pixmap):
        """添加图片预览小部件"""
        if pixmap and not pixmap.isNull():
            # 创建唯一的图片ID
            image_id = self.next_image_id
            self.next_image_id += 1
            
            # 创建图片预览小部件
            image_widget = ImagePreviewWidget(pixmap, image_id, self)
            image_widget.image_deleted.connect(self.remove_image)
            
            # 添加到图片预览区域（文本编辑框内的容器）
            self.feedback_text.images_layout.addWidget(image_widget)
            self.image_widgets[image_id] = image_widget
            
            # 显示图片预览区域
            self.feedback_text.show_images_container(True)
            
            # 保存最后一个图片用于提交
            self.image_pixmap = pixmap
            
            # 不再显示清除图片按钮，因为已经移除了这个功能
            
            # 显示图片使用提示
            if hasattr(self, 'image_usage_label'):
                self.image_usage_label.setVisible(True)
            
            # 更新提交按钮文本
            self._update_submit_button_text()
            
            return image_id
        return None
    
    def remove_image(self, image_id):
        """移除图片预览小部件"""
        if image_id in self.image_widgets:
            # 移除小部件
            widget = self.image_widgets.pop(image_id)
            self.feedback_text.images_layout.removeWidget(widget)
            widget.deleteLater()
            
            # 如果没有图片了，隐藏图片预览区域和清除按钮
            if not self.image_widgets:
                self.feedback_text.show_images_container(False)
                self.image_pixmap = None
                # 不再显示清除图片按钮，因为已经移除了这个功能
                
                # 隐藏图片使用提示
                if hasattr(self, 'image_usage_label'):
                    self.image_usage_label.setVisible(False)
            else:
                # 更新最后一个图片
                last_id = max(self.image_widgets.keys())
                self.image_pixmap = self.image_widgets[last_id].original_pixmap
            
            # 更新提交按钮文本
            self._update_submit_button_text()
    
    def clear_all_images(self):
        """清除所有图片预览"""
        # 直接删除所有图片，不显示确认对话框
        
        # 复制ID列表，因为在循环中会修改字典
        image_ids = list(self.image_widgets.keys())
        for image_id in image_ids:
            self.remove_image(image_id)
        
        self.image_pixmap = None
        self.feedback_text.show_images_container(False)
        
        # 不再需要隐藏清除图片按钮，因为已经移除了这个功能
        
        # 隐藏图片使用提示
        if hasattr(self, 'image_usage_label'):
            self.image_usage_label.setVisible(False)
        
        # 更新提交按钮文本
        self._update_submit_button_text()
    
    def _update_submit_button_text(self):
        """根据当前输入情况更新提交按钮文本"""
        has_text = bool(self.feedback_text.toPlainText().strip())
        has_images = bool(self.image_widgets)
        
        if has_text and has_images:
            self.submit_button.setText(f"发送图片反馈 ({len(self.image_widgets)} 张)")
            self.submit_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff6f00;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 11pt;
                    min-width: 120px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #ff8f00;
                }
                QPushButton:pressed {
                    background-color: #e56a00;
                }
            """)
            # 更新提交按钮的工具提示
            self.submit_button.setToolTip("点击后将自动关闭窗口并激活Cursor对话框")
        elif has_images:
            self.submit_button.setText(f"发送 {len(self.image_widgets)} 张图片")
            self.submit_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff6f00;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                    font-size: 11pt;
                    min-width: 120px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #ff8f00;
                }
                QPushButton:pressed {
                    background-color: #e56a00;
                }
            """)
            self.submit_button.setToolTip("点击后将自动关闭窗口并激活Cursor对话框")
        elif has_text:
            self.submit_button.setText("提交反馈")
            self.submit_button.setStyleSheet("")  # 重置为默认样式
            self.submit_button.setToolTip("")  # 清除工具提示
        else:
            self.submit_button.setText("提交")
            self.submit_button.setStyleSheet("")  # 重置为默认样式
            self.submit_button.setToolTip("")  # 清除工具提示

    def _show_canned_responses(self):
        """显示常用语对话框"""
        # 临时禁用自动最小化功能
        self.disable_auto_minimize = True
        
        print("DEBUG: FeedbackUI._show_canned_responses - START", file=sys.stderr)
        
        try:
            # 获取常用语列表
            settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
            settings.beginGroup("CannedResponses")
            responses = settings.value("phrases", [])
            settings.endGroup()
            
            # 确保responses是列表
            if responses is None:
                responses = []
                print("DEBUG: 没有找到常用语设置，使用空列表", file=sys.stderr)
            elif not isinstance(responses, list):
                # 如果从QSettings读取的不是列表，尝试转换
                try:
                    if isinstance(responses, str):
                        responses = [responses]
                    else:
                        responses = list(responses)
                except:
                    responses = []
                print(f"DEBUG: 常用语设置不是列表，转换后: {responses}", file=sys.stderr)
            
            print(f"DEBUG: 加载常用语，数量: {len(responses)}", file=sys.stderr)
            if responses:
                print(f"DEBUG: 第一项: {responses[0]}", file=sys.stderr)
            
            # 显示常用语对话框
            dialog = SelectCannedResponseDialog(responses, self)
            dialog.setWindowModality(Qt.ApplicationModal)  # 设置为模态对话框
            print("DEBUG: FeedbackUI._show_canned_responses - About to call dialog.exec()", file=sys.stderr)
            dialog.exec()
            print("DEBUG: FeedbackUI._show_canned_responses - dialog.exec() finished", file=sys.stderr)
            
            # 注意：不需要检查结果，因为双击项目时会直接插入文本并关闭对话框
        finally:
            # 恢复自动最小化功能
            self.disable_auto_minimize = False
            print("DEBUG: FeedbackUI._show_canned_responses - END", file=sys.stderr)

    def _add_images_from_clipboard(self):
        """从剪贴板添加图片"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        added_images = 0
        
        # 检查剪贴板中是否有图片
        if mime_data.hasImage():
            pixmap = QPixmap(clipboard.pixmap())
            if not pixmap.isNull() and pixmap.width() > 0:
                self._add_image_widget(pixmap)
                added_images += 1
                print(f"DEBUG: 从剪贴板添加了图片，尺寸: {pixmap.width()}x{pixmap.height()}", file=sys.stderr)
        
        # 检查剪贴板中是否有URLs（可能是图片文件）
        if mime_data.hasUrls():
            for url in mime_data.urls():
                # 只处理本地文件URL
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    # 检查是否是图片文件
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            self._add_image_widget(pixmap)
                            added_images += 1
                            print(f"DEBUG: 从剪贴板URL添加了图片: {file_path}", file=sys.stderr)
        
        # 更新提交按钮文本
        self._update_submit_button_text()
        
        # 显示添加成功或失败的反馈
        if added_images > 0:
            self.status_label.setText(f"成功添加了 {added_images} 张图片")
            self.status_label.setStyleSheet("color: green;")
            
            # 显示图片处理提示
            if self.image_usage_label:
                self.image_usage_label.setVisible(True)
        else:
            self.status_label.setText("剪贴板中没有找到有效图片")
            self.status_label.setStyleSheet("color: #ff6f00;")
        
        # 使状态标签可见
        self.status_label.setVisible(True)
        
        # 设置定时器在3秒后隐藏状态标签
        QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))
        
        return added_images
        
    def _remove_image(self, widget):
        """移除图片控件"""
        if widget in self.image_widgets:
            self.image_widgets.remove(widget)
            # 从布局中移除并销毁控件
            self.images_layout.removeWidget(widget)
            widget.deleteLater()
            
            # 更新提交按钮文本
            self._update_submit_button_text()
            
            # 隐藏空的图片区域
            self.images_scroll_area.setVisible(len(self.image_widgets) > 0)
            
            # 更新图片处理提示标签的可见性
            if self.image_usage_label:
                self.image_usage_label.setVisible(len(self.image_widgets) > 0)
            
            # 显示反馈
            self.status_label.setText("已移除图片")
            self.status_label.setStyleSheet("color: green;")
            self.status_label.setVisible(True)
            
            # 设置定时器在3秒后隐藏状态标签
            QTimer.singleShot(3000, lambda: self.status_label.setVisible(False))
            
            print(f"DEBUG: 移除了图片，剩余 {len(self.image_widgets)} 张", file=sys.stderr)


class ManageCannedResponsesDialog(QDialog):
    """常用语管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置对话框属性
        self.setWindowTitle("管理常用语")
        self.resize(500, 500)  # 增加对话框尺寸
        self.setMinimumSize(400, 400)  # 增加最小尺寸
        
        # 设置模态属性
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        
        # 创建设置对象，用于存储常用语
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # 创建UI
        self._create_ui()
        
        # 加载常用语
        self._load_canned_responses()
    
    def _create_ui(self):
        """创建UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 添加说明标签
        description_label = QLabel("管理您的常用反馈短语。点击列表项进行编辑，编辑完成后点击\"更新\"按钮。")
        description_label.setWordWrap(True)
        # 启用文本选择
        description_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        main_layout.addWidget(description_label)
        
        # 创建列表部件
        self.responses_list = QListWidget()
        self.responses_list.setAlternatingRowColors(True)
        self.responses_list.setSelectionMode(QListWidget.SingleSelection)
        self.responses_list.itemClicked.connect(self._on_item_selected)
        main_layout.addWidget(self.responses_list)
        
        # 创建编辑区域
        edit_group = QGroupBox("编辑常用语")
        edit_layout = QVBoxLayout(edit_group)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语或编辑选中的项目")
        edit_layout.addWidget(self.input_field)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # 添加按钮
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self._add_response)
        buttons_layout.addWidget(self.add_button)
        
        # 更新按钮
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self._update_response)
        self.update_button.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.update_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self._delete_response)
        self.delete_button.setEnabled(False)  # 初始禁用
        buttons_layout.addWidget(self.delete_button)
        
        # 清空按钮
        self.clear_button = QPushButton("清空全部")
        self.clear_button.clicked.connect(self._clear_responses)
        buttons_layout.addWidget(self.clear_button)
        
        # 添加按钮布局到编辑区域
        edit_layout.addLayout(buttons_layout)
        
        # 添加编辑组到主布局
        main_layout.addWidget(edit_group)
        
        # 对话框底部按钮
        dialog_buttons_layout = QHBoxLayout()
        dialog_buttons_layout.setSpacing(10)
        
        # 添加弹性空间，将按钮推到右侧
        dialog_buttons_layout.addStretch()
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        dialog_buttons_layout.addWidget(self.close_button)
        
        # 添加对话框按钮布局到主布局
        main_layout.addLayout(dialog_buttons_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                font-size: 11pt;
                padding: 5px;
            }
            QLineEdit {
                font-size: 11pt;
                padding: 8px;
                height: 20px;
            }
            QPushButton {
                padding: 8px 16px;
                min-width: 80px;
            }
            QLabel {
                font-size: 10pt;
                color: #aaa;
            }
        """)
    
    def _load_canned_responses(self):
        """从设置加载常用语"""
        self.settings.beginGroup("CannedResponses")
        responses = self.settings.value("phrases", [])
        self.settings.endGroup()
        
        if responses:
            # 清空列表并添加项目
            self.responses_list.clear()
            for response in responses:
                if response.strip():  # 跳过空字符串
                    self.responses_list.addItem(response)
    
    def _save_canned_responses(self):
        """保存常用语到设置"""
        responses = []
        for i in range(self.responses_list.count()):
            responses.append(self.responses_list.item(i).text())
        
        self.settings.beginGroup("CannedResponses")
        self.settings.setValue("phrases", responses)
        self.settings.endGroup()
    
    def _on_item_selected(self, item):
        """处理项目选中事件"""
        if item:
            # 将选中的文本放入编辑框
            self.input_field.setText(item.text())
            
            # 启用更新和删除按钮
            self.update_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            # 禁用更新和删除按钮
            self.update_button.setEnabled(False)
            self.delete_button.setEnabled(False)
    
    def _add_response(self):
        """添加新的常用语"""
        text = self.input_field.text().strip()
        if text:
            # 检查是否已存在
            exists = False
            for i in range(self.responses_list.count()):
                item = self.responses_list.item(i)
                item_widget = self.responses_list.itemWidget(item)
                if item_widget:
                    # 获取文本标签
                    text_label = item_widget.layout().itemAt(0).widget()
                    if text_label and isinstance(text_label, QLabel) and text_label.text() == text:
                        exists = True
                        break
            
            if exists:
                QMessageBox.warning(self, "重复项", "此常用语已存在，请输入不同的内容。")
                return
                
            # 添加到列表
            self._add_item_to_list(text)
            
            # 保存设置
            self._save_responses()
            
            # 清空输入框
            self.input_field.clear()
            
            # 显示成功提示
            QToolTip.showText(
                QCursor.pos(),
                "成功添加常用语",
                self,
                QRect(),
                2000
            )
            
            print(f"DEBUG: 成功添加常用语: {text}", file=sys.stderr)
    
    def _update_response(self):
        """更新选中的常用语"""
        current_item = self.responses_list.currentItem()
        if current_item:
            text = self.input_field.text().strip()
            if text:
                # 检查是否与其他项重复（排除自身）
                for i in range(self.responses_list.count()):
                    item = self.responses_list.item(i)
                    if item != current_item and item.text() == text:
                        QMessageBox.warning(self, "重复项", "此常用语已存在，请输入不同的内容。")
                        return
                
                # 更新项目文本
                current_item.setText(text)
                
                # 保存设置
                self._save_canned_responses()
                
                # 清空输入框并重置按钮状态
                self.input_field.clear()
                self.update_button.setEnabled(False)
                self.delete_button.setEnabled(False)
    
    def _delete_response(self):
        """删除选中的常用语"""
        current_row = self.responses_list.currentRow()
        if current_row >= 0:
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除", 
                "确定要删除此常用语吗？", 
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 移除项目
                self.responses_list.takeItem(current_row)
                
                # 保存设置
                self._save_canned_responses()
                
                # 清空输入框并重置按钮状态
                self.input_field.clear()
                self.update_button.setEnabled(False)
                self.delete_button.setEnabled(False)
    
    def _clear_responses(self):
        """清空所有常用语"""
        if self.responses_list.count() > 0:
            # 确认清空
            reply = QMessageBox.question(
                self, "确认清空", 
                "确定要清空所有常用语吗？此操作不可撤销。", 
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 清空列表
                self.responses_list.clear()
                
                # 保存设置
                self._save_canned_responses()
                
                # 清空输入框并重置按钮状态
                self.input_field.clear()
                self.update_button.setEnabled(False)
                self.delete_button.setEnabled(False)
    
    def get_all_responses(self):
        """获取所有常用语"""
        responses = []
        for i in range(self.responses_list.count()):
            responses.append(self.responses_list.item(i).text())
        return responses

class SelectCannedResponseDialog(QDialog):
    """常用语选择对话框 - 完全重构版"""
    
    def __init__(self, responses, parent=None):
        super().__init__(parent)
        print("DEBUG: SelectCannedResponseDialog.__init__ - START", file=sys.stderr)
        self.setWindowTitle("常用语管理")
        self.resize(500, 450)
        self.setMinimumSize(450, 400)
        
        # 设置模态属性
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        
        # 保存父窗口引用和响应数据
        self.parent_window = parent
        self.selected_response = None
        
        # 确保responses是列表
        self.responses = responses if responses else []
        print(f"DEBUG: SelectCannedResponseDialog.__init__ - Received {len(self.responses)} responses", file=sys.stderr)
        
        # 创建设置对象
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # 创建界面
        self._create_ui()
        
        # 加载常用语数据
        self._load_responses()
        
        print(f"DEBUG: SelectCannedResponseDialog.__init__ - END, Loaded {len(self.responses)} responses into UI", file=sys.stderr)
    
    def _create_ui(self):
        """创建用户界面"""
        print("DEBUG: SelectCannedResponseDialog._create_ui - START", file=sys.stderr)
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题标签
        title = QLabel("常用语列表")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        # 提示标签
        hint = QLabel("双击插入文本，点击删除按钮移除项目")
        hint.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        layout.addWidget(hint)
        
        # 常用语列表 - 使用DraggableListWidget以支持拖拽排序
        self.list_widget = DraggableListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        
        # 禁止自动选择第一项
        self.list_widget.setProperty("NoAutoSelect", True)
        self.list_widget.setAttribute(Qt.WA_MacShowFocusRect, False)  # 在macOS上禁用焦点矩形
        
        # 连接双击信号 - 注意：我们需要同时连接自定义信号和标准信号
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        # 连接自定义双击信号到处理方法
        self.list_widget.item_double_clicked.connect(self._insert_text_to_parent)
        
        # 连接拖拽完成信号到保存响应函数
        self.list_widget.drag_completed.connect(self._save_responses)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
                font-size: 11pt;
            }
            QListWidget::item {
                border-bottom: 1px solid #444;
                padding: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #444444;
            }
            QListWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QListWidget::item:focus {
                background-color: transparent;
                border: none;
            }
        """)
        # 设置拖拽模式和提示
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setToolTip("拖拽项目可以调整顺序")
        # 禁用水平滚动条
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(self.list_widget, 1)  # 1表示可伸缩
        
        # 添加常用语区域
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语")
        self.input_field.returnPressed.connect(self._add_response)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                font-size: 11pt;
            }
        """)
        input_layout.addWidget(self.input_field)
        
        self.add_button = QPushButton("保存")
        self.add_button.clicked.connect(self._add_response)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
        """)
        input_layout.addWidget(self.add_button)
        
        layout.addLayout(input_layout)
        
        # 设置整体对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
            QLabel {
                color: white;
            }
        """)
        print("DEBUG: SelectCannedResponseDialog._create_ui - END", file=sys.stderr)
    
    def _load_responses(self):
        """加载常用语到列表"""
        print(f"DEBUG: SelectCannedResponseDialog._load_responses - START, {len(self.responses)} responses to load", file=sys.stderr)
        self.list_widget.clear()
        for i, response in enumerate(self.responses):
            print(f"DEBUG: SelectCannedResponseDialog._load_responses - Loading item {i+1}: '{response}'", file=sys.stderr)
            if response and response.strip():
                self._add_item_to_list(response)
        
        # 清除所有选择，避免第一项被自动选中
        self.list_widget.clearSelection()
        # 设置当前项为None，确保没有项目被选中
        self.list_widget.setCurrentItem(None)
        # 使用样式表禁用选中项的高亮
        current_stylesheet = self.list_widget.styleSheet()
        self.list_widget.setStyleSheet(current_stylesheet + """
            QListWidget::item:selected {
                background-color: transparent;
                border: none;
            }
        """)
        print("DEBUG: SelectCannedResponseDialog._load_responses - Cleared selection", file=sys.stderr)
        print("DEBUG: SelectCannedResponseDialog._load_responses - END", file=sys.stderr)
    
    def _add_item_to_list(self, text):
        """将常用语添加到列表 - 单行显示，过长省略"""
        print(f"DEBUG: SelectCannedResponseDialog._add_item_to_list - Adding: '{text}'", file=sys.stderr)
        # 创建列表项
        item = QListWidgetItem()
        self.list_widget.addItem(item)

        # 创建自定义小部件
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2) # 调整边距
        layout.setSpacing(5) # 调整间距

        # 文本标签 - 单行，过长省略
        label = QLabel(text)
        # 在PySide6中，QLabel没有setTextElideMode方法，但可以通过样式表和属性实现省略效果
        label.setStyleSheet("color: white; font-size: 11pt; text-overflow: ellipsis;")
        label.setWordWrap(False)  # 禁用自动换行
        # 设置最大宽度，以便在宽度受限时出现省略号
        label.setMaximumWidth(350) # 限制宽度，以便显示省略号
        # 设置属性以确保文本正确省略
        label.setAttribute(Qt.WA_TranslucentBackground)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # 允许水平扩展
        layout.addWidget(label, 1)  # 1表示可伸缩

        # 删除按钮 - 改为无文字的红色方块
        delete_btn = QPushButton("")  # 不显示文字
        delete_btn.setFixedSize(40, 25)  # 固定大小的方块
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f; /* 明显的红色 */
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f44336; /* 鼠标悬停时更亮的红色 */
            }
            QPushButton:pressed {
                background-color: #b71c1c; /* 按下时更深的红色 */
            }
        """)
        delete_btn.setToolTip("删除此常用语")  # 添加工具提示，代替文字说明
        delete_btn.clicked.connect(lambda: self._delete_response(text))
        layout.addWidget(delete_btn)

        # 设置小部件
        self.list_widget.setItemWidget(item, widget)

        # 设置固定项目高度以适应单行文本和按钮
        # 这个值可能需要根据字体大小和按钮高度微调
        font_metrics = QFontMetrics(label.font())
        single_line_height = font_metrics.height()
        button_height = delete_btn.sizeHint().height()
        item_height = max(single_line_height + 10, button_height + 10) # 确保至少能容纳按钮，并给文本留出边距
        item.setSizeHint(QSize(self.list_widget.viewport().width() - 10, item_height)) # 宽度适应视口
    
    def _add_response(self):
        """添加新的常用语"""
        text = self.input_field.text().strip()
        if not text:
            return
            
        # 检查是否重复
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                label = widget.layout().itemAt(0).widget()
                if label and isinstance(label, QLabel) and label.text() == text:
                    QMessageBox.warning(self, "重复项", "此常用语已存在")
                    return
        
        # 添加到列表
        self._add_item_to_list(text)
        
        # 更新内部数据
        self.responses.append(text)
        
        # 保存设置
        self._save_responses()
        
        # 清空输入框
        self.input_field.clear()
    
    def _delete_response(self, text):
        """删除常用语"""
        # 查找并删除项目
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                label = widget.layout().itemAt(0).widget()
                if label and isinstance(label, QLabel) and label.text() == text:
                    # 从列表中移除
                    self.list_widget.takeItem(i)
                    
                    # 从数据中移除
                    if text in self.responses:
                        self.responses.remove(text)
                    
                    # 保存设置
                    self._save_responses()
                    return
    
    def _on_item_double_clicked(self, item):
        """双击项目时插入文本到父窗口"""
        widget = self.list_widget.itemWidget(item)
        if widget:
            label = widget.layout().itemAt(0).widget()
            if label and isinstance(label, QLabel):
                text = label.text()
                print(f"DEBUG: 双击选择常用语: {text}", file=sys.stderr)
                
                # 插入到父窗口输入框
                if self.parent_window and hasattr(self.parent_window, 'feedback_text'):
                    self.parent_window.feedback_text.insertPlainText(text)
                    print("DEBUG: 已插入文本到输入框", file=sys.stderr)
                    
                    # 保存选择结果并关闭
                    self.selected_response = text
                    self.accept()
    
    def _save_responses(self):
        """保存常用语到设置"""
        # 在保存前更新responses列表，以确保顺序与UI中显示的一致
        self.responses = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget:
                label = widget.layout().itemAt(0).widget()
                if label and isinstance(label, QLabel):
                    text = label.text()
                    self.responses.append(text)
        
        print(f"DEBUG: SelectCannedResponseDialog._save_responses - Saving {len(self.responses)} responses", file=sys.stderr)
        
        # 保存到设置
        self.settings.beginGroup("CannedResponses")
        self.settings.setValue("phrases", self.responses)
        self.settings.endGroup()
        self.settings.sync()
        print(f"DEBUG: 已保存 {len(self.responses)} 个常用语", file=sys.stderr)
    
    def closeEvent(self, event):
        """关闭对话框时保存常用语顺序"""
        self._save_responses()
        super().closeEvent(event)
    
    def get_selected_response(self):
        """获取选择的常用语"""
        return self.selected_response

    def _insert_text_to_parent(self, text):
        """处理双击文本插入到父窗口的输入框
        
        这是一个新的方法，用于处理来自DraggableListWidget的双击信号
        """
        if text and self.parent_window and hasattr(self.parent_window, 'feedback_text'):
            # 插入文本并关闭对话框
            self.parent_window.feedback_text.insertPlainText(text)
            print(f"DEBUG: 通过新方法插入文本到输入框: {text}", file=sys.stderr)
            # 保存选定的常用语
            self.selected_response = text
            # 关闭对话框
            self.accept()
        else:
            print(f"DEBUG: 无法插入文本: text={bool(text)}, parent={bool(self.parent_window)}", file=sys.stderr)

# 添加自定义可拖放列表部件类
class DraggableListWidget(QListWidget):
    """可拖放列表部件，带增强的拖放和双击功能"""
    
    # 添加自定义信号，当拖放完成时发出
    drag_completed = Signal()
    item_double_clicked = Signal(str)  # 发送双击项的文本内容
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化拖拽起始位置
        self.drag_start_position = None
        
        # 启用基本拖放功能
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        
        # 禁用横向滚动条
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 使拖动项目更明显
        self.setAlternatingRowColors(True)
        
        # 禁用自动选择第一项
        self.setCurrentRow(-1)
        
        # 设置更大的图标和项目大小，使拖放区域更明确
        self.setIconSize(QSize(32, 32))
        self.setStyleSheet("""
            QListWidget {
                background-color: #333333;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px;
                font-size: 11pt;
            }
            QListWidget::item {
                border-bottom: 1px solid #404040;
                padding: 8px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected:!active {
                background-color: transparent;
            }
            QListWidget::item:selected:active {
                background-color: rgba(42, 130, 218, 0.5);
                border: 1px solid #2a82da;
            }
            /* 禁用横向滚动条 */
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
        """)
        
    def showEvent(self, event):
        """窗口显示时清除选择"""
        super().showEvent(event)
        # 确保没有选中项
        self.clearSelection()
        self.setCurrentItem(None)
    
    def mouseDoubleClickEvent(self, event):
        """重写鼠标双击事件处理，确保能正确捕获双击"""
        item = self.itemAt(event.pos())
        if item:
            item_widget = self.itemWidget(item)
            if item_widget:
                text_label = item_widget.layout().itemAt(0).widget()
                if text_label and isinstance(text_label, QLabel):
                    text = text_label.text()
                    print(f"DEBUG: 双击事件捕获，文本内容: {text}", file=sys.stderr)
                    # 发出自定义双击信号
                    self.item_double_clicked.emit(text)
                    return
        
        # 如果没有处理，调用基类方法
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """重写鼠标按下事件，改进拖拽行为"""
        if event.button() == Qt.LeftButton:
            # 记录拖拽起始位置
            self.drag_start_position = event.pos()
            # 获取当前项，用于拖拽
            self.drag_item = self.itemAt(event.pos())
        
        # 调用基类的鼠标按下事件处理
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """重写鼠标移动事件，优化拖拽触发条件"""
        if (event.buttons() & Qt.LeftButton) and self.drag_start_position:
            # 计算移动距离，如果超过阈值则开始拖拽
            distance = (event.pos() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                print("DEBUG: 开始拖拽操作", file=sys.stderr)
                # 如果有拖拽项，则选中它用于拖拽
                if hasattr(self, 'drag_item') and self.drag_item:
                    self.drag_item.setSelected(True)
                    
        # 调用基类方法继续处理
        super().mouseMoveEvent(event)
    
    def dropEvent(self, event):
        """重写dropEvent以在拖放完成后发出信号"""
        # 调用基类的dropEvent方法以正常处理拖放操作
        super().dropEvent(event)
        
        # 拖放完成后，清除选择状态
        QTimer.singleShot(100, self.clearSelection)
        
        # 拖放完成后发出信号
        print("DEBUG: 拖放操作完成，发出drag_completed信号", file=sys.stderr)
        self.drag_completed.emit()

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    print("进入feedback_ui函数...", file=sys.stderr)
    print(f"DEBUG: 函数接收到的预定义选项: {predefined_options}", file=sys.stderr)
    app = QApplication.instance() or QApplication()
    print("QApplication实例化完成", file=sys.stderr)
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")
    
    # 设置应用程序属性
    app.setQuitOnLastWindowClosed(True)
    
    print("设置应用程序样式完成", file=sys.stderr)
    
    # 应用全局样式表
    # 注意：以下样式表仅使用Qt支持的样式属性
    app.setStyleSheet("""
        /* 全局样式 */
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 10pt;
        }
        
        /* 分组框样式 */
        QGroupBox {
            border: 1px solid #555;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: rgba(45, 45, 45, 180);
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 8px;
            color: #aaa;
            font-weight: bold;
        }
        
        /* 标签样式 */
        QLabel {
            color: #ffffff;  /* 更亮的白色，用于提示文本 */
            padding: 2px;
            font-size: 11pt;
        }
        
        /* 按钮样式 */
        QPushButton {
            background-color: #2a82da;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 11pt;
            min-width: 120px;
            min-height: 36px;
        }
        
        QPushButton:hover {
            background-color: #3a92ea;
        }
        
        QPushButton:pressed {
            background-color: #1a72ca;
        }
        
        QPushButton:disabled {
            background-color: #555;
            color: #999;
        }
        
        /* 文本编辑框样式 */
        QTextEdit {
            background-color: #333;
            color: #ffffff;  /* 纯白色文本，提高可见度 */
            border: 1px solid #555;
            border-radius: 4px;
            padding: 4px;
            selection-background-color: #2a82da;
            font-size: 11pt;  /* 增加字体大小 */
        }
        
        QTextEdit:focus {
            border: 1px solid #2a82da;
        }
        
        /* 占位符文本样式 */
        QTextEdit[placeholderText] {
            color: #999;
        }
        
        /* 复选框样式 */
        QCheckBox {
            color: #b8b8b8;  /* 选项文本颜色 */
            spacing: 10px;
            font-size: 11pt;
            min-height: 30px;
            padding: 2px;
        }
        
        QCheckBox::indicator {
            width: 24px;
            height: 24px;
            border: 1px solid #555;
            border-radius: 4px;
            background-color: #333;
        }
        
        QCheckBox::indicator:checked {
            background-color: #2a82da;
            border: 1px solid #2a82da;
            border-width: 2px;
            border-color: #1a72ca;
        }
        
        QCheckBox::indicator:hover:!checked {
            border: 1px solid #2a82da;
            background-color: #3a3a3a;
        }
        
        QCheckBox::indicator:checked:hover {
            background-color: #3a92ea;
            border-width: 2px;
            border-color: #2a82da;
        }
        
        /* 添加QLabel样式来显示勾选标记 */
        QCheckBox::indicator:checked + QLabel {
            color: white;
        }
        
        /* 分隔线样式 */
        QFrame[frameShape="4"] {
            color: #444;
            max-height: 1px;
            margin: 10px 0;
        }
        
        /* 滚动区域样式 */
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 10px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #555;
            min-height: 20px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #777;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
    """)
    
    # 确保预定义选项是一个列表，即使是空列表
    if predefined_options is None:
        predefined_options = []
        print("未提供预定义选项，使用空列表", file=sys.stderr)
    
    print("准备创建FeedbackUI实例...", file=sys.stderr)
    ui = FeedbackUI(prompt, predefined_options)
    print("FeedbackUI实例创建完成，准备运行...", file=sys.stderr)
    result = ui.run()
    print("UI运行完成，获得结果", file=sys.stderr)

    if output_file and result:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        # Save the result to the output file
        with open(output_file, "w") as f:
            json.dump(result, f)
        return None

    return result

if __name__ == "__main__":
    print("开始执行主程序...", file=sys.stderr)
    parser = argparse.ArgumentParser(description="Run the feedback UI")
    parser.add_argument("--prompt", default="I implemented the changes you requested.", help="The prompt to show to the user")
    parser.add_argument("--predefined-options", default="", help="Pipe-separated list of predefined options (|||)")
    parser.add_argument("--output-file", help="Path to save the feedback result as JSON")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with more verbose output")
    parser.add_argument("--full-ui", action="store_true", default=False, help="显示完整UI界面，包含所有功能")
    args = parser.parse_args()
    
    print(f"命令行参数: {args}", file=sys.stderr)

    # 调试模式标志
    debug_mode = args.debug
    
    if debug_mode:
        print("DEBUG: 运行在调试模式", file=sys.stderr)
        
    # 处理预定义选项
    if args.predefined_options:
        # 有传入预定义选项，使用传入的选项
        predefined_options = [opt for opt in args.predefined_options.split("|||") if opt]
        print(f"使用传入的预定义选项: {predefined_options}", file=sys.stderr)
    else:
        # 没有传入预定义选项
        if args.full_ui:
            # 仅在手动运行脚本且明确指定--full-ui参数时才使用示例选项
            predefined_options = ["示例选项1", "示例选项2", "示例选项3"]
            print(f"启用完整UI模式并使用示例预定义选项: {predefined_options}", file=sys.stderr)
        else:
            # 没有选项
            predefined_options = []
            print("使用空选项列表", file=sys.stderr)
    
    print(f"最终使用的预定义选项: {predefined_options}", file=sys.stderr)
    
    print("创建UI...", file=sys.stderr)
    result = feedback_ui(args.prompt, predefined_options, args.output_file)
    print("UI执行完成", file=sys.stderr)
    if result:
        pretty_result = json.dumps(result, indent=2, ensure_ascii=False)
        print(f"\n反馈结果:\n{pretty_result}")
        
        # 在调试模式下验证结果格式
        if debug_mode:
            print("\nDEBUG: 验证反馈结果格式", file=sys.stderr)
            if "content" not in result:
                print("ERROR: 结果缺少 'content' 字段", file=sys.stderr)
            else:
                content = result["content"]
                if not isinstance(content, list):
                    print(f"ERROR: 'content' 不是列表类型: {type(content)}", file=sys.stderr)
                else:
                    print(f"DEBUG: 内容列表包含 {len(content)} 项", file=sys.stderr)
                    for i, item in enumerate(content):
                        if "type" not in item:
                            print(f"ERROR: 内容项 {i+1} 缺少 'type' 字段", file=sys.stderr)
                        elif item["type"] == "text":
                            if "text" not in item:
                                print(f"ERROR: 文本项 {i+1} 缺少 'text' 字段", file=sys.stderr)
                            else:
                                print(f"DEBUG: 文本项 {i+1} 有效，长度: {len(item['text'])}", file=sys.stderr)
                        elif item["type"] == "image":
                            if "data" not in item:
                                print(f"ERROR: 图片项 {i+1} 缺少 'data' 字段", file=sys.stderr)
                            elif "mimeType" not in item:
                                print(f"ERROR: 图片项 {i+1} 缺少 'mimeType' 字段", file=sys.stderr)
                            else:
                                print(f"DEBUG: 图片项 {i+1} 有效, MIME类型: {item['mimeType']}", file=sys.stderr)
                                print(f"DEBUG: Base64数据长度: {len(item['data'])}", file=sys.stderr)
                        else:
                            print(f"WARNING: 内容项 {i+1} 有未知类型: {item['type']}", file=sys.stderr)
            
    sys.exit(0)

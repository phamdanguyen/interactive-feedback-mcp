# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import argparse
import base64  # 确保导入 base64 模块
from typing import Optional, TypedDict, List, Dict, Any
from io import BytesIO  # 导入 BytesIO 用于处理二进制数据

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame, QSizePolicy, QScrollArea, QToolTip, QDialog, QListWidget,
    QMessageBox, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSettings, QEvent, QSize, QStringListModel, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QPixmap, QCursor, QPainter

# 添加图片处理相关常量
MAX_IMAGE_WIDTH = 1280  # 最大图片宽度 - 从1920降低到1280
MAX_IMAGE_HEIGHT = 720  # 最大图片高度 - 从1080降低到720
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 最大文件大小 (2MB) - 从5MB降低到2MB

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
        # 按Enter键发送消息，按Shift+Enter换行
        if event.key() == Qt.Key_Return:
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
        # 强制只插入纯文本，忽略所有格式
        if source.hasText():
            # 使用insertPlainText而不是默认的insertHtml或insertText
            self.insertPlainText(source.text())
        else:
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
        print("初始化FeedbackUI...", file=sys.stderr)
        super().__init__()
        self.prompt = prompt
        self.predefined_options = predefined_options or []

        self.feedback_result = None
        self.image_pixmap = None  # 存储粘贴的图片
        self.next_image_id = 0  # 用于生成唯一的图片ID
        self.image_widgets = {}  # 存储图片预览部件 {id: widget}
        
        # 用于控制是否自动最小化的标志
        self.disable_auto_minimize = False
        
        self.setWindowTitle("Interactive Feedback MCP")
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
        
        # Load general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(800, 600)
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 800) // 2
            y = (screen.height() - 600) // 2
            self.move(x, y)
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
        self.setCentralWidget(central_widget)
        
        # 主布局 - 垂直布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        print("创建反馈分组框...", file=sys.stderr)
        # 创建反馈分组框
        self.feedback_group = QGroupBox("Feedback")
        self.feedback_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 反馈区域布局 - 垂直布局
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setSpacing(12)

        # 创建提示文字的滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内部控件调整大小
        scroll_area.setFrameShape(QFrame.NoFrame)  # 无边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示垂直滚动条
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 设置滚动区域的最大高度，确保不会占用太多空间
        scroll_area.setMaximumHeight(150)  # 根据需要调整这个值
        
        # 创建容器小部件用于放置描述标签
        description_container = QWidget()
        description_layout = QVBoxLayout(description_container)
        description_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加描述标签
        self.description_label = QLabel(self.prompt)
        self.description_label.setWordWrap(True)
        self.description_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.description_label.setStyleSheet("font-weight: bold; margin-bottom: 8px;")  # 添加粗体和底部间距
        description_layout.addWidget(self.description_label)

        # 将容器设置为滚动区域的小部件
        scroll_area.setWidget(description_container)
        
        # 将滚动区域添加到反馈布局
        feedback_layout.addWidget(scroll_area)

        # 添加预定义选项（如果有）
        self.option_checkboxes = []
        
        # 创建选项框架，无论是否有预定义选项都创建
        options_frame = QFrame()
        options_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 选项布局 - 垂直或网格布局
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(2, 2, 2, 2)  # 减少所有边距，使元素更紧凑
        options_layout.setSpacing(4)  # 减小间距
        
        # 无论是否有预定义选项，都创建常用语按钮
        # 常用语按钮始终显示在外部区域
        canned_responses_container = QWidget()
        canned_layout = QHBoxLayout(canned_responses_container)
        canned_layout.setContentsMargins(0, 0, 0, 0)
        canned_layout.addStretch(1)  # 将按钮推到右侧
        
        # 常用语按钮
        canned_responses_button = QPushButton("常用语")
        canned_responses_button.setFixedSize(80, 30)  # 调整大小更明显
        canned_responses_button.setToolTip("选择或管理常用反馈短语")
        canned_responses_button.clicked.connect(self._show_canned_responses)
        canned_responses_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px;
                font-size: 10pt;
                font-weight: bold;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """)
        canned_layout.addWidget(canned_responses_button)
        
        # 如果有预定义选项时，创建复选框
        if self.predefined_options and len(self.predefined_options) > 0:
            # 创建复选框
            for option in self.predefined_options:
                # 创建水平布局用于放置选项
                option_row = QHBoxLayout()
                option_row.setContentsMargins(0, 0, 0, 0)
                
                # 创建复选框
                checkbox = QCheckBox(option)
                self.option_checkboxes.append(checkbox)
                option_row.addWidget(checkbox)
                
                # 添加到选项布局
                options_layout.addLayout(option_row)
        
        # 添加选项框架和常用语按钮容器到布局
        feedback_layout.addWidget(options_frame)
        feedback_layout.addWidget(canned_responses_container)
            
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        feedback_layout.addWidget(separator)

        # 自由文本反馈区
        # 创建文本编辑区和提交按钮的容器
        text_input_container = QWidget()
        text_input_layout = QVBoxLayout(text_input_container)
        text_input_layout.setContentsMargins(0, 0, 0, 0)
        text_input_layout.setSpacing(8)
        
        # 文本编辑框
        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feedback_text.setPlaceholderText("在此输入反馈内容 (纯文本格式，按Enter发送，Shift+Enter换行，Ctrl+V粘贴图片)")
        
        # 连接文本变化信号，更新提交按钮文本
        self.feedback_text.textChanged.connect(self._update_submit_button_text)
        
        # 功能按钮区域 - 总是创建，确保界面完整
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(8)
        
        # 添加清除所有图片按钮 - 初始不可见但会在需要时显示
        self.clear_images_button = QPushButton("清除所有图片")
        self.clear_images_button.setVisible(False)  # 初始隐藏，但布局中已预留位置
        self.clear_images_button.setToolTip("清除所有已粘贴的图片")
        self.clear_images_button.clicked.connect(self.clear_all_images)
        self.clear_images_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        buttons_layout.addWidget(self.clear_images_button)
        
        # 添加弹性空间，将后续按钮推到右侧
        buttons_layout.addStretch(1)
        
        # 按顺序添加所有控件到文本输入布局
        text_input_layout.addWidget(self.feedback_text, 1)  # 设置拉伸因子为1，允许垂直拉伸
        text_input_layout.addWidget(buttons_container)  # 添加功能按钮区域
        
        # 提交按钮 - 修改为占据整行，使其更明显
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.submit_button.setMinimumHeight(40)  # 设置按钮最小高度
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
        获取指定ID或最后一个图片的 Base64 编码数据和 MIME 类型。
        返回一个符合 MCP 服务要求的字典 {type: "image", data: base64_string, mimeType: "image/png"},
        如果无有效图片或处理失败，则返回 None。
        
        Args:
            image_id: 指定图片ID，如果为None则使用最后添加的图片
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
            
        print(f"DEBUG: 原始图片尺寸: {pixmap_to_save.width()}x{pixmap_to_save.height()}", file=sys.stderr)
        
        # 检查并缩放图片，确保不超过最大尺寸限制
        if pixmap_to_save.width() > MAX_IMAGE_WIDTH or pixmap_to_save.height() > MAX_IMAGE_HEIGHT:
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
        
        # 优先使用 PNG 格式 (更适合截图和UI界面)
        save_format = "PNG"
        mime_type = "image/png"
        saved_successfully = False
        
        if buffer.open(QIODevice.WriteOnly):
            if pixmap_to_save.save(buffer, save_format):
                saved_successfully = True
                print(f"DEBUG: 成功保存为 PNG 格式, 大小: {byte_array.size()} 字节", file=sys.stderr)
            else:
                print("DEBUG: PNG 格式保存失败", file=sys.stderr)
            buffer.close()
        
        # 如果 PNG 失败或文件过大，尝试 JPEG
        if (not saved_successfully or byte_array.isEmpty() or 
            (byte_array.size() > MAX_IMAGE_BYTES)):
                
            print(f"DEBUG: 尝试转换为 JPEG 格式 (PNG失败或过大: {byte_array.size()} 字节)", file=sys.stderr)
            byte_array.clear()
            buffer = QBuffer(byte_array)
            save_format = "JPEG"
            mime_type = "image/jpeg"
            
            # 尝试不同的质量级别，以找到适合的大小
            quality_levels = [85, 70, 50, 30]
            
            for quality in quality_levels:
                if buffer.open(QIODevice.WriteOnly):
                    if pixmap_to_save.save(buffer, save_format, quality):
                        saved_successfully = True
                        print(f"DEBUG: 成功保存为 JPEG 格式，质量: {quality}%, 大小: {byte_array.size()} 字节", file=sys.stderr)
                        buffer.close()
                        
                        # 如果文件大小满足要求，跳出循环
                        if byte_array.size() <= MAX_IMAGE_BYTES:
                            break
                        
                        # 如果文件仍然太大，继续尝试更低的质量
                        byte_array.clear()
                        buffer = QBuffer(byte_array)
                    else:
                        print(f"DEBUG: JPEG 格式保存失败 (质量: {quality}%)", file=sys.stderr)
                        buffer.close()
        
        if not saved_successfully or byte_array.isEmpty():
            print("ERROR: 无法将图片保存为 PNG 或 JPEG 格式", file=sys.stderr)
            QMessageBox.critical(self, "图像处理错误", "无法将图像保存为 PNG 或 JPEG 格式。")
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
            
            # 返回符合 MCP 服务要求的字典结构
            result = {
                "type": "image",
                "data": base64_encoded_data,
                "mimeType": mime_type  # 确保 MIME 类型与实际保存的格式匹配
            }
            
            # 验证数据格式是否符合MCP要求
            if "type" not in result or "data" not in result or "mimeType" not in result:
                print("WARNING: 返回的图片数据结构缺少必要字段", file=sys.stderr)
            
            print(f"DEBUG: 返回图片数据结构: type={result['type']}, mimeType={result['mimeType']}", file=sys.stderr)
            return result
            
        except Exception as e:
            print(f"ERROR: Base64编码失败: {e}", file=sys.stderr)
            QMessageBox.critical(self, "图像处理错误", f"图像数据编码失败: {e}")
            return None
    
    def get_all_images_content_data(self):
        """获取所有图片的内容数据列表"""
        result = []
        print(f"DEBUG: 开始处理所有图片, 共 {len(self.image_widgets)} 张", file=sys.stderr)
        
        for image_id in self.image_widgets.keys():
            print(f"DEBUG: 处理图片 ID: {image_id}", file=sys.stderr)
            image_data = self.get_image_content_data(image_id)
            if image_data:
                result.append(image_data)
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
        
        # 构建最终的 MCP 响应结构
        content_list = []
        
        # 1. 添加文本内容
        final_text_parts = []
        
        # 添加选定的选项
        if selected_options:
            final_text_parts.append("; ".join(selected_options))
        
        # 添加用户的文本反馈
        if feedback_text:
            final_text_parts.append(feedback_text)
        
        # 组合所有文本部分
        combined_text = "\n\n".join(final_text_parts)
        
        # 如果有文本内容，添加到 content 列表
        if combined_text:
            content_list.append({
                "type": "text",
                "text": combined_text
            })
            print(f"DEBUG: 添加文本内容, 长度: {len(combined_text)}", file=sys.stderr)
        
        # 2. 添加图片内容
        image_contents = self.get_all_images_content_data()
        if image_contents:
            content_list.extend(image_contents)
            print(f"DEBUG: 添加了 {len(image_contents)} 张图片到内容列表", file=sys.stderr)
            
        # 3. 检查是否有内容可提交
        if not content_list:
            print("DEBUG: 没有内容可提交", file=sys.stderr)
            QMessageBox.warning(self, "提交失败", "请输入反馈文本或添加图片。")
            return
        
        # 4. 验证内容格式是否符合MCP要求
        is_valid = True
        for item in content_list:
            if "type" not in item:
                print(f"ERROR: 内容项缺少 'type' 字段: {item}", file=sys.stderr)
                is_valid = False
            elif item["type"] == "text" and "text" not in item:
                print(f"ERROR: 文本内容项缺少 'text' 字段: {item}", file=sys.stderr)
                is_valid = False
            elif item["type"] == "image" and ("data" not in item or "mimeType" not in item):
                print(f"ERROR: 图片内容项缺少 'data' 或 'mimeType' 字段: {item}", file=sys.stderr)
                is_valid = False
        
        if not is_valid:
            QMessageBox.critical(self, "提交失败", "反馈内容格式无效，请重试。")
            return
        
        # 显示提交中对话框
        submit_dialog = QMessageBox(self)
        submit_dialog.setWindowTitle("提交中")
        submit_dialog.setText("正在处理反馈内容...")
        submit_dialog.setStandardButtons(QMessageBox.NoButton)
        submit_dialog.setIcon(QMessageBox.Information)
        submit_dialog.show()
        QApplication.processEvents()  # 立即更新 UI
        
        try:
            # 对于旧版本兼容，构建纯文本版本的反馈
            text_only_parts = []
            
            # 添加选定的选项和文本反馈
            if combined_text:
                text_only_parts.append(combined_text)
                
            # 如果有图片，添加图片信息
            if self.image_widgets:
                # 获取所有图片信息
                image_infos = []
                for image_id, widget in self.image_widgets.items():
                    pixmap = widget.original_pixmap
                    image_infos.append(f"图片 {image_id+1}: {pixmap.width()}x{pixmap.height()}")
                
                # 添加图片信息到反馈中
                image_info_text = "已添加 {} 张图片: {}".format(
                    len(image_infos), 
                    ", ".join(image_infos)
                )
                text_only_parts.append(image_info_text)
                
            # 用换行符连接多个部分
            final_text_feedback = "\n\n".join(text_only_parts)
            
            # 为了调试目的，打印 MCP 格式的数据
            mcp_data = {"content": content_list}
            print(f"DEBUG: MCP 格式提交数据: {json.dumps(mcp_data)}", file=sys.stderr)
            
            # 打印更多详细的内容结构信息
            for i, item in enumerate(content_list):
                item_type = item.get("type", "unknown")
                print(f"DEBUG: 内容项 {i+1}: 类型={item_type}", file=sys.stderr)
                if item_type == "text":
                    text_content = item.get("text", "")
                    print(f"DEBUG: 文本内容长度: {len(text_content)}", file=sys.stderr)
                    # 只打印前50个字符作为示例
                    if text_content:
                        print(f"DEBUG: 文本内容示例: {text_content[:50]}{'...' if len(text_content) > 50 else ''}", file=sys.stderr)
                elif item_type == "image":
                    mime_type = item.get("mimeType", "unknown")
                    data = item.get("data", "")
                    print(f"DEBUG: 图片MIME类型: {mime_type}, Base64数据长度: {len(data)}", file=sys.stderr)
                    if data:
                        # 只打印Base64数据的前30个字符
                        print(f"DEBUG: Base64数据开头: {data[:30]}...", file=sys.stderr)
            
            # 直接返回正确格式的数据，而不是将其序列化为字符串
            # 关键修改：返回 MCP 格式的数据结构
            self.feedback_result = mcp_data
            
            print("DEBUG: 反馈结果设置完成", file=sys.stderr)
            
            # 关闭提交对话框并显示成功信息
            submit_dialog.close()
            QMessageBox.information(self, "提交成功", "反馈已成功提交！")
            
        except Exception as e:
            # 关闭提交对话框并显示错误信息
            submit_dialog.close()
            error_message = f"提交反馈时发生错误: {str(e)}"
            print(f"ERROR: {error_message}", file=sys.stderr)
            QMessageBox.critical(self, "提交失败", error_message)
            return
        
        print("DEBUG: 提交完成，关闭窗口", file=sys.stderr)
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
        QApplication.instance().exec()
        print("事件循环结束，窗口关闭...", file=sys.stderr)

        if not self.feedback_result:
            # 返回空的内容列表而不是空字符串
            print("未获得反馈结果，返回空内容列表", file=sys.stderr)
            return FeedbackResult(content=[])

        print(f"返回反馈结果: {self.feedback_result}", file=sys.stderr)
        return self.feedback_result

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
        """处理粘贴图片操作"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasImage():
            # 从剪贴板获取图片
            image = clipboard.image()
            if not image.isNull():
                # 将QImage转换为QPixmap并保存
                pixmap = QPixmap.fromImage(image)
                self.add_image_preview(pixmap)
                return True
        return False
    
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
            
            # 显示清除所有图片按钮
            self.clear_images_button.setVisible(True)
            
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
                self.clear_images_button.setVisible(False)
            else:
                # 更新最后一个图片
                last_id = max(self.image_widgets.keys())
                self.image_pixmap = self.image_widgets[last_id].original_pixmap
            
            # 更新提交按钮文本
            self._update_submit_button_text()
    
    def clear_all_images(self):
        """清除所有图片预览"""
        # 弹出确认对话框
        reply = QMessageBox.question(
            self, 
            "确认", 
            "确定要清除所有图片吗？", 
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 默认选择No，避免误操作
        )
        
        if reply == QMessageBox.Yes:
            # 复制ID列表，因为在循环中会修改字典
            image_ids = list(self.image_widgets.keys())
            for image_id in image_ids:
                self.remove_image(image_id)
            
            self.image_pixmap = None
            self.feedback_text.show_images_container(False)
            
            # 隐藏清除图片按钮
            self.clear_images_button.setVisible(False)
            
            # 更新提交按钮文本
            self._update_submit_button_text()
    
    def _update_submit_button_text(self):
        """根据当前输入情况更新提交按钮文本"""
        has_text = bool(self.feedback_text.toPlainText().strip())
        has_images = bool(self.image_widgets)
        
        if has_text and has_images:
            self.submit_button.setText(f"提交反馈 (含 {len(self.image_widgets)} 张图片)")
        elif has_images:
            self.submit_button.setText(f"提交 {len(self.image_widgets)} 张图片")
        elif has_text:
            self.submit_button.setText("提交反馈")
        else:
            self.submit_button.setText("提交")

    def _show_canned_responses(self):
        """显示常用语对话框"""
        # 临时禁用自动最小化功能
        self.disable_auto_minimize = True
        
        try:
            # 获取常用语列表
            settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
            settings.beginGroup("CannedResponses")
            responses = settings.value("phrases", [])
            settings.endGroup()
            
            # 显示常用语对话框
            dialog = SelectCannedResponseDialog(responses, self)
            dialog.setWindowModality(Qt.ApplicationModal)  # 设置为模态对话框
            dialog.exec()
            
            # 注意：不需要检查结果，因为双击项目时会直接插入文本并关闭对话框
        finally:
            # 恢复自动最小化功能
            self.disable_auto_minimize = False

class ManageCannedResponsesDialog(QDialog):
    """常用语管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置对话框属性
        self.setWindowTitle("管理常用语")
        self.resize(500, 400)
        self.setMinimumSize(400, 300)
        
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
            existing_items = self.responses_list.findItems(text, Qt.MatchExactly)
            if existing_items:
                QMessageBox.warning(self, "重复项", "此常用语已存在，请输入不同的内容。")
                return
            
            # 添加到列表
            self.responses_list.addItem(text)
            
            # 保存设置
            self._save_canned_responses()
            
            # 清空输入框
            self.input_field.clear()
    
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
    """常用语选择对话框"""
    
    def __init__(self, responses, parent=None):
        super().__init__(parent)
        self.setWindowTitle("常用语 - 已更新")
        self.resize(400, 350)  # 调整为更合适的大小
        self.setMinimumSize(350, 300)
        
        # 设置模态属性
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        
        # 保存常用语列表和父窗口引用
        self.responses = responses
        self.parent_window = parent
        self.selected_response = None
        self.drag_start_position = None  # 记录拖拽开始位置
        
        # 创建设置对象，用于存储常用语
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # 简化窗口样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QListWidget {
                background-color: #333333;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                border-bottom: 1px solid #404040;
                padding: 8px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #505050;
            }
            QLineEdit {
                background-color: #404040;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton {
                background-color: #2a82da;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """)
        
        # 创建UI
        self._create_ui()
        
        # 加载常用语
        self._load_responses()
    
    def _on_item_double_clicked(self, item):
        """双击列表项时，将文本插入到父窗口的输入框"""
        # 获取项目对应的小部件
        item_widget = self.responses_list.itemWidget(item)
        if item_widget:
            # 获取文本标签（第一个子部件）
            text_label = item_widget.layout().itemAt(0).widget()
            if text_label and isinstance(text_label, QLabel):
                text = text_label.text()
                # 如果有父窗口，将文本插入到输入框
                if self.parent_window and hasattr(self.parent_window, 'feedback_text'):
                    # 插入文本并关闭对话框
                    self.parent_window.feedback_text.insertPlainText(text)
                    self.accept()  # 关闭对话框
                    
                    # 保存选定的常用语
                    self.selected_response = text
    
    def _load_responses(self):
        """从设置加载常用语到列表"""
        self.responses_list.clear()
        for response in self.responses:
            if response.strip():  # 跳过空字符串
                self._add_item_to_list(response)
    
    def _add_item_to_list(self, text):
        """添加带有删除按钮的项目到列表，简化布局"""
        # 创建列表项
        item = QListWidgetItem()
        self.responses_list.addItem(item)
        
        # 创建项目小部件
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(5, 2, 5, 2)
        item_layout.setSpacing(10)
        
        # 文本标签
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        text_label.setStyleSheet("color: #ffffff;")
        item_layout.addWidget(text_label, 1)
        
        # 删除按钮 - 使用固定尺寸和直接样式
        delete_button = QPushButton("×")
        delete_button.setFixedSize(26, 26)
        delete_button.setCursor(Qt.PointingHandCursor)
        # 直接应用样式表
        delete_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                color: #dddddd;
                border: none;
                border-radius: 13px;
                font-size: 16pt;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
                min-width: 26px;
                min-height: 26px;
                max-width: 26px;
                max-height: 26px;
                line-height: 26px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #ff5050;
                color: white;
            }
            QPushButton:pressed {
                background-color: #cc3030;
            }
        """)
        delete_button.clicked.connect(lambda checked, t=text: self._delete_response(t))
        delete_button.setToolTip("删除此常用语")
        item_layout.addWidget(delete_button)
        
        # 设置项目小部件和高度
        item.setSizeHint(QSize(item_widget.sizeHint().width(), max(40, text_label.sizeHint().height() + 10)))
        self.responses_list.setItemWidget(item, item_widget)
    
    def _add_response(self):
        """添加新的常用语"""
        text = self.input_field.text().strip()
        if text:
            # 检查是否已存在
            existing_items = self.responses_list.findItems(text, Qt.MatchExactly)
            if existing_items:
                QMessageBox.warning(self, "重复项", "此常用语已存在，请输入不同的内容。")
                return
            
            # 添加到列表
            self.responses_list.addItem(text)
            
            # 保存设置
            self._save_canned_responses()
            
            # 清空输入框
            self.input_field.clear()
    
    def _delete_response(self, text_to_delete):
        """删除指定的常用语"""
        # 查找并删除匹配的项目
        for i in range(self.responses_list.count()):
            item = self.responses_list.item(i)
            item_widget = self.responses_list.itemWidget(item)
            if item_widget:
                text_label = item_widget.layout().itemAt(0).widget()
                if text_label and isinstance(text_label, QLabel) and text_label.text() == text_to_delete:
                    # 找到匹配项，删除它
                    self.responses_list.takeItem(i)
                    
                    # 更新常用语列表并保存
                    self._save_responses()
                    break
    
    def _save_responses(self):
        """保存当前列表中的常用语到设置"""
        responses = []
        for i in range(self.responses_list.count()):
            item = self.responses_list.item(i)
            item_widget = self.responses_list.itemWidget(item)
            if item_widget:
                text_label = item_widget.layout().itemAt(0).widget()
                if text_label and isinstance(text_label, QLabel):
                    responses.append(text_label.text())
        
        # 保存到设置
        self.settings.beginGroup("CannedResponses")
        self.settings.setValue("phrases", responses)
        self.settings.endGroup()
    
    def closeEvent(self, event):
        """关闭对话框时保存常用语顺序"""
        self._save_responses()
        super().closeEvent(event)
    
    def get_selected_response(self):
        """获取选择的常用语"""
        return self.selected_response

    def _create_ui(self):
        """创建简化版UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 添加标题标签
        title_label = QLabel("常用语列表 - 已更新")
        title_label.setStyleSheet("font-size: 13pt; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 添加提示标签
        hint_label = QLabel("双击插入文本，点击×删除，拖动可调整顺序")
        hint_label.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        main_layout.addWidget(hint_label)
        
        # 创建自定义列表部件
        self.responses_list = DraggableListWidget()
        self.responses_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.responses_list.setMinimumHeight(150)
        
        # 启用拖动后自动保存顺序
        self.responses_list.model().rowsMoved.connect(self._save_responses)
        
        main_layout.addWidget(self.responses_list, 1)  # 列表占据更多空间
        
        # 创建底部输入区域，使用简单布局
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(0)  # 移除间距使按钮紧贴输入框
        
        # 创建输入框容器
        input_frame = QFrame()
        input_frame.setFrameShape(QFrame.StyledPanel)
        input_frame.setStyleSheet("""
            QFrame {
                background-color: #404040;
                border: none;
                border-radius: 4px;
                padding: 0px;
            }
        """)
        input_frame_layout = QHBoxLayout(input_frame)
        input_frame_layout.setContentsMargins(8, 0, 0, 0)  # 左侧留出一些内边距
        input_frame_layout.setSpacing(0)
        
        # 输入框 - 无边框样式
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语")
        self.input_field.returnPressed.connect(self._add_response)
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                color: #ffffff;
                border: none;
                padding: 8px 0px;
                font-size: 11pt;
            }
        """)
        input_frame_layout.addWidget(self.input_field)
        
        # 保存按钮 - 集成到输入框内
        save_button = QPushButton("保存")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self._add_response)
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #2a82da;
                color: white;
                border: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 60px;
                max-width: 60px;
            }
            QPushButton:hover {
                background-color: #3a92ea;
            }
            QPushButton:pressed {
                background-color: #1a72ca;
            }
        """)
        input_frame_layout.addWidget(save_button)
        
        # 将输入框容器添加到主布局
        input_layout.addWidget(input_frame)
        
        # 添加到主布局
        main_layout.addWidget(input_container)

# 添加自定义可拖放列表部件类
class DraggableListWidget(QListWidget):
    """简化的可拖放列表部件，使用Qt内置的拖放功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # 启用基本拖放功能，但不做任何自定义处理
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QListWidget.SingleSelection)
        # 使拖动项目更明显
        self.setAlternatingRowColors(True)

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    print("进入feedback_ui函数...", file=sys.stderr)
    app = QApplication.instance() or QApplication()
    print("QApplication实例化完成", file=sys.stderr)
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")
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
    
    # 确保至少有一个预定义选项，以便显示完整的UI
    if predefined_options is None or len(predefined_options) == 0:
        print("未提供预定义选项，添加一个示例选项以显示完整UI", file=sys.stderr)
        predefined_options = ["示例选项 (可以取消选择)"]
    
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
    parser.add_argument("--full-ui", action="store_true", default=True, help="显示完整UI界面，包含所有功能")
    args = parser.parse_args()
    
    print(f"命令行参数: {args}", file=sys.stderr)

    # 调试模式标志
    debug_mode = args.debug
    
    if debug_mode:
        print("DEBUG: 运行在调试模式", file=sys.stderr)
        
    # 如果没有指定预定义选项但设置了full-ui，添加一些示例选项
    if args.full_ui and not args.predefined_options:
        predefined_options = ["选项 A", "选项 B", "选项 C"]
        print(f"启用完整UI模式，使用示例预定义选项: {predefined_options}", file=sys.stderr)
    else:
        predefined_options = [opt for opt in args.predefined_options.split("|||") if opt] if args.predefined_options else None
    
    print(f"预定义选项: {predefined_options}", file=sys.stderr)
    
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

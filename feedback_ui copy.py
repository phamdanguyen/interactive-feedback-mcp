# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by pawa (https://github.com/pawaovo) with ideas from https://github.com/noopstudios/interactive-feedback-mcp
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
import re  # 添加re模块用于正则表达式处理
import webbrowser  # 添加webbrowser模块用于打开网页链接

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
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QPixmap, QCursor, QPainter, QClipboard, QImage, QFont, QKeySequence, QShortcut, QDrag, QPen, QAction, QFontMetrics, QTextCharFormat

# 添加自定义ClickableLabel类
class ClickableLabel(QLabel):
    """自定义标签类，允许文本选择但禁止光标变化，支持点击信号"""
    
    # 添加点击信号
    clicked = Signal()
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # 设置文本可选标志 - 只读
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        # 使用更现代的样式
        self.setStyleSheet("""
            QLabel {
                color: #ffffff;
                selection-background-color: #2374E1;
                selection-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 2px;
            }
        """)
        
        # 设置光标为手型指针，表示可点击
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)  # 启用鼠标跟踪以便处理所有鼠标移动事件
        
        # 创建事件过滤器对象，并安装到自身
        self._cursor_filter = CursorOverrideFilter(self)
        self.installEventFilter(self._cursor_filter)
    
    # 重写mouseMoveEvent确保光标保持为手型指针
    def mouseMoveEvent(self, event):
        QApplication.restoreOverrideCursor()  # 先清除可能的光标堆栈
        QApplication.setOverrideCursor(Qt.PointingHandCursor)  # 强制设置为手型光标
        super().mouseMoveEvent(event)
    
    # 重写以下事件来确保光标始终为手型指针
    def enterEvent(self, event):
        QApplication.setOverrideCursor(Qt.PointingHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 触发点击信号
            self.clicked.emit()
            event.accept()
        else:
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
    # 设置全局默认字体
    default_font = QFont("Segoe UI", 10)
    app.setFont(default_font)
    
    # 创建深色调色板
    darkPalette = app.palette()
    
    # 更新主要颜色 - 使用更一致的深色调
    darkPalette.setColor(QPalette.Window, QColor(30, 30, 30))  # 从(45, 45, 45)改深为(30, 30, 30)
    darkPalette.setColor(QPalette.WindowText, Qt.white)  # 白色文本
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    
    # 输入区域和列表背景
    darkPalette.setColor(QPalette.Base, QColor(45, 45, 45))  # #2D2D2D - 稍浅的控件背景
    darkPalette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
    
    # 工具提示
    darkPalette.setColor(QPalette.ToolTipBase, QColor(45, 45, 45))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    
    # 文本颜色
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    
    # 阴影和边框
    darkPalette.setColor(QPalette.Dark, QColor(40, 40, 40))
    darkPalette.setColor(QPalette.Shadow, QColor(25, 25, 25))
    
    # 按钮颜色 - 采用更深沉的灰色系
    darkPalette.setColor(QPalette.Button, QColor(60, 60, 60))  # #3C3C3C - 灰色按钮背景
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    
    # 强调色和高亮 - 使用更柔和的深灰色系
    darkPalette.setColor(QPalette.BrightText, QColor(240, 240, 240))
    darkPalette.setColor(QPalette.Link, QColor(80, 80, 80))  # 更协调的灰色链接
    darkPalette.setColor(QPalette.Highlight, QColor(70, 70, 70))  # 灰色高亮
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    
    # 占位符文本
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    
    # 设置全局应用样式表
    app.setStyleSheet("""
        /* 全局字体设置 */
        * {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        /* 文本编辑控件 */
        QTextEdit, QLineEdit {
            background-color: #2D2D2D;
            color: white;
            border-radius: 8px;
            padding: 8px;
            border: 1px solid #3A3A3A;
        }
        
        /* 按钮样式 */
        QPushButton {
            background-color: #3C3C3C;  /* 改为灰色 */
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
            background-color: #444444;  /* 鼠标悬停时变亮 */
        }
        
        QPushButton:pressed {
            background-color: #333333;  /* 按下时变暗 */
        }
        
        QPushButton:disabled {
            background-color: #555;
            color: #999;
        }
        
        /* 特殊的提交按钮样式 */
        QPushButton#submit_button {
            background-color: #252525;  /* 进一步变浅的背景色 */
            color: white;
            border: 2px solid #3A3A3A;  /* 使用较深的边框样式 */
            padding: 12px 20px;
            font-weight: bold;
            font-size: 13pt;
            border-radius: 15px;  /* 增加圆角半径使其更圆润 */
            min-height: 60px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2), 0 3px 5px rgba(0, 0, 0, 0.15);  /* 使用适中的阴影效果 */
        }
        
        QPushButton#submit_button:hover {
            background-color: #303030;  /* 悬停时背景更亮 */
            border: 2px solid #454545;  /* 边框变亮 */
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.25), 0 4px 6px rgba(0, 0, 0, 0.2);  /* 悬停时阴影更明显 */
        }
        
        QPushButton#submit_button:pressed {
            background-color: #202020;  /* 按下时稍深 */
            border: 2px solid #353535;
            box-shadow: 0 3px 5px rgba(0, 0, 0, 0.15), 0 1px 3px rgba(0, 0, 0, 0.1);  /* 按下时阴影减弱 */
        }
        
        /* 次要按钮样式 */
        QPushButton#secondary_button {
            background-color: transparent;  /* 改为透明背景 */
            color: white;
            border: 1px solid #454545;  /* 保留边框效果 */
            font-size: 10pt;
            padding: 5px 10px;
            min-height: 32px;
            min-width: 120px;
            max-height: 32px;
        }
        
        QPushButton#secondary_button:hover {
            background-color: rgba(64, 64, 64, 0.3);  /* 半透明悬停效果 */
            border: 1px solid #555555;
        }
        
        QPushButton#secondary_button:pressed {
            background-color: rgba(48, 48, 48, 0.4);  /* 半透明按下效果 */
        }
        
        /* 固定窗口激活按钮样式 */
        QPushButton#pin_window_active {
            background-color: rgba(80, 80, 80, 0.5);  /* 半透明背景 */
            color: white;
            border: 1px solid #606060;
            font-size: 10pt;
            padding: 5px 10px;
            min-height: 32px;
            min-width: 120px;
            max-height: 32px;
        }
        
        QPushButton#pin_window_active:hover {
            background-color: rgba(85, 85, 85, 0.6);
            border: 1px solid #676767;
        }
        
        QPushButton#pin_window_active:pressed {
            background-color: rgba(69, 69, 69, 0.6);
        }
        
        /* 复选框样式 */
        QCheckBox {
            color: #b8b8b8;  /* 选项文本颜色 */
            spacing: 8px;
            font-size: 11pt;
            min-height: 28px;  /* 减小高度 */
            padding: 1px;  /* 减少内边距 */
        }
        
        QCheckBox::indicator {
            width: 22px;
            height: 22px;
            border: 1px solid #444444;  /* 更柔和的边框色 */
            border-radius: 4px;
            background-color: transparent;  /* 未选中时无背景填充 */
        }
        
        QCheckBox::indicator:checked {
            background-color: #4D4D4D;  /* 选中后为灰黑色调填充 */
            border: 2px solid #555555;  /* 边框变粗 */
            border-width: 2px;
            border-color: #555555;
            transform: scale(1.05);  /* 轻微放大效果 */
            image: none;  /* 移除图标引用 */
            background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='#ffffff' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
            background-position: center;
            background-repeat: no-repeat;
        }
        
        QCheckBox::indicator:hover:!checked {
            border: 1px solid #666666;  /* 悬停时边框更明显 */
            background-color: #333333;  /* 悬停时有轻微背景 */
        }
        
        QCheckBox::indicator:checked:hover {
            background-color: #555555;  /* 选中状态悬停时更亮 */
            border-width: 2px;
            border-color: #666666;
        }
        
        /* 标签样式 */
        QLabel {
            color: white;
            background-color: transparent;
        }
    """)
    
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
        
        # 设置高质量字体
        font = QFont("Segoe UI", 13)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setHintingPreference(QFont.PreferFullHinting)
        font.setWeight(QFont.Normal)
        font.setLetterSpacing(QFont.PercentageSpacing, 101.5)  # 增加1.5%的字母间距
        font.setWordSpacing(1.0)  # 增加词间距
        self.setFont(font)
        
        # 性能优化：添加文件引用缓存
        self._file_reference_cache = {
            'text': '',         # 当前文本内容的缓存
            'references': [],   # 检测到的引用列表
            'positions': {}     # 引用位置映射 {引用名称: (起始位置, 结束位置)}
        }
        # 缓存是否有效的标志
        self._cache_valid = False
        # 记录上次光标位置
        self._last_cursor_pos = 0
        
        # 增强按键响应性
        self.setCursorWidth(2)  # 增加光标宽度使其更明显
        self.setAcceptDrops(True)
        
        # 提高光标可见性和响应度
        self.viewport().setCursor(Qt.IBeamCursor)  # 确保使用I型光标
        
        # 优化键盘响应
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 针对连续按键优化的计时器
        self._key_repeat_timer = QTimer(self)
        self._key_repeat_timer.setSingleShot(True)
        self._key_repeat_timer.setInterval(10)  # 短间隔，确保快速响应
        self._key_repeat_timer.timeout.connect(self._ensure_cursor_visible)
        
        # 记录重复按键状态
        self._is_key_repeating = False
        self._current_repeat_key = None
        
        # 创建图片预览容器（重叠在文本编辑框上）
        self.images_container = QWidget(self)
        self.images_layout = QHBoxLayout(self.images_container)
        self.images_layout.setContentsMargins(10, 10, 10, 10)  # 增加内边距
        self.images_layout.setSpacing(10)  # 增加间距
        self.images_layout.setAlignment(Qt.AlignLeft)
        
        # 设置图片容器的背景和样式，更现代的半透明外观
        self.images_container.setStyleSheet("""
            background-color: #4a4a4a;  /* 使用更浅的灰色，让对比更明显 */
            border-top: 1px solid #555555;
            border-radius: 0 0 10px 10px;  /* 底部圆角 */
            padding: 8px;
        """)
        
        # 默认隐藏图片预览区域
        self.images_container.setVisible(False)
        
        # 更新文本编辑区样式，添加更现代的样式包括圆角和边框
        self.setStyleSheet("""
            QTextEdit {
                color: #ffffff;
                font-size: 13pt;
                font-family: 'Segoe UI', 'Microsoft YaHei UI', Arial, sans-serif;
                font-weight: 400;
                line-height: 1.4;
                letter-spacing: 0.015em;
                word-spacing: 0.05em;
                background-color: #272727;  /* 比#1F1F1F更浅一些 */
                border: 2px solid #3A3A3A;  /* 加粗边框，与顶部区域一致 */
                border-radius: 10px;
                padding: 12px;
                selection-background-color: #505050;
                selection-color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1);  /* 添加阴影效果 */
                transition: all 0.3s ease;  /* 添加过渡效果 */
            }
            
            /* 添加悬停效果 */
            QTextEdit:hover {
                border: 2px solid #454545;  /* 悬停时边框颜色略亮 */
                background-color: #272727;  /* 保持与默认状态相同的背景色 */
            }
            
            /* 滚动条样式 */
            QScrollBar:vertical {
                background: #2D2D2D;
                width: 8px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #606060;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 设置占位符文本颜色
        palette = self.palette()
        palette.setColor(QPalette.PlaceholderText, QColor("#777777"))
        self.setPalette(palette)
        
        # 启用拖放功能
        self.setAcceptDrops(True)
        
        # 调试输出
        print("DEBUG: FeedbackTextEdit 初始化完成，拖放功能已启用", file=sys.stderr)
        
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
        key = event.key()
        
        # 记录重复按键状态
        if event.isAutoRepeat():
            self._is_key_repeating = True
            self._current_repeat_key = key
        else:
            self._is_key_repeating = False
            self._current_repeat_key = None
            
        # 首先处理特殊按键：方向键、Home和End键
        if key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down, Qt.Key_Home, Qt.Key_End):
            # 直接调用父类方法处理光标移动，避免任何额外处理
            super().keyPressEvent(event)
            # 更新最后光标位置
            self._last_cursor_pos = self.textCursor().position()
            # 确保光标可见，用于连续按键
            self._schedule_ensure_cursor_visible()
            return
            
        # 更新当前光标位置以优化后续处理
        cursor_pos = self.textCursor().position()
        self._last_cursor_pos = cursor_pos
            
        # 处理退格键和删除键
        if key == Qt.Key_Backspace:
            # 优化：仅当有拖放文件引用且当前位置可能在引用后面时才检查特殊删除
            parent = self._find_parent()
            if parent and parent.dropped_file_references and self._near_file_reference(cursor_pos, is_backspace=True):
                if self._handle_file_reference_deletion(is_backspace=True):
                    self._invalidate_cache()  # 文本改变，使缓存失效
                    self._schedule_ensure_cursor_visible()
                    return
                    
            # 获取当前光标位置
            cursor = self.textCursor()
            # 直接调用标准删除操作，而不触发额外的处理
            if not cursor.hasSelection():
                # 如果没有选择文本，则简单地删除前一个字符
                cursor.deletePreviousChar()
            else:
                # 如果有选择文本，则删除选定内容
                cursor.removeSelectedText()
            
            self._invalidate_cache()  # 文本改变，使缓存失效
            self._schedule_ensure_cursor_visible()
            return
            
        elif key == Qt.Key_Delete:
            # 优化：仅当有拖放文件引用且当前位置可能在引用前面时才检查特殊删除
            parent = self._find_parent()
            if parent and parent.dropped_file_references and self._near_file_reference(cursor_pos, is_backspace=False):
                if self._handle_file_reference_deletion(is_backspace=False):
                    self._invalidate_cache()  # 文本改变，使缓存失效
                    self._schedule_ensure_cursor_visible()
                    return
                    
            # 获取当前光标位置
            cursor = self.textCursor()
            # 直接调用标准删除操作，而不触发额外的处理
            if not cursor.hasSelection():
                # 如果没有选择文本，则简单地删除后一个字符
                cursor.deleteChar()
            else:
                # 如果有选择文本，则删除选定内容
                cursor.removeSelectedText()
            
            self._invalidate_cache()  # 文本改变，使缓存失效
            self._schedule_ensure_cursor_visible()
            return
            
        # 按Enter键发送消息，按Shift+Enter换行
        elif key == Qt.Key_Return:
            # 如果按下Shift+Enter，则执行换行操作
            if event.modifiers() == Qt.ShiftModifier:
                super().keyPressEvent(event)
                self._invalidate_cache()  # 文本改变，使缓存失效
                self._schedule_ensure_cursor_visible()
            # 如果按下Ctrl+Enter或单独按Enter，则发送消息
            elif event.modifiers() == Qt.ControlModifier or event.modifiers() == Qt.NoModifier:
                parent = self._find_parent()
                if parent:
                    # 调用父窗口的提交方法
                    parent._submit_feedback()
            else:
                super().keyPressEvent(event)
                self._invalidate_cache()  # 文本改变，使缓存失效
                self._schedule_ensure_cursor_visible()
        # 处理Ctrl+V粘贴图片
        elif key == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
            # 查找剪贴板是否有图片
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            # 如果剪贴板有图片且有父FeedbackUI实例，则调用粘贴图片方法
            if mime_data.hasImage():
                parent = self._find_parent()
                if parent:
                    # 如果成功处理了图片粘贴，则不执行默认粘贴行为
                    if parent.handle_paste_image():
                        return
            
            # 如果没有图片或没找到父FeedbackUI实例，则执行默认粘贴行为
            super().keyPressEvent(event)
            self._invalidate_cache()  # 文本改变，使缓存失效
            self._schedule_ensure_cursor_visible()
        else:
            # 其他按键直接传递给父类处理
            super().keyPressEvent(event)
            self._invalidate_cache()  # 文本改变，使缓存失效
            self._schedule_ensure_cursor_visible()
            
    def keyReleaseEvent(self, event):
        """处理按键释放事件，重置重复按键状态"""
        self._is_key_repeating = False
        self._current_repeat_key = None
        super().keyReleaseEvent(event)
        
    def _schedule_ensure_cursor_visible(self):
        """调度确保光标可见的函数，避免过于频繁的视图更新"""
        # 即使计时器已经活动也重新启动，确保最后一次按键也能触发更新
        self._key_repeat_timer.start()
        
    def _ensure_cursor_visible(self):
        """确保光标可见并且UI响应"""
        # 获取当前光标
        cursor = self.textCursor()
        
        # 确保光标可见
        self.ensureCursorVisible()
        
        # 强制视口更新
        self.viewport().update()
        
    # 重写鼠标事件，确保与键盘事件的一致处理
    def mousePressEvent(self, event):
        # 停止按键重复计时器
        self._key_repeat_timer.stop()
        self._is_key_repeating = False
        self._current_repeat_key = None
        
        # 正常处理鼠标事件
        super().mousePressEvent(event)
        
        # 更新光标位置
        self._last_cursor_pos = self.textCursor().position()
        
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        # 确保光标可见
        self.ensureCursorVisible()
        
    # 重写显示事件，优化初始光标显示
    def showEvent(self, event):
        super().showEvent(event)
        # 显示时确保光标可见
        QTimer.singleShot(10, self.ensureCursorVisible)

    def _find_parent(self):
        """查找父FeedbackUI实例，使用缓存提高性能"""
        parent = self.parent()
        while parent and not isinstance(parent, FeedbackUI):
            parent = parent.parent()
        return parent
        
    def _invalidate_cache(self):
        """使缓存失效，在文本内容变化时调用"""
        self._cache_valid = False
        
    def _update_reference_cache(self):
        """更新文件引用缓存"""
        if self._cache_valid:
            return
            
        parent = self._find_parent()
        if not parent or not parent.dropped_file_references:
            self._cache_valid = True
            return
            
        # 获取当前文本
        text = self.toPlainText()
        
        # 如果当前文本与缓存相同，不需要重新计算
        if text == self._file_reference_cache['text']:
            self._cache_valid = True
            return
            
        # 更新缓存的文本
        self._file_reference_cache['text'] = text
        self._file_reference_cache['references'] = []
        self._file_reference_cache['positions'] = {}
        
        # 寻找所有文件引用的位置
        for display_name in parent.dropped_file_references:
            start_pos = 0
            while True:
                pos = text.find(display_name, start_pos)
                if pos == -1:
                    break
                    
                self._file_reference_cache['references'].append(display_name)
                self._file_reference_cache['positions'][display_name] = (pos, pos + len(display_name))
                start_pos = pos + len(display_name)
                
        self._cache_valid = True
        
    def _near_file_reference(self, cursor_pos, is_backspace=True):
        """快速检查光标是否在文件引用附近，避免完整扫描"""
        self._update_reference_cache()
        
        for display_name, (start, end) in self._file_reference_cache['positions'].items():
            if is_backspace and cursor_pos == end:
                # 退格键：如果光标正好在引用后面
                return True
            elif not is_backspace and cursor_pos == start:
                # 删除键：如果光标正好在引用前面
                return True
                
        return False

    def _handle_file_reference_deletion(self, is_backspace=True):
        """
        处理文件引用的特殊删除行为
        
        Args:
            is_backspace (bool): 是否是退格键，True表示退格键，False表示删除键
            
        Returns:
            bool: 如果处理了特殊删除行为返回True，否则返回False
        """
        # 使用优化过的父窗口查找
        parent_window = self._find_parent()
            
        if not parent_window or not parent_window.dropped_file_references:
            return False
            
        # 更新引用缓存
        self._update_reference_cache()
        
        # 获取当前光标位置
        cursor = self.textCursor()
        
        # 如果有选中文本，不做特殊处理
        if cursor.hasSelection():
            return False
            
        cursor_pos = cursor.position()
        
        if is_backspace:  # 退格键
            # 利用缓存快速检查光标是否在引用后面
            for display_name, (start, end) in self._file_reference_cache['positions'].items():
                if cursor_pos == end:
                    # 选中整个文件引用
                    cursor.setPosition(start)
                    cursor.setPosition(end, QTextCursor.KeepAnchor)
                    # 删除选中内容
                    cursor.removeSelectedText()
                    
                    # 从字典中移除引用
                    if display_name in parent_window.dropped_file_references:
                        del parent_window.dropped_file_references[display_name]
                        print(f"DEBUG: 已删除文件引用: {display_name}", file=sys.stderr)
                    
                    # 使缓存失效
                    self._invalidate_cache()
                    
                    return True
        else:  # 删除键
            # 利用缓存快速检查光标是否在引用前面
            for display_name, (start, end) in self._file_reference_cache['positions'].items():
                if cursor_pos == start:
                    # 选中整个文件引用
                    cursor.setPosition(end, QTextCursor.KeepAnchor)
                    # 删除选中内容
                    cursor.removeSelectedText()
                    
                    # 从字典中移除引用
                    if display_name in parent_window.dropped_file_references:
                        del parent_window.dropped_file_references[display_name]
                        print(f"DEBUG: 已删除文件引用: {display_name}", file=sys.stderr)
                    
                    # 使缓存失效
                    self._invalidate_cache()
                    
                    return True
                    
        return False

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
        
    def dragEnterEvent(self, event):
        """处理拖拽进入事件"""
        mime_data = event.mimeData()
        
        # 打印所有可用的格式
        print(f"DEBUG: 拖拽数据格式: {mime_data.formats()}", file=sys.stderr)
        
        # 接受多种类型的拖拽数据
        if mime_data.hasUrls() or mime_data.hasText() or mime_data.hasHtml() or mime_data.hasImage():
            print("DEBUG: dragEnterEvent - 接受拖拽事件", file=sys.stderr)
            event.acceptProposedAction()
        else:
            print("DEBUG: dragEnterEvent - 拒绝拖拽事件", file=sys.stderr)
            event.ignore()
            
    def dragMoveEvent(self, event):
        """处理拖拽移动事件"""
        if event.mimeData().hasUrls() or event.mimeData().hasText() or event.mimeData().hasHtml() or event.mimeData().hasImage():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """处理拖拽放下事件"""
        mime_data = event.mimeData()
        print("DEBUG: dropEvent - 开始处理拖拽事件", file=sys.stderr)
        print(f"DEBUG: 拖拽数据格式: {mime_data.formats()}", file=sys.stderr)
        
        # 获取父FeedbackUI实例
        parent_window = self.parent()
        while parent_window and not isinstance(parent_window, FeedbackUI):
            parent_window = parent_window.parent()
            
        if not parent_window:
            print("ERROR: dropEvent - 未找到父FeedbackUI实例", file=sys.stderr)
            event.ignore()
            return
            
        # 确保父窗口有dropped_file_references字典
        if not hasattr(parent_window, 'dropped_file_references'):
            parent_window.dropped_file_references = {}
            
        # 处理拖拽的URL（文件）
        if mime_data.hasUrls():
            urls = mime_data.urls()
            print(f"DEBUG: dropEvent - URL数量: {len(urls)}", file=sys.stderr)
            
            # 如果URLs数量为0但声称有URLs，可能是特殊情况
            # 尝试从文本中获取文件路径
            if len(urls) == 0 and mime_data.hasText():
                print("DEBUG: dropEvent - URLs为空，尝试从文本中获取文件路径", file=sys.stderr)
                return self._process_text_drop(event, mime_data, parent_window)
            
            for url in urls:
                url_str = url.toString()
                print(f"DEBUG: dropEvent - 处理URL: {url_str}", file=sys.stderr)
                
                # 处理本地文件
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    file_name = os.path.basename(file_path)
                    print(f"DEBUG: dropEvent - 本地文件: {file_name}, 路径: {file_path}", file=sys.stderr)
                    
                    # 处理图片文件
                    if os.path.isfile(file_path) and os.path.splitext(file_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        try:
                            print(f"DEBUG: dropEvent - 尝试加载图片: {file_path}", file=sys.stderr)
                            pixmap = QPixmap(file_path)
                            if not pixmap.isNull() and pixmap.width() > 0:
                                print(f"DEBUG: dropEvent - 成功加载图片，添加到预览区", file=sys.stderr)
                                parent_window.add_image_preview(pixmap)
                                continue  # 成功处理为图片，跳过后续的文件引用处理
                            else:
                                print(f"DEBUG: dropEvent - 图片加载失败，作为文件处理", file=sys.stderr)
                        except Exception as e:
                            print(f"ERROR: dropEvent - 加载图片出错: {e}", file=sys.stderr)
                    
                    # 处理为文件引用 @文件名
                    self._insert_file_reference(parent_window, file_path, file_name)
        
        # 如果没有URL但有文本，可能是从资源管理器拖拽的特殊格式
        elif mime_data.hasText():
            return self._process_text_drop(event, mime_data, parent_window)
        else:
            # 如果既没有URL也没有文本，则调用父类方法
            print("DEBUG: dropEvent - 非文件拖拽，调用父类方法处理", file=sys.stderr)
            super().dropEvent(event)
            return
            
        # 接受事件
        event.acceptProposedAction()
        
        # 拖放操作完成后，确保输入框获得焦点并设置光标位置
        QTimer.singleShot(100, lambda: self._focus_after_drop(event.pos()))
    
    def _process_text_drop(self, event, mime_data, parent_window):
        """处理文本拖拽，尝试从文本中提取文件路径
        
        Args:
            event: 拖拽事件
            mime_data: 拖拽的MIME数据
            parent_window: FeedbackUI实例
            
        Returns:
            bool: 是否成功处理
        """
        text = mime_data.text()
        print(f"DEBUG: _process_text_drop - 拖拽文本: '{text}'", file=sys.stderr)
        
        # 检查文本是否包含文件URL格式
        if text.startswith("file:///"):
            # 尝试解析文件URL
            try:
                from urllib.parse import unquote
                # 移除前缀并解码URL
                clean_path = unquote(text.replace("file:///", ""))
                # Windows路径修正
                if sys.platform.startswith("win"):
                    if not clean_path.startswith("C:") and len(clean_path) > 1:
                        clean_path = clean_path[0] + ":" + clean_path[1:]
                
                print(f"DEBUG: _process_text_drop - 解析后的路径: {clean_path}", file=sys.stderr)
                
                if os.path.exists(clean_path):
                    file_name = os.path.basename(clean_path)
                    print(f"DEBUG: _process_text_drop - 有效文件路径: {clean_path}", file=sys.stderr)
                    
                    # 处理图片文件
                    if os.path.isfile(clean_path) and os.path.splitext(clean_path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        try:
                            pixmap = QPixmap(clean_path)
                            if not pixmap.isNull() and pixmap.width() > 0:
                                parent_window.add_image_preview(pixmap)
                                event.acceptProposedAction()
                                # 设置焦点到文本输入框（延迟执行以确保事件已完全处理）
                                QTimer.singleShot(100, lambda: parent_window._set_text_focus())
                                return True
                        except Exception as e:
                            print(f"ERROR: _process_text_drop - 加载图片失败: {e}", file=sys.stderr)
                    
                    # 处理为文件引用
                    self._insert_file_reference(parent_window, clean_path, file_name)
                    event.acceptProposedAction()
                    return True
            except Exception as e:
                print(f"ERROR: _process_text_drop - 解析文件URL失败: {e}", file=sys.stderr)
        
        # 检查是否包含Windows文件路径格式（例如 "D:\path\to\file.txt"）
        windows_path_pattern = re.compile(r'^[a-zA-Z]:[/\\].+')
        if windows_path_pattern.match(text):
            path = text.replace('\\', '\\\\')  # 确保路径中的反斜杠正确处理
            print(f"DEBUG: _process_text_drop - 检测到Windows路径格式: {path}", file=sys.stderr)
            
            if os.path.exists(path):
                file_name = os.path.basename(path)
                print(f"DEBUG: _process_text_drop - 有效Windows路径: {path}", file=sys.stderr)
                
                # 处理图片文件
                if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                    try:
                        pixmap = QPixmap(path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            parent_window.add_image_preview(pixmap)
                            event.acceptProposedAction()
                            # 设置焦点到文本输入框（延迟执行以确保事件已完全处理）
                            QTimer.singleShot(100, lambda: parent_window._set_text_focus())
                            return True
                    except Exception as e:
                        print(f"ERROR: _process_text_drop - 加载Windows路径图片失败: {e}", file=sys.stderr)
                
                # 处理为文件引用
                self._insert_file_reference(parent_window, path, file_name)
                event.acceptProposedAction()
                return True
        
        # 尝试普通的文本路径解析
        possible_paths = text.split('\n')
        for path in possible_paths:
            path = path.strip()
            if path and os.path.exists(path):
                file_name = os.path.basename(path)
                print(f"DEBUG: _process_text_drop - 从文本提取文件路径: {path}", file=sys.stderr)
                
                # 处理图片文件
                if os.path.isfile(path) and os.path.splitext(path)[1].lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                    try:
                        pixmap = QPixmap(path)
                        if not pixmap.isNull() and pixmap.width() > 0:
                            parent_window.add_image_preview(pixmap)
                            event.acceptProposedAction()
                            # 设置焦点到文本输入框（延迟执行以确保事件已完全处理）
                            QTimer.singleShot(100, lambda: parent_window._set_text_focus())
                            return True
                    except Exception as e:
                        print(f"ERROR: _process_text_drop - 从文本路径加载图片失败: {e}", file=sys.stderr)
                
                # 处理为文件引用 @文件名
                self._insert_file_reference(parent_window, path, file_name)
                event.acceptProposedAction()
                return True
        
        # 特殊情况：从网络浏览器拖拽链接
        if text.startswith("http://") or text.startswith("https://"):
            # 这里我们可以选择直接插入链接文本，或者进一步处理
            print(f"DEBUG: _process_text_drop - 检测到网页链接: {text}", file=sys.stderr)
            self.insertPlainText(text)
            event.acceptProposedAction()
            return True
                
        # 如果是普通文本，直接插入
        print(f"DEBUG: _process_text_drop - 作为普通文本插入: {text}", file=sys.stderr)
        self.insertPlainText(text)
        event.acceptProposedAction()
        
        # 设置焦点（延迟执行以确保事件已完全处理）
        QTimer.singleShot(100, lambda: self._focus_after_drop(event.pos()))
        
        return True
    
    def _insert_file_reference(self, parent_window, file_path, file_name):
        """插入文件引用到文本编辑框
        
        Args:
            parent_window: FeedbackUI实例
            file_path: 文件完整路径
            file_name: 文件名
        """
        print(f"DEBUG: _insert_file_reference - 开始处理: {file_name}", file=sys.stderr)
        
        # 创建显示名 @文件名
        display_name = f"@{file_name}"
        
        # 处理同名文件
        counter = 1
        original_display_name = display_name
        while display_name in parent_window.dropped_file_references:
            display_name = f"{original_display_name} ({counter})"
            counter += 1
        
        # 存储映射关系
        parent_window.dropped_file_references[display_name] = file_path
        print(f"DEBUG: _insert_file_reference - 添加映射: {display_name} -> {file_path}", file=sys.stderr)
        
        try:
            # 在光标位置插入显示名，并设置为蓝色
            cursor = self.textCursor()
            
            # 保存当前格式
            current_format = cursor.charFormat()
            
            # 创建蓝色文本格式 - 使用更鲜明的蓝色并加粗
            blue_format = QTextCharFormat()
            blue_format.setForeground(QColor("#1a73e8"))  # 更鲜艳的蓝色
            blue_format.setFontWeight(QFont.Bold)  # 加粗
            blue_format.setFontUnderline(False)  # 移除下划线
            
            # 插入前清除可能的选择
            cursor.clearSelection()
            
            # 应用蓝色格式并插入文本
            print(f"DEBUG: _insert_file_reference - 插入文本: {display_name}", file=sys.stderr)
            cursor.setCharFormat(blue_format)
            cursor.insertText(display_name)
            
            # 恢复原始格式
            cursor.setCharFormat(current_format)
            
            # 插入空格，便于继续输入
            cursor.insertText(" ")
            
            # 强制更新显示
            self.update()
            
            # 设置焦点和光标
            QTimer.singleShot(100, lambda: self._ensure_focus(cursor))
            
            print("DEBUG: _insert_file_reference - 文本插入完成", file=sys.stderr)
        except Exception as e:
            print(f"ERROR: _insert_file_reference - 插入文本出错: {e}", file=sys.stderr)
            
    def _ensure_focus(self, cursor):
        """确保文本框获取焦点并设置光标位置"""
        window = self.window()
        if window:
            window.activateWindow()
            window.raise_()
            
        # 强制设置焦点
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.MouseFocusReason)
        
        # 设置光标位置
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _focus_after_drop(self, pos):
        """在拖放操作完成后，确保输入框获得焦点并设置光标位置"""
        # 先激活窗口
        window = self.window()
        if window:
            window.activateWindow()
            window.raise_()
        
        # 为文本编辑框设置强制焦点
        self.activateWindow()
        self.raise_()
        self.setFocus(Qt.MouseFocusReason)  # 使用MouseFocusReason更接近实际操作
        
        # 将鼠标位置转换为文本位置并设置光标
        try:
            cursor_pos = self.cursorForPosition(pos)
            self.setTextCursor(cursor_pos)
        except Exception:
            # 如果转换位置失败，则将光标放在文本末尾
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
        
        # 确保光标可见
        self.ensureCursorVisible()

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
        
        # print("初始化FeedbackUI...", file=sys.stderr) # 清理
        self.prompt = prompt
        
        # print(f"DEBUG: 收到的预定义选项: {predefined_options}", file=sys.stderr) # 清理
        self.predefined_options = predefined_options or []
        # print(f"DEBUG: 初始化使用的预定义选项: {self.predefined_options}", file=sys.stderr) # 清理

        self.result = None  # 使用统一的属性名 result
        self.image_pixmap = None  # 存储粘贴的图片
        self.next_image_id = 0  # 用于生成唯一的图片ID
        self.image_widgets = {}  # 存储图片预览部件 {id: widget}
        
        # 存储常用语数据
        self.canned_responses = []
        
        # 用于存储拖拽文件引用 {显示名: 文件路径}
        self.dropped_file_references = {}
        print("DEBUG: FeedbackUI.__init__ - 初始化dropped_file_references字典", file=sys.stderr)
        
        # 用于控制是否自动最小化的标志
        self.disable_auto_minimize = False
        
        # 用于控制窗口是否固定的标志
        self.window_pinned = False
        
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
                # print(f"警告: 图标文件不存在: {icon_path}", file=sys.stderr) # 可以保留用于调试，或移除
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
                # print(f"DEBUG: 应用最小宽度1000 (恢复的宽度为 {self.width()})", file=sys.stderr) # 清理
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
            
        # 加载窗口固定状态
        self.window_pinned = self.settings.value("windowPinned", False, type=bool)
        self.settings.endGroup() # End "MainWindow_General" group

        # 加载常用语数据
        self._load_canned_responses()

        # 加载快捷图标和数字图标的显示状态
        self.show_shortcut_icons = self.settings.value("CannedResponses/showShortcutIcons", True, type=bool)
        self.number_icons_visible = self.settings.value("CannedResponses/numberIconsVisible", True, type=bool)
        
        print(f"DEBUG: 初始化时的图标显示状态 - 快捷图标:{self.show_shortcut_icons}, 数字图标:{self.number_icons_visible}", file=sys.stderr)

        # print("开始创建UI...", file=sys.stderr) # 清理
        self._create_ui()
        # print("UI创建完成", file=sys.stderr) # 清理
        
        # 更新数字图标显示状态
        self._update_number_icons()
        
        # 应用快捷图标和数字图标的显示状态
        if hasattr(self, 'shortcuts_container'):
            self.shortcuts_container.setVisible(self.show_shortcut_icons)
            if hasattr(self, 'number_icons_container'):
                self.number_icons_container.setVisible(self.number_icons_visible and self.show_shortcut_icons)
        
        # 如果窗口应该被固定，应用固定设置
        if self.window_pinned:
            QTimer.singleShot(100, self._apply_window_pin_state)

    def _load_canned_responses(self):
        """从设置中加载常用语数据"""
        self.settings.beginGroup("CannedResponses")
        responses = self.settings.value("phrases", [])
        self.settings.endGroup()
        
        # 确保responses是一个列表
        if responses is None:
            self.canned_responses = []
        elif isinstance(responses, str):
            # 如果是单个字符串，转换为列表
            self.canned_responses = [responses]
        else:
            try:
                # 尝试转换为列表
                self.canned_responses = list(responses)
            except:
                self.canned_responses = []
        
        print(f"DEBUG: 已加载 {len(self.canned_responses)} 个常用语", file=sys.stderr)

    def _update_number_icons(self):
        """更新数字图标的显示状态和工具提示"""
        # 如果没有数字图标或未初始化，直接返回
        if not hasattr(self, 'shortcut_number_icons') or not self.shortcut_number_icons:
            return
            
        # 遍历所有数字图标
        for i, icon in enumerate(self.shortcut_number_icons):
            # 图标索引从0开始，但显示从1开始
            display_index = i + 1
            
            # 检查是否有对应的常用语
            if i < len(self.canned_responses):
                # 有对应的常用语，设置工具提示为常用语内容
                canned_response = self.canned_responses[i]
                # 如果常用语太长，截断显示
                tooltip_text = canned_response if len(canned_response) <= 50 else canned_response[:47] + "..."
                icon.setToolTip(tooltip_text)
                
                # 设置活跃状态样式 - 更明确的样式规则
                icon.setStyleSheet(f"""
                    QLabel#number_icon_{display_index} {{
                        color: #777777 !important;  /* 改为更深的灰色，添加!important提高优先级 */
                        background-color: rgba(60, 60, 60, 0.5);  /* 半透明背景，表示可用 */
                        border-radius: 14px;  /* 完全圆形 */
                        font-size: 14px;
                        font-weight: bold;
                    }}
                    
                    QLabel#number_icon_{display_index}:hover {{
                        color: #aaaaaa !important;  /* 悬停时颜色为浅灰色，添加!important */
                        background-color: rgba(85, 85, 85, 0.6);  /* 悬停时背景变为较亮的半透明灰色 */
                    }}
                """)
                
                # 将鼠标光标设为手形，表示可点击
                icon.setCursor(Qt.PointingHandCursor)
                
                # 确保图标可见
                icon.setVisible(True)
            else:
                # 没有对应的常用语，隐藏图标
                icon.setVisible(False)

    def _create_ui(self):
        # print("创建中央窗口部件...", file=sys.stderr) # 清理
        central_widget = QWidget()
        central_widget.setMinimumWidth(1000)  # 确保中央部件也足够宽
        self.setCentralWidget(central_widget)
        
        # 主布局：垂直排列
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)  # 将顶部边距进一步减少到5px
        main_layout.setSpacing(20)  # 增加元素间距
        
        # 创建反馈组框架，用于包含所有反馈相关的UI元素
        self.feedback_group = QGroupBox()
        self.feedback_group.setTitle("")  # 无标题
        self.feedback_group.setStyleSheet("""
            QGroupBox {
                background-color: transparent;  /* 透明背景 */
                border: none;  /* 移除边框 */
                margin-top: 0px;  /* 减少顶部边距 */
                padding-top: 0px;  /* 减少顶部内边距 */
            }
        """)  # 使用透明背景和无边框
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setContentsMargins(15, 5, 15, 15)  # 减少顶部内边距到5px
        feedback_layout.setSpacing(18)  # 保持合理的元素间距
        
        # 创建提示文字的滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # 允许内部控件调整大小
        scroll_area.setFrameShape(QFrame.NoFrame)  # 无边框
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # 禁用水平滚动条
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # 需要时显示垂直滚动条
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # 设置滚动区域的样式，添加边框和圆角
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;  /* 完全透明背景 */
                border: none;  /* 移除边框 */
                border-radius: 0px;  /* 移除圆角 */
                padding: 0px;
            }
            
            /* 滚动区域内容背景 */
            QScrollArea QWidget {
                background-color: transparent;  /* 内部小部件也设为透明 */
            }
            
            QScrollBar:vertical {
                background-color: transparent;  /* 透明背景 */
                width: 8px;  /* 减小宽度 */
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: rgba(85, 85, 85, 0.3);  /* 半透明滚动条 */
                min-height: 20px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: rgba(119, 119, 119, 0.4);  /* 悬停时稍微明显一点 */
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # 设置滚动区域的最大高度，确保不会占用太多空间
        scroll_area.setMaximumHeight(250)  # 从230增加到250，以显示更多提示文本
        
        # 创建容器小部件用于放置描述标签
        description_container = QWidget()
        description_layout = QVBoxLayout(description_container)
        description_layout.setContentsMargins(15, 5, 15, 15)  # 减少顶部内边距到5px，其他保持不变
        
        # 确保容器背景透明
        description_container.setStyleSheet("background: transparent;")
        
        # 添加描述标签
        self.description_label = ClickableLabel(self.prompt)
        self.description_label.setWordWrap(True)
        self.description_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.description_label.setStyleSheet("""
            font-weight: bold; 
            margin-bottom: 12px; 
            font-size: 14pt; 
            color: white;
            padding: 5px 0;
            background: transparent;
        """)  # 增加字体大小与边距
        description_layout.addWidget(self.description_label)
        
        # 添加图片处理说明
        self.image_usage_label = ClickableLabel("如果图片反馈异常，建议切换cluade3.5")
        self.image_usage_label.setWordWrap(True)
        self.image_usage_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.image_usage_label.setStyleSheet("""
            color: #ff8c00; 
            font-size: 11pt; 
            margin-top: 8px;
            padding: 2px 0;
            background: transparent;
        """)
        self.image_usage_label.setVisible(False)  # 初始隐藏，只有添加图片后才显示
        description_layout.addWidget(self.image_usage_label)
        
        # 粘贴优化提示（仅在首次启动时显示，现在默认不显示）
        self.paste_optimization_label = ClickableLabel("新功能: 已优化粘贴后的发送逻辑，图片和文本会一次性完整发送到Cursor。使用Ctrl+V粘贴内容。")
        self.paste_optimization_label.setWordWrap(True)
        self.paste_optimization_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.paste_optimization_label.setStyleSheet("""
            color: #4caf50; 
            font-style: italic; 
            font-size: 11pt; 
            margin-top: 8px;
            padding: 2px 0;
            background: transparent;
        """)
        # 默认隐藏粘贴优化提示
        self.paste_optimization_label.setVisible(False)
        description_layout.addWidget(self.paste_optimization_label)
        
        # 创建状态标签
        self.status_label = ClickableLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setStyleSheet("""
            color: #ffffff;
            margin-top: 5px;
            padding: 2px 0;
            background: transparent;
        """)
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
        
        # 选项布局
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(2, 0, 2, 0)  # 进一步减少边距
        options_layout.setSpacing(0)  # 将间距减为0

        # 不添加常用语按钮，因为已经在顶部添加了
        
        # 如果有预定义选项时，创建复选框和标签
        if self.predefined_options and len(self.predefined_options) > 0:
            for option_text in self.predefined_options:
                option_row_layout = QHBoxLayout()
                option_row_layout.setContentsMargins(0, 0, 0, 0)
                option_row_layout.setSpacing(8)  # 保持内部间距
                
                # 创建复选框 - 不再包含文本
                checkbox = QCheckBox()
                checkbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # 固定大小
                self.option_checkboxes.append(checkbox)
                
                # 创建一个容器窗口用于添加背景和圆角
                option_container = QFrame()
                option_container.setObjectName("optionContainer")
                option_container.setStyleSheet("""
                    QFrame#optionContainer {
                        background-color: transparent;  /* 完全透明背景 */
                        border-radius: 8px;
                        border: none;  /* 移除边框 */
                        padding: 2px; /* 减少内边距 */
                        margin: 0px;  /* 完全移除外边距 */
                    }
                    QFrame#optionContainer:hover {
                        background-color: transparent;  /* 保持透明，取消悬停时的背景变化 */
                        border: none;  /* 悬停时也无边框 */
                    }
                """)
                
                # 为容器创建水平布局
                container_layout = QHBoxLayout(option_container)
                container_layout.setContentsMargins(8, 2, 8, 2)  # 进一步减少内边距
                container_layout.setSpacing(8)  # 减少水平间距
                
                # 将复选框添加到容器布局
                container_layout.addWidget(checkbox)
                
                # 创建文本标签 - 使用ClickableLabel，仅用于显示和文本选择
                label = ClickableLabel(option_text)
                label.setWordWrap(True)
                label.setStyleSheet("""
                    color: #aaaaaa;  /* 灰色文字，不再使用透明效果 */
                    font-size: 11pt;
                    padding: 2px 0;
                """)
                self.option_labels.append(label)
                
                # 将标签添加到容器布局
                container_layout.addWidget(label)
                container_layout.setStretchFactor(checkbox, 0)  # 复选框不伸缩
                container_layout.setStretchFactor(label, 1)     # 标签获取所有额外空间
                
                # 将选项容器添加到选项布局，而不是直接添加行布局
                options_layout.addWidget(option_container)
        
        # 添加选项框架和常用语按钮容器到布局
        feedback_layout.addWidget(options_frame)
        #feedback_layout.addWidget(canned_responses_container)  # 已经添加到options_layout中，不需要再次添加
            
        # 添加分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: rgba(85, 85, 85, 0.2);")  # 进一步降低不透明度
        feedback_layout.addWidget(separator)

        # 添加快捷图标容器 - 常用语快捷数字图标
        # 注意：我们将通过修改现有的布局间距来利用已有的28px空间，而不是增加额外空间
        # 原有的布局间距是18px (feedback_layout.setSpacing(18))，
        # text_input_layout的顶部内边距是10px (text_input_layout.setContentsMargins(0, 10, 0, 10))
        # 现在我们将调整这些值，并在它们之间插入我们的容器，总共仍保持28px的空间
        # 将原有的feedback_layout.setSpacing(18)改为5px间距
        feedback_layout.setSpacing(5)  # 从3px增加到5px，增加上方间距

        # 创建快捷图标容器
        self.shortcuts_container = QWidget()
        self.shortcuts_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.shortcuts_container.setFixedHeight(30)  # 容器高度保持30px不变
        self.shortcuts_container.setStyleSheet("""
            background-color: transparent;  /* 透明背景，移除填充效果 */
        """)
        shortcuts_container_layout = QHBoxLayout(self.shortcuts_container)
        shortcuts_container_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_container_layout.setSpacing(0)
        
        # 使用绝对定位布局，这样我们可以精确控制@图标的位置
        # 注释掉下面这行重复设置布局的代码，因为前面已经设置了布局
        # self.shortcuts_container.setLayout(QHBoxLayout())

        # 创建一个新的@图标标签，使用自定义绘制方法确保@符号居中
        class AtIconLabel(QLabel):
            """专用于@图标的自定义标签，确保@符号完美居中"""
            
            clicked = Signal()  # 继承点击信号
            
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setCursor(Qt.PointingHandCursor)
                self.setFixedSize(28, 28)
                # 移除背景色和边框半径，使@符号没有圆形外框
                self.setStyleSheet("""
                    background-color: transparent;
                """)
            
            def paintEvent(self, event):
                # 先调用父类的绘制事件处理
                super().paintEvent(event)
                
                # 创建QPainter进行自定义绘制
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setRenderHint(QPainter.TextAntialiasing)
                
                # 设置@符号颜色
                # 调整颜色为更亮的灰色，使@符号在没有背景的情况下更加明显
                painter.setPen(QColor("#cccccc"))
                
                # 设置字体
                font = QFont()
                font.setPointSize(18)  # 大幅增加字体大小，使@符号尽可能填满圆形框
                font.setBold(True)
                painter.setFont(font)
                
                # 绘制@符号 - 完全居中，并稍微上移
                rect = self.rect()
                # 创建一个上移2px的矩形区域用于绘制文本
                adjusted_rect = QRect(rect.x(), rect.y() - 2, rect.width(), rect.height())
                painter.drawText(adjusted_rect, Qt.AlignCenter, "@")
                
                painter.end()
            
            def mousePressEvent(self, event):
                if event.button() == Qt.LeftButton:
                    event.accept()
                else:
                    super().mousePressEvent(event)
            
            def mouseReleaseEvent(self, event):
                if event.button() == Qt.LeftButton:
                    # 触发点击信号
                    self.clicked.emit()
                    event.accept()
                else:
                    super().mouseReleaseEvent(event)

        # 使用新的专用AtIconLabel
        at_icon = AtIconLabel(self.shortcuts_container)
        at_icon.move(12, 1)  # 向右移动，从8px调整为12px，使其与选项框对齐
        at_icon.clicked.connect(self._toggle_number_icons_visibility)  # 连接点击信号到处理函数
        self.at_icon = at_icon  # 保存为实例变量以便后续访问

        # 创建数字图标容器
        number_icons_container = QWidget(self.shortcuts_container)
        number_icons_container.setGeometry(38, 0, 902, 30)  # 调整左边距，确保与@图标有合适的间距
        number_icons_layout = QHBoxLayout(number_icons_container)
        number_icons_layout.setContentsMargins(0, 1, 0, 1)  # 上下各留1px的间隙
        number_icons_layout.setSpacing(1)  # 图标之间的间距为1px
        
        # 保存为实例变量，以便在其他方法中访问
        self.number_icons_container = number_icons_container

        # 初始化存储数字图标的列表
        self.shortcut_number_icons = []

        # 创建10个数字图标
        for i in range(1, 11):  # 数字1到10
            # 创建一个包含分隔线的容器
            icon_container = QWidget()
            icon_container.setFixedSize(28, 28)  # 与@图标相同大小
            
            # 使用QLabel作为数字图标
            number_label = QLabel(str(i), icon_container)
            number_label.setGeometry(0, 0, 28, 28)  # 占据整个容器
            number_label.setAlignment(Qt.AlignCenter)
            number_label.setObjectName(f"number_icon_{i}")  # 设置对象名称用于CSS样式表选择器
            
            # 基本样式和悬停效果 - 使用更明确的样式规则，确保字体颜色正确设置
            number_label.setStyleSheet(f"""
                QLabel#number_icon_{i} {{
                    color: #999999 !important;  /* 更灰的数字颜色，添加!important确保优先级 */
                    background-color: rgba(49, 49, 49, 0.4);  /* 更透明的背景 */
                    border-radius: 14px;  /* 完全圆形 */
                    font-size: 14px;
                    font-weight: bold;
                }}
                
                QLabel#number_icon_{i}:hover {{
                    color: #dddddd !important;  /* 悬停时数字变为浅灰，而非纯白，添加!important */
                    background-color: rgba(85, 85, 85, 0.55);  /* 悬停时背景更透明 */
                }}
            """)
            
            # 光标变为手型，提示可点击
            number_label.setCursor(Qt.PointingHandCursor)
            
            # 设置工具提示 (Tooltip) - 当前为示例文本，将在后续任务中动态更新
            number_label.setToolTip(f"常用语 {i}")
            
            # 为标签添加事件过滤器，以处理鼠标点击事件
            number_label.installEventFilter(self)
            
            # 为标签存储索引信息，用于点击时识别
            number_label.setProperty("shortcut_index", i - 1)  # 存储0-based索引
            
            # 移除添加分隔线的代码块
            
            # 添加到布局
            number_icons_layout.addWidget(icon_container)
            
            # 保存到图标列表中
            self.shortcut_number_icons.append(number_label)
        
        # 将快捷图标容器添加到主布局
        feedback_layout.addWidget(self.shortcuts_container)

        # 应用之前保存的数字图标可见性设置
        number_icons_visible = self.settings.value("CannedResponses/numberIconsVisible", True, type=bool)
        if hasattr(self, 'number_icons_container'):
            self.number_icons_container.setVisible(number_icons_visible)
            
            # 移除@图标样式变化
            # 不根据数字图标可见性设置@图标颜色

        # 自由文本反馈区
        # 创建文本编辑区和提交按钮的容器
        text_input_container = QWidget()
        text_input_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        text_input_container.setMinimumWidth(950)  # 确保文本输入区域足够宽
        text_input_layout = QVBoxLayout(text_input_container)
        text_input_layout.setContentsMargins(0, 1, 0, 10)  # 将顶部内边距从3px减少到1px
        text_input_layout.setSpacing(15)  # 保持合理间距
        
        # 文本编辑框
        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.feedback_text.setMinimumWidth(950)  # 确保文本编辑框足够宽
        self.feedback_text.setMinimumHeight(250)  # 增加最小高度到250，提供更多可见行数
        self.feedback_text.setPlaceholderText("在此输入反馈内容 (纯文本格式，按Enter发送，Shift+Enter换行，Ctrl+V粘贴图片)")
        

        
        # 连接文本变化信号，更新提交按钮文本
        self.feedback_text.textChanged.connect(self._update_submit_button_text)
        
        # 功能按钮区域 - 总是创建，确保界面完整
        buttons_container = QWidget()
        buttons_layout = QVBoxLayout(buttons_container)  # 改为垂直布局，上方放次要按钮，下方放主按钮
        buttons_layout.setContentsMargins(0, 10, 0, 0)  # 增加顶部内边距
        buttons_layout.setSpacing(10)  # 减小按钮组之间的间距
        
        # 次要按钮区域 - 水平布局
        secondary_buttons_layout = QHBoxLayout()
        secondary_buttons_layout.setContentsMargins(5, 0, 5, 0)  # 减少上下边距
        secondary_buttons_layout.setSpacing(15)  # 保持按钮间距
        secondary_buttons_layout.setAlignment(Qt.AlignLeft)  # 左对齐
        
        # 添加常用语按钮到左侧
        self.bottom_canned_responses_button = QPushButton("常用语")
        self.bottom_canned_responses_button.setObjectName("secondary_button")  # 设置对象名以应用辅助按钮样式
        self.bottom_canned_responses_button.setToolTip("选择或管理常用反馈短语")
        self.bottom_canned_responses_button.clicked.connect(self._show_canned_responses)
        secondary_buttons_layout.addWidget(self.bottom_canned_responses_button)
        
        # 添加固定窗口按钮
        self.pin_window_button = QPushButton("固定窗口")
        self.pin_window_button.setObjectName("secondary_button")  # 初始设为辅助按钮样式
        self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
        self.pin_window_button.clicked.connect(self._toggle_pin_window)
        secondary_buttons_layout.addWidget(self.pin_window_button)
        
        # 将次要按钮布局添加到主按钮容器
        buttons_layout.addLayout(secondary_buttons_layout)
        
        # 主提交按钮布局 - 水平布局，用于包含提交按钮并保持其宽度为100%
        submit_button_layout = QHBoxLayout()
        submit_button_layout.setContentsMargins(5, 0, 5, 0)
        
        # 修改提交按钮，为其设置对象名称以启用特殊样式
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.setObjectName("submit_button") # 设置对象名称以匹配QSS选择器
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.submit_button.setMinimumHeight(60)  # 增加按钮高度，使其更醒目
        self.submit_button.clicked.connect(self._submit_feedback)
        
        # 将提交按钮添加到提交按钮布局
        submit_button_layout.addWidget(self.submit_button)
        
        # 将提交按钮布局添加到主按钮容器
        buttons_layout.addLayout(submit_button_layout)
        
        # 将水平布局添加到文本输入布局
        text_input_layout.addWidget(self.feedback_text, 1)  # 设置拉伸因子为1，允许垂直拉伸
        
        # 创建一个单独的容器来放置次要按钮
        secondary_buttons_container = QWidget()
        secondary_buttons_container_layout = QHBoxLayout(secondary_buttons_container)
        secondary_buttons_container_layout.setContentsMargins(5, 0, 5, 0)
        secondary_buttons_container_layout.setSpacing(15)
        secondary_buttons_container_layout.setAlignment(Qt.AlignLeft)
        
        # 添加常用语按钮到左侧
        self.bottom_canned_responses_button = QPushButton("常用语")
        self.bottom_canned_responses_button.setObjectName("secondary_button")
        self.bottom_canned_responses_button.setToolTip("选择或管理常用反馈短语")
        self.bottom_canned_responses_button.clicked.connect(self._show_canned_responses)
        secondary_buttons_container_layout.addWidget(self.bottom_canned_responses_button)
        
        # 添加固定窗口按钮
        self.pin_window_button = QPushButton("固定窗口")
        self.pin_window_button.setObjectName("secondary_button")
        self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
        self.pin_window_button.clicked.connect(self._toggle_pin_window)
        secondary_buttons_container_layout.addWidget(self.pin_window_button)
        
        # 添加次要按钮容器到布局，设置较小的上下间距
        text_input_layout.addWidget(secondary_buttons_container)
        
        # 创建提交按钮容器
        submit_button_container = QWidget()
        submit_button_layout = QHBoxLayout(submit_button_container)
        submit_button_layout.setContentsMargins(5, 5, 5, 0)  # 减少顶部的间距
        
        # 修改提交按钮，为其设置对象名称以启用特殊样式
        self.submit_button = QPushButton("提交反馈")
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.submit_button.setMinimumHeight(60)
        self.submit_button.clicked.connect(self._submit_feedback)
        
        # 将提交按钮添加到布局
        submit_button_layout.addWidget(self.submit_button)
        
        # 添加提交按钮容器到文本输入布局
        text_input_layout.addWidget(submit_button_container)
        
        # 将文本输入容器添加到反馈布局
        feedback_layout.addWidget(text_input_container)
        
        # 将反馈分组框添加到主布局
        main_layout.addWidget(self.feedback_group)
        
        # 创建GitHub链接容器 - 移至主布局底部
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setContentsMargins(0, 0, 0, 0)  # 彻底移除边距，使GitHub标签完全贴近窗口底部
        github_layout.setAlignment(Qt.AlignCenter)  # 居中对齐
        
        # 创建GitHub链接标签
        github_label = QLabel()
        github_label.setText("<a href='#' style='color: #aaaaaa; text-decoration: none;'>GitHub</a>")
        github_label.setOpenExternalLinks(False)  # 不自动打开链接
        github_label.setToolTip("访问项目GitHub仓库")
        github_label.setCursor(Qt.PointingHandCursor)  # 设置指针光标
        github_label.linkActivated.connect(self._open_github_repo)
        
        # 设置GitHub图标标签样式
        github_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                color: #aaaaaa;
                padding: 0px;
                margin: 0px;
            }
            QLabel:hover {
                color: #ffffff;
            }
        """)
        
        # 将GitHub标签添加到布局
        github_layout.addWidget(github_label)
        
        # 添加GitHub链接容器到主布局
        main_layout.addWidget(github_container)
        
        # 初始更新一次提交按钮文本
        self._update_submit_button_text()
        
        # print(f"UI创建完成，包含 {len(self.option_checkboxes)} 个选项复选框", file=sys.stderr)

    def _set_text_focus(self):
        """设置焦点到文本输入框并激活光标"""
        if hasattr(self, 'feedback_text') and self.feedback_text is not None:
            # 激活主窗口
            self.activateWindow()
            self.raise_()
            
            # 设置焦点到文本框
            self.feedback_text.activateWindow()
            self.feedback_text.raise_()
            self.feedback_text.setFocus(Qt.MouseFocusReason)
            
            # 确保光标可见并在文本末尾
            cursor = self.feedback_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.feedback_text.setTextCursor(cursor)
            self.feedback_text.ensureCursorVisible()

    def get_image_content_data(self, image_id=None) -> Optional[Dict[str, Any]]:
        """
        Processes a QPixmap (identified by image_id or the last added one)
        into a dictionary containing Base64 encoded image data and its metadata.
        The image is resized and compressed if necessary to meet defined limits.
        Output structure: {"image_data": {"type": "image", "data": "base64...", "mimeType": "image/jpeg"}, 
                           "metadata": {"width": ..., "height": ..., "format": ..., "size": ...}}
        Returns None if processing fails or no valid image is found.
        """
        # print(f"DEBUG: 开始处理图片 ID: {image_id}", file=sys.stderr) # 清理或根据需要保留详细日志级别
        
        pixmap_to_save = None 
        if self.image_widgets:
            if image_id is not None and image_id in self.image_widgets:
                pixmap_to_save = self.image_widgets[image_id].original_pixmap
            elif self.image_widgets: 
                last_id = max(self.image_widgets.keys())
                pixmap_to_save = self.image_widgets[last_id].original_pixmap
        else:
            return None
            
        if pixmap_to_save is None or pixmap_to_save.isNull():
            return None
            
        original_width = pixmap_to_save.width()
        original_height = pixmap_to_save.height()
        
        if original_width > MAX_IMAGE_WIDTH or original_height > MAX_IMAGE_HEIGHT:
            pixmap_to_save = pixmap_to_save.scaled(
                MAX_IMAGE_WIDTH, 
                MAX_IMAGE_HEIGHT,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
        
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        save_format = "JPEG" # Currently defaults to JPEG
        mime_type = "image/jpeg"
        saved_successfully = False
        quality = 80
        
        if buffer.open(QIODevice.WriteOnly):
            if pixmap_to_save.save(buffer, save_format, quality):
                saved_successfully = True
            buffer.close() 
        
        if (not saved_successfully or byte_array.isEmpty() or 
            (byte_array.size() > MAX_IMAGE_BYTES)):
            quality_levels = [70, 60, 50, 40]
            for lower_quality in quality_levels:
                byte_array.clear()
                buffer = QBuffer(byte_array)
                if buffer.open(QIODevice.WriteOnly):
                    if pixmap_to_save.save(buffer, save_format, lower_quality):
                        saved_successfully = True
                        buffer.close()
                        if byte_array.size() <= MAX_IMAGE_BYTES:
                            quality = lower_quality
                            break
                    else:
                        buffer.close()
        
        if not saved_successfully or byte_array.isEmpty():
            QMessageBox.critical(self, "图像处理错误", "无法将图像保存为 JPEG 格式。")
            return None
            
        if byte_array.size() > MAX_IMAGE_BYTES:
            QMessageBox.critical(self, "图像过大", 
                              f"图像大小 ({byte_array.size() // 1024} KB) 超过了限制 ({MAX_IMAGE_BYTES // 1024} KB)。\n"
                              "请使用更小的图像或进一步压缩。")
            return None
            
        image_data_bytes = byte_array.data()
        if not image_data_bytes:
            return None
        
        try:
            base64_encoded_data = base64.b64encode(image_data_bytes).decode('utf-8')
            
            # Basic validation of base64 string (optional, as b64decode will fail if invalid)
            # try: 
            #     decoded = base64.b64decode(base64_encoded_data)
            #     if len(decoded) != len(image_data_bytes):
            #         pass 
            # except Exception as e: 
            #     pass 
            
            metadata = {
                "width": pixmap_to_save.width(),
                "height": pixmap_to_save.height(),
                "format": save_format.lower(), 
                "size": byte_array.size()
            }
            image_data_dict = {
                "type": "image",
                "data": base64_encoded_data,
                "mimeType": mime_type
            }
            
            return { 
                "image_data": image_data_dict,
                "metadata": metadata # Metadata is generated but currently not used by server.py for MCP message
            }
            
        except Exception as e:
            QMessageBox.critical(self, "图像处理错误", f"图像数据编码失败: {e}")
            return None
    
    def get_all_images_content_data(self) -> List[Dict[str, Any]]:
        """
        Collects processed data for all currently added images.
        Calls get_image_content_data for each image.
        Returns a list of dictionaries, where each dictionary contains
        an "image_item" (for direct MCP use) and a "metadata_item".
        """
        result = []
        # print(f"DEBUG: 开始处理所有图片, 共 {len(self.image_widgets)} 张", file=sys.stderr) # 清理
        for image_id in self.image_widgets.keys():
            # print(f"DEBUG: 处理图片 ID: {image_id}", file=sys.stderr) # 清理
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
                # print(f"DEBUG: 成功处理图片 ID: {image_id}", file=sys.stderr) # 清理
            # else:
                # print(f"DEBUG: 图片处理失败 ID: {image_id}", file=sys.stderr) # 清理
        # print(f"DEBUG: 总共成功处理 {len(result)}/{len(self.image_widgets)} 张图片", file=sys.stderr) # 清理
        return result

    def _submit_feedback(self):
        """
        Handles the submission of feedback.
        Collects text from predefined options and the text input field.
        Collects all added images using get_all_images_content_data.
        Packages everything into the self.result dictionary with the structure 
        {"content": [list of text and image items]}.
        The old logic for direct keyboard injection via cursor_direct_input has been removed.
        The UI now solely relies on returning this structured data for MCP processing by server.py.
        """
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []
        
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    # 获取选项文本并去除可能的编号前缀（如"1. ", "2. "等）
                    option_text = self.predefined_options[i].strip()
                    # 使用正则表达式匹配并删除前面的数字和点号
                    option_text = re.sub(r'^\d+\.\s*', '', option_text)
                    selected_options.append(option_text)
        
        # 构建最终文本，将选项和用户输入组合起来
        if selected_options and feedback_text:
            # 如果有选中选项和用户输入文字，使用换行符分隔
            combined_text = f"{'; '.join(selected_options)}\n{feedback_text}"
        elif selected_options:
            # 如果只有选中选项，无需换行
            combined_text = f"{'; '.join(selected_options)}"
        else:
            # 如果只有用户输入文字
            combined_text = feedback_text
        
        content_list = [] # This list will hold dictionaries for text and image items
        if combined_text:
            content_list.append({
                "type": "text",
                "text": combined_text
            })

        # 处理拖拽的文件引用
        if self.dropped_file_references:
            final_text_content = self.feedback_text.toPlainText()
            for display_name, file_path in self.dropped_file_references.items():
                if display_name in final_text_content:
                    content_list.append({
                        "type": "file_reference",
                        "display_name": display_name,
                        "path": file_path
                    })

        # The old keyboard injection logic (using cursor_direct_input) has been removed.
        # All data, including images, is now packaged for MCP transport.
        
        all_images_data = self.get_all_images_content_data()
        if all_images_data:
            for image_set in all_images_data:
                if "image_item" in image_set and image_set["image_item"]:
                    content_list.append(image_set["image_item"])
        
        if not content_list:
            self.result = FeedbackResult(content=[])
            self.close()
            return
        
        self.result = FeedbackResult(content=content_list)
        self.close()

    def closeEvent(self, event):
        # Save general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("windowPinned", self.window_pinned)
        self.settings.endGroup()

        # 清空拖拽文件引用
        self.dropped_file_references.clear()

        super().closeEvent(event)
        
    def _apply_window_pin_state(self):
        """应用保存的窗口固定状态"""
        # 先设置按钮状态，再调整窗口标志
        if self.window_pinned:
            # 更新按钮样式为活跃状态 - 使用对象名称而不是直接设置样式表
            self.pin_window_button.setObjectName("pin_window_active")
            self.pin_window_button.setText("取消固定")
            self.pin_window_button.setToolTip("点击取消固定窗口")
            
            # 保存当前窗口位置和大小
            current_geometry = self.geometry()
            
            # 设置窗口标志
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            
            # 延迟显示以减少闪烁
            QTimer.singleShot(10, lambda: self._restore_window_state(current_geometry))
        else:
            # 恢复按钮默认样式
            self.pin_window_button.setObjectName("secondary_button")
            self.pin_window_button.setText("固定窗口")
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
            
            # 保存当前窗口位置和大小
            current_geometry = self.geometry()
            
            # 恢复标准窗口标志
            self.setWindowFlags(Qt.Window)
            
            # 延迟显示以减少闪烁
            QTimer.singleShot(10, lambda: self._restore_window_state(current_geometry))
        
        # 强制刷新样式
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        
        # 保存窗口固定状态
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("windowPinned", self.window_pinned)
        self.settings.endGroup()

    def run(self) -> FeedbackResult:
        # print("开始运行UI...", file=sys.stderr) # 清理
        self.show()
        # print("UI窗口已显示，准备进入事件循环...", file=sys.stderr) # 清理
        
        # 添加一个单次定时器，在窗口显示后强制应用宽度
        # 这是处理某些系统上可能出现的窗口尺寸设置不正确的问题的方法
        QTimer.singleShot(100, self._enforce_window_size)
        
        # 添加一个单次定时器，设置焦点到文本输入框
        QTimer.singleShot(200, self._set_text_focus)
        
        QApplication.instance().exec()
        # print("事件循环结束，窗口关闭...", file=sys.stderr) # 清理

        if not self.result:
            # print("未获得反馈结果，返回空内容列表", file=sys.stderr) # 清理
            return FeedbackResult(content=[])

        # print(f"返回反馈结果: {self.result}", file=sys.stderr) # 清理
        return self.result
        
    def _enforce_window_size(self):
        """强制应用窗口尺寸，确保宽度为1000，高度至少为750"""
        needs_resize = False
        
        # 检查宽度
        if self.width() < 1000:
            # print(f"DEBUG: 强制应用窗口宽度，当前宽度为 {self.width()}, 调整到 1000", file=sys.stderr) # 清理
            needs_resize = True
            
        # 检查高度
        if self.height() < 750:
            # print(f"DEBUG: 强制应用窗口高度，当前高度为 {self.height()}, 调整到 750", file=sys.stderr) # 清理
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
            # 如果窗口固定，不执行自动最小化
            if self.window_pinned:
                # 固定状态下什么都不做，保持窗口可见
                return super().event(event)
                
            # 未固定状态的默认行为：如果窗口当前可见且未最小化，且未禁用自动最小化功能
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
                # print("DEBUG: 从剪贴板处理了图片内容", file=sys.stderr) # 清理
        
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
                # print("DEBUG: 从剪贴板处理了文本内容", file=sys.stderr) # 清理
        
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
                            # print(f"DEBUG: 从剪贴板URL处理了图片: {file_path}", file=sys.stderr) # 清理
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
            
            # 设置焦点到文本输入框
            QTimer.singleShot(100, self._set_text_focus)
            
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
            # 使用全局样式表中定义的submit_button样式
            self.submit_button.setObjectName("submit_button")
            # 更新提交按钮的工具提示
            self.submit_button.setToolTip("点击后将自动关闭窗口并激活Cursor对话框")
        elif has_images:
            self.submit_button.setText(f"发送 {len(self.image_widgets)} 张图片")
            # 使用全局样式表中定义的submit_button样式
            self.submit_button.setObjectName("submit_button")
            self.submit_button.setToolTip("点击后将自动关闭窗口并激活Cursor对话框")
        elif has_text:
            self.submit_button.setText("提交反馈")
            # 使用全局样式表中定义的submit_button样式
            self.submit_button.setObjectName("submit_button")
            self.submit_button.setToolTip("")  # 清除工具提示
        else:
            self.submit_button.setText("提交")
            # 使用全局样式表中定义的submit_button样式
            self.submit_button.setObjectName("submit_button")
            self.submit_button.setToolTip("")  # 清除工具提示
        
        # 刷新样式
        self.submit_button.style().unpolish(self.submit_button)
        self.submit_button.style().polish(self.submit_button)

    def _show_canned_responses(self):
        """显示常用语对话框"""
        self.disable_auto_minimize = True
        
        try:
            settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
            settings.beginGroup("CannedResponses")
            responses = settings.value("phrases", [])
            settings.endGroup()
            
            if responses is None:
                responses = []
            elif not isinstance(responses, list):
                try:
                    if isinstance(responses, str):
                        responses = [responses]
                    else:
                        responses = list(responses)
                except:
                    responses = []
            
            # 显示常用语对话框
            dialog = SelectCannedResponseDialog(responses, self)
            dialog.setWindowModality(Qt.ApplicationModal)
            result = dialog.exec()
            
            # 对话框关闭后，重新加载常用语并更新图标状态
            self._load_canned_responses()
            
            # 读取用户在对话框中设置的常用语图标显示状态
            show_icons_enabled = settings.value("CannedResponses/showShortcutIcons", True, type=bool)
            
            # 更新快捷图标容器显示状态
            self._update_shortcut_icons_visibility(show_icons_enabled)
            
            # 强制更新数字图标
            self._update_number_icons()
            
            # 确保在启用时显示数字图标
            if show_icons_enabled and hasattr(self, 'number_icons_container'):
                # 读取并应用数字图标的显示状态
                number_icons_visible = settings.value("CannedResponses/numberIconsVisible", True, type=bool)
                if hasattr(self, 'number_icons_container'):
                    self.number_icons_container.setVisible(number_icons_visible)
                    print(f"DEBUG: 设置数字图标可见性为: {number_icons_visible}", file=sys.stderr)
            
        finally:
            self.disable_auto_minimize = False

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
                # print(f"DEBUG: 从剪贴板添加了图片，尺寸: {pixmap.width()}x{pixmap.height()}", file=sys.stderr) # 清理
        
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
                            # print(f"DEBUG: 从剪贴板URL添加了图片: {file_path}", file=sys.stderr) # 清理
        
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
            
            # print(f"DEBUG: 移除了图片，剩余 {len(self.image_widgets)} 张", file=sys.stderr)

    def _toggle_pin_window(self):
        """切换窗口固定状态"""
        # 保存当前窗口位置和大小
        current_geometry = self.geometry()
        
        # 切换固定状态
        self.window_pinned = not self.window_pinned
        
        # 根据状态设置窗口标志
        if self.window_pinned:
            # 设置窗口标志
            self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
            # 更新按钮文本和工具提示
            self.pin_window_button.setText("取消固定")
            self.pin_window_button.setToolTip("点击取消固定窗口")
            # 更新按钮样式类名
            self.pin_window_button.setObjectName("pin_window_active")
        else:
            # 恢复标准窗口标志
            self.setWindowFlags(Qt.Window)
            # 恢复按钮文本和工具提示
            self.pin_window_button.setText("固定窗口")
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化")
            # 恢复按钮样式类名
            self.pin_window_button.setObjectName("secondary_button")
        
        # 强制刷新样式
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        
        # 延迟显示以减少闪烁
        QTimer.singleShot(10, lambda: self._restore_window_state(current_geometry))
        
        # 保存窗口固定状态
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("windowPinned", self.window_pinned)
        self.settings.endGroup()
        
    def _open_github_repo(self):
        """打开GitHub仓库页面"""
        webbrowser.open("https://github.com/pawaovo/interactive-feedback-mcp")

    def _restore_window_state(self, geometry):
        """恢复窗口位置和大小，并激活窗口"""
        self.setGeometry(geometry)  # 恢复原来的位置和大小
        self.show()
        self.raise_()
        self.activateWindow()

    def eventFilter(self, watched, event):
        """事件过滤器，处理数字图标的点击事件"""
        # 检查是否是鼠标按下事件
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # 检查是否是数字图标
            if hasattr(watched, 'property') and watched.property("shortcut_index") is not None:
                shortcut_index = watched.property("shortcut_index")
                # 处理数字图标点击事件
                self._handle_number_icon_click(shortcut_index)
                return True  # 事件已处理
        
        # 对于其他事件，交给父类处理
        return super().eventFilter(watched, event)
    
    def _handle_number_icon_click(self, index):
        """处理数字图标点击事件，插入对应常用语到文本编辑框"""
        # 检查是否有对应的常用语
        if 0 <= index < len(self.canned_responses):
            # 获取对应的常用语
            text = self.canned_responses[index]
            
            # 如果文本为空或不是字符串，不执行插入
            if not text or not isinstance(text, str):
                return
            
            # 获取对应的图标
            icon = self.shortcut_number_icons[index]
            display_index = index + 1
            
            # 移除点击高亮效果的相关代码
            # 不再保存原始样式
            # 不再设置高亮样式
            
            # 插入到文本编辑框
            if hasattr(self, 'feedback_text'):
                # 获取当前光标
                cursor = self.feedback_text.textCursor()
                
                # 插入文本
                cursor.insertText(text)
                
                # 设置新的光标位置
                self.feedback_text.setTextCursor(cursor)
                
                # 确保文本编辑框获得焦点
                self.feedback_text.setFocus()
                
                print(f"DEBUG: 点击图标 {index+1}，插入常用语: {text[:20]}...", file=sys.stderr)
            
            # 移除使用定时器恢复原样式的代码

    def _update_shortcut_icons_visibility(self, visible=None):
        """更新快捷图标容器的可见性
        
        Args:
            visible (bool, optional): 是否可见，如果不提供则使用当前设置值
        """
        if visible is None:
            # 如果未提供可见性参数，从设置中读取当前状态
            visible = self.settings.value("CannedResponses/showShortcutIcons", True, type=bool)
        
        # 更新实例变量
        self.show_shortcut_icons = visible
        
        # 更新UI显示
        if hasattr(self, 'shortcuts_container'):
            self.shortcuts_container.setVisible(visible)
            
            # 如果设置为隐藏整个容器，先保存数字图标的可见性状态
            number_icons_visible = False
            if hasattr(self, 'number_icons_container'):
                number_icons_visible = self.number_icons_container.isVisible()
            
            # 当快捷图标区域被重新显示时，恢复之前保存的数字图标可见性设置
            if visible and hasattr(self, 'number_icons_container'):
                saved_number_icons_visible = self.settings.value("CannedResponses/numberIconsVisible", True, type=bool)
                self.number_icons_container.setVisible(saved_number_icons_visible)
                
            # 强制更新数字图标
            self._update_number_icons()

    def _toggle_number_icons_visibility(self):
        """切换数字图标的显示/隐藏状态，但保持@图标始终可见"""
        # 获取数字图标容器的引用，需要确保该容器已经被创建并作为实例变量存在
        if hasattr(self, 'number_icons_container') and self.number_icons_container:
            # 切换显示/隐藏状态
            current_visibility = self.number_icons_container.isVisible()
            self.number_icons_container.setVisible(not current_visibility)
            
            # 保存当前状态以便下次使用
            self.settings.setValue("CannedResponses/numberIconsVisible", not current_visibility)
            print(f"DEBUG: 切换数字图标可见性为: {not current_visibility}", file=sys.stderr)
            
            # 确保在显示时更新图标状态
            if not current_visibility:  # 如果之前是隐藏的，现在要显示
                self._update_number_icons()  # 更新数字图标状态

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
        main_layout.setContentsMargins(18, 18, 18, 18)  # 增加边距
        main_layout.setSpacing(18)  # 增加间距
        
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
        edit_layout.setContentsMargins(12, 15, 12, 15)  # 调整内边距
        edit_layout.setSpacing(12)  # 调整间距
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入新的常用语或编辑选中的项目")
        edit_layout.addWidget(self.input_field)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)  # 减小按钮间距
        
        # 添加按钮
        self.add_button = QPushButton("添加")
        self.add_button.clicked.connect(self._add_response)
        self.add_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.add_button)
        
        # 更新按钮
        self.update_button = QPushButton("更新")
        self.update_button.clicked.connect(self._update_response)
        self.update_button.setEnabled(False)  # 初始禁用
        self.update_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.update_button)
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.clicked.connect(self._delete_response)
        self.delete_button.setEnabled(False)  # 初始禁用
        self.delete_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.delete_button)
        
        # 清空按钮
        self.clear_button = QPushButton("清空全部")
        self.clear_button.clicked.connect(self._clear_responses)
        self.clear_button.setObjectName("secondary_button")
        buttons_layout.addWidget(self.clear_button)
        
        # 添加按钮布局到编辑区域
        edit_layout.addLayout(buttons_layout)
        
        # 添加编辑组到主布局
        main_layout.addWidget(edit_group)
        
        # 底部的按钮行布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # 设置间距
        button_layout.addStretch(1)  # 添加弹性空间，将按钮推到右侧
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setObjectName("secondary_button")
        button_layout.addWidget(self.close_button)
        
        # 添加对话框按钮布局到主布局
        main_layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QListWidget {
                font-size: 11pt;
                padding: 5px;
                background-color: #2D2D2D;
            }
            QListWidget::item {
                border-bottom: 1px solid #3A3A3A;
                padding: 6px;
            }
            QListWidget::item:hover {
                background-color: transparent; /* 移除悬停效果 */
            }
            QListWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QListWidget::item:focus {
                background-color: transparent;
                border: none;
            }
            QLineEdit {
                font-size: 11pt;
                padding: 8px;
                height: 20px;
                background-color: #333333;
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
            
            # print(f"DEBUG: 成功添加常用语: {text}", file=sys.stderr)
    
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
        # print("DEBUG: SelectCannedResponseDialog.__init__ - START", file=sys.stderr)
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
        # print(f"DEBUG: SelectCannedResponseDialog.__init__ - Received {len(self.responses)} responses", file=sys.stderr)
        
        # 创建设置对象
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # 创建界面
        self._create_ui()
        
        # 加载常用语数据
        self._load_responses()
        
        # print(f"DEBUG: SelectCannedResponseDialog.__init__ - END, Loaded {len(self.responses)} responses into UI", file=sys.stderr)
    
    def _create_ui(self):
        """创建用户界面"""
        # print("DEBUG: SelectCannedResponseDialog._create_ui - START", file=sys.stderr)
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(16)  # 增加间距
        layout.setContentsMargins(18, 18, 18, 18)  # 增加边距
        
        # 创建顶部布局，包含标题和复选框
        top_layout = QHBoxLayout()
        
        # 标题标签
        title = QLabel("常用语列表")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: white;")
        top_layout.addWidget(title)
        
        # 添加弹性空间，将复选框推到右边
        top_layout.addStretch(1)
        
        # 添加快捷图标显示控制复选框
        self.show_shortcut_icons_checkbox = QCheckBox("常用语图标")
        self.show_shortcut_icons_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                color: #ffffff;
                spacing: 8px;  /* 复选框与文本之间的间距 */
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1px solid #555555;
                border-radius: 3px;
                background-color: #333333;
            }
            QCheckBox::indicator:checked {
                background-color: #555555;
                border: 1px solid #666666;
            }
        """)
        top_layout.addWidget(self.show_shortcut_icons_checkbox)
        
        # 添加顶部布局到主布局
        layout.addLayout(top_layout)
        
        # 提示标签
        hint = QLabel("双击插入文本，点击删除按钮移除项目")
        hint.setStyleSheet("font-size: 9pt; color: #aaaaaa;")
        layout.addWidget(hint)
        
        # 从设置中读取当前状态
        show_icons_enabled = self.settings.value("CannedResponses/showShortcutIcons", True, type=bool)
        self.show_shortcut_icons_checkbox.setChecked(show_icons_enabled)
        
        layout.addSpacing(5)  # 添加一点额外的间距
        
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
                background-color: transparent; /* 移除悬停时的背景色变化 */
            }
            QListWidget::item:selected:!active {
                background-color: transparent;
            }
            QListWidget::item:selected:active {
                background-color: transparent; /* 移除选中时的背景色变化 */
                border: 1px solid #404040; /* 只保留轻微边框标示 */
            }
            /* 禁用横向滚动条 */
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
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
        self.add_button.setObjectName("secondary_button")  # 使用统一的secondary_button对象名
        input_layout.addWidget(self.add_button)
        
        layout.addLayout(input_layout)
        
        # 设置整体对话框样式
        self.setStyleSheet("""
            QDialog {
                background-color: #222222;
            }
            QLabel {
                color: white;
            }
            QListWidget {
                background-color: #2D2D2D;
                color: white;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                padding: 4px;
                font-size: 11pt;
            }
            QListWidget::item {
                border-bottom: 1px solid #3A3A3A;
                padding: 6px;  /* 减少内边距 */
                margin: 1px;   /* 减少外边距 */
            }
            QListWidget::item:hover {
                background-color: transparent; /* 移除悬停时的背景色变化 */
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
        # print("DEBUG: SelectCannedResponseDialog._create_ui - END", file=sys.stderr)
    
    def _load_responses(self):
        """加载常用语到列表"""
        # print(f"DEBUG: SelectCannedResponseDialog._load_responses - START, {len(self.responses)} responses to load", file=sys.stderr)
        self.list_widget.clear()
        for i, response in enumerate(self.responses):
            # print(f"DEBUG: SelectCannedResponseDialog._load_responses - Loading item {i+1}: '{response}'", file=sys.stderr)
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
        # print("DEBUG: SelectCannedResponseDialog._load_responses - Cleared selection", file=sys.stderr)
        # print("DEBUG: SelectCannedResponseDialog._load_responses - END", file=sys.stderr)
    
    def _add_item_to_list(self, text):
        """将常用语添加到列表 - 单行显示，过长省略"""
        # print(f"DEBUG: SelectCannedResponseDialog._add_item_to_list - Adding: '{text}'", file=sys.stderr)
        # 创建列表项
        item = QListWidgetItem()
        self.list_widget.addItem(item)

        # 创建自定义小部件
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 3, 6, 3)  # 减少边距，使项目更紧凑
        layout.setSpacing(8)  # 保持间距

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
                # print(f"DEBUG: 双击选择常用语: {text}", file=sys.stderr)
                
                # 插入到父窗口输入框
                if self.parent_window and hasattr(self.parent_window, 'feedback_text'):
                    feedback_text = self.parent_window.feedback_text
                    feedback_text.insertPlainText(text)
                    
                    # 确保设置焦点到文本输入框并激活光标
                    QTimer.singleShot(100, lambda: self._set_parent_focus(feedback_text))
                    
                    # print("DEBUG: 已插入文本到输入框", file=sys.stderr)
                    
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
        
        # print(f"DEBUG: SelectCannedResponseDialog._save_responses - Saving {len(self.responses)} responses", file=sys.stderr)
        
        # 保存到设置
        self.settings.beginGroup("CannedResponses")
        self.settings.setValue("phrases", self.responses)
        self.settings.endGroup()
        self.settings.sync()
        # print(f"DEBUG: 已保存 {len(self.responses)} 个常用语", file=sys.stderr)
    
    def closeEvent(self, event):
        """处理关闭事件，保存常用语状态"""
        # print(f"DEBUG: SelectCannedResponseDialog.closeEvent - START", file=sys.stderr)
        # 保存常用语
        self._save_responses()
        
        # 保存快捷图标的显示状态
        show_icons_enabled = self.show_shortcut_icons_checkbox.isChecked()
        self.settings.setValue("CannedResponses/showShortcutIcons", show_icons_enabled)
        
        # 调用父类方法
        super().closeEvent(event)
        # print("DEBUG: SelectCannedResponseDialog.closeEvent - END", file=sys.stderr)
    
    def get_selected_response(self):
        """获取选择的常用语"""
        return self.selected_response

    def _insert_text_to_parent(self, text):
        """处理双击文本插入到父窗口的输入框
        
        这是一个新的方法，用于处理来自DraggableListWidget的双击信号
        """
        if text and self.parent_window and hasattr(self.parent_window, 'feedback_text'):
            # 插入文本并关闭对话框
            feedback_text = self.parent_window.feedback_text
            feedback_text.insertPlainText(text)
            
            # 确保设置焦点到文本输入框并激活光标
            QTimer.singleShot(10, lambda: self._set_parent_focus(feedback_text))
            
            # print(f"DEBUG: 通过新方法插入文本到输入框: {text}", file=sys.stderr)
            # 保存选定的常用语
            self.selected_response = text
            # 关闭对话框
            self.accept()
        else:
            # print(f"DEBUG: 无法插入文本: text={bool(text)}, parent={bool(self.parent_window)}", file=sys.stderr)
            pass
            
    def _set_parent_focus(self, text_edit):
        """设置父窗口文本输入框的焦点和光标位置"""
        if text_edit:
            text_edit.setFocus()
            # 将光标设置在文本末尾
            cursor = text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            text_edit.setTextCursor(cursor)

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
                background-color: transparent; /* 移除悬停时的背景色变化 */
            }
            QListWidget::item:selected:!active {
                background-color: transparent;
            }
            QListWidget::item:selected:active {
                background-color: transparent; /* 移除选中时的背景色变化 */
                border: 1px solid #404040; /* 只保留轻微边框标示 */
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
                    # print(f"DEBUG: 双击事件捕获，文本内容: {text}", file=sys.stderr)
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
                # print("DEBUG: 开始拖拽操作", file=sys.stderr)
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
        # print("DEBUG: 拖放操作完成，发出drag_completed信号", file=sys.stderr)
        self.drag_completed.emit()

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    # print("进入feedback_ui函数...", file=sys.stderr)
    app = QApplication.instance() or QApplication()
    # print("QApplication实例化完成", file=sys.stderr)
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")
    
    # 设置应用程序属性
    app.setQuitOnLastWindowClosed(True)
    
    # print("设置应用程序样式完成", file=sys.stderr)
    
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
            background-color: rgba(30, 30, 30, 180);  /* 更改为与最外层一致的颜色 */
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
            background-color: #3C3C3C;  /* 改为灰色 */
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
            background-color: #444444;  /* 鼠标悬停时变亮 */
        }
        
        QPushButton:pressed {
            background-color: #333333;  /* 按下时变暗 */
        }
        
        QPushButton:disabled {
            background-color: #555;
            color: #999;
        }
        
        /* 添加特定按钮样式 */
        QPushButton#submit_button {
            background-color: #252525;  /* 进一步变浅的背景色 */
            color: white;
            border: 2px solid #3A3A3A;  /* 使用较深的边框样式 */
            padding: 12px 20px;
            font-weight: bold;
            font-size: 13pt;
            border-radius: 15px;  /* 增加圆角半径使其更圆润 */
            min-height: 60px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2), 0 3px 5px rgba(0, 0, 0, 0.15);  /* 使用适中的阴影效果 */
        }
        
        QPushButton#submit_button:hover {
            background-color: #303030;  /* 悬停时背景更亮 */
            border: 2px solid #454545;  /* 边框变亮 */
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.25), 0 4px 6px rgba(0, 0, 0, 0.2);  /* 悬停时阴影更明显 */
        }
        
        QPushButton#submit_button:pressed {
            background-color: #202020;  /* 按下时稍深 */
            border: 2px solid #353535;
            box-shadow: 0 3px 5px rgba(0, 0, 0, 0.15), 0 1px 3px rgba(0, 0, 0, 0.1);  /* 按下时阴影减弱 */
        }
        
        QPushButton#secondary_button {
            background-color: transparent;  /* 改为透明背景 */
            color: white;
            border: 1px solid #454545;  /* 保留边框效果 */
            font-size: 10pt;
            padding: 5px 10px;
            min-height: 32px;
            min-width: 120px;
            max-height: 32px;
        }
        
        QPushButton#secondary_button:hover {
            background-color: rgba(64, 64, 64, 0.3);  /* 半透明悬停效果 */
            border: 1px solid #555555;
        }
        
        QPushButton#secondary_button:pressed {
            background-color: rgba(48, 48, 48, 0.4);  /* 半透明按下效果 */
        }
        
        QPushButton#pin_window_active {
            background-color: rgba(80, 80, 80, 0.5);  /* 半透明背景 */
            color: white;
            border: 1px solid #606060;
            font-size: 10pt;
            padding: 5px 10px;
            min-height: 32px;
            min-width: 120px;
            max-height: 32px;
        }
        
        QPushButton#pin_window_active:hover {
            background-color: rgba(85, 85, 85, 0.6);
            border: 1px solid #676767;
        }
        
        QPushButton#pin_window_active:pressed {
            background-color: rgba(69, 69, 69, 0.6);
        }
        
        /* 文本编辑框样式 */
        QTextEdit {
            background-color: #282828;  /* 更浅一些的灰色 */
            color: #ffffff;  /* 纯白色文本，提高可见度 */
            font-size: 13pt;
            font-family: 'Segoe UI', 'Microsoft YaHei UI', Arial, sans-serif;
            font-weight: 400;
            line-height: 1.4;
            letter-spacing: 0.015em;
            word-spacing: 0.05em;
            border: 2px solid #3A3A3A; /* 加粗边框，与顶部区域一致 */
            border-radius: 10px;
            padding: 12px;
            selection-background-color: #505050;
            min-height: 250px;  /* 确保最小高度符合需求 */
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.1);  /* 添加阴影效果 */
            transition: all 0.3s ease;  /* 添加过渡效果 */
        }
        
        QTextEdit:hover {
            border: 2px solid #454545;  /* 悬停时只改变边框颜色，不改变背景 */
            background-color: #282828;  /* 保持与默认状态相同背景色 */
        }
        
        QTextEdit:focus {
            border: 2px solid #505050; /* 与边框粗细保持一致 */
        }
        
        /* 占位符文本样式 */
        QTextEdit[placeholderText] {
            color: #999;
        }
        
        /* 复选框样式 */
        QCheckBox {
            color: #b8b8b8;  /* 选项文本颜色 */
            spacing: 8px;
            font-size: 11pt;
            min-height: 28px;  /* 减小高度 */
            padding: 1px;  /* 减少内边距 */
        }
        
        QCheckBox::indicator {
            width: 22px;
            height: 22px;
            border: 1px solid #444444;  /* 更柔和的边框色 */
            border-radius: 4px;
            background-color: transparent;  /* 未选中时无背景填充 */
        }
        
        QCheckBox::indicator:checked {
            background-color: #4D4D4D;  /* 选中后为灰黑色调填充 */
            border: 2px solid #555555;  /* 边框变粗 */
            border-width: 2px;
            border-color: #555555;
            transform: scale(1.05);  /* 轻微放大效果 */
            image: none;  /* 移除图标引用 */
            background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='#ffffff' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
            background-position: center;
            background-repeat: no-repeat;
        }
        
        QCheckBox::indicator:hover:!checked {
            border: 1px solid #666666;  /* 悬停时边框更明显 */
            background-color: #333333;  /* 悬停时有轻微背景 */
        }
        
        QCheckBox::indicator:checked:hover {
            background-color: #555555;  /* 选中状态悬停时更亮 */
            border-width: 2px;
            border-color: #666666;
        }
        
        /* 添加QLabel样式来显示勾选标记 */
        QCheckBox::indicator:checked + QLabel {
            color: white;
        }
        
        /* 分隔线样式 */
        QFrame[frameShape="4"] {
            color: #555555;  /* 改为浅灰色 */
            max-height: 1px;
            margin: 10px 0;
            background-color: #555555; /* 明确设置背景色 */
            border: none; /* 移除边框 */
        }
        
        /* 滚动区域样式 */
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        
        QScrollBar:vertical {
            background-color: transparent;  /* 透明背景 */
            width: 8px;  /* 减小宽度 */
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: rgba(85, 85, 85, 0.3);  /* 半透明滚动条 */
            min-height: 20px;
            border-radius: 4px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: rgba(119, 119, 119, 0.4);  /* 悬停时稍微明显一点 */
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
        # print("未提供预定义选项，使用空列表", file=sys.stderr)
    
    # print("准备创建FeedbackUI实例...", file=sys.stderr)
    ui = FeedbackUI(prompt, predefined_options)
    # print("FeedbackUI实例创建完成，准备运行...", file=sys.stderr)
    result = ui.run()
    # print("UI运行完成，获得结果", file=sys.stderr)

    if output_file and result:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        # Save the result to the output file
        with open(output_file, "w") as f:
            json.dump(result, f)
        return None

    return result

if __name__ == "__main__":
    # print("开始执行主程序...", file=sys.stderr)
    parser = argparse.ArgumentParser(description="Run the feedback UI")
    parser.add_argument("--prompt", default="I implemented the changes you requested.", help="The prompt to show to the user")
    parser.add_argument("--predefined-options", default="", help="Pipe-separated list of predefined options (|||)")
    parser.add_argument("--output-file", help="Path to save the feedback result as JSON")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with more verbose output")
    parser.add_argument("--full-ui", action="store_true", default=False, help="显示完整UI界面，包含所有功能")
    args = parser.parse_args()
    
    # print(f"命令行参数: {args}", file=sys.stderr)

    # 调试模式标志
    debug_mode = args.debug
    
    # if debug_mode:
        # print("DEBUG: 运行在调试模式", file=sys.stderr)
        
    # 处理预定义选项
    if args.predefined_options:
        # 有传入预定义选项，使用传入的选项
        predefined_options = [opt for opt in args.predefined_options.split("|||") if opt]
        # print(f"使用传入的预定义选项: {predefined_options}", file=sys.stderr)
    else:
        # 没有传入预定义选项
        if args.full_ui:
            # 仅在手动运行脚本且明确指定--full-ui参数时才使用示例选项
            predefined_options = ["示例选项1", "示例选项2", "示例选项3"]
            # print(f"启用完整UI模式并使用示例预定义选项: {predefined_options}", file=sys.stderr)
        else:
            # 没有选项
            predefined_options = []
            # print("使用空选项列表", file=sys.stderr)
    
    # print(f"最终使用的预定义选项: {predefined_options}", file=sys.stderr)
    
    # print("创建UI...", file=sys.stderr)
    result = feedback_ui(args.prompt, predefined_options, args.output_file)
    # print("UI执行完成", file=sys.stderr)
    if result:
        pretty_result = json.dumps(result, indent=2, ensure_ascii=False)
        # print(f"\n反馈结果:\n{pretty_result}")
        
        # if debug_mode: # 调试模式下的验证可以保留，或者根据需要移除
            # print("\nDEBUG: 验证反馈结果格式", file=sys.stderr)
            # if "content" not in result:
                # print("ERROR: 结果缺少 'content' 字段", file=sys.stderr)
            # else:
                # content = result["content"]
                # if not isinstance(content, list):
                    # print(f"ERROR: 'content' 不是列表类型: {type(content)}", file=sys.stderr)
                # else:
                    # print(f"DEBUG: 内容列表包含 {len(content)} 项", file=sys.stderr)
                    # for i, item in enumerate(content):
                        # if "type" not in item:
                            # print(f"ERROR: 内容项 {i+1} 缺少 'type' 字段", file=sys.stderr)
                        # elif item["type"] == "text":
                            # if "text" not in item:
                                # print(f"ERROR: 文本项 {i+1} 缺少 'text' 字段", file=sys.stderr)
                            # else:
                                # print(f"DEBUG: 文本项 {i+1} 有效，长度: {len(item['text'])}", file=sys.stderr)
                        # elif item["type"] == "image":
                            # if "data" not in item:
                                # print(f"ERROR: 图片项 {i+1} 缺少 'data' 字段", file=sys.stderr)
                            # elif "mimeType" not in item:
                                # print(f"ERROR: 图片项 {i+1} 缺少 'mimeType' 字段", file=sys.stderr)
                            # else:
                                # print(f"DEBUG: 图片项 {i+1} 有效, MIME类型: {item['mimeType']}", file=sys.stderr)
                                # print(f"DEBUG: Base64数据长度: {len(item['data'])}", file=sys.stderr)
                        # else:
                            # print(f"WARNING: 内容项 {i+1} 有未知类型: {item['type']}", file=sys.stderr)
    sys.exit(0)

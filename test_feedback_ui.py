#!/usr/bin/env python
# 创建一个新测试文件，用于直接显示完整的FeedbackUI实例

import os
import sys
from PySide6.QtWidgets import QApplication

# 导入FeedbackUI和相关函数
from feedback_ui import FeedbackUI, get_dark_mode_palette

def main():
    """运行测试UI显示"""
    print("开始运行测试UI...")
    
    # 创建QApplication实例
    app = QApplication(sys.argv)
    app.setPalette(get_dark_mode_palette(app))
    app.setStyle("Fusion")
    
    # 设置全局样式表 (可选)
    app.setStyleSheet("""
        /* 添加自定义样式，让UI组件更明显 */
        QPushButton {
            background-color: #2a82da;
            color: white;
            font-size: 11pt;
            padding: 8px 16px;
        }
        
        QGroupBox {
            border: 2px solid #555;
            background-color: rgba(45, 45, 45, 180);
            margin-top: 12px;
            padding-top: 15px;
        }
        
        QTextEdit {
            background-color: #333;
            color: #ffffff;
            border: 1px solid #555;
            padding: 6px;
            font-size: 12pt;
        }
    """)
    
    # 创建FeedbackUI实例，带有预定义选项
    prompt = "测试完整UI显示 - 请确认所有功能都可见"
    predefined_options = ["选项1", "选项2", "选项3"]
    
    # 明确创建FeedbackUI实例并显示
    ui = FeedbackUI(prompt, predefined_options)
    ui.show()  # 明确调用show()方法显示窗口
    
    # 进入应用程序事件循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
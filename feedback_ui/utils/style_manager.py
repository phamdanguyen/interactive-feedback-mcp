# feedback_ui/utils/style_manager.py
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QPalette, QColor, Qt # Qt 已在之前添加

# 全局 QSS 样式表 (Global QSS Stylesheet)
# 注意: box-shadow 和 transform 等高级CSS属性在Qt QSS中不被直接支持。
# 对于这些，可能需要使用其他技术（如 QGraphicsDropShadowEffect）或接受一定的视觉差异。
# Note: Advanced CSS properties like box-shadow and transform are not directly supported in Qt QSS.
# For these, other techniques (e.g., QGraphicsDropShadowEffect) might be needed, or accept visual differences.
GLOBAL_QSS = """
    /* 全局字体设置 (Global Font Settings) */
    * {
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QWidget { font-size: 10pt; }

    QGroupBox {
        border: 1px solid #555;
        border-radius: 6px;
        margin-top: 12px; /* 为标题留出空间 (Space for title) */
        padding-top: 12px; /* 确保内容在标题下方 (Ensure content is below title) */
        background-color: transparent;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 8px;
        color: #aaa;
        font-weight: bold;
    }

    QLabel { color: white; padding: 2px; font-size: 11pt; }

    /* ClickableLabel from clickable_label.py */
    ClickableLabel {
        color: #ffffff;
        selection-background-color: #2374E1; /* Qt.blue is similar */
        selection-color: white;
        /* padding already applied in QLabel general rule, can be more specific if needed */
    }
     /* AtIconLabel from clickable_label.py, specific styling if needed beyond QLabel */
    AtIconLabel {
        background-color: transparent;
    }


    QPushButton {
        background-color: #3C3C3C; color: white; border: none;
        border-radius: 6px; padding: 8px 16px; font-weight: bold;
        font-size: 11pt; min-width: 120px; min-height: 36px;
    }
    QPushButton:hover { background-color: #444444; }
    QPushButton:pressed { background-color: #333333; }
    QPushButton:disabled { background-color: #555; color: #999; }

    QPushButton#submit_button {
        background-color: #252525; color: white; border: 2px solid #3A3A3A;
        padding: 12px 20px; font-weight: bold; font-size: 13pt;
        border-radius: 15px; min-height: 60px;
    }
    QPushButton#submit_button:hover { background-color: #303030; border: 2px solid #454545; }
    QPushButton#submit_button:pressed { background-color: #202020; border: 2px solid #353535; }

    QPushButton#secondary_button, QPushButton#delete_canned_item_button {
        background-color: transparent; color: white; border: 1px solid #454545;
        font-size: 10pt; padding: 5px 10px; min-height: 32px;
        min-width: 100px; max-height: 32px;
    }
    QPushButton#secondary_button:hover, QPushButton#delete_canned_item_button:hover {
        background-color: rgba(64, 64, 64, 0.3); border: 1px solid #555555;
    }
    QPushButton#secondary_button:pressed, QPushButton#delete_canned_item_button:pressed {
        background-color: rgba(48, 48, 48, 0.4);
    }
    /* Specific style for delete button in dialogs if it has objectName "delete_canned_item_button" */
    QPushButton#delete_canned_item_button { 
        background-color: #d32f2f; min-width: 40px; 
    }
    QPushButton#delete_canned_item_button:hover { background-color: #f44336; }
    QPushButton#delete_canned_item_button:pressed { background-color: #b71c1c; }

    QPushButton#pin_window_active {
        background-color: rgba(80, 80, 80, 0.5); color: white; border: 1px solid #606060;
        font-size: 10pt; padding: 5px 10px; min-height: 32px;
        min-width: 120px; max-height: 32px;
    }
    QPushButton#pin_window_active:hover { background-color: rgba(85, 85, 85, 0.6); border: 1px solid #676767; }
    QPushButton#pin_window_active:pressed { background-color: rgba(69, 69, 69, 0.6); }

    /* QTextEdit and FeedbackTextEdit from feedback_text_edit.py */
    QTextEdit, FeedbackTextEdit {
        background-color: #272727; color: #ffffff; font-size: 13pt;
        font-family: 'Segoe UI', 'Microsoft YaHei UI', Arial, sans-serif;
        font-weight: 400;
        border: 2px solid #3A3A3A; border-radius: 10px; padding: 12px;
        selection-background-color: #505050; selection-color: white;
        min-height: 250px;
    }
    QTextEdit:hover, FeedbackTextEdit:hover { border: 2px solid #454545; background-color: #272727; }
    QTextEdit:focus, FeedbackTextEdit:focus { border: 2px solid #505050; }
    /* PlaceholderText color is set via QPalette in FeedbackTextEdit and MainWindow */

    QCheckBox { color: #b8b8b8; spacing: 8px; font-size: 11pt; min-height: 28px; padding: 1px; }
    QCheckBox::indicator {
        width: 22px; height: 22px; border: 1px solid #444444;
        border-radius: 4px; background-color: transparent;
    }
    QCheckBox::indicator:checked {
        background-color: #4D4D4D; border: 2px solid #555555;
        image: none; /* Crucial for SVG background-image to work */
        background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'><path fill='#ffffff' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
        background-position: center; background-repeat: no-repeat;
    }
    QCheckBox::indicator:hover:!checked { border: 1px solid #666666; background-color: #333333; }
    QCheckBox::indicator:checked:hover { background-color: #555555; border-color: #666666; }

    QFrame[frameShape="4"] /* HLine */ {
        color: #555555; max-height: 1px; margin: 10px 0;
        background-color: #555555; border: none;
    }
    QScrollArea { background-color: transparent; border: none; }
    QScrollBar:vertical { background: transparent; width: 8px; margin: 0px; }
    QScrollBar::handle:vertical { background: rgba(85,85,85,0.3); min-height: 20px; border-radius: 4px; }
    QScrollBar::handle:vertical:hover { background: rgba(119,119,119,0.4); }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

    /* FeedbackTextEdit's internal images_container (QWidget) */
    FeedbackTextEdit > QWidget {
        background-color: #4a4a4a;
        border-top: 1px solid #555555;
        border-radius: 0 0 10px 10px; /* Only bottom corners rounded */
        padding: 8px;
    }

    /* ImagePreviewWidget from image_preview.py */
    ImagePreviewWidget {
        background-color: rgba(51, 51, 51, 200);
        border: 1px solid #555;
        border-radius: 4px;
        margin: 2px;
    }
    ImagePreviewWidget:hover {
        border: 1px solid #2a82da; /* Highlight on hover */
    }

    /* Dialog specific styles */
    ManageCannedResponsesDialog QListWidget, 
    SelectCannedResponseDialog QListWidget, 
    DraggableListWidget {
        font-size: 11pt; padding: 5px; background-color: #2D2D2D;
        border: 1px solid #3A3A3A; border-radius: 4px; color: white;
    }
    ManageCannedResponsesDialog QListWidget::item, 
    SelectCannedResponseDialog QListWidget::item, 
    DraggableListWidget::item {
        border-bottom: 1px solid #3A3A3A; padding: 6px; margin: 1px;
    }
    ManageCannedResponsesDialog QListWidget::item:hover, 
    SelectCannedResponseDialog QListWidget::item:hover, 
    DraggableListWidget::item:hover {
        background-color: transparent; /* No hover background for items */
    }
    ManageCannedResponsesDialog QListWidget::item:selected, 
    SelectCannedResponseDialog QListWidget::item:selected, 
    DraggableListWidget::item:selected {
        background-color: transparent; border: none; /* No selection background */
    }
    ManageCannedResponsesDialog QListWidget::item:focus, 
    SelectCannedResponseDialog QListWidget::item:focus, 
    DraggableListWidget::item:focus {
        background-color: transparent; border: none; /* No focus background */
    }

    ManageCannedResponsesDialog QLineEdit, 
    SelectCannedResponseDialog QLineEdit {
        font-size: 11pt; padding: 8px;
        background-color: #333333; color: white; 
        border: 1px solid #444; border-radius: 4px;
    }

    /* Labels within dialogs */
    ManageCannedResponsesDialog QLabel, 
    SelectCannedResponseDialog QLabel {
        font-size: 10pt; color: #aaa;
    }
    /* Specific title label in SelectCannedResponseDialog */
    SelectCannedResponseDialog QLabel#DialogTitleLabel { /* Assuming you set objectName */
         font-size: 14pt; font-weight: bold; color: white;
    }
    SelectCannedResponseDialog QLabel#DialogHintLabel { /* Assuming you set objectName */
         font-size: 9pt; color: #aaaaaa;
    }

    /* CheckBox within SelectCannedResponseDialog */
    SelectCannedResponseDialog QCheckBox {
        font-size: 11pt; color: #ffffff; spacing: 8px;
    }
    SelectCannedResponseDialog QCheckBox::indicator {
        width: 18px; height: 18px; border: 1px solid #555555;
        border-radius: 3px; background-color: #333333;
    }
    SelectCannedResponseDialog QCheckBox::indicator:checked {
        background-color: #555555; border: 1px solid #666666;
         background-image: url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='18' height='18' viewBox='0 0 24 24'><path fill='#ffffff' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z'/></svg>");
        background-position: center; background-repeat: no-repeat;
    }
    
    /* QLabel within DraggableListWidget items (for text display) */
    DraggableListWidget QLabel {
         color: white; font-size: 11pt; /* text-overflow: ellipsis; Not directly supported */
    }
"""

def get_dark_mode_palette() -> QPalette:
    """Creates and returns a dark mode QPalette.
       创建并返回一个暗色模式的 QPalette。
    """
    darkPalette = QPalette()

    # 使用 QPalette.ColorRole 枚举成员
    darkPalette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
    darkPalette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
    darkPalette.setColor(QPalette.ColorRole.AlternateBase, QColor(50, 50, 50))
    darkPalette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
    darkPalette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    darkPalette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.ColorRole.Dark, QColor(40, 40, 40))
    darkPalette.setColor(QPalette.ColorRole.Shadow, QColor(25, 25, 25))
    darkPalette.setColor(QPalette.ColorRole.Button, QColor(60, 60, 60))
    darkPalette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.ColorRole.BrightText, QColor(240, 240, 240))
    darkPalette.setColor(QPalette.ColorRole.Link, QColor(80, 160, 255)) # 稍亮的链接颜色 (Slightly brighter link color)
    darkPalette.setColor(QPalette.ColorRole.Highlight, QColor(70, 70, 70)) # 文本编辑、列表视图等的选择背景 (Selection background for text edits, list views etc.)
    darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white) # 选定文本颜色 (Selected text color)
    darkPalette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.ColorRole.PlaceholderText, QColor(127, 127, 127)) # QLineEdit, QTextEdit 占位符 (Placeholders)

    return darkPalette

def apply_global_style(app: QApplication):
    """Applies the global dark mode palette and QSS to the application.
       将全局暗色模式调色板和QSS应用于应用程序。
    """
    default_font = QFont("Segoe UI", 10) # 确保设置默认字体 (Ensure default font is set)
    app.setFont(default_font)
    
    app.setPalette(get_dark_mode_palette())
    app.setStyleSheet(GLOBAL_QSS)
    app.setStyle("Fusion") # Fusion 风格通常与 QSS 配合良好 (Fusion style often works best with QSS)

# feedback_ui/main_window.py
import os
import sys
import json
import re # 正则表达式 (Regular expressions)
import webbrowser # 打开网页链接 (For opening web links)
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QGroupBox, QFrame, QSizePolicy,
    QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QEvent, QObject # QObject for parent type hint
from PySide6.QtGui import QIcon, QTextCursor, QPixmap # Added QPixmap

# --- 从子模块导入 (Imports from submodules) ---
from .utils.constants import FeedbackResult, ContentItem # APP_NAME, SETTINGS_GROUP_MAIN etc. are used by SettingsManager
from .utils.settings_manager import SettingsManager
from .utils.image_processor import get_image_items_from_widgets # Renamed from get_all_images_content_data
# style_manager is typically used in main.py to apply global styles

from .widgets.clickable_label import ClickableLabel, AtIconLabel # CursorOverrideFilter is internal to ClickableLabel
from .widgets.feedback_text_edit import FeedbackTextEdit
from .widgets.image_preview import ImagePreviewWidget

from .dialogs.select_canned_response_dialog import SelectCannedResponseDialog
# ManageCannedResponsesDialog is often launched from SelectCannedResponseDialog or a menu,
# but can be imported if there's a direct button for it.
# For simplicity, we assume SelectCannedResponseDialog handles management access.

class FeedbackUI(QMainWindow):
    """
    Main window for the Interactive Feedback MCP application.
    交互式反馈MCP应用程序的主窗口。
    """
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.output_result: Optional[FeedbackResult] = None # Stores the final result (存储最终结果)

        # --- 内部状态 (Internal State) ---
        self.image_pixmap: Optional[QPixmap] = None # Stores the last added/pasted QPixmap (obsolete, use image_widgets)
        self.next_image_id = 0
        self.image_widgets: Dict[int, ImagePreviewWidget] = {} # image_id: widget
        self.canned_responses: List[str] = []
        self.dropped_file_references: Dict[str, str] = {} # display_name: file_path
        self.disable_auto_minimize = False # Prevents window minimizing on deactivate (防止窗口在失活时最小化)
        self.window_pinned = False # Whether the window is pinned on top (窗口是否置顶)

        self.settings_manager = SettingsManager(self)

        self._setup_window()
        self._load_settings() # Load persistent settings like canned responses and window state
        
        self._create_ui_layout() # Create the main UI layout and widgets
        self._connect_signals() # Connect signals from UI elements

        self._update_number_icons_display()
        self._update_shortcut_icons_visibility_state(self.show_shortcut_icons) # Initial visibility
        self._apply_pin_state_on_load() # Apply pinned state from settings

    def _setup_window(self):
        """Sets up basic window properties like title, icon, size."""
        self.setWindowTitle("交互式反馈 MCP (Interactive Feedback MCP)")
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700) # Ensure a decent minimum height
        self.setWindowFlags(Qt.WindowType.Window) # Standard window

        # --- 设置窗口图标 (Set Window Icon) ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Assume 'images' folder is relative to this file's directory or the project root
        # Here, relative to 'feedback_ui' package. If main.py is one level up, adjust path.
        icon_path_relative_to_package = os.path.join("images", "feedback.png")
        # Construct path from the script directory of main_window.py
        # This assumes 'images' is a sibling to 'utils', 'widgets' etc. or accessible from project root.
        # For a structure like:
        # project_root/
        #   main.py
        #   feedback_ui/
        #     main_window.py
        #     images/
        #       feedback.png
        # The path should be relative to main_window.py location.
        icon_path = os.path.join(os.path.dirname(__file__), "images", "feedback.png")

        if not os.path.exists(icon_path):
             # Try path relative to where main.py might be (one level up)
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images", "feedback.png")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 图标文件未找到于 '{icon_path}'。(Warning: Icon file not found at '{icon_path}'.)", file=sys.stderr)
            # Consider creating the 'images' directory if it doesn't exist, though icon must be present.
            # images_dir = os.path.dirname(icon_path)
            # if not os.path.exists(images_dir):
            #     try:
            #         os.makedirs(images_dir, exist_ok=True)
            #     except OSError as e:
            #         print(f"警告: 创建 'images' 目录失败: {e}", file=sys.stderr)


    def _load_settings(self):
        """Loads settings using SettingsManager."""
        self.resize(1000, 750) # Default size
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - 1000) // 2, (screen.height() - 750) // 2) # Center

        geom = self.settings_manager.get_main_window_geometry()
        if geom:
            self.restoreGeometry(geom)
            if self.width() < 1000: self.setMinimumWidth(1000) # Enforce min width after restore
            if self.height() < 700: self.setMinimumHeight(700)


        state = self.settings_manager.get_main_window_state()
        if state: self.restoreState(state)
            
        self.window_pinned = self.settings_manager.get_main_window_pinned()
        self._load_canned_responses_from_settings()
        self.show_shortcut_icons = self.settings_manager.get_show_shortcut_icons()
        self.number_icons_visible = self.settings_manager.get_number_icons_visible()


    def _create_ui_layout(self):
        """Creates the main UI layout and populates it with widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 5, 20, 10)
        main_layout.setSpacing(15) # Adjusted spacing

        # --- Feedback Group (反馈区域组) ---
        self.feedback_group = QGroupBox() # Title can be set if needed
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setContentsMargins(15, 5, 15, 15)
        feedback_layout.setSpacing(10) # Spacing within the group

        # --- Description Area (描述区域) ---
        self._create_description_area(feedback_layout)

        # --- Predefined Options (预定义选项) ---
        if self.predefined_options:
            self._create_options_checkboxes(feedback_layout)
            
        # --- Separator (分隔线) ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        feedback_layout.addWidget(separator)

        # --- Shortcut Icons Panel (快捷图标面板) ---
        self._create_shortcut_icons_panel(feedback_layout)
        
        # --- Text Input and Submission Area (文本输入与提交区域) ---
        self._create_input_submission_area(feedback_layout)
        
        main_layout.addWidget(self.feedback_group)
        
        # --- GitHub Link (GitHub 链接) ---
        self._create_github_link_area(main_layout)
        
        self._update_submit_button_text_status() # Initial state of submit button

    def _create_description_area(self, parent_layout: QVBoxLayout):
        """Creates the scrollable area for prompts and status messages."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setMaximumHeight(200) # Limit height of description area

        desc_widget_container = QWidget() # Container for labels inside scroll area
        desc_layout = QVBoxLayout(desc_widget_container)
        desc_layout.setContentsMargins(15, 5, 15, 15) # Padding for text
        
        self.description_label = ClickableLabel(self.prompt, self)
        self.description_label.setWordWrap(True)
        desc_layout.addWidget(self.description_label)
        
        self.image_usage_label = ClickableLabel(
            "如果图片反馈异常，建议切换Claude 3.5 Sonnet模型。(If image feedback is abnormal, try Claude 3.5 Sonnet)", self)
        self.image_usage_label.setWordWrap(True)
        self.image_usage_label.setVisible(False) # Initially hidden
        desc_layout.addWidget(self.image_usage_label)
        
        # This label seems to be for a specific feature announcement, might be temporary
        self.paste_optimization_label = ClickableLabel(
            "新功能: 已优化粘贴后的发送逻辑，图片和文本会一次性完整发送到Cursor。使用Ctrl+V粘贴内容。\n"
            "(New: Optimized paste logic. Images and text are sent completely. Use Ctrl+V.)", self)
        self.paste_optimization_label.setWordWrap(True)
        self.paste_optimization_label.setVisible(False) # Initially hidden
        desc_layout.addWidget(self.paste_optimization_label)
        
        self.status_label = ClickableLabel("", self) # For status messages
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status_label.setVisible(False)
        desc_layout.addWidget(self.status_label)

        scroll_area.setWidget(desc_widget_container)
        parent_layout.addWidget(scroll_area)

    def _create_options_checkboxes(self, parent_layout: QVBoxLayout):
        """Creates checkboxes for predefined options."""
        self.option_checkboxes: List[QCheckBox] = []
        self.option_labels: List[ClickableLabel] = [] # To make labels clickable for toggling checkbox

        options_frame = QFrame() # Frame to group options
        options_frame_layout = QVBoxLayout(options_frame)
        options_frame_layout.setContentsMargins(0,0,0,0) # No margins for the frame itself
        options_frame_layout.setSpacing(2) # Small spacing between option rows

        for i, option_text in enumerate(self.predefined_options):
            option_container = QWidget() # Container for one checkbox and label
            row_layout = QHBoxLayout(option_container)
            row_layout.setContentsMargins(8, 2, 8, 2)
            row_layout.setSpacing(8)

            checkbox = QCheckBox(self)
            checkbox.setObjectName(f"optionCheckbox_{i}")
            self.option_checkboxes.append(checkbox)
            row_layout.addWidget(checkbox)

            label = ClickableLabel(option_text, self)
            label.setWordWrap(True)
            # Connect label click to toggle checkbox
            label.clicked.connect(checkbox.toggle) # Toggle associated checkbox
            checkbox.toggled.connect(lambda checked, lbl=label: lbl.setProperty("isChecked", checked)) # For QSS
            
            self.option_labels.append(label)
            row_layout.addWidget(label, 1) # Label takes more space
            options_frame_layout.addWidget(option_container)
        
        parent_layout.addWidget(options_frame)

    def _create_shortcut_icons_panel(self, parent_layout: QVBoxLayout):
        """Creates the panel with '@' icon and number shortcut icons for canned responses."""
        self.shortcuts_container = QWidget(self)
        self.shortcuts_container.setFixedHeight(30)
        shortcuts_container_layout = QHBoxLayout(self.shortcuts_container)
        shortcuts_container_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_container_layout.setSpacing(5) # Spacing between @ and numbers

        self.at_icon = AtIconLabel(self.shortcuts_container)
        # self.at_icon.move(12, 1) # Use layout instead of move
        shortcuts_container_layout.addWidget(self.at_icon)

        self.number_icons_container = QWidget(self.shortcuts_container)
        number_icons_layout = QHBoxLayout(self.number_icons_container)
        number_icons_layout.setContentsMargins(0, 1, 0, 1) # Tight margins
        number_icons_layout.setSpacing(2) # Tight spacing between number icons

        self.shortcut_number_icons: List[QLabel] = []
        for i in range(1, 11): # Up to 10 shortcuts
            icon_widget = QWidget() # Container for each number label for better spacing/sizing control
            icon_widget.setFixedSize(28, 28)
            icon_layout = QVBoxLayout(icon_widget) # Use layout to center
            icon_layout.setContentsMargins(0,0,0,0)
            
            number_label = QLabel(str(i), icon_widget)
            # number_label.setGeometry(0,0,28,28) # Layout handles geometry
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            number_label.setObjectName(f"number_icon_{i}") # For QSS
            number_label.setCursor(Qt.CursorShape.PointingHandCursor)
            number_label.setToolTip(f"常用语 {i} (Canned Response {i})")
            number_label.installEventFilter(self) # For click handling
            number_label.setProperty("shortcut_index", i - 1) # Store index
            
            icon_layout.addWidget(number_label)
            number_icons_layout.addWidget(icon_widget)
            self.shortcut_number_icons.append(number_label)
        
        number_icons_layout.addStretch(1) # Push icons to the left
        shortcuts_container_layout.addWidget(self.number_icons_container, 1) # Number container takes available space
        parent_layout.addWidget(self.shortcuts_container)

    def _create_input_submission_area(self, parent_layout: QVBoxLayout):
        """Creates the text input field and action buttons."""
        text_input_area_widget = QWidget()
        text_input_layout = QVBoxLayout(text_input_area_widget)
        text_input_layout.setContentsMargins(0, 5, 0, 0) # Top margin for separation
        text_input_layout.setSpacing(10)

        self.feedback_text = FeedbackTextEdit(self)
        self.feedback_text.setPlaceholderText(
            "在此输入反馈内容 (纯文本格式，Enter发送，Shift+Enter换行，Ctrl+V粘贴图片)\n"
            "(Enter feedback here (plain text, Enter to send, Shift+Enter for newline, Ctrl+V to paste images))")
        text_input_layout.addWidget(self.feedback_text, 1) # Text edit takes most space

        # --- Secondary Buttons (Canned Responses, Pin Window) ---
        secondary_buttons_bar = QHBoxLayout()
        secondary_buttons_bar.setSpacing(15)
        
        self.bottom_canned_responses_button = QPushButton("常用语 (Canned)", self)
        self.bottom_canned_responses_button.setObjectName("secondary_button")
        self.bottom_canned_responses_button.setToolTip("选择或管理常用反馈短语 (Select or manage canned responses)")
        secondary_buttons_bar.addWidget(self.bottom_canned_responses_button)
        
        self.pin_window_button = QPushButton("固定窗口 (Pin Window)", self)
        self.pin_window_button.setObjectName("secondary_button") # Initial style
        self.pin_window_button.setToolTip("固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)")
        secondary_buttons_bar.addWidget(self.pin_window_button)
        secondary_buttons_bar.addStretch(1) # Push buttons to left
        text_input_layout.addLayout(secondary_buttons_bar)

        # --- Submit Button ---
        self.submit_button = QPushButton("提交反馈 (Submit Feedback)", self)
        self.submit_button.setObjectName("submit_button")
        self.submit_button.setMinimumHeight(50) # Slightly reduced from 60
        text_input_layout.addWidget(self.submit_button)
        
        parent_layout.addWidget(text_input_area_widget)

    def _create_github_link_area(self, parent_layout: QVBoxLayout):
        """Creates the GitHub link at the bottom."""
        github_container = QWidget()
        github_layout = QHBoxLayout(github_container)
        github_layout.setContentsMargins(0, 5, 0, 0) # Top margin
        github_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        github_label = QLabel(self)
        github_label.setText("<a href='https://github.com/pawaovo/interactive-feedback-mcp' style='color: #aaaaaa; text-decoration: none;'>项目 GitHub (Project GitHub)</a>")
        github_label.setOpenExternalLinks(False) # Handle via linkActivated
        github_label.setToolTip("访问项目GitHub仓库 (Visit project GitHub repository)")
        github_label.setCursor(Qt.CursorShape.PointingHandCursor)
        github_label.linkActivated.connect(self._open_github_repo_link)
        github_layout.addWidget(github_label)
        parent_layout.addWidget(github_container)

    def _connect_signals(self):
        """Connects signals from UI elements to their respective slots."""
        if hasattr(self, 'at_icon'): # Check if shortcuts panel was created
             self.at_icon.clicked.connect(self._toggle_number_icons_visibility_action)
        
        self.feedback_text.textChanged.connect(self._update_submit_button_text_status)
        
        if hasattr(self, 'bottom_canned_responses_button'):
            self.bottom_canned_responses_button.clicked.connect(self._show_canned_responses_dialog)
        
        if hasattr(self, 'pin_window_button'):
            self.pin_window_button.clicked.connect(self._toggle_pin_window_action)
        
        self.submit_button.clicked.connect(self._prepare_and_submit_feedback)

    # --- Event Handlers and Slots ---
    def event(self, event: QEvent) -> bool:
        """Handles window deactivation for auto-minimize feature."""
        if event.type() == QEvent.Type.WindowDeactivate:
            if not self.window_pinned and self.isVisible() and \
               not self.isMinimized() and not self.disable_auto_minimize:
                QTimer.singleShot(100, self.showMinimized) # Auto-minimize if not pinned
        return super().event(event)

    def closeEvent(self, event: QEvent): # QCloseEvent
        """Saves settings before closing the window."""
        self.settings_manager.set_main_window_geometry(self.saveGeometry())
        self.settings_manager.set_main_window_state(self.saveState())
        self.settings_manager.set_main_window_pinned(self.window_pinned)
        self.dropped_file_references.clear() # Clear temp data
        super().closeEvent(event)

    def eventFilter(self, watched_object: QObject, event: QEvent) -> bool:
        """Filters events for number shortcut icon clicks."""
        if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if isinstance(watched_object, QLabel) and hasattr(watched_object, 'property'):
                shortcut_idx = watched_object.property("shortcut_index")
                if shortcut_idx is not None: # Ensure property exists and is not None
                    self._handle_number_icon_click_action(shortcut_idx)
                    return True # Event handled
        return super().eventFilter(watched_object, event)

    # --- UI Update and Action Methods (UI更新和操作方法) ---
    def _load_canned_responses_from_settings(self):
        """Loads canned responses from settings manager."""
        self.canned_responses = self.settings_manager.get_canned_responses()

    def _update_number_icons_display(self):
        """Updates the visibility and tooltips of number shortcut icons."""
        if not hasattr(self, 'shortcut_number_icons') or not self.shortcut_number_icons:
            return
            
        for i, icon_label in enumerate(self.shortcut_number_icons):
            if i < len(self.canned_responses):
                response_text = self.canned_responses[i]
                tooltip = response_text if len(response_text) <= 60 else response_text[:57] + "..."
                icon_label.setToolTip(tooltip)
                # Styles are now primarily handled by global QSS using objectName
                # icon_label.setStyleSheet(...) # Remove direct style manipulation
                icon_label.setVisible(True)
            else:
                icon_label.setVisible(False)
                icon_label.setToolTip("") # Clear tooltip

    def _update_shortcut_icons_visibility_state(self, visible: Optional[bool] = None):
        """Updates visibility of the entire shortcut icons panel and its components."""
        if visible is None: # If no explicit state, use saved setting
            self.show_shortcut_icons = self.settings_manager.get_show_shortcut_icons()
        else:
            self.show_shortcut_icons = visible
        
        if hasattr(self, 'shortcuts_container'):
            self.shortcuts_container.setVisible(self.show_shortcut_icons)
            if self.show_shortcut_icons and hasattr(self, 'number_icons_container'):
                # Visibility of number icons sub-panel depends on its own setting
                self.number_icons_visible = self.settings_manager.get_number_icons_visible()
                self.number_icons_container.setVisible(self.number_icons_visible)
            elif hasattr(self, 'number_icons_container'): # Hide if main shortcut panel is hidden
                self.number_icons_container.setVisible(False)
        self._update_number_icons_display() # Refresh individual number icons

    def _toggle_number_icons_visibility_action(self):
        """Toggles the visibility of the number icons sub-panel."""
        if hasattr(self, 'number_icons_container'):
            new_visibility = not self.number_icons_container.isVisible()
            self.number_icons_container.setVisible(new_visibility)
            self.settings_manager.set_number_icons_visible(new_visibility)
            self.number_icons_visible = new_visibility # Update internal state
            if new_visibility: # Refresh display if becoming visible
                self._update_number_icons_display()

    def _handle_number_icon_click_action(self, index: int):
        """Inserts canned response text when a number icon is clicked."""
        if 0 <= index < len(self.canned_responses):
            text_to_insert = self.canned_responses[index]
            if text_to_insert and isinstance(text_to_insert, str):
                self.feedback_text.insertPlainText(text_to_insert)
                self.feedback_text.setFocus() # Focus back to text edit

    def _update_submit_button_text_status(self):
        """Updates the submit button's text and enabled state based on content."""
        has_text = bool(self.feedback_text.toPlainText().strip())
        has_images = bool(self.image_widgets)
        
        button_text = "提交 (Submit)" # Default
        tooltip_text = ""

        if has_text and has_images:
            button_text = f"发送图文 ({len(self.image_widgets)} 图) (Send Text & {len(self.image_widgets)} Img)"
            tooltip_text = "点击后将自动关闭窗口并激活Cursor对话框 (Will close window and activate Cursor)"
        elif has_images:
            button_text = f"发送 {len(self.image_widgets)} 张图片 (Send {len(self.image_widgets)} Images)"
            tooltip_text = "点击后将自动关闭窗口并激活Cursor对话框"
        elif has_text:
            button_text = "提交反馈 (Submit Feedback)"
        
        self.submit_button.setText(button_text)
        self.submit_button.setToolTip(tooltip_text)
        self.submit_button.setEnabled(has_text or has_images) # Enable if any content
        
        # Re-apply style if objectName changes for state (not used here, but good practice if it did)
        # self.submit_button.style().unpolish(self.submit_button)
        # self.submit_button.style().polish(self.submit_button)

    def _show_canned_responses_dialog(self):
        """Shows the dialog to select/manage canned responses."""
        self.disable_auto_minimize = True # Prevent auto-minimize while dialog is open
        try:
            # Pass current responses to dialog for editing
            dialog = SelectCannedResponseDialog(self.canned_responses[:], self) # Pass a copy
            dialog.exec() # exec_() for PySide2, exec() for PySide6

            # After dialog closes, reload and update UI as settings might have changed
            self._load_canned_responses_from_settings()
            # Update visibility based on what might have changed in dialog's settings save
            self._update_shortcut_icons_visibility_state(
                self.settings_manager.get_show_shortcut_icons()
            )
            # Individual number icons (tooltips, visibility)
            self._update_number_icons_display()

        finally:
            self.disable_auto_minimize = False # Re-enable auto-minimize

    def _apply_pin_state_on_load(self):
        """Applies the pinned window state when the UI loads."""
        if self.window_pinned:
            # Call _toggle_pin_window_action to set flags and button style correctly,
            # but ensure it doesn't flip the self.window_pinned state again if called naively.
            # So, set the state first, then update UI.
            self._update_pin_button_and_flags()
        
    def _update_pin_button_and_flags(self):
        """Updates the pin button appearance and window flags based on self.window_pinned."""
        current_geometry = self.geometry() # Save current geometry
        if self.window_pinned:
            self.pin_window_button.setText("取消固定 (Unpin)")
            self.pin_window_button.setToolTip("点击取消固定窗口 (Click to unpin window)")
            self.pin_window_button.setObjectName("pin_window_active") # For QSS
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.pin_window_button.setText("固定窗口 (Pin Window)")
            self.pin_window_button.setToolTip("固定窗口，防止自动最小化 (Pin window to prevent auto-minimize)")
            self.pin_window_button.setObjectName("secondary_button") # Revert to default style
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        
        # Re-apply stylesheet for objectName changes
        self.pin_window_button.style().unpolish(self.pin_window_button)
        self.pin_window_button.style().polish(self.pin_window_button)
        
        # Must re-show window for flags to take effect on some platforms
        self.setGeometry(current_geometry) # Restore geometry
        self.show()
        # QTimer.singleShot(10, lambda: self._restore_geometry_after_flags_change(current_geometry))

    def _toggle_pin_window_action(self):
        """Toggles the window pinned state."""
        self.window_pinned = not self.window_pinned
        self.settings_manager.set_main_window_pinned(self.window_pinned)
        self._update_pin_button_and_flags()

    def _open_github_repo_link(self, link_url: str): # Parameter name changed
        """Opens the project's GitHub repository link in a web browser."""
        if link_url == "#": # Assuming the href was just a placeholder
            webbrowser.open("https://github.com/pawaovo/interactive-feedback-mcp")
        else:
            webbrowser.open(link_url) # Open the actual link if provided

    def _set_initial_focus(self):
        """Sets initial focus to the feedback text edit."""
        if hasattr(self, 'feedback_text') and self.feedback_text:
            self.feedback_text.setFocus(Qt.FocusReason.OtherFocusReason)
            cursor = self.feedback_text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.feedback_text.setTextCursor(cursor)
            self.feedback_text.ensureCursorVisible()

    def _enforce_min_window_size(self):
        """Ensures the window meets minimum size requirements after showing."""
        resized = False
        if self.width() < 1000:
            self.resize(1000, self.height())
            resized = True
        if self.height() < 700:
            self.resize(self.width(), 700)
            resized = True
            
        if resized: # If resized, re-center
            screen = QApplication.primaryScreen().geometry()
            self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    # --- Image Handling Methods (图像处理方法) ---
    def handle_paste_image(self) -> bool:
        """Handles pasting an image from the clipboard."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        image_pasted = False
        
        if mime_data.hasImage():
            q_image = clipboard.image() # Returns QImage
            if not q_image.isNull():
                pixmap = QPixmap.fromImage(q_image)
                if self.add_image_preview(pixmap):
                    image_pasted = True
        # Text pasting is handled by FeedbackTextEdit's insertFromMimeData
        return image_pasted

    def add_image_preview(self, pixmap: QPixmap) -> Optional[int]:
        """Adds an image preview widget for the given pixmap."""
        if pixmap and not pixmap.isNull():
            image_id = self.next_image_id
            self.next_image_id += 1
            
            # Create the preview widget
            image_widget = ImagePreviewWidget(pixmap, image_id, self.feedback_text.images_container)
            image_widget.image_deleted.connect(self._remove_image_widget) # Connect signal
            
            # Add to layout in FeedbackTextEdit's images_container
            self.feedback_text.images_layout.addWidget(image_widget)
            self.image_widgets[image_id] = image_widget # Track the widget
            
            self.feedback_text.show_images_container(True) # Ensure container is visible
            if hasattr(self, 'image_usage_label'): self.image_usage_label.setVisible(True)
            self._update_submit_button_text_status()
            QTimer.singleShot(50, self._set_initial_focus) # Refocus text edit
            return image_id
        return None
    
    def _remove_image_widget(self, image_id: int):
        """Removes an image preview widget by its ID."""
        if image_id in self.image_widgets:
            widget_to_remove = self.image_widgets.pop(image_id)
            self.feedback_text.images_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater() # Schedule for deletion
            
            if not self.image_widgets: # If no images left
                self.feedback_text.show_images_container(False)
                if hasattr(self, 'image_usage_label'): self.image_usage_label.setVisible(False)
            
            self._update_submit_button_text_status()

    def _clear_all_image_previews(self): # If a "clear all images" button is added
        """Removes all current image previews."""
        for image_id in list(self.image_widgets.keys()): # Iterate over a copy
            self._remove_image_widget(image_id)

    # --- Feedback Submission (反馈提交) ---
    def _prepare_and_submit_feedback(self):
        """Collects all feedback data (text, options, images, file refs) and sets the result."""
        final_content_list: List[ContentItem] = []

        # 1. Collect text from FeedbackTextEdit
        feedback_plain_text = self.feedback_text.toPlainText().strip()
        
        # 2. Collect selected predefined options
        selected_option_texts: List[str] = []
        if hasattr(self, 'option_checkboxes'): # Ensure checkboxes were created
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    # Get original option text, remove potential numbering like "1. "
                    opt_text = self.predefined_options[i].strip()
                    opt_text = re.sub(r'^\d+\.\s*', '', opt_text) # Remove "N. " prefix
                    selected_option_texts.append(opt_text)
        
        # 3. Combine options and main feedback text
        combined_text_parts = []
        if selected_option_texts:
            combined_text_parts.append("; ".join(selected_option_texts))
        if feedback_plain_text: # Add main text if present
            combined_text_parts.append(feedback_plain_text)
        
        final_text_for_submission = "\n".join(combined_text_parts).strip()
        
        if final_text_for_submission:
            final_content_list.append({
                "type": "text", "text": final_text_for_submission,
                "data": None, "mimeType": None, "display_name": None, "path": None # Fill optional fields
            })

        # 4. Collect file references (that are still present in the text)
        current_text_content_for_refs = self.feedback_text.toPlainText() # Get final text
        for display_name, file_path in self.dropped_file_references.items():
            if display_name in current_text_content_for_refs: # Check if reference still exists
                final_content_list.append({
                    "type": "file_reference", "text": None,
                    "data": None, "mimeType": None,
                    "display_name": display_name, "path": file_path
                })
        
        # 5. Collect image data
        image_content_items = get_image_items_from_widgets(self.image_widgets)
        final_content_list.extend(image_content_items)
        
        # Set the result and close
        self.output_result = FeedbackResult(content=final_content_list if final_content_list else [])
        self.close() # This will trigger closeEvent to save settings

    # --- Public method to run the UI (公共方法运行UI) ---
    def run_ui_and_get_result(self) -> FeedbackResult:
        """
        Shows the UI, waits for user interaction, and returns the feedback result.
        显示UI，等待用户交互，并返回反馈结果。
        """
        self.show()
        # Enforce size and focus after a short delay to ensure window is fully initialized
        QTimer.singleShot(100, self._enforce_min_window_size)
        QTimer.singleShot(200, self._set_initial_focus)
        
        # Start the application event loop if this is the main window being run directly
        # If part of a larger app, this might be handled differently.
        # Here, assuming it's run somewhat modally.
        if QApplication.instance(): # Check if an app instance already exists
            QApplication.instance().exec() # exec_() for PySide2
        else:
            # This case should ideally not happen if main.py sets up QApplication
            print("警告: QApplication 实例未找到。UI 可能无法正常运行。", file=sys.stderr)
            # (Warning: QApplication instance not found. UI may not run correctly.)


        # Return the collected result, or an empty result if window was closed prematurely
        return self.output_result if self.output_result else FeedbackResult(content=[])


# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import argparse
import platform
import subprocess
from typing import Optional, TypedDict, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSettings, QThread
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor

class FeedbackResult(TypedDict):
    interactive_feedback: str

def is_system_dark_mode():
    """Detect if system is in dark mode"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "Dark"
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    elif system == "Windows":
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            reg_keypath = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            reg_key = winreg.OpenKey(registry, reg_keypath)
            reg_value = winreg.QueryValueEx(reg_key, 'AppsUseLightTheme')[0]
            return reg_value == 0
        except (ImportError, OSError, FileNotFoundError):
            return False
    elif system == "Linux":
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True,
                text=True,
                timeout=5
            )
            theme = result.stdout.strip().strip("'\"").lower()
            return "dark" in theme
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    return False

def get_dark_mode_palette(app: QApplication):
    """Get dark mode palette following Apple design principles and WCAG standards"""
    darkPalette = app.palette()
    
    darkPalette.setColor(QPalette.Window, QColor(28, 28, 30))
    darkPalette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(174, 174, 178))
    
    darkPalette.setColor(QPalette.Base, QColor(44, 44, 46))
    darkPalette.setColor(QPalette.AlternateBase, QColor(58, 58, 60))
    
    darkPalette.setColor(QPalette.ToolTipBase, QColor(72, 72, 74))
    darkPalette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    
    darkPalette.setColor(QPalette.Text, QColor(255, 255, 255))
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(174, 174, 178))
    
    darkPalette.setColor(QPalette.Dark, QColor(72, 72, 74))
    darkPalette.setColor(QPalette.Shadow, QColor(0, 0, 0))
    
    darkPalette.setColor(QPalette.Button, QColor(58, 58, 60))
    darkPalette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(174, 174, 178))
    
    darkPalette.setColor(QPalette.BrightText, QColor(255, 69, 58))
    darkPalette.setColor(QPalette.Link, QColor(10, 132, 255))
    darkPalette.setColor(QPalette.Highlight, QColor(10, 132, 255))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(99, 99, 102))
    darkPalette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(174, 174, 178))
    
    darkPalette.setColor(QPalette.PlaceholderText, QColor(174, 174, 178))
    
    return darkPalette

def get_light_mode_palette(app: QApplication):
    """Get light mode palette following Apple design principles and WCAG standards"""
    lightPalette = app.palette()
    
    lightPalette.setColor(QPalette.Window, QColor(255, 255, 255))
    lightPalette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    lightPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(142, 142, 147))
    
    lightPalette.setColor(QPalette.Base, QColor(255, 255, 255))
    lightPalette.setColor(QPalette.AlternateBase, QColor(242, 242, 247))
    
    lightPalette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    lightPalette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    
    lightPalette.setColor(QPalette.Text, QColor(0, 0, 0))
    lightPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(142, 142, 147))
    
    lightPalette.setColor(QPalette.Dark, QColor(209, 209, 214))
    lightPalette.setColor(QPalette.Shadow, QColor(0, 0, 0, 30))
    
    lightPalette.setColor(QPalette.Button, QColor(242, 242, 247))
    lightPalette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    lightPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(142, 142, 147))
    
    lightPalette.setColor(QPalette.BrightText, QColor(255, 59, 48))
    lightPalette.setColor(QPalette.Link, QColor(0, 122, 255))
    lightPalette.setColor(QPalette.Highlight, QColor(0, 122, 255))
    lightPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(209, 209, 214))
    lightPalette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    lightPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(142, 142, 147))
    
    lightPalette.setColor(QPalette.PlaceholderText, QColor(142, 142, 147))
    
    return lightPalette

class ThemeWatcher(QObject):
    """System theme change watcher"""
    theme_changed = Signal(bool)  # True for dark mode, False for light mode
    
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_theme)
        self.current_dark_mode = is_system_dark_mode()
        
    def start_watching(self, interval_ms=1000):
        """Start theme monitoring, checks every second by default"""
        self.timer.start(interval_ms)
        
    def stop_watching(self):
        """Stop theme monitoring"""
        self.timer.stop()
        
    def check_theme(self):
        """Check if current theme has changed"""
        current_mode = is_system_dark_mode()
        if current_mode != self.current_dark_mode:
            self.current_dark_mode = current_mode
            self.theme_changed.emit(current_mode)

class FeedbackTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() == Qt.ShiftModifier:
                # Shift+Enter: insert line break
                super().keyPressEvent(event)
            elif event.modifiers() == Qt.ControlModifier:
                # Ctrl+Enter: submit (for compatibility)
                self._submit_feedback()
            elif event.modifiers() == Qt.NoModifier:
                # Enter alone: submit directly
                self._submit_feedback()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def _submit_feedback(self):
        """Helper method to submit feedback"""
        # Find the parent FeedbackUI instance and call submit
        parent = self.parent()
        while parent and not isinstance(parent, FeedbackUI):
            parent = parent.parent()
        if parent:
            parent._submit_feedback()

class FeedbackUI(QMainWindow):
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None):
        super().__init__()
        self.prompt = prompt
        self.predefined_options = predefined_options or []

        self.feedback_result = None
        
        # Create theme watcher
        self.theme_watcher = ThemeWatcher()
        self.theme_watcher.theme_changed.connect(self.on_theme_changed)
        
        self.setWindowTitle("Interactive Feedback MCP")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "images", "feedback.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # Load general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(800, 480)  # Reduced height for more compact default size
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 800) // 2
            y = (screen.height() - 480) // 2
            self.move(x, y)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
        self.settings.endGroup() # End "MainWindow_General" group

        self._create_ui()
        
        # Start theme monitoring
        self.theme_watcher.start_watching()
    
    def on_theme_changed(self, is_dark_mode: bool):
        """Handle system theme changes"""
        app = QApplication.instance()
        if is_dark_mode:
            app.setPalette(get_dark_mode_palette(app))
        else:
            app.setPalette(get_light_mode_palette(app))
        
        # Update stylesheet for new theme
        self._update_stylesheet(is_dark_mode)
        
        # Force UI redraw
        self.update()

    def _get_dynamic_stylesheet(self, is_dark_mode: bool = None):
        """Get dynamic stylesheet with colors based on theme mode"""
        if is_dark_mode is None:
            is_dark_mode = is_system_dark_mode()
            
        # Select colors based on theme
        if is_dark_mode:
            # Dark mode colors
            hover_color = "rgba(10, 132, 255, 0.8)"
            pressed_color = "rgba(10, 132, 255, 0.6)"
            checkbox_hover_bg = "rgba(10, 132, 255, 0.05)"
            checkbox_hover_checked = "rgba(10, 132, 255, 0.9)"
            checkbox_border = "rgba(174, 174, 178, 0.6)"
            checkbox_disabled_border = "rgba(174, 174, 178, 0.3)"
            checkbox_disabled_bg = "rgba(174, 174, 178, 0.1)"
            separator_color = "rgba(255, 255, 255, 0.1)"
            scrollbar_handle = "rgba(255, 255, 255, 0.3)"
            scrollbar_handle_hover = "rgba(255, 255, 255, 0.5)"
        else:
            # Light mode colors
            hover_color = "rgba(0, 122, 255, 0.8)"
            pressed_color = "rgba(0, 122, 255, 0.6)"
            checkbox_hover_bg = "rgba(0, 122, 255, 0.05)"
            checkbox_hover_checked = "rgba(0, 122, 255, 0.9)"
            checkbox_border = "rgba(142, 142, 147, 0.6)"
            checkbox_disabled_border = "rgba(142, 142, 147, 0.3)"
            checkbox_disabled_bg = "rgba(142, 142, 147, 0.1)"
            separator_color = "rgba(0, 0, 0, 0.1)"
            scrollbar_handle = "rgba(0, 0, 0, 0.3)"
            scrollbar_handle_hover = "rgba(0, 0, 0, 0.5)"
        
        return f"""
            QMainWindow {{
                background-color: palette(window);
            }}
            
            QGroupBox {{
                border: none;
                background-color: transparent;
                margin: 0px;
                padding: 0px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 0px;
                padding: 0px;
                color: transparent;
                background-color: transparent;
            }}
            
            QLabel {{
                color: palette(text);
                font-size: 14px;
                font-weight: 400;
                line-height: 1.5;
                margin-bottom: 8px;
            }}
            
            QTextEdit {{
                border: 1px solid palette(dark);
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
                background-color: palette(base);
                color: palette(text);
                selection-background-color: palette(highlight);
                selection-color: palette(highlighted-text);
                min-height: 80px;
            }}
            
            QTextEdit:focus {{
                border: 2px solid palette(highlight);
                outline: none;
            }}
            
            QPushButton {{
                background-color: palette(highlight);
                color: palette(highlighted-text);
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 500;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
                min-height: 24px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            
            QPushButton:pressed {{
                background-color: {pressed_color};
                transform: scale(0.98);
            }}
            
            QPushButton:disabled {{
                background-color: palette(button);
                color: palette(disabled, button-text);
                opacity: 0.5;
            }}
            
            QPushButton:focus {{
                outline: 2px solid palette(highlight);
                outline-offset: 2px;
            }}
            
            QCheckBox {{
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif;
                color: palette(text);
                spacing: 12px;
                padding: 8px 0px;
                min-height: 32px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 1.5px solid {checkbox_border};
                border-radius: 4px;
                background-color: white;
            }}
            
            QCheckBox::indicator:hover {{
                border-color: palette(highlight);
                background-color: {checkbox_hover_bg};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: palette(highlight);
                border-color: palette(highlight);
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEw0LjMgNy43TDEuNCA0LjgiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
            }}
            
            QCheckBox::indicator:checked:hover {{
                background-color: {checkbox_hover_checked};
            }}
            
            QCheckBox::indicator:focus {{
                outline: 2px solid palette(highlight);
                outline-offset: 2px;
            }}
            
            QCheckBox:disabled {{
                color: palette(disabled, text);
            }}
            
            QCheckBox::indicator:disabled {{
                border-color: {checkbox_disabled_border};
                background-color: {checkbox_disabled_bg};
            }}
            
            QFrame[frameShape="4"] {{
                color: {separator_color};
                background-color: {separator_color};
                border: none;
                max-height: 1px;
                margin: 12px 0px;
            }}
        """
    
    def _update_stylesheet(self, is_dark_mode: bool = None):
        """Update stylesheet to adapt to theme changes"""
        stylesheet = self._get_dynamic_stylesheet(is_dark_mode)
        self.setStyleSheet(stylesheet)
        
        # Also update description label scrollbar style
        if hasattr(self, 'description_label'):
            if is_dark_mode is None:
                is_dark_mode = is_system_dark_mode()
                
            scrollbar_handle = "rgba(255, 255, 255, 0.3)" if is_dark_mode else "rgba(0, 0, 0, 0.3)"
            scrollbar_handle_hover = "rgba(255, 255, 255, 0.5)" if is_dark_mode else "rgba(0, 0, 0, 0.5)"
            
            description_style = f"""
                QTextEdit {{
                    border: none;
                    background-color: transparent;
                    color: palette(text);
                    font-size: 14px;
                    font-weight: 400;
                    padding: 0px;
                    margin: 0px;
                }}
                QScrollBar:vertical {{
                    background-color: transparent;
                    width: 8px;
                    border-radius: 4px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {scrollbar_handle};
                    border-radius: 4px;
                    min-height: 20px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background-color: {scrollbar_handle_hover};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    border: none;
                    background: none;
                }}
            """
            self.description_label.setStyleSheet(description_style)

    def _create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)  # Apple 8pt grid: 2 units
        layout.setContentsMargins(20, 20, 20, 20)  # Slightly reduced for better balance

        # Apply dynamic stylesheet
        self._update_stylesheet()

        # Feedback section - using 8pt grid system
        self.feedback_group = QGroupBox("")
        feedback_layout = QVBoxLayout(self.feedback_group)
        feedback_layout.setSpacing(16)  # Apple 8pt grid: 2 units
        feedback_layout.setContentsMargins(0, 0, 0, 0)

        # Description label (from self.prompt) - Support multiline with scroll
        # Top area: expandable description text box
        self.description_label = QTextEdit()
        self.description_label.setPlainText(self.prompt)
        self.description_label.setReadOnly(True)
        # Remove maximum height to allow expansion when window is resized
        self.description_label.setMinimumHeight(80)
        self.description_label.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.description_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.description_label.setFrameStyle(QFrame.NoFrame)
        
        # Set dynamic style for description text
        self._update_description_style()
        
        # Add with stretch factor to allow expansion
        feedback_layout.addWidget(self.description_label, 1)

        # Middle area: predefined options (dynamic height based on option count)
        self.option_checkboxes = []
        if self.predefined_options and len(self.predefined_options) > 0:
            options_frame = QFrame()
            # Calculate height dynamically based on option count
            option_count = len(self.predefined_options)
            calculated_height = option_count * 40 + 24  # 40px per option + 24px padding (reduced)
            options_frame.setMinimumHeight(calculated_height)
            options_frame.setMaximumHeight(calculated_height)  # Fixed height to prevent expansion
            
            options_layout = QVBoxLayout(options_frame)
            options_layout.setContentsMargins(0, 12, 0, 12)  # Reduced for better balance
            options_layout.setSpacing(8)  # Apple 8pt grid: 1 unit
            
            for option in self.predefined_options:
                checkbox = QCheckBox(option)
                checkbox.setFixedHeight(32)  # Apple 8pt grid: 4 units
                self.option_checkboxes.append(checkbox)
                options_layout.addWidget(checkbox)
            
            # Add stretch to align options to top
            options_layout.addStretch()
            
            # Add with no stretch factor to maintain fixed size
            feedback_layout.addWidget(options_frame, 0)
            
            # Add a separator
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            feedback_layout.addWidget(separator)

        # Bottom area: fixed size text input and submit button
        input_frame = QFrame()
        input_frame.setMinimumHeight(180)
        input_frame.setMaximumHeight(180)  # Fixed height to prevent expansion
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(12)  # Reduced for better balance
        
        # Free-form text feedback
        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.setMinimumHeight(120)
        self.feedback_text.setMaximumHeight(120)  # Fixed height

        self.feedback_text.setPlaceholderText("Enter your feedback here (Press Enter to submit, Shift+Enter for new line)")
        submit_button = QPushButton("Send Feedback")
        submit_button.clicked.connect(self._submit_feedback)
        submit_button.setDefault(True)

        input_layout.addWidget(self.feedback_text)
        input_layout.addWidget(submit_button)
        
        # Add with no stretch factor to maintain fixed size
        feedback_layout.addWidget(input_frame, 0)

        # Add widgets
        layout.addWidget(self.feedback_group)

    def _submit_feedback(self):
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []
        
        # Get selected predefined options if any
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    selected_options.append(self.predefined_options[i])
        
        # Combine selected options and feedback text
        final_feedback_parts = []
        
        # Add selected options
        if selected_options:
            final_feedback_parts.append("; ".join(selected_options))
        
        # Add user's text feedback
        if feedback_text:
            final_feedback_parts.append(feedback_text)
            
        # Join with a newline if both parts exist
        final_feedback = "\n\n".join(final_feedback_parts)
            
        self.feedback_result = FeedbackResult(
            interactive_feedback=final_feedback,
        )
        self.close()

    def closeEvent(self, event):
        # Stop theme monitoring
        self.theme_watcher.stop_watching()
        
        # Save general UI settings for the main window (geometry, state)
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()

        super().closeEvent(event)

    def run(self) -> FeedbackResult:
        self.show()
        QApplication.instance().exec()

        if not self.feedback_result:
            return FeedbackResult(interactive_feedback="")

        return self.feedback_result

    def _update_description_style(self):
        """Update description label style"""
        is_dark_mode = is_system_dark_mode()
        scrollbar_handle = "rgba(255, 255, 255, 0.3)" if is_dark_mode else "rgba(0, 0, 0, 0.3)"
        scrollbar_handle_hover = "rgba(255, 255, 255, 0.5)" if is_dark_mode else "rgba(0, 0, 0, 0.5)"
        
        description_style = f"""
            QTextEdit {{
                border: none;
                background-color: transparent;
                color: palette(text);
                font-size: 14px;
                font-weight: 400;
                padding: 0px;
                margin: 0px;
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {scrollbar_handle};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {scrollbar_handle_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """
        if hasattr(self, 'description_label'):
            self.description_label.setStyleSheet(description_style)

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    app = QApplication.instance() or QApplication()
    
    # Automatically select palette based on system theme
    if is_system_dark_mode():
        app.setPalette(get_dark_mode_palette(app))
    else:
        app.setPalette(get_light_mode_palette(app))
    
    app.setStyle("Fusion")
    ui = FeedbackUI(prompt, predefined_options)
    result = ui.run()

    if output_file and result:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        # Save the result to the output file
        with open(output_file, "w") as f:
            json.dump(result, f)
        return None

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the feedback UI")
    parser.add_argument("--prompt", default="I implemented the changes you requested.", help="The prompt to show to the user")
    parser.add_argument("--predefined-options", default="", help="Pipe-separated list of predefined options (|||)")
    parser.add_argument("--output-file", help="Path to save the feedback result as JSON")
    args = parser.parse_args()

    predefined_options = [opt for opt in args.predefined_options.split("|||") if opt] if args.predefined_options else None
    
    result = feedback_ui(args.prompt, predefined_options, args.output_file)
    if result:
        print(f"\nFeedback received:\n{result['interactive_feedback']}")
    sys.exit(0)

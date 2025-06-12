"""
主题颜色常量定义
统一管理所有UI组件的颜色，避免重复定义
"""


class ThemeColors:
    """主题颜色管理类"""

    # 深色主题颜色
    DARK_THEME = {
        # 基础颜色
        "background": "#2c2c2c",
        "text": "#f0f0f0",
        "border": "#555555",
        # 按钮颜色
        "button_bg": "#3C3C3C",
        "button_text": "#FFFFFF",
        "button_hover": "#555555",
        "button_pressed": "#333333",
        # 选择控件颜色（复选框、单选按钮等）
        "checkbox_bg": "transparent",
        "checkbox_border": "#444444",
        "checkbox_checked_bg": "#4D4D4D",
        "checkbox_checked_border": "#555555",
        "checkbox_hover_bg": "#333333",
        "checkbox_hover_border": "#666666",
        # 预览窗口颜色
        "preview_bg": "#2d2d2d",
        "preview_border": "#555555",
        "preview_text": "#ffffff",
        "preview_item_bg": "#3c3c3c",
        "preview_item_border": "#444444",
        "preview_item_hover_bg": "#555555",
        "preview_item_hover_border": "#666666",
        # 高亮和强调色
        "highlight": "#4D4D4D",
        "highlight_text": "#FFFFFF",
        "accent": "#4D4D4D",
        # 输入框颜色
        "input_bg": "#272727",
        "input_text": "#ffffff",
        "input_border": "#444444",
        "input_hover_border": "#555555",
        "input_focus_border": "#666666",
        # 分割器颜色
        "splitter_base": "#444444",
        "splitter_hover": "#555555",
        "splitter_pressed": "#333333",
        # 优化按钮颜色
        "optimization_button_bg": "#404040",
        "optimization_button_text": "#ffffff",
        "optimization_button_border": "#555555",
        "optimization_button_hover_bg": "#505050",
        "optimization_button_hover_border": "#666666",
        "optimization_button_pressed_bg": "#303030",
        "optimization_button_pressed_border": "#444444",
    }

    # 浅色主题颜色
    LIGHT_THEME = {
        # 基础颜色
        "background": "#f0f0f0",
        "text": "#111111",
        "border": "#CCCCCC",
        # 按钮颜色
        "button_bg": "#e1e1e1",
        "button_text": "#111111",
        "button_hover": "#dddddd",
        "button_pressed": "#bbbbbb",
        # 选择控件颜色（复选框、单选按钮等）
        "checkbox_bg": "#fdfdfd",
        "checkbox_border": "#adadad",
        "checkbox_checked_bg": "#6B6B6B",
        "checkbox_checked_border": "#777777",
        "checkbox_hover_bg": "#fafafa",
        "checkbox_hover_border": "#777777",
        # 预览窗口颜色
        "preview_bg": "#FFFFFF",
        "preview_border": "#CCCCCC",
        "preview_text": "#333333",
        "preview_item_bg": "#F8F9FA",
        "preview_item_border": "#E0E0E0",
        "preview_item_hover_bg": "#E0E0E0",
        "preview_item_hover_border": "#BBBBBB",
        # 高亮和强调色
        "highlight": "#6B6B6B",
        "highlight_text": "#FFFFFF",
        "accent": "#6B6B6B",
        # 输入框颜色
        "input_bg": "#ffffff",
        "input_text": "#111111",
        "input_border": "#dcdcdc",
        "input_hover_border": "#bbb",
        "input_focus_border": "#999",
        # 分割器颜色
        "splitter_base": "#cccccc",
        "splitter_hover": "#dddddd",
        "splitter_pressed": "#bbbbbb",
        # 优化按钮颜色
        "optimization_button_bg": "#f8f8f8",
        "optimization_button_text": "#333333",
        "optimization_button_border": "#cccccc",
        "optimization_button_hover_bg": "#eeeeee",
        "optimization_button_hover_border": "#bbbbbb",
        "optimization_button_pressed_bg": "#e0e0e0",
        "optimization_button_pressed_border": "#aaaaaa",
    }

    @classmethod
    def get_theme_colors(cls, theme_name: str) -> dict:
        """获取指定主题的颜色配置"""
        if theme_name == "dark":
            return cls.DARK_THEME
        else:
            return cls.LIGHT_THEME

    @classmethod
    def get_preview_colors(cls, theme_name: str) -> dict:
        """获取预览窗口相关的颜色配置"""
        colors = cls.get_theme_colors(theme_name)
        return {
            "bg_color": colors["preview_bg"],
            "border_color": colors["preview_border"],
            "text_color": colors["preview_text"],
            "item_bg": colors["preview_item_bg"],
            "item_border": colors["preview_item_border"],
            "item_hover_bg": colors["preview_item_hover_bg"],
            "item_hover_border": colors["preview_item_hover_border"],
        }

    @classmethod
    def get_checkbox_colors(cls, theme_name: str) -> dict:
        """获取复选框相关的颜色配置"""
        colors = cls.get_theme_colors(theme_name)
        return {
            "text_color": colors["text"],
            "bg_color": colors["checkbox_bg"],
            "border_color": colors["checkbox_border"],
            "checked_bg": colors["checkbox_checked_bg"],
            "checked_border": colors["checkbox_checked_border"],
            "hover_bg": colors["checkbox_hover_bg"],
            "hover_border": colors["checkbox_hover_border"],
        }

    @classmethod
    def get_splitter_colors(cls, theme_name: str) -> dict:
        """获取分割器相关的颜色配置"""
        colors = cls.get_theme_colors(theme_name)
        return {
            "base_color": colors["splitter_base"],
            "hover_color": colors["splitter_hover"],
            "pressed_color": colors["splitter_pressed"],
        }

    @classmethod
    def get_optimization_button_colors(cls, theme_name: str) -> dict:
        """获取优化按钮相关的颜色配置"""
        colors = cls.get_theme_colors(theme_name)
        return {
            "bg_color": colors["optimization_button_bg"],
            "text_color": colors["optimization_button_text"],
            "border_color": colors["optimization_button_border"],
            "hover_bg": colors["optimization_button_hover_bg"],
            "hover_border": colors["optimization_button_hover_border"],
            "pressed_bg": colors["optimization_button_pressed_bg"],
            "pressed_border": colors["optimization_button_pressed_border"],
        }

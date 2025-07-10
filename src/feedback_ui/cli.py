# cli.py (Application Entry Point / 应用程序入口点)
import sys
import os
import json
import argparse
from typing import Optional, List

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale

# --- 从 feedback_ui 包导入 (Imports from the feedback_ui package) ---
# Note: Changed to relative imports as this is now part of the package
from .main_window import FeedbackUI
from .utils.style_manager import apply_theme
from .utils.settings_manager import SettingsManager
from .utils.constants import FeedbackResult

# Import the compiled resources
# This should work as long as it's in the same package directory
from . import resources_rc

# (可选) 设置高DPI缩放，如果需要 (Optional: Set High DPI scaling if needed)
# QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
# QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)


def start_feedback_tool(
    prompt: str,
    predefined_options: Optional[List[str]] = None,
    output_file_path: Optional[str] = None,
) -> Optional[FeedbackResult]:
    """
    Initializes and runs the Feedback UI application.
    初始化并运行反馈UI应用程序。

    Args:
        prompt (str): The main question or prompt for the user.
                      (用户的主要问题或提示。)
        predefined_options (Optional[List[str]]): A list of predefined choices for the user.
                                                   (为用户预定义选项的列表。)
        output_file_path (Optional[str]): Path to save the feedback result as JSON. If None, result is returned.
                                          (将反馈结果保存为JSON的路径。如果为None，则返回结果。)

    Returns:
        Optional[FeedbackResult]: The feedback collected from the user, or None if UI was quit unexpectedly.
                                   (从用户收集的反馈，如果UI意外退出则为None。)
    """
    app = QApplication.instance()  # Check if an instance already exists
    if not app:  # Create one if not
        app = QApplication(sys.argv)

    # 应用全局样式和调色板 (Apply global styles and palette)
    settings = SettingsManager()
    initial_theme = settings.get_current_theme()
    apply_theme(app, initial_theme)
    app.setQuitOnLastWindowClosed(True)  # Ensure app exits when main window closes

    # 创建并设置全局翻译器
    translator = setup_translator(settings.get_current_language())
    if translator:
        app.installTranslator(translator)

    if predefined_options is None:
        predefined_options = []

    ui_window = FeedbackUI(prompt, predefined_options)
    collected_result = (
        ui_window.run_ui_and_get_result()
    )  # This will block until UI closes

    if output_file_path and collected_result:
        # 确保输出目录存在 (Ensure output directory exists)
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                print(f"错误: 无法创建输出目录 '{output_dir}': {e}", file=sys.stderr)
                print(
                    f"(Error: Could not create output directory '{output_dir}': {e})",
                    file=sys.stderr,
                )
                # Decide if to proceed without saving or raise error

        try:
            with open(output_file_path, "w", encoding="utf-8") as f:
                # ensure_ascii=False for proper non-ASCII char handling (like Chinese)
                # indent=2 for pretty printing
                json.dump(collected_result, f, ensure_ascii=False, indent=2)
            print(f"反馈结果已保存到: {output_file_path}")
            print(f"(Feedback result saved to: {output_file_path})")
            # If saving to file, the server script usually doesn't need the direct result back
            # return None
        except IOError as e:
            print(f"错误: 无法写入输出文件 '{output_file_path}': {e}", file=sys.stderr)
            print(
                f"(Error: Could not write to output file '{output_file_path}': {e})",
                file=sys.stderr,
            )
            # Fall through to return result if saving failed, so it's not lost

    return collected_result


def setup_translator(lang_code: str) -> Optional[QTranslator]:
    """
    设置应用程序的翻译器
    Setup the application translator based on language code
    """
    if not lang_code or lang_code == "zh_CN":  # 默认中文不需要翻译
        print("应用程序使用默认中文语言")
        return None

    translator = QTranslator()

    # 尝试从Qt资源系统加载翻译文件
    # Try to load translation file from Qt resource system
    if translator.load(f":/translations/{lang_code}.qm"):
        print(f"应用程序成功加载 {lang_code} 语言翻译")
        return translator
    else:
        print(f"警告：无法从资源系统加载 {lang_code} 翻译文件。将使用默认语言。")
        print(
            f"Warning: Could not load {lang_code} translation from resource system. Using default language."
        )
        return None


def main():
    """Main function to run the command-line interface."""
    parser = argparse.ArgumentParser(
        description="运行交互式反馈UI (Run Interactive Feedback UI)"
    )
    parser.add_argument(
        "--prompt",
        default="我已根据您的要求实施了更改。(I have implemented the changes you requested.)",
        help="向用户显示的提示信息 (The prompt to show to the user)",
    )
    parser.add_argument(
        "--predefined-options",
        default="",
        help="用 '|||' 分隔的预定义选项列表 (Pipe-separated list of predefined options, e.g., \"Opt1|||Opt2\")",
    )
    parser.add_argument(
        "--output-file",
        help="将反馈结果保存为JSON的文件路径 (Path to save the feedback result as JSON)",
    )
    # --debug flag from original script seems unused internally for UI, but kept for interface consistency
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式 (Enable debug mode - currently no specific UI effect)",
    )
    # --full-ui flag for demo purposes
    parser.add_argument(
        "--full-ui",
        action="store_true",
        default=False,
        help="显示包含所有功能的完整UI界面 (演示目的) (Show full UI with all features for demo)",
    )
    args = parser.parse_args()

    # Process predefined options with V3.2 three-layer fallback logic
    options_list: List[str] = []
    if args.predefined_options:
        options_list = [
            opt.strip() for opt in args.predefined_options.split("|||") if opt.strip()
        ]
    elif args.full_ui:  # Demo options if --full-ui is used and no options provided
        options_list = [
            "这是一个很棒的功能！ (This is a great feature!)",
            "我发现了一个小问题... (I found a small issue...)",
            "可以考虑增加... (Could you consider adding...)",
        ]

    # V3.2 严格边界控制：应用三层回退逻辑
    try:
        # 导入V3.2配置和规则引擎
        import sys
        import os

        # 兼容包安装模式和开发模式的导入
        try:
            # 首先尝试直接导入（适用于包安装模式）
            from interactive_feedback_server.utils.rule_engine import (
                resolve_final_options,
            )
            from interactive_feedback_server.utils.config_manager import get_config
        except ImportError:
            # 如果直接导入失败，尝试开发模式的路径解析
            current_file = os.path.abspath(__file__)
            feedback_ui_dir = os.path.dirname(current_file)  # src/feedback_ui
            src_dir = os.path.dirname(feedback_ui_dir)  # src
            project_root = os.path.dirname(src_dir)  # 项目根目录

            # 添加到路径
            if project_root not in sys.path:
                sys.path.insert(0, project_root)

            from src.interactive_feedback_server.utils.rule_engine import (
                resolve_final_options,
            )
            from src.interactive_feedback_server.utils.config_manager import get_config

        # 获取配置
        config = get_config()

        # 严格的三层回退逻辑：
        # 1. 如果有预定义选项，作为AI选项传入（第一层）
        # 2. 如果没有预定义选项，传入None让规则引擎处理（第二层）
        # 3. 规则引擎无法处理时自动使用后备选项（第三层）
        ai_options_for_engine = options_list if options_list else None

        final_options = resolve_final_options(
            ai_options=ai_options_for_engine,  # 严格按照边界规则传入
            text=args.prompt,  # 使用提示文本
            config=config,
        )

        # 更新选项列表
        if final_options:
            options_list = final_options

    except Exception as e:
        print(f"V3.2 Error - 三层回退逻辑失败: {e}", file=sys.stderr)
        # 极端情况下的保底选项
        if not options_list:
            options_list = ["继续", "取消", "需要帮助"]

    final_result = start_feedback_tool(args.prompt, options_list, args.output_file)

    # If not saving to a file, print the result to stdout for the calling process (e.g., server.py)
    if final_result and not args.output_file:
        # Standard way to output JSON for inter-process communication is compact
        # Pretty print for direct human reading if needed, but server might expect compact
        # json.dump(final_result, sys.stdout, ensure_ascii=False) # Compact JSON to stdout

        # For demonstration or direct script run, pretty print:
        pretty_result = json.dumps(final_result, indent=2, ensure_ascii=False)
        print("\n--- 反馈UI结果 (Feedback UI Result) ---")
        print(pretty_result)
        print("--- 结束结果 (End Result) ---\n")

    sys.exit(0)  # Successful exit


if __name__ == "__main__":
    main()

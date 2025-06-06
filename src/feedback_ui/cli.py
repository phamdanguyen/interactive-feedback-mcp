# cli.py (Application Entry Point / 应用程序入口点)
import sys
import os
import json
import argparse
from typing import Optional, List, Dict, Any

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

# 确保我们能从 src/ 目录导入模块
# 这对于直接从命令行运行此脚本至关重要
try:
    import src
except ImportError:
    # 如果失败，则手动将项目根目录添加到 sys.path
    # This is crucial for running the script directly from the command line
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

# 再次尝试导入，现在应该可以了
# Now the imports should work
from src.feedback_ui.main_window import FeedbackUI
from src.feedback_ui.utils.constants import FeedbackResult


def start_feedback_tool(
    prompt: str,
    predefined_options: Optional[List[str]] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    使用新的事件驱动模型启动反馈UI。
    Launches the feedback UI using the new event-driven model.
    """
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        is_new_app = True
    else:
        is_new_app = False

    result_data = {}

    # 创建一个虚拟的 task_id，因为这个UI是独立运行的
    # Create a dummy task_id as this UI is running standalone
    task_id = "standalone_task"

    ui_window = FeedbackUI(
        task_id=task_id, prompt=prompt, predefined_options=predefined_options
    )

    def on_feedback(received_task_id, data):
        nonlocal result_data
        if received_task_id == task_id:
            result_data = data
            app.quit()  # 收到反馈后退出应用

    def on_close(received_task_id):
        # 如果窗口被用户关闭而没有提交反馈
        if not result_data:
            app.quit()

    # 连接信号
    ui_window.feedback_provided.connect(on_feedback)
    ui_window.closed.connect(on_close)

    ui_window.show()
    ui_window.activateWindow()
    ui_window.raise_()

    if is_new_app:
        app.exec()

    # 将结果写入文件或打印到stdout
    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"错误: 无法写入输出文件 '{output_file}': {e}", file=sys.stderr)
            # 即使写入失败，也尝试将结果打印到stdout
            print("\n--- UI 结果 ---")
            print(json.dumps(result_data, ensure_ascii=False, indent=4))
    else:
        # 如果没有指定输出文件，则打印到标准输出
        print(json.dumps(result_data, ensure_ascii=False, indent=4))

    return result_data


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

    # Process predefined options
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

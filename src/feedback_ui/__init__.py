# feedback_ui/__init__.py
# This file makes the 'feedback_ui' directory a Python package.
# 这个文件使得 'feedback_ui' 目录成为一个 Python 包。

# You can make key classes or functions available directly when importing the package:
# 如果希望在导入 feedback_ui 包时可以直接访问某些核心类或函数，可以在这里导入它们：
# For example:
# from .main_window import FeedbackUI
# from .utils.constants import FeedbackResult, ContentItem

# This allows imports like:
# from feedback_ui import FeedbackUI
#
# Instead of:
# from feedback_ui.main_window import FeedbackUI

# For now, let's keep it minimal. Users of the package will import from submodules.
# 目前，我们保持最小化。包的使用者将从子模块导入。
__version__ = "2.5.5"  # (可选) 包版本 (Optional: package version)

# print(f"反馈UI包已加载 (Feedback UI package loaded) - version {__version__}")

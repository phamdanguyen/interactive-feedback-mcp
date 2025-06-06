# UI 优化任务清单

本文档详细描述了针对交互式反馈UI的后续优化任务，旨在提升用户体验、操作便捷性和交互流畅性。

---

## 任务一：空反馈提交与窗口关闭逻辑优化

**目标**: 允许用户通过提交空内容或直接关闭窗口来中止会话，程序应返回明确的"空结果"，以防止调用后续的MCP服务。

**执行步骤**:

1.  **修改 `FeedbackUI._submit_feedback()` 方法** (`feedback_ui.py`):
    *   调整判断逻辑，允许在输入框无文本、无图片、无文件引用的情况下执行提交操作。
    *   当提交内容为空时，构建一个空的 `FeedbackResult`（例如 `{'content': []}`），将其赋值给 `self.result`，然后调用 `self.close()` 关闭窗口。

2.  **修改 `FeedbackUI.closeEvent()` 方法** (`feedback_ui.py`):
    *   在此方法中，检查 `self.result` 是否已被设置。如果是由用户直接点击关闭按钮触发（即 `self.result` 仍为初始状态），则显式地将其设置为代表"用户中止"的空结果。
    *   确保事件被 `event.accept()` 处理，允许窗口正常关闭。

3.  **初始化 `self.result`** (`feedback_ui.py`):
    *   在 `FeedbackUI` 的 `__init__` 构造函数中，为 `self.result` 设置一个安全的初始默认值（例如，空结果），以应对所有未正常提交的退出场景。

---

## 任务二：窗口位置与大小的记忆与还原

**目标**: UI窗口应能记住其上次关闭时的位置和尺寸，并在下次打开时自动还原，以提升用户体验的连贯性。

**执行步骤**:

1.  **在 `FeedbackUI.closeEvent()` 中保存状态** (`feedback_ui.py`):
    *   在窗口关闭前，使用 `QSettings` 保存窗口的几何信息和状态。
    *   代码示例:
        ```python
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        ```

2.  **在 `FeedbackUI` 初始化时恢复状态** (`feedback_ui.py`):
    *   在窗口创建时（例如在 `__init__` 或 `_create_ui` 的末尾），从 `QSettings` 读取已保存的 `geometry` 和 `windowState`。
    *   如果读取到的值有效，则调用 `self.restoreGeometry()` 和 `self.restoreState()` 方法来应用这些设置。

---

## 任务三：支持回车键（Enter）提交反馈

**目标**: 用户在输入框中按下"Enter"键应直接触发表单提交，同时保留 `Shift+Enter` 作为换行操作。

**执行步骤**:

1.  **修改 `FeedbackTextEdit.keyPressEvent()` 方法** (`feedback_ui.py`):
    *   在该方法中，检测 `Qt.Key_Return` (回车键) 事件。
    *   通过 `QApplication.keyboardModifiers()` 检查是否有修饰键（如 Shift）被同时按下。
    *   如果只有回车键被按下，则阻止其默认的换行行为，并调用父窗口的 `_submit_feedback()` 方法。
    *   如果 `Shift+Enter` 被按下，则执行默认的换行操作。

---

## 任务四：优化文件拖拽后的交互流畅性

**目标**: 当用户将文件或图片拖拽到输入框后，输入光标应能自动激活，使用户无需再次点击即可直接输入文字。

**执行步骤**:

1.  **修改 `FeedbackTextEdit.dropEvent()` 方法** (`feedback_ui.py`):
    *   在成功处理完拖入的文件（无论是插入文件引用还是添加图片预览）的逻辑分支末尾，确保调用一个函数来重新激活输入焦点。
    *   可以复用或完善已有的 `_focus_after_drop()` 方法，确保其执行以下操作：
        1.  调用 `self.setFocus()` 将焦点设置回文本框。
        2.  将光标移动到文本末尾 `self.moveCursor(QTextCursor.End)` 或拖放发生的位置。
        3.  调用 `self.ensureCursorVisible()` 确保光标在视野内可见。

---

本文档将作为后续代码实现的指导蓝图。 
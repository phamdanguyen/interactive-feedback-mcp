# 任务：优化UI输入框性能

**版本**: 1.0
**日期**: 2024-08-01
**负责人**: AI Assistant

---

## 1. 问题描述

当前UI中的核心反馈输入框（`FeedbackTextEdit`）在用户进行文本操作时存在明显的性能问题。具体表现为：

-   在删除文字（尤其长按`Backspace`或`Delete`键）时，出现卡顿和延迟。
-   使用键盘方向键（上、下、左、右）移动光标时，光标的移动不流畅，有跳跃感。
-   整体输入体验缺乏原生输入框的"丝滑感"，尤其是在快速输入或编辑时。

此问题严重影响了用户体验，需要进行针对性优化。

---

## 2. 根本原因分析 (RCA)

经过对`feedback_ui/widgets/feedback_text_edit.py`的代码审查，已定位性能瓶颈的根本原因在于对按键事件（`keyPressEvent`）的**不当处理**和**过度渲染**。

**核心 culprit**: `_ensure_cursor_visible_slot` 函数中的 `self.viewport().update()` 调用。

### 详细分析:

1.  **高频事件触发**: 当用户按住一个键（如`Backspace`）时，`keyPressEvent`会因系统的按键重复机制而被高频率触发。

2.  **不必要的定时器**: 在`keyPressEvent`中，几乎每次按键都会调用`_schedule_ensure_cursor_visible()`，此函数会启动一个10毫秒的`QTimer`。

3.  **强制重绘**: 定时器到期后，会执行`_ensure_cursor_visible_slot`方法。此方法在调用`self.ensureCursorVisible()`之后，还调用了`self.viewport().update()`。

**结论**: `self.viewport().update()`会强制Qt立即重绘整个输入框的视口（viewport）。在高频率的按键事件下，这相当于向UI线程发送了大量的重绘请求（每秒可达几十甚至上百次），完全绕过了Qt自身的渲染优化机制。这导致了CPU资源的浪费和UI线程的阻塞，最终表现为用户感知的卡顿和延迟。

---

## 3. 解决方案与实施计划

为了解决此问题，我们采用分阶段优化的策略。

### **第一阶段：核心性能修复 (立即执行)**

此阶段的目标是快速解决最核心的性能瓶颈，恢复输入的流畅性。

-   **任务 1.1：移除强制刷新**
    -   **文件**: `feedback_ui/widgets/feedback_text_edit.py`
    -   **函数**: `_ensure_cursor_visible_slot`
    -   **操作**: **删除或注释掉** `self.viewport().update()` 这一行。`self.ensureCursorVisible()` 通常足以处理光标的可见性问题。

-   **任务 1.2：优化定时器调用**
    -   **文件**: `feedback_ui/widgets/feedback_text_edit.py`
    -   **函数**: `keyPressEvent`
    -   **操作**: 审视`_schedule_ensure_cursor_visible()`的调用时机。移除在普通字符输入、删除和方向键移动时的调用。仅在可能引发光标位置问题的复杂操作（如粘贴内容、拖拽文件、插入特殊引用）后保留此调用。

---

### **第二阶段：进阶架构优化 (可选)**

在完成第一阶段并验证效果后，可以考虑进行此项优化，以获得更好的长期可维护性和性能。

-   **任务 2.1：迁移基类至 `QPlainTextEdit`**
    -   **背景**: 当前组件继承自为富文本设计的`QTextEdit`，而我们的实际需求是纯文本输入。`QPlainTextEdit`是专为纯文本设计的，其内部实现更轻量，性能更好。
    -   **文件**: `feedback_ui/widgets/feedback_text_edit.py`
    -   **操作**:
        1.  将 `class FeedbackTextEdit(QTextEdit):` 修改为 `class FeedbackTextEdit(QPlainTextEdit):`。
        2.  审查并重构与`QTextEdit`的`QTextDocument`富文本特性相关的功能，例如文件/图像的拖拽和插入逻辑。`QPlainTextEdit`处理这些的方式可能有所不同，需要适配。
        3.  移除在`__init__`中所有与禁用富文本相关的代码（如`setAcceptRichText(False)`），因为`QPlainTextEdit`默认就是纯文本。

---

## 4. 预期成果

-   完成**第一阶段**后，输入框的卡顿和延迟问题应得到完全解决。用户在输入、删除和移动光标时将体验到如原生应用般丝滑流畅的交互。
-   完成**第二阶段**后，组件的底层架构将更加合理，代码更简洁，且在处理大量文本时性能表现会更佳。

--- 
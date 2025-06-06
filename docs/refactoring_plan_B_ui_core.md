# 优化方案B: `feedback_ui` 核心重构 (UI Core Refactoring Plan)

## 1. 目标 (Objective)

对庞大的 `feedback_ui/main_window.py` 文件进行重构，应用关注点分离 (Separation of Concerns) 的原则，将其拆分为更小、更专注、可维护的组件。目标是提升代码的可读性、可维护性和可测试性。

## 2. 背景与问题 (Background & Problem)

`main_window.py` 文件目前超过700行，混合了UI布局定义、复杂的事件处理、数据状态管理以及与后端通信的业务逻辑。这种"上帝对象" (God Object) 模式使得添加新功能或修复 Bug 变得非常困难和危险，因为任何微小的改动都可能引发意想不到的副作用。

## 3. 详细任务分解 (Detailed Task Breakdown)

### 任务 3.1: 引入 MVVM/MVC 设计模式

- **描述**: 规划并引入一种清晰的设计模式来分离数据、逻辑和视图。
    - **View (视图)**: 负责所有UI元素的创建、布局和样式。它应该是"哑"的，只负责展示数据和捕获用户输入。
    - **ViewModel/Model (视图模型/模型)**: 创建一个 `FeedbackViewModel` 类，用于封装UI的状态（如输入框文本、附件列表、当前主题）和业务逻辑（如点击"发送"按钮时如何打包数据）。
    - **Controller (控制器)**: 使用 PySide 的信号与槽机制作为控制器，将 View 的用户交互（如 `button.clicked`）连接到 ViewModel 中的方法。
- **验收标准**:
    - 创建 `feedback_ui/viewmodels/feedback_viewmodel.py` 文件。
    - `FeedbackViewModel` 类管理UI状态，并提供公共方法供视图调用。
    - `main_window.py` 中的业务逻辑和状态管理代码被迁移到 `FeedbackViewModel`。

### 任务 3.2: UI组件化拆分

- **描述**: 将 `main_window.py` 中功能独立的UI区域拆分为可复用的自定义 `QWidget`。
- **建议拆分的组件**:
    - `AttachmentWidget`: 负责展示和管理图片/文件附件的区域。应包含添加、删除附件的逻辑，并通过信号通知外部变化。
    - `OptionsBarWidget`: 负责显示预定义选项的按钮列表。
    - `TextInputWidget`: 包含富文本输入框及其相关的工具栏（如加粗、斜体等）。
- **验收标准**:
    - 在 `feedback_ui/widgets/` 目录下创建上述新的组件文件。
    - `main_window.py` 的代码量显著减少，其主要职责变为组合这些子组件。
    - 子组件通过信号（如 `attachmentAdded`, `optionSelected`）与主窗口或 ViewModel 通信，而不是被动地由主窗口查询状态。

### 任务 3.3: 信号与槽的深化应用

- **描述**: 审查并重构事件处理逻辑，确保组件间的通信优先使用信号与槽，而不是直接方法调用，以实现低耦合。
- **验收标准**:
    - 子组件暴露的接口主要是信号和槽。
    - 主窗口或 ViewModel 通过连接到子组件的信号来响应变化。

## 4. 预期收益 (Expected Benefits)

- **可维护性**: 定位和修复 Bug 更快，因为逻辑被封装在独立的、职责明确的模块中。
- **可读性**: 代码结构更清晰，新成员更容易理解项目。
- **可扩展性**: 添加新功能（如支持更多附件类型）时，只需修改或扩展特定组件，而不会影响整个UI。
- **可测试性**: `ViewModel` 可以独立于UI进行单元测试，确保业务逻辑的正确性。 
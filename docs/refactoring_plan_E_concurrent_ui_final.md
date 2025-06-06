# 最终方案E: 并发UI架构转型实施计划 (修正版)

## 1. 目标 (Objective)
将 `interactive_feedback` 工具从"启动独立进程、同步等待"模式，彻底重构为"应用内创建多窗口、同步契约"模式。在实现高性能、可并发UI交互的同时，确保对上游调用者（Cursor）的行为兼容，不破坏现有工作流。

## 2. 背景与问题 (Background & Problem)
经过分析 `cli.py`，我们确认当前系统通过 `subprocess.run` 启动独立的UI进程。这是一个**同步阻塞**操作，导致任何时候只能存在一个UI窗口，后续请求必须排队等待。这严重限制了应用的并发能力和用户体验。

**本方案的核心是解决此瓶颈，同时规避因异步改造带来的流程失控风险。**

## 3. 新架构设计：应用内多窗口 + 同步等待循环

我们将重构主服务，使其在自身进程内集成Qt事件循环，并通过 `WindowManager` 管理多个UI窗口。最关键的是，在 `interactive_feedback` 工具函数内部，我们将使用一个局部的 `QEventLoop` 来"暂停"执行并等待UI结果，从而**维持对外的同步行为**。

**新架构流程图:**
```mermaid
graph TD
    subgraph "主线程 (Main GUI Thread)"
        Start[调用 interactive_feedback] --> L_Create(1. 创建局部 QEventLoop);
        L_Create --> W_Create(2. 创建 Worker 和 QThread);
        W_Create --> Connect(3. 连接信号槽);
        Connect --> T_Start(4. 启动后台线程);
        T_Start --> L_Exec(5. loop.exec_() 阻塞等待);
        
        subgraph "后台任务 (Worker Thread)"
            T_Start --触发--> R[worker.run()];
            R --> ReqUI(发射 request_ui 信号);
        end

        subgraph "窗口管理 (WindowManager)"
            ReqUI --连接--> WM_Create[manager.create_window()];
            WM_Create --> ShowUI(显示UI窗口);
        end

        subgraph "UI交互"
            ShowUI --> UserInput{用户输入...};
            UserInput --> EmitFeedback(UI发射 feedback_provided 信号);
        end
        
        EmitFeedback --连接--> L_Quit(6. 槽函数接收结果并调用 loop.quit());
        L_Quit --> L_Exec --唤醒--> Return(7. loop结束, interactive_feedback 返回结果);
    end

    linkStyle 4 stroke:blue,stroke-width:2px,stroke-dasharray: 2 2;
    linkStyle 8 stroke:green,stroke-width:2px;
    linkStyle 11 stroke:red,stroke-width:2px,stroke-dasharray: 5 5;
```

## 4. 详细任务分解 (Detailed Task Breakdown)

### 第一阶段：集成Qt事件循环
**目标**: 让主服务 `cli.py` 能够同时运行 `FastMCP` 服务和 Qt 事件循环。

- **任务 1.1: 改造 `cli.py` 依赖与结构**
  - **描述**: 在 `cli.py` 顶部添加 `PyQt5` 的必要导入。将 `PyQt5` 确立为项目的核心依赖。
  - **验收标准**: `import` 语句已添加，`pyproject.toml` 已更新。

- **任务 1.2: 实现MCP服务后台运行**
  - **描述**: 创建一个 `McpServiceWorker(QObject)` 类，其 `run_mcp` 方法内调用 `mcp.run()`。在主程序中，将此 `worker` 移入一个后台 `QThread` 运行。
  - **验收标准**: `McpServiceWorker` 类已创建并正确实现。

- **任务 1.3: 启动双循环**
  - **描述**: 修改 `cli.py` 的 `main()` 函数。先启动运行MCP的后台线程，然后在主线程中创建 `QApplication` 实例并调用 `app.exec_()`。
  - **验收标准**: `cli.py` 启动后，FastMCP服务和Qt事件循环能同时稳定运行。

- **任务 1.4: 实例化 `WindowManager`**
  - **描述**: 在 `main()` 函数中，`QApplication` 创建后，实例化全局的 `WindowManager`。
  - **验收标准**: `self.window_manager = WindowManager()` 代码已添加。

### 第二阶段：核心业务组件改造
**目标**: 将现有UI和服务逻辑，适配到新的应用内模型。

- **任务 2.1: 实现 `InteractiveUI`**
  - **描述**: 分析现有 `feedback-ui` 包（需要找到其源码），将其UI布局和核心交互逻辑迁移至一个新的 `src/feedback_ui/interactive_ui.py` 文件中。
  - **验收标准**: 新的 `InteractiveUI` 类能接收初始化数据，并在用户完成操作后，通过 `feedback_provided = pyqtSignal(str, dict)` 信号，将结果和自身的 `task_id` 一同发射出去。

- **任务 2.2: 实现 `FeedbackWorker`**
  - **描述**: 在 `src/workers/` 目录下创建 `feedback_worker.py`。此类将负责处理原 `interactive_feedback` 工具的后台逻辑。
  - **验收标准**: `FeedbackWorker` 的 `run()` 方法不再启动子进程，而是发射 `request_ui = pyqtSignal(str, dict)` 信号，请求 `WindowManager` 创建UI窗口。

### 第三阶段：重构核心工具函数
**目标**: 用新的异步事件驱动流程，替换旧的同步阻塞流程，并维持对外的同步契约。

- **任务 3.1: 增强 `WindowManager`**
  - **描述**: 为 `WindowManager` 增加一个中继信号 `feedback_received = pyqtSignal(str, dict)` 和一个接收 `InteractiveUI` 信号的槽 `on_feedback_provided(task_id, data)`。该槽函数在接收到UI反馈后，会立即发射中继信号。
  - **验收标准**: `WindowManager` 已增加新的信号和槽。

- **任务 3.2: 重写 `interactive_feedback` 工具函数**
  - **描述**: 这是重构的核心。彻底删除旧的 `subprocess` 逻辑。
  - **验收标准**:
    1.  函数内部创建局部的 `QEventLoop` 和用于存储结果的变量。
    2.  创建并启动 `FeedbackWorker` 的后台线程。
    3.  正确连接信号槽：`worker.request_ui` -> `manager.create_window`；`manager.feedback_received` -> 本地槽函数。
    4.  本地槽函数负责接收结果并调用 `loop.quit()`。
    5.  调用 `loop.exec_()` 进行阻塞等待。
    6.  函数能在 `loop` 结束后，正确返回从UI获取的结果。

### 第四阶段：测试、清理与文档化
**目标**: 确保新架构的健壮性，并完成项目收尾工作。

- **任务 4.1: 端到端测试**
  - **描述**: 更新 `tests/test_concurrent_ui.py`，使其直接调用重构后的 `interactive_feedback` 工具，并进行压力测试。
  - **验收标准**: 在并发调用下，多个UI窗口能正常工作，且每个调用都能正确返回结果，程序无崩溃或死锁。

- **任务 4.2: 代码与项目清理**
  - **描述**: 删除所有用于开发的占位符文件 (`placeholder_*.py`)。评估并决定是否可以废弃和删除旧的、独立的 `feedback-ui` 包及其命令行入口点。
  - **验收标准**: 项目中无残留的废弃代码。

- **任务 4.3: 更新项目文档**
  - **描述**: 更新 `README.md` 和所有受影响的架构文档，详细描述最终的"应用内多窗口"模型、新的依赖关系和运行机制。
  - **验收标准**: 文档与最终代码实现完全一致。 
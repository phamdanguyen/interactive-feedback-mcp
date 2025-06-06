# 🗣️ Interactive Feedback MCP

一个**高性能**的 [MCP Server](https://modelcontextprotocol.io/)，用于在AI辅助开发工具（如 [Cursor](https://www.cursor.com)、[Cline](https://cline.bot) 和 [Windsurf](https://windsurf.com)）中实现高效的人机协作工作流。

本服务已从传统的单体进程模型，全面升级为**应用内并发UI架构**。这意味着它可以在同一个应用进程中，同时管理和显示**多个、互不干扰的反馈窗口**，极大地提升了处理并发请求的能力和用户体验。

**详细信息请参阅：**
*   [功能说明.md](./功能说明.md) - 了解本服务提供的各项功能。
*   [安装与配置指南.md](./安装与配置指南.md) - 获取详细的安装和设置步骤。

**注意：** 此服务器设计为与MCP客户端（例如Cursor、VS Code）在本地一同运行，因为它需要直接访问用户的操作系统以显示UI。

## 🖼️ 示例

![Interactive Feedback Example](https://i.postimg.cc/dt7qgFfW/image.png)
*(请注意，示例图片可能未反映最新的UI调整，但核心交互流程保持不变)*

## 💡 为何使用此工具？

在像Cursor这样的环境中，您发送给LLM的每个提示都被视为一个独立的请求——每个请求都会计入您的每月限额（例如，500个高级请求）。当您迭代模糊指令或纠正被误解的输出时，这会变得效率低下，因为每次后续澄清都会触发一个全新的请求。

此MCP服务器引入了一种变通方法：它允许模型在最终确定响应之前暂停并请求澄清。模型不会直接完成请求，而是触发一个工具调用 (`interactive_feedback`)，打开一个交互式反馈窗口。然后，您可以提供更多细节或要求更改——模型会继续会话，所有这些都在单个请求内完成。

从本质上讲，这只是巧妙地利用工具调用来推迟请求的完成。由于工具调用不计为单独的高级交互，因此您可以在不消耗额外请求的情况下循环执行多个反馈周期。

简而言之，这有助于您的AI助手在猜测之前请求澄清，而不会浪费另一个请求。这意味着更少的错误答案、更好的性能和更少的API使用浪费。

- **💰 减少高级API调用：** 避免浪费昂贵的API调用来基于猜测生成代码。
- **✅ 更少错误：** 行动前的澄清意味着更少的错误代码和时间浪费。
- **⏱️ 更快周期：** 快速确认胜过调试错误的猜测。
- **🎮 更好协作：** 将单向指令转变为对话，让您保持控制。

## 🌟 核心功能与最新改进

### 1. **并发UI支持 (全新架构)**
   - **多窗口管理**：得益于应用内 `Qt` 事件循环和 `WindowManager`，本服务现在可以同时处理来自AI的多个反馈请求。
   - **独立交互**：每个请求都会生成一个独立的、非阻塞的UI窗口。您可以同时与多个窗口进行交互，顺序和优先级完全由您决定。
   - **向后兼容**：尽管内部架构已完全重构，但对外的 `interactive_feedback` 工具接口保持了**100%的向后兼容性**，现有工作流无需任何修改即可享受新架构带来的性能提升。

### 2. 交互式反馈窗口
   - **触发方式**：
     - AI 助手通过调用本 MCP 服务提供的 `interactive_feedback` 工具时，会自动弹出反馈窗口。
     - 用户也可以主动告知 AI 助手："请用 `interactive_feedback mcp` 工具与我对话"来手动触发。
   - 当AI助手需要澄清或在完成任务前需要您的确认时，会弹出一个UI窗口。
   - 您可以在此窗口中输入文本反馈。支持通过按 `Enter`键发送反馈，按 `Shift+Enter` 组合键进行换行。
   - 如果AI助手提供了预定义选项，您可以直接勾选，选中的选项文本会自动整合到最终发送的反馈内容中。

### 3. 图片处理
   - **粘贴图片和文本：** 您可以直接在反馈输入框中粘贴图片（例如，使用Ctrl+V）。支持同时粘贴文本和多张图片。
   - **拖拽图片：** 支持从本地文件系统直接拖拽图片文件到文本输入框中进行添加。
   - **图片预览与管理：** 粘贴的图片会在输入框下方显示缩略图预览。鼠标悬停会显示更大预览及尺寸信息，点击缩略图可以将其移除。
   - **图片处理机制：** 为了优化传输和 AI 处理，图片在发送前会进行尺寸调整（如缩放到512x512，保持宽高比）和格式转换（统一为JPEG，可能调整压缩质量）。
   - **依赖项：** 此功能依赖 `pyperclip`、`pyautogui`、`Pillow` 和 `pywin32` (仅Windows)。

### 4. 文件引用拖拽
   - **文件拖拽**：用户可以将本地文件系统中的文件拖拽到文本输入框中。
   - **引用生成**：拖拽文件后，会在文本框的光标位置插入一个特殊格式的引用文本，如 `@{文件名}`，通常以特殊颜色（如蓝色加粗带下划线）显示。
   - **多文件与同名处理**：支持拖拽多个文件。如果拖拽的文件与已存在的引用同名，会自动在显示名后添加序号（如 `@{文件名} (1)`）以区分。
   - **引用删除**：用户可以通过标准的文本编辑操作（如退格键、删除键）删除这些文件引用文本。
   - **数据传递**：文件引用的显示名及其对应的本地文件路径会作为结构化数据的一部分返回给 AI 助手。

### 5. 常用语管理
   - 您可以保存和管理常用的反馈短语，以便快速插入。
   - 通过"常用语"按钮访问此功能，可以打开常用语管理对话框进行添加、编辑、删除和排序。双击常用语可将其插入主反馈输入框。
   - 快捷图标功能：可在常用语管理中启用。启用后，输入框上方会显示常用语快捷图标（数字代表顺序），点击数字图标即可将对应常用语发送至输入框。点击图标前的 `@` 符号可展开/收起图标列表。

### 6. UI和体验优化
   - **输入框优化：** 修复了长按BackSpace键删除文字时的卡顿问题，提供更流畅的输入体验。
   - **选项复制：** 现在可以方便地从预定义选项的文本标签中复制文本。
   - **界面调整：** 顶部提示文字区域高度增加到200px，以更好地显示提示信息。
   - **窗口行为与控制：**
     - **窗口固定**：提供"固定窗口"按钮，点击后窗口将保持在最前端显示。
     - **自动最小化**：默认情况下，当反馈窗口失去焦点时会自动最小化（除非窗口被固定）。
     - **UI持久化**：窗口的大小、位置以及固定状态会被保存，并在下次启动时恢复。
   - **深色模式 UI**：界面采用深色主题。
   - **快捷键支持**：除 `Enter` 和 `Shift+Enter` 外，还包括 `Ctrl+V` (或 `Cmd+V`) 粘贴。

## 🛠️ 工具

此服务器通过模型上下文协议 (MCP) 公开以下工具：

- `interactive_feedback`:
    - **功能：** 向用户发起交互式会话，显示提示信息，提供可选选项，并收集用户的文本、图片和文件引用反馈。
    - **参数：**
        - `message` (str): **必须参数**。要向用户显示的提示信息、问题或上下文说明。
        - `predefined_options` (List[str], 可选): 一个字符串列表，每个字符串代表一个用户可以选择的预定义选项。如果提供，这些选项会显示为复选框。
    - **返回给AI助手的数据格式：**
      该工具会返回一个包含结构化反馈内容的元组 (Tuple)。元组中的每个元素可以是字符串 (文本反馈或文件引用信息) 或 `fastmcp.Image` 对象 (图片反馈)。
      具体来说，从UI收集到的数据会转换成以下 `content` 项列表，并由服务进一步处理成 FastMCP兼容的元组：
      ```json
      // UI返回给服务的原始JSON结构示例
      {
        "content": [
          {"type": "text", "text": "用户的文本反馈..."},
          {"type": "image", "data": "base64_encoded_image_data", "mimeType": "image/jpeg"},
          {"type": "file_reference", "display_name": "@example.txt", "path": "/path/to/local/example.txt"}
          // ... 可能有更多项
        ]
      }
      ```
      *   **文本内容** (`type: "text"`)：包含用户输入的文本和/或选中的预定义选项组合文本。
      *   **图片内容** (`type: "image"`)：包含 Base64 编码后的图片数据和图片的 MIME 类型 (如 `image/jpeg`)。这些会被转换为 `fastmcp.Image` 对象。
      *   **文件引用** (`type: "file_reference"`)：包含用户拖拽的文件的显示名 (如 `@filename.txt`) 和其在用户本地的完整路径。这些信息通常会作为文本字符串传递给AI助手。

      **注意：**
      * 即便没有任何用户输入（例如用户直接关闭反馈窗口），工具也会返回一个表示"无反馈"的特定消息，如 `("[User provided no feedback]",)`。

## 📦 安装与配置

1.  **先决条件：**
    *   Python 3.11 或更新版本。
    *   [uv](https://github.com/astral-sh/uv) (一个快速的Python包安装和解析工具)。
    *   Git

2.  **获取代码：**
    *   克隆此仓库：
        `git clone https://github.com/pawaovo/interactive-feedback-mcp.git`
    *   进入仓库目录: `cd interactive-feedback-mcp`

3.  **安装依赖：**
    *   运行以下命令，`uv` 将会自动创建虚拟环境并安装所有依赖，包括核心的 `PyQt5` 和其他UI支持库。
        `uv pip install -r requirements.txt`

4.  **配置MCP服务 (例如在Cursor中):**
    *   找到您的 `mcp_servers.json` 文件 (通常在 `.cursor-ai/` 目录下)。
    *   添加以下配置，并**务必修改 `args` 中的路径**，使其指向您克隆本仓库的**绝对路径**。

    ```json
    {
      "mcpServers": {
        "interactive-feedback": {
          "command": "python",
          "args": [
            "-m",
            "src.interactive_feedback_server.cli",
            "--storage-path",
            "/path/to/your/storage/directory" 
          ],
          "cwd": "/path/to/interactive-feedback-mcp",
          "timeout": 600,
          "autoApprove": [
            "interactive_feedback"
          ]
        }
      }
    }
    ```
    **配置说明:**
    - **`command`**: 使用 `python`。
    - **`args`**: 
        - 使用 `-m src.interactive_feedback_server.cli` 来通过模块化方式运行服务，这是新的、正确的启动方式。
        - **`--storage-path`**: (可选但推荐) 指定一个目录用于存储UI设置和常用语等持久化数据。如果省略，数据将保存在项目根目录的 `.ui_settings` 文件夹下。**请将 `/path/to/your/storage/directory` 替换为您希望的实际存储路径。**
    - **`cwd`**: **必须设置**。将其设置为您克隆的 `interactive-feedback-mcp` 项目的根目录绝对路径。这对于确保所有相对路径和模块都能被正确找到至关重要。

5.  **添加AI助手规则 (User Rules):**

    将以下规则添加到您的AI助手中，以引导它在需要时使用本工具：
    ```text
    If requirements or instructions are unclear use the tool interactive_feedback to ask clarifying questions to the user before proceeding, do not make assumptions. Whenever possible, present the user with predefined options through the interactive_feedback MCP tool to facilitate quick decisions.

    Whenever you're about to complete a user request, call the interactive_feedback tool to request user feedback before ending the process. If the feedback is empty you can end the request and don't call the tool in loop.
    ```

## 📝 使用技巧

### 处理图片
- **粘贴：** 在反馈窗口的文本输入框中按 `Ctrl+V` (或 `Cmd+V`) 粘贴图片。您可以同时粘贴多张图片和文本。
- **图片预览：** 粘贴的图片会在输入框下方显示可点击的缩略图预览。点击缩略图可以移除对应的图片。

### 常用语
- 点击反馈窗口左下角的"常用语"按钮，可以管理和选择预设的反馈短语，快速填写输入框。

## 🙏 致谢

- 原始概念和初步开发由 Fábio Ferreira ([@fabiomlferreira](https://x.com/fabiomlferreira)) 完成。
- 由 pawa ([@pawaovo](https://github.com/pawaovo)) 进行了功能增强，并借鉴了 [interactive-feedback-mcp](https://github.com/noopstudios/interactive-feedback-mcp) 项目中的一些想法。
- 当前版本由 pawaovo 进行了架构重构和功能扩展。

## 📄 许可证

此项目使用 MIT 许可证。详情请参阅 `LICENSE` 文件。



# 🗣️ Interactive Feedback MCP

一个简单的 [MCP Server](https://modelcontextprotocol.io/)，用于在AI辅助开发工具（如 [Cursor](https://www.cursor.com)、[Cline](https://cline.bot) 和 [Windsurf](https://windsurf.com)）中实现人机协作工作流。该服务器允许您轻松地直接向AI代理提供反馈，弥合AI与您之间的差距。

**详细信息请参阅：**
*   [功能说明.md](./功能说明.md) - 了解本服务提供的各项功能。
*   [安装与配置指南.md](./安装与配置指南.md) - 获取详细的安装和设置步骤。

**注意：** 此服务器设计为与MCP客户端（例如Cursor、VS Code）在本地一同运行，因为它需要直接访问用户的操作系统以显示UI和执行键盘/鼠标操作。

## 🖼️ 示例

![Interactive Feedback Example](https://i.postimg.cc/dtCw6NWD/Q1.png)
![Interactive Feedback Example](https://i.postimg.cc/kgF936Pm/Q2.png)
![Interactive Feedback Example](https://i.postimg.cc/g0zpYzG6/Q3.png)
*(请注意，示例图片可能未反映最新的UI调整，但核心交互流程保持不变)*

## 💡 为何使用此工具？

在像Cursor这样的环境中，您发送给LLM的每个提示都被视为一个独立的请求——每个请求都会计入您的每月限额（例如，500个高级请求）。当您迭代模糊指令或纠正被误解的输出时，这会变得效率低下，因为每次后续澄清都会触发一个全新的请求。

此MCP服务器引入了一种变通方法：它允许模型在最终确定响应之前暂停并请求澄清。模型不会直接完成请求，而是触发一个工具调用 (`interactive_feedback`)，打开一个交互式反馈窗口。然后，您可以提供更多细节或要求更改——模型会继续会话，所有这些都在单个请求内完成。

从本质上讲，这只是巧妙地利用工具调用来推迟请求的完成。由于工具调用不计为单独的高级交互，因此您可以在不消耗额外请求的情况下循环执行多个反馈周期。

简而言明，这有助于您的AI助手在猜测之前请求澄清，而不会浪费另一个请求。这意味着更少的错误答案、更好的性能和更少的API使用浪费。

- **💰 减少高级API调用：** 避免浪费昂贵的API调用来基于猜测生成代码。
- **✅ 更少错误：** 行动前的澄清意味着更少的错误代码和时间浪费。
- **⏱️ 更快周期：** 快速确认胜过调试错误的猜测。
- **🎮 更好协作：** 将单向指令转变为对话，让您保持控制。

## 🌟 核心功能与最新改进

### 1. 交互式反馈窗口
   - **触发方式**：
     - AI 助手通过调用本 MCP 服务提供的 `interactive_feedback` 工具时，会自动弹出反馈窗口。
     - 用户也可以主动告知 AI 助手："请用 `interactive_feedback mcp` 工具与我对话"来手动触发。
   - 当AI助手需要澄清或在完成任务前需要您的确认时，会弹出一个UI窗口。
   - 您可以在此窗口中输入文本反馈。支持通过按 `Enter`键发送反馈，按 `Shift+Enter` 组合键进行换行。
   - 如果AI助手提供了预定义选项，您可以直接勾选，选中的选项文本会自动整合到最终发送的反馈内容中。

### 2. 图片处理
   - **粘贴图片和文本：** 您可以直接在反馈输入框中粘贴图片（例如，使用Ctrl+V）。支持同时粘贴文本和多张图片。
   - **拖拽图片：** 支持从本地文件系统直接拖拽图片文件到文本输入框中进行添加。
   - **图片预览与管理：** 粘贴的图片会在输入框下方显示缩略图预览。鼠标悬停会显示更大预览及尺寸信息，点击缩略图可以将其移除。
   - **图片处理机制：** 为了优化传输和 AI 处理，图片在发送前会进行尺寸调整（如缩放到512x512，保持宽高比）和格式转换（统一为JPEG，可能调整压缩质量）。
   - **依赖项：** 此功能依赖 `pyperclip`、`pyautogui`、`Pillow` 和 `pywin32` (仅Windows)。

### 3. 文件引用拖拽 ✨ 最新优化
   - **文件拖拽**：用户可以将本地文件系统中的文件拖拽到文本输入框中。
   - **引用生成**：拖拽文件后，会在文本框的光标位置插入一个特殊格式的引用文本，如 `@{文件名}`，以**蓝色加粗**样式显示，与普通文本明确区分。
   - **智能光标定位**：拖拽文件后，光标自动定位到文件引用末尾，用户可以立即继续输入文本。
   - **智能重复检测**：支持拖拽多个文件。只有当输入框中真正存在同名文件时，才会自动添加序号（如 `@{文件名}(1)`）以区分。删除文件后再次拖拽不会错误添加序号。
   - **引用删除**：用户可以通过标准的文本编辑操作（如退格键、删除键）删除这些文件引用文本，系统会自动清理相关引用数据。
   - **数据传递**：文件引用的显示名及其对应的本地文件路径会作为结构化数据的一部分返回给 AI 助手。

### 4. 文件选择功能 ✨ 新增功能
   - **选择文件按钮**：界面提供专门的"选择文件"按钮，点击可打开系统文件选择对话框。
   - **多文件选择**：支持同时选择多个文件，包括图片文件和普通文件。
   - **智能处理**：自动识别图片文件（支持常见格式如jpg、png、gif等）和普通文件，分别进行相应处理。
   - **统一体验**：通过按钮选择的文件与拖拽文件享有相同的处理逻辑和显示效果。

### 5. 常用语管理 ✨ 最新优化
   - **常用语存储**：您可以保存和管理常用的反馈短语，以便快速插入。
   - **hover预览功能**：鼠标悬停在"常用语"按钮上时，会显示常用语预览窗口，支持滚动查看所有常用语（无数量限制）。
   - **流畅交互**：鼠标可以从按钮流畅移动到预览窗口，点击预览中的常用语可直接插入到输入框。
   - **主题适配**：预览窗口支持深色/浅色主题动态切换，与整体UI风格保持一致。
   - **管理对话框**：通过"常用语"按钮点击可打开管理对话框，支持添加、编辑、删除和排序。双击常用语可将其插入主反馈输入框。
   - **优化布局**：管理对话框采用更清晰的布局结构，输入区域独立，底部左侧保存按钮，右侧关闭按钮。

### 6. 终端窗口功能 ✨ 新增功能
   - **多终端支持**：支持PowerShell、Git Bash、Command Prompt三种终端类型。
   - **hover预览**：鼠标悬停在"终端"按钮上时显示终端类型选择预览窗口。
   - **嵌入式终端**：点击终端类型后打开独立的嵌入式终端窗口，支持完整的命令行交互。
   - **工作目录设置**：终端自动设置为项目根目录作为工作目录。
   - **窗口管理**：终端窗口支持独立的大小调整、位置记忆等功能。

### 7. 界面布局选择 ✨ 新增功能
   - **双布局模式**：支持垂直布局（上下分布）和水平布局（左右分布）两种界面模式。
   - **实时切换**：在设置页面可以实时切换布局模式，无需重启应用。
   - **可拖拽分割器**：两种布局模式都支持拖拽分割器手动调整各区域大小。
   - **双击重置**：双击分割器手柄可快速重置为默认比例。
   - **状态保存**：分割器位置和布局选择会自动保存，下次启动时恢复。

### 8. UI和体验优化 ✨ 最新改进
   - **输入框优化：**
     - 修复了长按BackSpace键删除文字时的卡顿问题，提供更流畅的输入体验。
     - 智能提示文字：输入框获得焦点时自动隐藏提示文字，失去焦点且无内容时恢复显示。
     - 增强提示内容：包含拖拽文件和图片提示，以及快捷键说明（Enter提交，Shift+Enter换行，Ctrl+V粘贴）。
   - **设置页面优化：**
     - **统一UI风格**：所有设置项（主题、布局、语言、字体）都使用单选按钮形式，保持界面一致性。
     - **逻辑排序**：设置项按外观主题、界面布局、展示语言、字体大小的逻辑顺序排列。
   - **选项复制：** 现在可以方便地从预定义选项的文本标签中复制文本。
   - **界面调整：** 顶部提示文字区域支持动态调整，在不同布局模式下提供最佳显示效果。
   - **窗口行为与控制：**
     - **窗口固定**：提供"固定窗口"按钮，点击后窗口将保持在最前端显示。修复了取消固定时关闭按钮失效的问题。
     - **自动最小化**：默认情况下，当反馈窗口失去焦点时会自动最小化（除非窗口被固定）。
     - **UI持久化**：窗口的大小、位置、布局模式、分割器状态以及固定状态会被保存，并在下次启动时恢复。
   - **深色模式 UI**：界面采用深色主题。
   - **快捷键支持**：除 `Enter` 和 `Shift+Enter` 外，还包括 `Ctrl+V` (或 `Cmd+V`) 粘贴。

## 🛠️ 工具

此服务器通过模型上下文协议 (MCP) 公开以下工具：

- `interactive_feedback`:
    - **功能：** 向用户发起交互式会话，显示提示信息，提供可选选项，并收集用户的文本、图片和文件引用反馈。支持多种交互方式包括文本输入、图片粘贴/拖拽、文件拖拽/选择等。
    - **参数：**
        - `message` (str): **必须参数**。要向用户显示的提示信息、问题或上下文说明。
        - `predefined_options` (List[str], 可选): 一个字符串列表，每个字符串代表一个用户可以选择的预定义选项。如果提供，这些选项会显示为复选框。
    - **用户交互方式：**
        - **文本输入**：在主输入框中输入反馈文本
        - **图片处理**：通过Ctrl+V粘贴或拖拽图片文件
        - **文件引用**：通过拖拽文件或点击"选择文件"按钮添加文件引用
        - **常用语**：通过hover预览或管理对话框快速插入预设短语
        - **终端操作**：通过终端按钮打开嵌入式终端窗口
        - **布局调整**：通过拖拽分割器调整界面布局
    - **返回给AI助手的数据格式：**
      该工具会返回一个包含结构化反馈内容的元组 (Tuple)。元组中的每个元素可以是字符串 (文本反馈或文件引用信息) 或 `fastmcp.Image` 对象 (图片反馈)。
      具体来说，从UI收集到的数据会转换成以下 `content` 项列表，并由 `server.py` 进一步处理成 FastMCP兼容的元组：
      ```json
      // UI返回给server.py的原始JSON结构示例
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
      *   **图片内容** (`type: "image"`)：包含 Base64 编码后的图片数据和图片的 MIME 类型 (如 `image/jpeg`)。这些在 `server.py` 中会被转换为 `fastmcp.Image` 对象。
      *   **文件引用** (`type: "file_reference"`)：包含用户拖拽或选择的文件的显示名 (如 `@filename.txt`) 和其在用户本地的完整路径。这些信息通常会作为文本字符串传递给AI助手。

      **注意：**
      * 即便没有任何用户输入（例如用户直接关闭反馈窗口），工具也会返回一个表示"无反馈"的特定消息，如 `("[User provided no feedback]",)`。

## 📦 安装

### 方式一：直接从PyPI安装（推荐）

**使用uvx（推荐）：**
```bash
# 直接运行，无需安装
uvx interactive-feedback@latest
```

**使用pip：**
```bash
pip install interactive-feedback
```

### 方式二：开发安装

1.  **先决条件：**
    *   Python 3.11 或更新版本。
    *   [uv](https://github.com/astral-sh/uv) (一个快速的Python包安装和解析工具)。按以下方式安装：
        *   Windows: `pip install uv`
        *   Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
        *   或者参考 `uv` 官方文档获取其他安装方式。

2.  **获取代码：**
    *   克隆此仓库：
        `git clone https://github.com/pawaovo/interactive-feedback-mcp.git`
    *   或者下载源代码压缩包并解压。

3.  **安装依赖：**
    *   进入仓库目录 (`cd interactive-feedback-mcp`)。
    *   运行：
        `uv pip install -r requirements.txt`
    *   **图片支持的额外依赖：** 为了使图片粘贴正常工作，还需要以下包：
        `pyperclip`, `pyautogui`, `Pillow`。
        在Windows上，还需要 `pywin32`。
        这些通常可以通过 `uv pip install pyperclip pyautogui Pillow pywin32` (Windows) 或 `uv pip install pyperclip pyautogui Pillow` (其他系统) 来安装。`requirements.txt` 已包含这些。

## ⚙️ 配置

### 方式一：使用uvx（推荐）

将以下配置添加到您的 `claude_desktop_config.json` (Claude Desktop) 或 `mcp_servers.json` (Cursor, 通常在 `.cursor-ai/mcp_servers.json` 或用户配置目录中)：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uvx",
      "args": [
        "interactive-feedback@latest"
      ],
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

### 方式二：使用pip安装后配置

如果您使用pip安装，配置如下：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "interactive-feedback",
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

### 方式三：开发模式配置

如果您克隆了仓库进行开发，配置如下：

**重要提示：** 将 `/path/to/interactive-feedback-mcp` 替换为您在系统上克隆或解压本仓库的 **实际绝对路径**。
```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uv",
      "args": [
        "--directory",
        "path/to/interactive-feedback-mcp",
        "run",
        "server.py"
      ],
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

**关于 `command` 和 `args` 的说明:**
- 如果 `uv` 在您的系统路径中，并且您希望 `uv` 管理虚拟环境和运行脚本，可以使用 `"command": "uv", "args": ["run", "python", "server.py"]`。
- 如果您更倾向于直接使用系统Python（并已在全局或项目虚拟环境中安装了依赖），可以使用 `"command": "python", "args": ["server.py"]` (或python3)。
- **`cwd` (Current Working Directory):** 强烈建议设置 `cwd` 为此项目的根目录，以确保脚本能正确找到其依赖文件。

2.  将以下自定义规则添加到您的AI助手中 (例如，在 Cursor 的设置 -> Rules -> User Rules):

    ```text
    If requirements or instructions are unclear use the tool interactive_feedback to ask clarifying questions to the user before proceeding, do not make assumptions. Whenever possible, present the user with predefined options through the interactive_feedback MCP tool to facilitate quick decisions.

    Whenever you're about to complete a user request, call the interactive_feedback tool to request user feedback before ending the process. If the feedback is empty you can end the request and don't call the tool in loop.
    ```

    这将确保您的AI助手在提示不明确时以及在标记任务完成之前，总是使用此MCP服务器请求用户反馈。

## 🔧 故障排除

如果在安装或配置过程中遇到问题，请参考以下解决方案：

### uvx环境问题

**问题**：MCP配置中使用 `"command": "uvx"` 时出现"命令未找到"错误。

**解决方案**：

1. **检查uvx安装位置**：
   ```bash
   # Windows
   where uvx

   # Linux/macOS
   which uvx
   ```

2. **使用完整路径**：

   将MCP配置中的 `"uvx"` 替换为完整路径，例如：
   ```json
   {
     "mcpServers": {
       "interactive-feedback": {
         "command": "D:/python/Scripts/uv.exe",
         "args": ["tool", "run", "interactive-feedback@latest"],
         "timeout": 600,
         "autoApprove": ["interactive_feedback"]
       }
     }
   }
   ```

### MCP配置问题

**问题**：AI助手无法识别或启动服务。

**解决方案**：

1. **验证JSON格式**：确保配置文件语法正确
2. **检查文件位置**：确认 `mcp_servers.json` 在正确目录
3. **重启AI助手**：修改配置后重启应用程序
4. **询问AI助手**：将配置文件内容提供给AI，请求配置建议

**示例**：在Cursor中询问："我在配置MCP服务时遇到问题，请帮我检查这个配置：[粘贴您的配置]"

详细的故障排除指南请参阅 [安装与配置指南.md](./安装与配置指南.md#故障排除)。

## 📝 使用技巧

### 处理图片
- **粘贴：** 在反馈窗口的文本输入框中按 `Ctrl+V` (或 `Cmd+V`) 粘贴图片。您可以同时粘贴多张图片和文本。
- **拖拽：** 直接从文件管理器拖拽图片文件到文本输入框中。
- **选择：** 点击"选择文件"按钮，通过文件对话框选择图片文件。
- **图片预览：** 添加的图片会在输入框下方显示可点击的缩略图预览。点击缩略图可以移除对应的图片。

### 文件引用
- **拖拽文件：** 将任意文件从文件管理器拖拽到文本输入框，会生成蓝色的文件引用（如 `@文件名.txt`）。
- **选择文件：** 点击"选择文件"按钮选择多个文件，支持图片和普通文件的混合选择。
- **智能处理：** 系统自动识别图片文件和普通文件，分别进行相应的处理和显示。

### 常用语
- **hover预览：** 鼠标悬停在"常用语"按钮上可快速预览所有常用语，支持滚动查看。
- **快速插入：** 在预览窗口中点击常用语可直接插入到输入框，无需打开管理对话框。
- **管理：** 点击"常用语"按钮打开管理对话框，可以添加、编辑、删除和排序常用语。

### 终端操作
- **hover预览：** 鼠标悬停在"终端"按钮上可预览可用的终端类型（PowerShell、Git Bash、Command Prompt）。
- **快速启动：** 在预览窗口中点击终端类型可直接打开对应的嵌入式终端窗口。
- **工作目录：** 终端会自动设置项目根目录为工作目录，方便进行项目相关操作。

### 界面布局
- **布局切换：** 在设置页面可以选择垂直布局（上下分布）或水平布局（左右分布）。
- **分割器拖拽：** 拖拽分割器手柄可以调整各区域的大小，双击分割器可重置为默认比例。
- **状态保存：** 布局选择和分割器位置会自动保存，下次启动时恢复。

## 🙏 致谢

- 原始概念和初步开发由 Fábio Ferreira ([@fabiomlferreira](https://x.com/fabiomlferreira)) 完成。
- 由 pawa ([@pawaovo](https://github.com/pawaovo)) 进行了功能增强，并借鉴了 [interactive-feedback-mcp](https://github.com/noopstudios/interactive-feedback-mcp) 项目中的一些想法。
- 当前版本由 pawaovo 维护和进一步开发。

## 📄 许可证

此项目使用 MIT 许可证。详情请参阅 `LICENSE` 文件。



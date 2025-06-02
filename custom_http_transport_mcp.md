# MCP自定义HTTP传输机制方案文档

## 1. 背景与目标

当前MCP服务 (Interactive Feedback MCP) 使用 `stdio`作为其与客户端（如Cursor对话窗口）的传输机制。此机制导致在处理需要用户界面 (UI) 的工具（如 `interactive_feedback`）时，表现为串行行为：即一次只能显示和处理一个UI实例，后续UI请求需等待前一个关闭。

**目标**:
设计并实施一个新的自定义传输机制，以解决 `stdio` 的瓶颈，实现以下需求：
1.  **并发UI实例**: 不同的对话窗口（客户端）可以同时拥有并与之交互各自独立的MCP UI实例。
2.  **对话内串行**: 在同一个对话窗口内部，对UI工具的调用仍然保持串行（即一个UI关闭后，该对话窗口才能启动下一个UI）。
3.  **健壮性与可维护性**: 新机制应稳定可靠，易于理解和维护。
4.  **保留核心用户体验**: 用户通过UI窗口进行交互的核心体验保持不变。

## 2. 设计方案：基于HTTP的传输 (FastAPI)

我们将采用基于HTTP的传输机制，其中 `server.py` 将转变为一个使用FastAPI框架的轻量级HTTP服务器。

### 2.1. 核心组件与流程

1.  **HTTP服务器 (`server.py`)**:
    *   使用FastAPI框架构建。
    *   监听一个指定的IP地址和端口 (例如, `127.0.0.1:8765`)。
    *   提供一个核心API端点，例如 `/mcp/call_tool`，用于接收来自客户端的工具调用请求。

2.  **客户端 (例如Cursor插件)**:
    *   改造现有逻辑，不再通过 `stdio` 与 `server.py` 通信。
    *   当需要调用MCP工具时，向 `server.py` 的HTTP端点发送POST请求。

3.  **请求与响应**:
    *   **请求体 (JSON)**:
        ```json
        {
            "conversation_id": "unique_id_for_dialog_window",
            "tool_name": "name_of_the_tool_to_call",
            "tool_args": {
                "param1": "value1",
                "param2": "value2"
            }
        }
        ```
        其中 `conversation_id` 是一个由客户端生成和维护的字符串，用于唯一标识发起请求的对话窗口/上下文。
    *   **响应体 (JSON)**: 包含工具执行的结果或错误信息。

4.  **UI启动与管理 (`interactive_feedback` 工具特别处理)**:
    *   `interactive_feedback` 工具函数将接收 `conversation_id`。
    *   内部使用 `subprocess.Popen()` 以非阻塞方式启动 `feedback_ui.py` 进程。
    *   `server.py` 维护一个全局的、线程安全的字典（例如 `active_uis_by_conversation`），键为 `conversation_id`，值为包含 `Popen` 对象和临时输出文件路径等信息的字典。
    *   **对话内串行控制**:
        *   当收到针对 `interactive_feedback` 的请求时，服务器检查 `active_uis_by_conversation`。
        *   如果该 `conversation_id` 已有关联的活动UI进程（通过 `Popen_instance.poll() is None` 判断），则新的UI请求将不会立即启动。服务器可以返回一个"繁忙"状态或内部将其排队（推荐返回繁忙，让客户端决定重试逻辑）。
    *   **等待特定UI完成**: FastAPI端点处理函数在启动UI后，将调用对应 `Popen` 实例的 `communicate()` 方法。这会阻塞当前处理该HTTP请求的线程/异步任务，直到该特定的UI子进程结束。这不会阻塞整个FastAPI服务器处理其他并发请求。
    *   **结果收集**: UI进程 (`feedback_ui.py`) 将结果写入其唯一的临时文件。`communicate()` 返回后，`server.py` 读取该文件，清理 `active_uis_by_conversation` 中的条目，并将结果通过HTTP响应返回。

### 2.2. `server.py` 改造详情

1.  **依赖**: 添加 `fastapi` 和 `uvicorn` 到项目依赖。
2.  **移除 `mcp.run(transport="stdio")`**。
3.  **FastAPI应用初始化**:
    ```python
    from fastapi import FastAPI, HTTPException, Body
    from pydantic import BaseModel
    import uvicorn
    import threading
    import subprocess
    import tempfile
    import os
    import json
    from typing import Dict, Any, Optional, List # Added List

    # (保留现有的FastMCP实例 mcp 和其工具定义)
    # from fastmcp import FastMCP # Assuming FastMCP is imported
    # from pydantic import Field # Assuming Field is imported
    # mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR") 
    # @mcp.tool() 
    # def interactive_feedback(message: str = Field(description="The specific question for the user"),
    #                        predefined_options: Optional[List[str]] = Field(default=None, description="Predefined options"),
    #                        conversation_id: Optional[str] = Field(default=None, description="Conversation ID for concurrency control")) -> Dict[str, Any]: 
    #     # ... implementation ...
    #     pass

    app = FastAPI()

    # 全局追踪活动UI的状态
    active_uis_by_conversation: Dict[str, Dict[str, Any]] = {}
    active_uis_lock = threading.Lock()
    ```
4.  **请求模型定义**:
    ```python
    class MCPToolCallRequest(BaseModel):
        conversation_id: str
        tool_name: str
        tool_args: Dict[str, Any]
    ```
5.  **API端点实现 (`/mcp/call_tool`)**:
    ```python
    @app.post("/mcp/call_tool")
    async def call_mcp_tool(request: MCPToolCallRequest):
        tool_name = request.tool_name
        tool_args = request.tool_args
        conversation_id = request.conversation_id

        # Placeholder for mcp.tools - replace with actual mcp instance
        # For demonstration, using a dummy mcp object.
        # In real implementation, ensure 'mcp' is the initialized FastMCP instance.
        class MockTool:
            def __init__(self, func):
                self.fn = func
        
        class MockMCP:
            def __init__(self):
                self.tools = {
                    "interactive_feedback": MockTool(interactive_feedback_placeholder) 
                                            # Replace with actual interactive_feedback
                }
        
        # Replace dummy_mcp with your actual 'mcp' instance
        dummy_mcp = MockMCP() 

        if tool_name not in dummy_mcp.tools: # Replace dummy_mcp with mcp
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

        tool_function = dummy_mcp.tools[tool_name].fn # Replace dummy_mcp with mcp

        try:
            if tool_name == "interactive_feedback":
                tool_args_with_cid = tool_args.copy()
                tool_args_with_cid["conversation_id"] = conversation_id
                result = tool_function(**tool_args_with_cid)
            else:
                # For other tools, decide if conversation_id is needed or how to handle
                # For now, just passing original args
                result = tool_function(**tool_args) 
            return result
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            print(f"Error processing tool '{tool_name}' for conversation_id '{conversation_id}': {e}")
            import traceback
            import sys # Required for traceback
            traceback.print_exc(file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    # Placeholder for the actual interactive_feedback function
    # Ensure this function is defined or imported correctly and matches the expected signature.
    def interactive_feedback_placeholder(message: str, predefined_options: Optional[List[str]] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        # This is a placeholder. The actual logic for launching UI via Popen,
        # managing active_uis_by_conversation, and handling results needs to be implemented here
        # as detailed in section 2.2.6.
        print(f"Placeholder: interactive_feedback called for convo {conversation_id} with message: {message}")
        if not conversation_id:
             raise ValueError("conversation_id is required for interactive_feedback with HTTP transport.")
        # --- Begin actual Popen logic here ---
        # Lock, check active_uis, Popen, store, communicate, read result, clean up
        # For now, returning a dummy response
        return {"status": "ok", "message": "UI would be displayed here.", "conversation_id": conversation_id}
    ```
6.  **修改 `interactive_feedback` 工具函数 (详细实现应替换上述占位符)**:
    *   **签名**: `def interactive_feedback(message: str, predefined_options: Optional[List[str]] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:`
    *   **内部逻辑 (摘要 - 完整逻辑见方案文档对应部分)**:
        *   必要性检查: `if not conversation_id: raise ValueError(...)`
        *   `with active_uis_lock:`
            *   检查 `conversation_id` 是否已在 `active_uis_by_conversation` 且进程活动。若是，则 `raise HTTPException(status_code=409, ...)`。
            *   如果进程已结束，则清理旧条目。
        *   创建临时输出文件: `with tempfile.NamedTemporaryFile(...) as tmp: output_file = tmp.name`
        *   构造 `feedback_ui.py` 的参数列表 `args`。
        *   `try: process = subprocess.Popen(args, ...)`
        *   `with active_uis_lock: active_uis_by_conversation[conversation_id] = {"process": process, "output_file": output_file}`
        *   `except Exception as e: # 清理临时文件; raise Exception(...)`
        *   `stdout, stderr = process.communicate()`
        *   `return_code = process.returncode`
        *   `with active_uis_lock: # 清理 active_uis_by_conversation 条目`
        *   检查 `return_code` 和 `stderr`。
        *   检查 `output_file` 是否存在。
        *   读取 `output_file` 内容。
        *   `os.unlink(output_file)`
        *   返回读取到的 `ui_result`。
7.  **启动服务器 (main部分)**:
    ```python
    if __name__ == "__main__":
        # uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
        # 建议通过命令行启动: uvicorn server:app --host 127.0.0.1 --port 8765 --reload (开发时)
        print("To run the server, use the command: uvicorn server:app --host 127.0.0.1 --port 8765")
    ```

### 2.3. `feedback_ui.py` 的改动

*   **基本无需改动**。它仍然通过命令行参数接收信息，并将结果写入由 `--output-file` 参数指定的临时文件。

### 2.4. 客户端改造 (例如Cursor插件)

1.  **移除 `stdio` 通信逻辑**。
2.  **实现HTTP客户端逻辑**:
    *   使用如 `requests` (同步) 或 `httpx` (异步/同步) 库。
    *   **生成/获取 `conversation_id`**: 这是关键。客户端必须能够为每个独立的对话上下文（如每个Cursor对话标签页）生成一个唯一且在该上下文内持久的ID。
    *   **构造请求**: 组装包含 `conversation_id`, `tool_name`, `tool_args` 的JSON。
    *   **发送POST请求**到 `server.py` 的 `/mcp/call_tool` 端点。
    *   **处理响应**: 包括成功的结果和可能的HTTP错误（如404, 409, 500）。

### 2.5. 服务自启动与管理 (避免用户手动启动)

由于 `server.py` 转变为一个需要持续运行的HTTP服务，避免用户每次手动启动该服务至关重要。推荐采用以下"服务引导/检查"脚本方案：

1.  **创建引导脚本 (例如 `start_mcp_server.py`)**:
    *   **职责**:
        *   检查目标HTTP服务 (例如 `http://127.0.0.1:8765`) 是否已在运行。
        *   如果服务未运行，则在后台启动 `uvicorn server:app --host 127.0.0.1 --port 8765`。后台启动需确保与引导脚本分离，且引导脚本快速退出。
        *   如果服务已运行，则直接退出。
    *   **示例代码 (`start_mcp_server.py`)**:
        ```python
        # start_mcp_server.py (示例)
        import subprocess
        import time
        import socket
        import os
        import sys

        HOST = "127.0.0.1" # 应与 server.py 中 uvicorn 配置的host一致
        PORT = 8765       # 应与 server.py 中 uvicorn 配置的port一致
        SERVER_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # 假设 server.py 与此脚本同目录或相对路径可确定

        def is_server_running():
            try:
                with socket.create_connection((HOST, PORT), timeout=0.2): # 略微增加超时
                    return True
            except (socket.timeout, ConnectionRefusedError):
                return False

        if not is_server_running():
            print(f"MCP HTTP server not running on {HOST}:{PORT}. Attempting to start...", file=sys.stderr)
            try:
                # 构建启动uvicorn的命令
                # 确保 'uv' (或python) 和 'uvicorn' 在系统路径中或指定完整路径
                # 使用 'server:app' 指向 server.py 中的 FastAPI 实例 'app'
                cmd = [
                    "uvicorn", # 或者 python -m uvicorn
                    "server:app", 
                    f"--host={HOST}", 
                    f"--port={str(PORT)}",
                    # "--log-level=warning", # 可以根据需要调整日志级别
                    # "--workers=1" # 根据需要配置worker数量
                ]
                
                # 后台启动进程。具体参数因操作系统而异。
                # Windows: subprocess.CREATE_NEW_CONSOLE or subprocess.DETACHED_PROCESS
                # POSIX: start_new_session=True
                # 注意：一个更健壮的后台服务管理可能需要如 'pm2', 'supervisor', 或系统服务。
                # 此处为简化示例。
                
                creation_flags = 0
                if os.name == 'nt':
                    creation_flags = subprocess.CREATE_NEW_CONSOLE # 或者 DETACHED_PROCESS
                
                process = subprocess.Popen(
                    cmd,
                    cwd=SERVER_SCRIPT_DIR, # 确保uvicorn在正确的目录下找到 server.py
                    stdout=subprocess.DEVNULL, # 重定向后台服务的输出
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=creation_flags,
                    start_new_session=(os.name != 'nt') # POSIX系统中创建新会话以分离
                )
                print(f"MCP HTTP server process started (PID: {process.pid if hasattr(process, 'pid') else 'N/A'}). Checking status...", file=sys.stderr)
                time.sleep(2) # 等待服务启动
                
                if is_server_running():
                    print(f"MCP HTTP server successfully started and is running on {HOST}:{PORT}.", file=sys.stderr)
                else:
                    print(f"MCP HTTP server may have failed to start. Please check logs or start manually.", file=sys.stderr)
                    # 此处不 sys.exit(1)，因为引导脚本的主要目的是尝试启动
                    # 实际的工具调用仍会通过HTTP进行，如果服务未成功启动，HTTP调用会失败
            except Exception as e:
                print(f"Error attempting to start MCP HTTP server: {e}", file=sys.stderr)
                # 同上，不强制退出，让后续的HTTP调用来判断服务是否可用
        else:
            print(f"MCP HTTP server is already running on {HOST}:{PORT}.", file=sys.stderr)

        # 引导脚本完成其任务（检查/尝试启动），然后退出。
        # 它不处理实际的MCP工具通信，这部分由客户端通过HTTP完成。
        sys.exit(0)
        ```

2.  **修改客户端的 `mcp.json` (例如Cursor的配置)**:
    *   `"command"` 字段指向新创建的引导脚本 `start_mcp_server.py`。
    *   `"args"` 可能为空。
    *   **重要**: 此配置的目的是让客户端（如Cursor）在首次调用MCP服务时执行引导脚本，以确保HTTP服务正在运行。**然而，客户端（插件）实际的工具调用逻辑（发送工具名、参数等）必须被修改为直接通过HTTP与 `http://<HOST>:<PORT>/mcp/call_tool` 端点通信，而不是期望通过引导脚本的 `stdio` 进行。**引导脚本本身不应产生与工具调用协议相关的 `stdio` 输出。

3.  **客户端 (例如Cursor插件) 工具调用逻辑的调整**:
    *   当需要调用MCP工具时：
        1.  首先，客户端可以（可选地，如果 `mcp.json` 的 `command` 已经触发了引导脚本）确保服务已启动。或者依赖于首次工具调用时 `mcp.json` 自动执行引导脚本。
        2.  然后，客户端构造包含 `conversation_id`, `tool_name`, `tool_args` 的JSON。
        3.  客户端通过HTTP POST请求将此JSON发送到 `server.py` 运行的HTTP服务器地址 (例如 `http://127.0.0.1:8765/mcp/call_tool`)。
        4.  处理HTTP响应。

    *   **优点**:
        *   用户无需手动启动 `server.py` HTTP服务。
        *   服务在需要时被引导脚本检查并尝试启动。
    *   **缺点/复杂性**:
        *   引导脚本中后台进程的健壮启动和管理可能比较复杂，且有平台差异性。
        *   客户端的工具调用流程分为两部分：通过 `mcp.json` 触发引导脚本（间接确保服务运行），然后通过独立的HTTP请求进行实际的工具调用。这种分离需要客户端有能力执行HTTP请求。
        *   HTTP服务的关闭：此方案未显式处理HTTP服务的自动关闭。服务一旦启动，除非手动停止或发生错误，否则会一直运行。可能需要设计一个专门的"关闭服务"的MCP命令或外部机制。

## 3. 关键考虑因素

*   **`conversation_id` 的来源和管理**: 这是整个并发控制方案的基石。客户端必须正确实现。
*   **错误处理与健壮性**:
    *   HTTP错误码的使用（404工具未找到, 409 UI已激活, 500服务器内部错误）。
    *   UI进程启动失败、崩溃或未生成结果文件的处理。
    *   临时文件的可靠创建和清理。
*   **线程安全**: `active_uis_by_conversation` 字典的访问必须通过锁 (`threading.Lock`) 进行保护。
*   **服务器部署与生命周期**: `server.py` 现在是一个需要独立运行和管理的HTTP服务。需要考虑其启动、停止、日志记录等。
*   **端口冲突**: 确保所选端口未被其他服务占用。
*   **安全性**: 如果MCP服务暴露在本地网络而不仅仅是本机 (`127.0.0.1`)，需要考虑认证授权机制（当前方案未包含）。

## 4. 预期效果

*   来自不同对话窗口（不同 `conversation_id`）的UI请求可以并发处理，用户可以看到多个UI窗口同时存在。
*   对于同一个对话窗口（相同 `conversation_id`），如果一个UI正在活动，后续的UI请求会被告知繁忙或等待，实现了对话内的串行。
*   整体系统响应性可能因并发处理而提高。

## 5. 未来可能的增强

*   更复杂的排队机制而不是简单返回"繁忙"。
*   Webhook或WebSocket用于更实时的UI状态通知（如果需要）。
*   对 `FastMCP` 库进行更深度的集成，如果库本身支持或计划支持非 `stdio` 的传输。

This document outlines the proposed solution for enabling concurrent UI instances for the Interactive Feedback MCP by transitioning to an HTTP-based custom transport mechanism. 
# MCP HTTP传输机制实现 - TODO列表

本文档根据 `custom_http_transport_mcp.md` 方案文档生成，旨在提供一份详细的开发待办事项列表。

## 阶段一：环境准备与基础设置

*   [ ] **任务 1.1**: 确定项目依赖并更新。
    *   [ ] 添加 `fastapi` 到项目依赖文件（如 `requirements.txt` 或 `pyproject.toml`）。
    *   [ ] 添加 `uvicorn` (作为ASGI服务器) 到项目依赖。
    *   [ ] 考虑添加 `requests` 或 `httpx` (如果客户端部分也在此项目中管理，用于测试或作为客户端库)。
*   [ ] **任务 1.2**: 建立基础的FastAPI应用结构。
    *   [ ] 在 `server.py` 中，移除现有的 `mcp.run(transport="stdio")`。
    *   [ ] 初始化一个FastAPI应用实例 (`app = FastAPI()`)。
    *   [ ] 添加基本的 `if __name__ == "__main__":` 块，用于通过 `uvicorn` 启动（或提示如何启动）。
*   [ ] **任务 1.3**: 定义HTTP请求和响应模型。
    *   [ ] 创建Pydantic模型 `MCPToolCallRequest` 用于接收客户端请求，包含 `conversation_id`, `tool_name`, `tool_args`。

## 阶段二：`server.py` 核心改造 - HTTP服务与工具调用

*   [ ] **任务 2.1**: 实现核心API端点 `/mcp/call_tool`。
    *   [ ] 创建 `async def call_mcp_tool(request: MCPToolCallRequest)` 函数。
    *   [ ] 从请求中提取 `tool_name`, `tool_args`, `conversation_id`。
    *   [ ] 实现基本的工具查找逻辑 (从现有的 `mcp` 实例中查找 `mcp.tools[tool_name].fn`)。
        *   *注意：确保 `mcp` 实例及其已注册的工具在此 FastAPI 应用的上下文中是可访问的。*
    *   [ ] 实现基本的错误处理 (如工具未找到返回404，其他错误返回500)。
*   [ ] **任务 2.2**: 初始化并集成现有的 `FastMCP` 实例。
    *   [ ] 确保 `mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")` 仍然被正确初始化。
    *   [ ] 确保之前通过 `@mcp.tool()` 装饰器注册的工具函数（尤其是 `interactive_feedback`）可被 `/mcp/call_tool` 端点访问和调用。
*   [ ] **任务 2.3**: 实现全局UI追踪机制。
    *   [ ] 在 `server.py` 中定义全局字典 `active_uis_by_conversation: Dict[str, Dict[str, Any]] = {}`。
    *   [ ] 定义全局线程锁 `active_uis_lock = threading.Lock()`。

## 阶段三：`interactive_feedback` 工具的改造与并发控制

*   [ ] **任务 3.1**: 修改 `interactive_feedback` 函数签名。
    *   [ ] 确保函数接受 `conversation_id: Optional[str] = None` (或使其成为必需参数，并调整调用处)。
    *   [ ] (可选) 将 `predefined_options` 的类型提示改为 `Optional[List[str]]` 以保持一致性。
*   [ ] **任务 3.2**: 实现 `interactive_feedback` 内的并发控制逻辑。
    *   [ ] **前置检查**: 函数开始时，检查 `conversation_id` 是否提供，如果方案要求必须提供，则在此处报错。
    *   [ ] **加锁访问**: 使用 `with active_uis_lock:`保护对 `active_uis_by_conversation` 的访问。
    *   [ ] **检查活动UI**:
        *   如果 `conversation_id` 已存在于 `active_uis_by_conversation` 中。
        *   检查关联的 `Popen` 进程 (`proc_info["process"].poll() is None`)是否仍在运行。
        *   如果仍在运行，则 `raise HTTPException(status_code=409, detail="UI already active...")`。
        *   如果进程已结束，则从字典中安全移除旧条目，并清理其关联的临时文件。
*   [ ] **任务 3.3**: 修改UI启动方式为 `subprocess.Popen`。
    *   [ ] 使用 `tempfile.NamedTemporaryFile` 为每个UI实例创建唯一的输出文件。
    *   [ ] 构造传递给 `feedback_ui.py` 的命令行参数，包括新的输出文件路径。
    *   [ ] 使用 `process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)` 启动UI进程。
    *   [ ] **错误处理**: 如果 `Popen` 启动失败，应清理临时文件并向上抛出异常。
*   [ ] **任务 3.4**: 注册活动UI并等待其完成。
    *   [ ] 启动 `Popen` 成功后，在 `active_uis_lock` 保护下，将 `{"process": process, "output_file": output_file}` 存入 `active_uis_by_conversation`。
    *   [ ] 调用 `stdout, stderr = process.communicate()` 等待UI进程结束。
    *   [ ] 获取 `return_code = process.returncode`。
*   [ ] **任务 3.5**: 处理UI结果与清理。
    *   [ ] **加锁清理**: `communicate()` 返回后，在 `active_uis_lock` 保护下，从 `active_uis_by_conversation` 中移除当前 `conversation_id` 的条目。
    *   [ ] **检查返回码**: 如果 `return_code != 0`，记录 `stderr` 并抛出异常。确保清理临时文件。
    *   [ ] **读取结果**: 如果成功，检查输出文件是否存在，读取JSON结果。
    *   [ ] **清理临时文件**: 使用 `os.unlink(output_file)` 删除输出文件。
    *   [ ] 返回从UI获取的结果。
*   [ ] **任务 3.6**: 非 `interactive_feedback` 工具的处理。
    *   [ ] 在 `/mcp/call_tool` 端点中，对于非 `interactive_feedback` 的工具，确认其调用方式是否需要调整（是否需要 `conversation_id`等）。当前方案假设它们按原样调用。

## 阶段四：服务自启动与管理 (`start_mcp_server.py` 引导脚本)

*   [ ] **任务 4.1**: 创建引导脚本 `start_mcp_server.py`。
    *   [ ] 实现 `is_server_running()` 函数，通过socket连接尝试检查HTTP服务是否在运行。
    *   [ ] **启动逻辑**:
        *   如果 `is_server_running()` 返回 `False`：
            *   构造 `uvicorn server:app ...` 命令。
            *   使用 `subprocess.Popen` 在后台启动该命令。确保设置正确的 `cwd`。
            *   使用平台特定的参数（如 `CREATE_NEW_CONSOLE` on Windows, `start_new_session=True` on POSIX）或方法尝试将进程分离。
            *   重定向子进程的 `stdout`, `stderr`, `stdin` 到 `subprocess.DEVNULL`。
            *   添加短暂延时 (`time.sleep`) 并再次调用 `is_server_running()` 验证启动状态。
            *   向 `stderr` 打印启动日志/状态。
        *   如果 `is_server_running()` 返回 `True`，则打印服务已运行信息到 `stderr`。
    *   [ ] 引导脚本最后应 `sys.exit(0)`。
*   [ ] **任务 4.2**: （仅供参考，实际修改在客户端）规划 `mcp.json` 的调整。
    *   [ ] 记录 `mcp.json` 中的 `command` 应指向 `start_mcp_server.py`。
    *   [ ] 记录实际的工具调用将通过HTTP进行，不由引导脚本的 `stdio` 处理。

## 阶段五：客户端改造 (概念性，具体实现在客户端项目中)

*   [ ] **任务 5.1**: 规划客户端移除 `stdio` 通信的逻辑。
*   [ ] **任务 5.2**: 规划客户端实现HTTP通信的逻辑。
    *   [ ] 选择HTTP客户端库 (e.g., `requests`, `httpx`)。
    *   [ ] 核心：实现 `conversation_id` 的生成、维护和传递机制。确保每个对话窗口有唯一ID。
    *   [ ] 实现构造HTTP POST请求到 `/mcp/call_tool` 的逻辑，包含JSON体。
    *   [ ] 实现处理HTTP响应（成功和错误）的逻辑。
*   [ ] **任务 5.3**: （针对Cursor）研究并确定如何修改Cursor的 `mcp.json` 以适配新的引导脚本和HTTP通信模式。

## 阶段六：测试与文档

*   [ ] **任务 6.1**: 单元测试。
    *   [ ] 测试 `interactive_feedback` 的并发控制逻辑（模拟多个请求）。
    *   [ ] 测试 `start_mcp_server.py` 的服务检查和启动逻辑。
*   [ ] **任务 6.2**: 集成测试。
    *   [ ] 测试从客户端（模拟或真实）到 `server.py` (HTTP服务) 的完整调用流程。
    *   [ ] **重点测试并发场景**: 多个不同的 `conversation_id` 能否同时显示UI。
    *   [ ] **重点测试串行场景**: 同一个 `conversation_id` 的后续UI请求是否在第一个UI关闭前被正确处理（例如，返回409）。
*   [ ] **任务 6.3**: 更新项目 `README.md` 或相关文档。
    *   [ ] 如何安装新的依赖。
    *   [ ] 如何启动 `server.py` HTTP服务（通过 `uvicorn` 命令）。
    *   [ ] （如果适用）引导脚本 `start_mcp_server.py` 的作用和用法。
    *   [ ] API端点说明。
    *   [ ] 客户端如何与新的HTTP服务交互（`conversation_id` 的重要性等）。
*   [ ] **任务 6.4**: 更新 `custom_http_transport_mcp.md` 方案文档（如果在实施过程中有任何调整或学到的经验）。

## 阶段七：部署与维护考虑

*   [ ] **任务 7.1**: 确定 `server.py` HTTP服务的生产环境部署策略。
    *   [ ] 例如，作为系统服务 (systemd, launchd, Windows Service)。
    *   [ ] 使用进程管理器如 `pm2`, `supervisor`。
*   [ ] **任务 7.2**: 日志策略。
    *   [ ] 配置Uvicorn和FastAPI的日志级别和输出。
    *   [ ] 在关键逻辑点（如UI启动、错误处理）添加自定义日志。
*   [ ] **任务 7.3**: 考虑端口配置的灵活性（例如，通过环境变量配置端口）。

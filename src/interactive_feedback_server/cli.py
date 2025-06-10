# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by pawa (https://github.com/pawaovo) with ideas from https://github.com/noopstudios/interactive-feedback-mcp
import os
import sys
import json
import tempfile
import subprocess
import base64

# from typing import Annotated # Annotated 未在此文件中直接使用 (Annotated not directly used in this file)
from typing import (
    Dict,
    List,
    Any,
    Optional,
    Tuple,
    Union,
)  # 简化导入 (Simplified imports)

from fastmcp import FastMCP, Image
from pydantic import (
    Field,
)  # Field 由 FastMCP 内部使用 (Field is used internally by FastMCP)

# V3.2 新增导入 - 配置管理和规则引擎
from .utils import get_config, get_display_mode, resolve_final_options

# 服务启动时的基本信息打印可以保留，用于基本诊断
# Basic info print on server start can be kept for diagnostics
print(f"Server.py 启动 - Python解释器路径: {sys.executable}")
print(f"Server.py 当前工作目录: {os.getcwd()}")


mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

# V3.2 新增：响应缓存文件路径
RESPONSE_CACHE_FILE = os.path.join(
    tempfile.gettempdir(), "interactive_feedback_last_response.txt"
)


def launch_feedback_ui(
    summary: str, predefined_options_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Launches the feedback UI as a separate process using its command-line entry point.
    Collects user input and returns it as a structured dictionary.

    通过命令行入口点将反馈UI作为独立进程启动。
    收集用户输入并将其作为结构化字典返回。
    """
    tmp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp_file_path = tmp.name

        options_str = (
            "|||".join(predefined_options_list) if predefined_options_list else ""
        )

        # Build the argument list for the 'feedback-ui' command
        # This command is available after installing the package in editable mode.
        args_list = [
            "feedback-ui",
            "--prompt",
            summary,
            "--output-file",
            tmp_file_path,
            "--predefined-options",
            options_str,
        ]

        # Run the feedback-ui command
        process_result = subprocess.run(
            args_list,
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            close_fds=(
                os.name != "nt"
            ),  # close_fds is not supported on Windows when shell=False
            text=True,
            errors="ignore",
        )

        if process_result.returncode != 0:
            print(
                f"错误: 启动反馈UI (feedback-ui) 失败。返回码: {process_result.returncode}",
                file=sys.stderr,
            )
            print(
                f"(Error: Failed to launch feedback UI (feedback-ui). Return code: {process_result.returncode})",
                file=sys.stderr,
            )
            if process_result.stdout:
                print(f"UI STDOUT:\n{process_result.stdout}", file=sys.stderr)
            if process_result.stderr:
                print(f"UI STDERR:\n{process_result.stderr}", file=sys.stderr)
            raise Exception(
                f"启动反馈UI失败 (Failed to launch feedback UI): {process_result.returncode}. 详细信息请查看服务器日志 (Check server logs for details)."
            )

        with open(tmp_file_path, "r", encoding="utf-8") as f:
            ui_result_data = json.load(f)

        return ui_result_data

    except FileNotFoundError:
        print("错误: 'feedback-ui' 命令未找到。", file=sys.stderr)
        print("请确保项目已在可编辑模式下安装 (pip install -e .)", file=sys.stderr)
        print("(Error: 'feedback-ui' command not found.)", file=sys.stderr)
        print(
            "(Please ensure the project is installed in editable mode: pip install -e .)",
            file=sys.stderr,
        )
        raise
    except Exception as e:
        print(f"错误: 在 launch_feedback_ui 中发生异常: {e}", file=sys.stderr)
        print(f"(Error: Exception in launch_feedback_ui: {e})", file=sys.stderr)
        raise  # 重新抛出异常，让上层调用者知道发生了错误 (Re-throw exception for caller awareness)
    finally:
        # 确保临时文件在完成后被删除
        # Ensure the temporary file is deleted after completion
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError as e_unlink:
                print(
                    f"警告: 删除临时文件失败 '{tmp_file_path}': {e_unlink}",
                    file=sys.stderr,
                )
                print(
                    f"(Warning: Failed to delete temporary file '{tmp_file_path}': {e_unlink})",
                    file=sys.stderr,
                )


@mcp.tool()
def post_last_response(
    response: str = Field(
        description="AI's complete response to be cached for potential use in full display mode (AI的完整回复，用于完整显示模式)"
    ),
) -> str:
    """
    V3.2 New Tool: Cache AI's complete response for potential use in full display mode.
    This tool allows AI to store its complete response, which can be retrieved
    and displayed in the UI when full mode is enabled.

    V3.2 新工具：缓存AI的完整回复，用于完整显示模式。
    此工具允许AI存储其完整回复，在启用完整模式时可以在UI中检索和显示。

    Args:
        response: AI的完整回复内容

    Returns:
        str: 操作结果确认信息
    """
    try:
        # 将响应保存到临时文件
        with open(RESPONSE_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(response)

        return f"AI回复已缓存 (AI response cached): {len(response)} 字符"

    except Exception as e:
        error_msg = f"缓存AI回复失败 (Failed to cache AI response): {e}"
        print(error_msg, file=sys.stderr)
        return error_msg


def get_cached_response() -> str:
    """
    获取缓存的AI回复
    Get cached AI response

    Returns:
        str: 缓存的回复内容，如果不存在则返回空字符串
    """
    try:
        if os.path.exists(RESPONSE_CACHE_FILE):
            with open(RESPONSE_CACHE_FILE, "r", encoding="utf-8") as f:
                return f.read()
    except Exception as e:
        print(
            f"读取缓存回复失败 (Failed to read cached response): {e}", file=sys.stderr
        )

    return ""


@mcp.tool()
def interactive_feedback(
    message: str = Field(
        description="The specific question for the user (给用户的具体问题)"
    ),
    predefined_options: Optional[List[str]] = Field(
        default=None, description="Predefined options for the user (用户的预定义选项)"
    ),
) -> Tuple[Union[str, Image], ...]:  # 返回字符串和/或 fastmcp.Image 对象的元组
    """
    Requests interactive feedback from the user via a GUI.
    Processes the UI's output to return a tuple compatible with FastMCP,
    allowing for mixed text and image content to be sent back to Cursor.

    V3.2 Enhancement: Supports configurable display modes and three-layer fallback options.

    通过GUI请求用户的交互式反馈。
    处理UI的输出以返回与FastMCP兼容的元组，
    允许将混合的文本和图像内容发送回Cursor。

    V3.2 增强：支持可配置的显示模式和三层回退选项。
    """

    # V3.2 新增：获取配置和解析最终选项
    config = get_config()
    display_mode = get_display_mode(config)

    # 步骤1：决定提示内容（根据显示模式）
    prompt_to_display = message  # 精简模式默认只显示message

    # 如果是完整模式，这里可以扩展为显示更多内容
    # 当前版本保持简单，后续可根据需要扩展
    if display_mode == "full":
        # 完整模式可以在这里添加更多上下文信息
        # 目前保持与精简模式相同，主要区别在选项处理
        prompt_to_display = message

    # 步骤2：V3.2核心变更 - 三层回退选项逻辑
    final_options = resolve_final_options(
        ai_options=predefined_options, text=prompt_to_display, config=config
    )

    # 转换为UI需要的格式
    options_list_for_ui: Optional[List[str]] = None
    if final_options:
        # 确保所有选项都是字符串
        options_list_for_ui = [str(item) for item in final_options if item is not None]

    # 调试信息已移除以减少噪音

    # ui_output_dict 是从 UI 脚本获取的原始输出 (ui_output_dict is the raw output from the UI script)
    ui_output_dict = launch_feedback_ui(prompt_to_display, options_list_for_ui)

    processed_mcp_content: List[Union[str, Image]] = (
        []
    )  # 用于存储文本字符串和 fastmcp.Image 对象

    if (
        ui_output_dict
        and "content" in ui_output_dict
        and isinstance(ui_output_dict["content"], list)
    ):
        ui_content_list = ui_output_dict.get("content", [])
        for item in ui_content_list:
            if not isinstance(item, dict):  # 跳过无效的项目 (Skip invalid items)
                print(f"警告: 无效的内容项格式: {item}", file=sys.stderr)
                print(
                    f"(Warning: Invalid content item format: {item})", file=sys.stderr
                )
                continue

            item_type = item.get("type")
            if item_type == "text":
                text_content = item.get("text", "")
                if text_content:  # 仅添加非空文本 (Only add non-empty text)
                    processed_mcp_content.append(text_content)
            elif item_type == "image":
                base64_data = item.get("data")
                mime_type = item.get("mimeType")
                if base64_data and mime_type:
                    try:
                        image_format_str = mime_type.split("/")[
                            -1
                        ].lower()  # 清晰的变量名并转小写
                        if image_format_str == "jpeg":
                            image_format_str = "jpg"  # fastmcp.Image 期望 'jpg'

                        image_bytes = base64.b64decode(base64_data)
                        mcp_image = Image(data=image_bytes, format=image_format_str)
                        processed_mcp_content.append(mcp_image)
                    except Exception as e:
                        print(f"错误 server.py: 处理图像失败: {e}", file=sys.stderr)
                        print(
                            f"(Error server.py: Failed to process image: {e})",
                            file=sys.stderr,
                        )
                        # 提供用户可见的失败消息 (Provide a user-facing message about the failure)
                        processed_mcp_content.append(
                            f"[图像处理失败 (Image processing failed): {mime_type or 'unknown type'}]"
                        )
            elif item_type == "file_reference":
                display_name = item.get("display_name", "")
                file_path = item.get("path", "")
                if display_name and file_path:
                    # 为MCP格式化文件引用信息 (Format file reference info for MCP)
                    file_info = f"引用文件 (Referenced File): {display_name} [路径 (Path): {file_path}]"
                    processed_mcp_content.append(file_info)
            else:
                print(f"警告: 未知的内容项类型: {item_type}", file=sys.stderr)
                print(
                    f"(Warning: Unknown content item type: {item_type})",
                    file=sys.stderr,
                )

    if not processed_mcp_content:
        # 如果没有提供或处理任何反馈，则返回清晰的消息 (Return a clear message if no feedback was provided or processed)
        return ("[用户未提供反馈 (User provided no feedback)]",)

    # 返回所有已处理内容项（文本和图像）的元组
    # Return a tuple of all processed content items (text and images)
    return tuple(processed_mcp_content)


def main():
    """Main function to run the MCP server."""
    # 确保在主执行块中运行 MCP
    # Ensure MCP runs in the main execution block
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

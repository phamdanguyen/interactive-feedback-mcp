# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by pawa (https://github.com/pawaovo) with ideas from hhttps://github.com/noopstudios/interactive-feedback-mcp
import os
import sys
import json
import tempfile
import subprocess
import base64

# 添加调试信息
print(f"Server.py 启动 - Python解释器路径: {sys.executable}")
print(f"Server.py 当前工作目录: {os.getcwd()}")
# print(f"Server.py Python路径: {sys.path}") # 通常在开发/调试时有用，生产中可以注释掉

from typing import Annotated, Dict, List, Any, Optional, Tuple, Union

from fastmcp import FastMCP, Image
from pydantic import Field

# 导入Cursor集成模块 - 这些不再需要，因为我们不再使用旧的直接对话模式
# from cursor_integration import handle_direct_conversation_response, is_direct_conversation_response

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

def launch_feedback_ui(summary: str, predefinedOptions: list[str] | None = None) -> dict:
    """ 
    Launches the feedback_ui.py script as a separate process.
    Collects user input (text and/or images) and returns it as a structured dictionary.
    The dictionary is expected to follow the FeedbackResult TypedDict structure from feedback_ui.py,
    e.g., {"content": [{"type": "text", "text": "..."}, {"type": "image", "data": "base64...", "mimeType": "image/jpeg"}]}.
    """
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")
        
        # print(f"DEBUG server.py: 接收到的预定义选项: {predefinedOptions}", file=sys.stderr) # 清理调试信息
        
        if predefinedOptions and not isinstance(predefinedOptions, list):
            predefinedOptions = [str(predefinedOptions)]
            # print(f"DEBUG server.py: 预定义选项转换为列表: {predefinedOptions}", file=sys.stderr) # 清理调试信息
        # elif predefinedOptions is None or len(predefinedOptions) == 0: # 此条件分支不产生副作用，可以简化
            # print(f"DEBUG server.py: 没有收到有效的预定义选项", file=sys.stderr) # 清理调试信息
        # else:
            # print(f"DEBUG server.py: 使用有效的预定义选项列表: {predefinedOptions}", file=sys.stderr) # 清理调试信息
            
        options_str = "|||".join(predefinedOptions) if predefinedOptions else ""
        # print(f"DEBUG server.py: 传递的选项字符串: '{options_str}'", file=sys.stderr) # 清理调试信息

        args = [
            sys.executable,
            "-u",
            feedback_ui_path,
            "--prompt", summary,
            "--output-file", output_file,
            "--predefined-options", options_str
        ]
        result = subprocess.run(
            args,
            check=False,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            close_fds=True
        )
        if result.returncode != 0:
            stderr_output = result.stderr.decode('utf-8', errors='ignore')
            # 将详细错误打印到stderr，而不是仅仅是摘要
            print(f"ERROR: Failed to launch feedback UI. Return code: {result.returncode}", file=sys.stderr)
            if stderr_output:
                print(f"Stderr: {stderr_output}", file=sys.stderr)
            raise Exception(f"Failed to launch feedback UI: {result.returncode}. Check server logs for stderr.")
        # else: # 如果成功，stderr可能包含来自UI的调试信息，通常不需要在server日志中重复
            # stderr_output = result.stderr.decode('utf-8', errors='ignore')
            # if stderr_output:
            #     print(f"Debug output from feedback_ui.py: {stderr_output}", file=sys.stderr)

        with open(output_file, 'r') as f:
            result_data = json.load(f)
        os.unlink(output_file)
        return result_data # 重命名变量以避免与 subprocess.run 的 result 混淆
    except Exception as e:
        if 'output_file' in locals() and os.path.exists(output_file):
            os.unlink(output_file)
        # 重新抛出异常，以便上层调用者知道发生了错误
        # print(f"ERROR in launch_feedback_ui: {e}", file=sys.stderr) # 如果需要记录，可以选择性保留
        raise e

# 以下函数不再需要，因为逻辑已内联或改变
# def check_for_images(result: Dict[str, Any]) -> bool:
#     ...
# def extract_text_content(result: Dict[str, Any]) -> str:
#     ...
# def extract_images(result: Dict[str, Any]) -> List[Dict[str, str]]:
#     ...

@mcp.tool()
def interactive_feedback(
    message: str = Field(description="The specific question for the user"),
    predefined_options: list = Field(default=None, description="Predefined options for the user to choose from (optional)"),
) -> Tuple[Union[str, Image], ...]: # Returns a tuple of strings and/or fastmcp.Image objects
    """
    Requests interactive feedback from the user via a GUI.
    Processes the UI's output to return a tuple compatible with FastMCP,
    allowing for mixed text and image content to be sent back to Cursor.
    """
    # print(f"DEBUG server.py: interactive_feedback接收到的消息: {message}", file=sys.stderr) # 清理调试信息
    # print(f"DEBUG server.py: interactive_feedback接收到的选项: {predefined_options}", file=sys.stderr) # 清理调试信息
    
    predefined_options_list = None
    if predefined_options:
        if isinstance(predefined_options, list):
            predefined_options_list = [str(item) for item in predefined_options]
        else:
            predefined_options_list = [str(predefined_options)]
    
    # result_dict is the raw output from the feedback_ui.py script
    result_dict = launch_feedback_ui(message, predefined_options_list)

    processed_content: List[Union[str, Image]] = [] # To store text strings and fastmcp.Image objects

    if result_dict and "content" in result_dict:
        content_list = result_dict.get("content", [])
        for item in content_list:
            item_type = item.get("type")
            if item_type == "text":
                text_content = item.get("text", "")
                # Skip potential image metadata passed as text, as images are handled separately
                try:
                    json_data = json.loads(text_content)
                    if isinstance(json_data, dict) and "width" in json_data and "height" in json_data and "format" in json_data and "size" in json_data:
                        continue # This is image metadata, image itself is processed as Image object
                except (json.JSONDecodeError, TypeError):
                    pass # Not JSON or not the expected metadata structure, treat as normal text
                if text_content: # Only add non-empty text
                    processed_content.append(text_content)
            elif item_type == "image":
                base64_data = item.get("data")
                mime_type = item.get("mimeType")
                if base64_data and mime_type:
                    try:
                        image_format = mime_type.split('/')[-1]
                        if image_format == 'jpeg': # fastmcp.Image expects 'jpg' for JPEG format
                            image_format = 'jpg'
                        image_bytes = base64.b64decode(base64_data)
                        # Create a fastmcp.Image object for MCP transport
                        mcp_image = Image(data=image_bytes, format=image_format)
                        processed_content.append(mcp_image)
                    except Exception as e:
                        print(f"ERROR server.py: Failed to process image: {e}", file=sys.stderr)
                        # Provide a user-facing message about the failure
                        processed_content.append(f"[Image processing failed: {mime_type or 'unknown type'}]") 
            elif item_type == "file_reference":
                # 处理文件引用
                display_name = item.get("display_name", "")
                file_path = item.get("path", "")
                if display_name and file_path:
                    # 添加文件引用信息
                    file_info = f"{display_name} -> {file_path}"
                    processed_content.append(file_info)
    
    if not processed_content:
        # Return a clear message if no feedback was provided or processed
        return ("[User provided no feedback]",)

    # Return a tuple of all processed content items (text and images)
    return tuple(processed_content)

if __name__ == "__main__":
    mcp.run(transport="stdio")

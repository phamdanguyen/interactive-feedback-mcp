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
from typing import Dict, List, Any, Optional, Tuple, Union # 简化导入 (Simplified imports)

from fastmcp import FastMCP, Image
from pydantic import Field # Field 由 FastMCP 内部使用 (Field is used internally by FastMCP)

# 服务启动时的基本信息打印可以保留，用于基本诊断
# Basic info print on server start can be kept for diagnostics
print(f"Server.py 启动 - Python解释器路径: {sys.executable}")
print(f"Server.py 当前工作目录: {os.getcwd()}")


mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

def launch_feedback_ui(summary: str, predefined_options_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """ 
    Launches the main.py script (which runs the Feedback UI) as a separate process.
    Collects user input (text and/or images) and returns it as a structured dictionary.

    启动 main.py 脚本（运行反馈UI）作为一个独立的进程。
    收集用户输入（文本和/或图像）并将其作为结构化字典返回。
    """
    tmp_file_path = None # 初始化临时文件路径 (Initialize temp file path)
    try:
        # 创建一个临时文件用于接收UI的输出结果
        # Create a temporary file for the feedback UI result
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as tmp:
            tmp_file_path = tmp.name
        
        # 获取当前 server.py 脚本所在的目录
        # Get the directory where the current server.py script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 假设 main.py 与 server.py 在同一目录下 (Assume main.py is in the same directory as server.py)
        main_script_path = os.path.join(script_dir, "main.py")

        if not os.path.exists(main_script_path):
            # 如果 main.py 不在同一目录，尝试上一级目录（如果 server.py 在子目录中）
            # If main.py is not in the same directory, try one level up (if server.py is in a subdir)
            # This depends on your project structure.
            # For example, if server.py is in project_root/scripts/ and main.py is in project_root/
            # project_root_dir = os.path.dirname(script_dir)
            # main_script_path = os.path.join(project_root_dir, "main.py")
            # For now, let's assume they are in the same directory or main.py is easily findable.
            # A more robust solution might involve configuration or searching known paths.
            print(f"警告: main.py 未在预期路径找到: {main_script_path}", file=sys.stderr)
            print(f"(Warning: main.py not found at expected path: {main_script_path})", file=sys.stderr)
            # As a fallback, try looking for main.py in the current working directory if different
            if os.path.abspath(script_dir) != os.path.abspath(os.getcwd()):
                alt_main_script_path = os.path.join(os.getcwd(), "main.py")
                if os.path.exists(alt_main_script_path):
                    main_script_path = alt_main_script_path
                    print(f"信息: 在当前工作目录找到 main.py: {main_script_path}", file=sys.stderr)
                    print(f"(Info: Found main.py in current working directory: {main_script_path})", file=sys.stderr)
                else:
                     raise FileNotFoundError(f"无法定位 UI 入口脚本 main.py (Could not locate UI entry script main.py)")
            else:
                 raise FileNotFoundError(f"无法定位 UI 入口脚本 main.py (Could not locate UI entry script main.py)")


        options_str = "|||".join(predefined_options_list) if predefined_options_list else ""

        # 构建传递给 main.py 的参数列表
        # Build the list of arguments to pass to main.py
        args_list = [
            sys.executable,    # Python解释器路径 (Path to Python interpreter)
            "-u",              # 无缓冲标准输出/错误流 (Unbuffered stdout/stderr)
            main_script_path,  # 指向 main.py (Path to main.py)
            "--prompt", summary,
            "--output-file", tmp_file_path,
            "--predefined-options", options_str
        ]
        
        # 运行 main.py 脚本
        # Run the main.py script
        process_result = subprocess.run(
            args_list,
            check=False,        # 手动检查返回码 (Manually check return code)
            shell=False,        # 出于安全原因，不使用shell (Do not use shell for security reasons)
            stdout=subprocess.PIPE, # 捕获标准输出 (Capture stdout)
            stderr=subprocess.PIPE, # 捕获标准错误 (Capture stderr)
            stdin=subprocess.DEVNULL, # 禁止从 stdin 读取 (Prevent reading from stdin)
            close_fds=True,     # 在 POSIX 系统上推荐 (Recommended on POSIX systems)
            text=True,          # 将 stdout 和 stderr 解码为文本 (Decode stdout and stderr as text)
            errors='ignore'     # 解码时忽略错误 (Ignore errors during decoding)
        )

        if process_result.returncode != 0:
            print(f"错误: 启动反馈UI (main.py) 失败。返回码: {process_result.returncode}", file=sys.stderr)
            print(f"(Error: Failed to launch feedback UI (main.py). Return code: {process_result.returncode})", file=sys.stderr)
            if process_result.stdout: # 打印来自UI的stdout（如果有）
                print(f"UI STDOUT:\n{process_result.stdout}", file=sys.stderr)
            if process_result.stderr: # 打印来自UI的stderr（如果有）
                print(f"UI STDERR:\n{process_result.stderr}", file=sys.stderr)
            raise Exception(f"启动反馈UI失败 (Failed to launch feedback UI): {process_result.returncode}. 详细信息请查看服务器日志 (Check server logs for details).")
        
        # 从临时文件中读取UI的JSON输出
        # Read the JSON output from the UI from the temporary file
        with open(tmp_file_path, 'r', encoding='utf-8') as f:
            ui_result_data = json.load(f)
        
        return ui_result_data
    
    except Exception as e:
        print(f"错误: 在 launch_feedback_ui 中发生异常: {e}", file=sys.stderr)
        print(f"(Error: Exception in launch_feedback_ui: {e})", file=sys.stderr)
        raise # 重新抛出异常，让上层调用者知道发生了错误 (Re-throw exception for caller awareness)
    finally:
        # 确保临时文件在完成后被删除
        # Ensure the temporary file is deleted after completion
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError as e_unlink:
                print(f"警告: 删除临时文件失败 '{tmp_file_path}': {e_unlink}", file=sys.stderr)
                print(f"(Warning: Failed to delete temporary file '{tmp_file_path}': {e_unlink})", file=sys.stderr)


@mcp.tool()
def interactive_feedback(
    message: str = Field(description="The specific question for the user (给用户的具体问题)"),
    predefined_options: Optional[List[str]] = Field(default=None, description="Predefined options for the user (用户的预定义选项)"),
) -> Tuple[Union[str, Image], ...]: # 返回字符串和/或 fastmcp.Image 对象的元组
    """
    Requests interactive feedback from the user via a GUI.
    Processes the UI's output to return a tuple compatible with FastMCP,
    allowing for mixed text and image content to be sent back to Cursor.

    通过GUI请求用户的交互式反馈。
    处理UI的输出以返回与FastMCP兼容的元组，
    允许将混合的文本和图像内容发送回Cursor。
    """
    
    options_list_for_ui: Optional[List[str]] = None # 清晰的变量名 (Clear variable name)
    if predefined_options:
        if isinstance(predefined_options, list):
            # 确保所有选项都是字符串 (Ensure all options are strings)
            options_list_for_ui = [str(item) for item in predefined_options if item is not None]
        else: # 如果不是列表但存在，则包装成单元素列表 (If not a list but exists, wrap in single-element list)
            options_list_for_ui = [str(predefined_options)]
    
    # ui_output_dict 是从 UI 脚本获取的原始输出 (ui_output_dict is the raw output from the UI script)
    ui_output_dict = launch_feedback_ui(message, options_list_for_ui)

    processed_mcp_content: List[Union[str, Image]] = [] # 用于存储文本字符串和 fastmcp.Image 对象

    if ui_output_dict and "content" in ui_output_dict and isinstance(ui_output_dict["content"], list):
        ui_content_list = ui_output_dict.get("content", [])
        for item in ui_content_list:
            if not isinstance(item, dict): # 跳过无效的项目 (Skip invalid items)
                print(f"警告: 无效的内容项格式: {item}", file=sys.stderr)
                print(f"(Warning: Invalid content item format: {item})", file=sys.stderr)
                continue

            item_type = item.get("type")
            if item_type == "text":
                text_content = item.get("text", "")
                if text_content: # 仅添加非空文本 (Only add non-empty text)
                    processed_mcp_content.append(text_content)
            elif item_type == "image":
                base64_data = item.get("data")
                mime_type = item.get("mimeType")
                if base64_data and mime_type:
                    try:
                        image_format_str = mime_type.split('/')[-1].lower() # 清晰的变量名并转小写
                        if image_format_str == 'jpeg':
                            image_format_str = 'jpg' # fastmcp.Image 期望 'jpg'
                        
                        image_bytes = base64.b64decode(base64_data)
                        mcp_image = Image(data=image_bytes, format=image_format_str)
                        processed_mcp_content.append(mcp_image)
                    except Exception as e:
                        print(f"错误 server.py: 处理图像失败: {e}", file=sys.stderr)
                        print(f"(Error server.py: Failed to process image: {e})", file=sys.stderr)
                        # 提供用户可见的失败消息 (Provide a user-facing message about the failure)
                        processed_mcp_content.append(f"[图像处理失败 (Image processing failed): {mime_type or 'unknown type'}]")
            elif item_type == "file_reference":
                display_name = item.get("display_name", "")
                file_path = item.get("path", "")
                if display_name and file_path:
                    # 为MCP格式化文件引用信息 (Format file reference info for MCP)
                    file_info = f"引用文件 (Referenced File): {display_name} [路径 (Path): {file_path}]"
                    processed_mcp_content.append(file_info)
            else:
                print(f"警告: 未知的内容项类型: {item_type}", file=sys.stderr)
                print(f"(Warning: Unknown content item type: {item_type})", file=sys.stderr)
    
    if not processed_mcp_content:
        # 如果没有提供或处理任何反馈，则返回清晰的消息 (Return a clear message if no feedback was provided or processed)
        return ("[用户未提供反馈 (User provided no feedback)]",)

    # 返回所有已处理内容项（文本和图像）的元组
    # Return a tuple of all processed content items (text and images)
    return tuple(processed_mcp_content)

if __name__ == "__main__":
    # 确保在主执行块中运行 MCP
    # Ensure MCP runs in the main execution block
    mcp.run(transport="stdio")

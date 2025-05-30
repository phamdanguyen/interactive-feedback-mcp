# Interactive Feedback MCP
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import tempfile
import subprocess
import base64

# 添加调试信息
print(f"Server.py 启动 - Python解释器路径: {sys.executable}")
print(f"Server.py 当前工作目录: {os.getcwd()}")
print(f"Server.py Python路径: {sys.path}")

from typing import Annotated, Dict, List, Any, Optional

from fastmcp import FastMCP
from pydantic import Field

# 导入Cursor集成模块
from cursor_integration import handle_direct_conversation_response, is_direct_conversation_response

# The log_level is necessary for Cline to work: https://github.com/jlowin/fastmcp/issues/81
mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")

def launch_feedback_ui(summary: str, predefinedOptions: list[str] | None = None) -> dict[str, str]:
    # Create a temporary file for the feedback result
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    try:
        # Get the path to feedback_ui.py relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        feedback_ui_path = os.path.join(script_dir, "feedback_ui.py")
        
        # 添加调试信息，记录传入的预定义选项
        print(f"DEBUG server.py: 接收到的预定义选项: {predefinedOptions}", file=sys.stderr)
        
        # 确保predefinedOptions是一个有效的列表
        if predefinedOptions and not isinstance(predefinedOptions, list):
            predefinedOptions = [str(predefinedOptions)]
            print(f"DEBUG server.py: 预定义选项转换为列表: {predefinedOptions}", file=sys.stderr)
        elif predefinedOptions is None or len(predefinedOptions) == 0:
            print(f"DEBUG server.py: 没有收到有效的预定义选项", file=sys.stderr)
        else:
            print(f"DEBUG server.py: 使用有效的预定义选项列表: {predefinedOptions}", file=sys.stderr)
            
        # 如果有预定义选项，将其连接为|||分隔的字符串
        options_str = "|||".join(predefinedOptions) if predefinedOptions else ""
        print(f"DEBUG server.py: 传递的选项字符串: '{options_str}'", file=sys.stderr)

        # Run feedback_ui.py as a separate process
        # NOTE: There appears to be a bug in uv, so we need
        # to pass a bunch of special flags to make this work
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
            raise Exception(f"Failed to launch feedback UI: {result.returncode}, stderr: {result.stderr.decode('utf-8', errors='ignore')}")
        else:
            # 打印stderr中的调试信息
            stderr_output = result.stderr.decode('utf-8', errors='ignore')
            if stderr_output:
                print(f"Debug output: {stderr_output}", file=sys.stderr)

        # Read the result from the temporary file
        with open(output_file, 'r') as f:
            result = json.load(f)
        os.unlink(output_file)
        return result
    except Exception as e:
        if os.path.exists(output_file):
            os.unlink(output_file)
        raise e

def check_for_images(result: Dict[str, Any]) -> bool:
    """检查反馈结果中是否包含图片"""
    if not result or "content" not in result:
        return False
    
    content_list = result.get("content", [])
    for item in content_list:
        if item.get("type") == "image":
            return True
    
    return False

def extract_text_content(result: Dict[str, Any]) -> str:
    """提取反馈结果中的文本内容"""
    if not result or "content" not in result:
        return ""
    
    text_parts = []
    content_list = result.get("content", [])
    
    for item in content_list:
        if item.get("type") == "text":
            # 检查是否是图片元数据 (JSON格式的dict并包含width,height字段)
            text_content = item.get("text", "")
            try:
                json_data = json.loads(text_content)
                if isinstance(json_data, dict) and "width" in json_data and "height" in json_data:
                    # 这是图片元数据，跳过
                    continue
            except:
                # 不是JSON格式，视为普通文本
                pass
                
            text_parts.append(text_content)
    
    return "\n\n".join(filter(None, text_parts))

def extract_images(result: Dict[str, Any]) -> List[Dict[str, str]]:
    """提取反馈结果中的图片数据"""
    if not result or "content" not in result:
        return []
    
    images = []
    content_list = result.get("content", [])
    
    for item in content_list:
        if item.get("type") == "image" and "data" in item and "mimeType" in item:
            images.append({
                "data": item["data"],
                "mimeType": item["mimeType"]
            })
    
    return images

@mcp.tool()
def interactive_feedback(
    message: str = Field(description="The specific question for the user"),
    predefined_options: list = Field(default=None, description="Predefined options for the user to choose from (optional)"),
) -> Dict[str, Any]:
    """Request interactive feedback from the user"""
    print(f"DEBUG server.py: interactive_feedback接收到的消息: {message}", file=sys.stderr)
    print(f"DEBUG server.py: interactive_feedback接收到的选项: {predefined_options}", file=sys.stderr)
    
    # 确保预定义选项是有效的列表
    predefined_options_list = None
    if predefined_options:
        if isinstance(predefined_options, list):
            # 确保列表中的所有项都是字符串
            predefined_options_list = [str(item) for item in predefined_options]
            print(f"DEBUG server.py: 使用选项列表: {predefined_options_list}", file=sys.stderr)
        else:
            # 如果不是列表，尝试转换为字符串并放入列表
            predefined_options_list = [str(predefined_options)]
            print(f"DEBUG server.py: 非列表选项转换为: {predefined_options_list}", file=sys.stderr)
    
    result = launch_feedback_ui(message, predefined_options_list)
    
    # 检查是否包含图片
    has_images = check_for_images(result)
    print(f"DEBUG server.py: 反馈中包含图片: {has_images}", file=sys.stderr)
    
    if has_images:
        # 提取文本内容
        text_content = extract_text_content(result)
        print(f"DEBUG server.py: 提取的文本内容: {text_content}", file=sys.stderr)
        
        # 提取图片数据
        images = extract_images(result)
        print(f"DEBUG server.py: 提取的图片数量: {len(images)}", file=sys.stderr)
        
        # 返回特殊格式，指示需要切换到直接对话模式
        direct_conversation_response = {
            "action": "direct_conversation",
            "content": {
                "text": text_content,
                "images": images
            },
            "auto_submit": True
        }
        
        # 处理直接对话响应，转换为Cursor可识别的格式
        return handle_direct_conversation_response(direct_conversation_response)
    else:
        # 正常返回MCP响应结果
        return result

if __name__ == "__main__":
    mcp.run(transport="stdio")

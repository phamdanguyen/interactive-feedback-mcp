# Interactive Feedback MCP - Cursor Integration
# 该文件用于处理与Cursor的交互，特别是直接对话模式的切换

import json
import sys
from typing import Dict, Any, List

def handle_direct_conversation_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理返回需要直接对话的响应
    这个函数会被MCP服务器调用，用于告诉Cursor如何处理带图片的反馈
    
    Args:
        response: 包含直接对话指令的响应
    
    Returns:
        Dict[str, Any]: 转换后的响应，Cursor可以识别并处理
    """
    try:
        print("处理直接对话响应...", file=sys.stderr)
        
        # 验证响应格式
        if not isinstance(response, dict) or "action" not in response:
            print("错误: 响应格式无效", file=sys.stderr)
            return response
            
        if response["action"] != "direct_conversation":
            print(f"错误: 不支持的操作: {response.get('action')}", file=sys.stderr)
            return response
            
        content = response.get("content", {})
        text = content.get("text", "")
        images = content.get("images", [])
        auto_submit = response.get("auto_submit", True)
        
        print(f"文本内容: {text[:50]}{'...' if len(text) > 50 else ''}", file=sys.stderr)
        print(f"图片数量: {len(images)}", file=sys.stderr)
        print(f"自动提交: {auto_submit}", file=sys.stderr)
        
        # 构建Cursor可以识别的特殊响应格式
        # 这个格式需要与Cursor团队协商确定
        cursor_response = {
            "_cursor_integration": {
                "direct_conversation": True,
                "content": {
                    "text": text,
                    "images": images
                },
                "auto_submit": auto_submit
            },
            "content": [
                {
                    "type": "text",
                    "text": "您的反馈包含图片，将通过直接对话发送。"
                }
            ]
        }
        
        print("转换为Cursor响应格式成功", file=sys.stderr)
        return cursor_response
        
    except Exception as e:
        print(f"处理直接对话响应时出错: {e}", file=sys.stderr)
        # 出错时返回原始响应
        return response

def is_direct_conversation_response(response: Dict[str, Any]) -> bool:
    """
    检查响应是否为直接对话模式
    
    Args:
        response: 响应字典
    
    Returns:
        bool: 是否为直接对话模式
    """
    return (
        isinstance(response, dict) and 
        response.get("action") == "direct_conversation" and
        "content" in response
    )
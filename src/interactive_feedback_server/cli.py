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

from .utils import get_config, resolve_final_options

# 默认系统提示词
DEFAULT_SYSTEM_PROMPTS = {
    "optimize": "你是一个专业的文本优化助手。请将用户的输入文本改写为结构化、逻辑清晰的指令。只需要输出优化后的文本，不要包含任何技术参数、函数定义或元数据信息。",
    "reinforce": "你是一个指令执行助手。请严格按照用户提供的'强化指令'，对用户提供的'原始文本'进行处理和改写。只输出改写结果，不要包含任何技术信息。",
}

# 错误消息常量
ERROR_MESSAGES = {
    "simple_mode_missing_message": "[错误：精简模式需要message参数。AI应该传递处理后的简洁问题或提示。]",
    "full_mode_missing_response": "[错误：完整模式需要full_response参数。AI应该传递原始完整回复内容。]",
    "no_user_feedback": "[用户未提供反馈]",
}


def get_display_mode_fast():
    """
    快速直接读取显示模式，无缓存，确保获取最新配置

    Returns:
        str: "simple" 或 "full"
    """
    try:
        import json
        import os

        # 直接读取配置文件
        config_path = "config.json"
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("display_mode", "simple")
        else:
            return "simple"
    except Exception:
        return "simple"


def get_system_prompts():
    """
    获取系统提示词（优先从配置读取，否则使用默认值）
    Get system prompts (read from config first, fallback to defaults)

    Returns:
        dict: 包含optimize和reinforce提示词的字典
    """
    try:
        config = get_config()
        optimizer_config = config.get("expression_optimizer", {})
        custom_prompts = optimizer_config.get("prompts", {})

        # 合并自定义提示词和默认提示词
        prompts = DEFAULT_SYSTEM_PROMPTS.copy()
        prompts.update(custom_prompts)

        return prompts
    except Exception:
        return DEFAULT_SYSTEM_PROMPTS.copy()


print(f"Server.py 启动 - Python解释器路径: {sys.executable}")
print(f"Server.py 当前工作目录: {os.getcwd()}")


mcp = FastMCP("Interactive Feedback MCP", log_level="ERROR")


def launch_feedback_ui(
    summary: str, predefined_options_list: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Launches the feedback UI as a separate process using its command-line entry point.
    Collects user input and returns it as a structured dictionary.
    """
    tmp_file_path = None
    try:
        # 创建输出文件
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w", encoding="utf-8"
        ) as tmp:
            tmp_file_path = tmp.name

        options_str = (
            "|||".join(predefined_options_list) if predefined_options_list else ""
        )

        # Build the argument list for the 'feedback-ui' command
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
            encoding="utf-8",
            errors="replace",
        )

        if process_result.returncode != 0:
            print(
                f"错误: 启动反馈UI失败，返回码: {process_result.returncode}",
                file=sys.stderr,
            )
            if process_result.stdout:
                print(f"UI STDOUT:\n{process_result.stdout}", file=sys.stderr)
            if process_result.stderr:
                print(f"UI STDERR:\n{process_result.stderr}", file=sys.stderr)
            raise Exception(f"启动反馈UI失败: {process_result.returncode}")

        with open(tmp_file_path, "r", encoding="utf-8") as f:
            ui_result_data = json.load(f)

        return ui_result_data

    except FileNotFoundError:
        print("错误: 'feedback-ui' 命令未找到", file=sys.stderr)
        print("请确保项目已在可编辑模式下安装 (pip install -e .)", file=sys.stderr)
        raise
    except Exception as e:
        print(f"错误: launch_feedback_ui 异常: {e}", file=sys.stderr)
        raise
    finally:
        # 清理临时文件
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except OSError as e_unlink:
                print(
                    f"警告: 删除临时文件失败 '{tmp_file_path}': {e_unlink}",
                    file=sys.stderr,
                )


@mcp.tool()
def interactive_feedback(
    message: Optional[str] = Field(
        default=None,
        description="[SIMPLE mode only] Concise question or prompt processed by AI from its complete response (精简模式专用：AI从完整回复中处理出的简洁问题或提示)",
    ),
    full_response: Optional[str] = Field(
        default=None,
        description="[FULL mode only] AI's original complete response content from the chat dialog (完整模式专用：AI在对话中的原始完整回复内容)",
    ),
    predefined_options: Optional[List[str]] = Field(
        default=None, description="Predefined options for the user (用户的预定义选项)"
    ),
) -> Tuple[Union[str, Image], ...]:  # 返回字符串和/或 fastmcp.Image 对象的元组
    """
    Requests interactive feedback from the user via a GUI.
    Processes the UI's output to return a tuple compatible with FastMCP,
    allowing for mixed text and image content to be sent back to Cursor.

    CRITICAL USAGE FLOW:
    1. AI MUST first complete its full response in the chat dialog
    2. Call this tool with appropriate parameters (tool automatically detects user's display mode)
    3. Tool shows content in UI window based on user's display mode
    4. Tool returns user's feedback to continue the conversation

    This tool is for REQUESTING USER INPUT, not for displaying AI responses.
    AI responses should always appear in the chat dialog first.

    AUTOMATIC MODE DETECTION:
    - Tool automatically detects user's display mode preference
    - SIMPLE mode: Uses 'message' parameter (AI-processed concise question)
    - FULL mode: Uses 'full_response' parameter (AI's original complete response)
    - Wrong parameter for mode will return error message

    RECOMMENDED USAGE PATTERN:

    # AI can pass both parameters, tool will automatically select the correct one
    interactive_feedback(
        message="你希望我实现这些更改吗？",  # For simple mode users
        full_response="我分析了你的代码，发现了3个问题：\n1. 内存泄漏...\n2. 性能瓶颈...",  # For full mode users
        predefined_options=["修复方案A", "修复方案B", "让我想想"]
    )

    # Or AI can pass only the relevant parameter if known
    # For simple mode:
    interactive_feedback(
        message="你希望我实现这些更改吗？",
        predefined_options=["是的", "不是"]
    )

    # For full mode:
    interactive_feedback(
        full_response="我分析了你的代码，发现了3个问题...",
        predefined_options=["修复方案A", "修复方案B"]
    )

    AI RESPONSIBILITIES:
    - SIMPLE mode: AI should provide processed concise question/prompt in 'message'
    - FULL mode: AI should provide original complete response content in 'full_response'
    - RECOMMENDED: Pass both parameters to ensure compatibility with all user preferences

    Enhancement: Automatic mode detection with optimized execution order.
    """

    # 获取用户显示模式
    display_mode = get_display_mode_fast()

    # 延迟加载完整配置，只在需要时获取
    config = None

    # 根据用户模式严格匹配参数
    if display_mode == "full":
        # 完整模式：必须有full_response参数
        if full_response and full_response.strip():  # 检查非空内容
            prompt_to_display = full_response
        else:
            # 完整模式但没有有效的full_response，这是错误调用
            return (ERROR_MESSAGES["full_mode_missing_response"],)
    else:  # simple mode
        # 精简模式：必须有message参数
        if message and message.strip():  # 检查非空内容
            prompt_to_display = message
        else:
            # 精简模式但没有有效的message，这是错误调用
            return (ERROR_MESSAGES["simple_mode_missing_message"],)

    # 三层回退选项逻辑
    if config is None:
        config = get_config()  # 只在需要时加载完整配置

    final_options = resolve_final_options(
        ai_options=predefined_options, text=prompt_to_display, config=config
    )

    # 转换为UI需要的格式
    options_list_for_ui: Optional[List[str]] = None
    if final_options:
        options_list_for_ui = [str(item) for item in final_options if item is not None]

    # 启动UI并获取用户输入
    ui_output_dict = launch_feedback_ui(prompt_to_display, options_list_for_ui)

    # 处理UI输出内容
    processed_mcp_content: List[Union[str, Image]] = []

    if (
        ui_output_dict
        and "content" in ui_output_dict
        and isinstance(ui_output_dict["content"], list)
    ):
        ui_content_list = ui_output_dict.get("content", [])
        for item in ui_content_list:
            if not isinstance(item, dict):
                print(f"警告: 无效的内容项格式: {item}", file=sys.stderr)
                continue

            item_type = item.get("type")
            if item_type == "text":
                text_content = item.get("text", "")
                if text_content:
                    processed_mcp_content.append(text_content)
            elif item_type == "image":
                base64_data = item.get("data")
                mime_type = item.get("mimeType")
                if base64_data and mime_type:
                    try:
                        image_format_str = mime_type.split("/")[-1].lower()
                        if image_format_str == "jpeg":
                            image_format_str = "jpg"

                        image_bytes = base64.b64decode(base64_data)
                        mcp_image = Image(data=image_bytes, format=image_format_str)
                        processed_mcp_content.append(mcp_image)
                    except Exception as e:
                        print(f"错误: 处理图像失败: {e}", file=sys.stderr)
                        processed_mcp_content.append(
                            f"[图像处理失败: {mime_type or 'unknown type'}]"
                        )
            elif item_type == "file_reference":
                display_name = item.get("display_name", "")
                file_path = item.get("path", "")
                if display_name and file_path:
                    file_info = f"引用文件: {display_name} [路径: {file_path}]"
                    processed_mcp_content.append(file_info)
            else:
                print(f"警告: 未知的内容项类型: {item_type}", file=sys.stderr)

    if not processed_mcp_content:
        return (ERROR_MESSAGES["no_user_feedback"],)

    return tuple(processed_mcp_content)


@mcp.tool()
def optimize_user_input(
    original_text: str = Field(description="用户的原始输入文本"),
    mode: str = Field(description="优化模式: 'optimize' 或 'reinforce'"),
    reinforcement_prompt: Optional[str] = Field(
        default=None, description="在 'reinforce' 模式下用户的自定义指令"
    ),
) -> str:
    """
    使用配置的 LLM API 来优化或强化用户输入的文本。

    此功能可以帮助用户将口语化的、可能存在歧义的输入，转化为更结构化、
    更清晰、更便于 AI 模型理解的文本。

    Args:
        original_text: 用户的原始输入文本
        mode: 优化模式
            - 'optimize': 一键优化，使用预设的通用优化指令
            - 'reinforce': 提示词强化，使用用户自定义的强化指令
        reinforcement_prompt: 在 'reinforce' 模式下用户的自定义指令

    Returns:
        str: 优化后的文本或错误信息
    """
    try:
        # 导入LLM模块
        from .llm.factory import get_llm_provider
        from .llm.performance_manager import get_optimization_manager

        # 获取配置
        config = get_config().get("expression_optimizer", {})

        # 获取LLM provider
        provider, status_message = get_llm_provider(config)

        if not provider:
            return f"[优化功能不可用] {status_message}"

        # 获取系统提示词
        system_prompts = get_system_prompts()

        # 验证模式和参数
        if mode == "optimize":
            system_prompt = system_prompts["optimize"]
        elif mode == "reinforce":
            if not reinforcement_prompt:
                return "[错误] 'reinforce' 模式需要提供强化指令"
            system_prompt = system_prompts["reinforce"]
        else:
            return f"[错误] 无效的优化模式: {mode}。支持的模式: 'optimize', 'reinforce'"

        # 检查是否启用性能管理
        performance_config = config.get("performance", {})
        if performance_config.get("cache_enabled", True):
            # 使用性能管理器
            manager = get_optimization_manager(config)

            result = manager.optimize_with_cache(
                provider=provider,
                text=original_text,
                mode=mode,
                system_prompt=system_prompt,
                reinforcement=reinforcement_prompt or "",
            )
        else:
            # 直接调用provider
            if mode == "reinforce":
                prompt = (
                    f"强化指令: '{reinforcement_prompt}'\n\n原始文本: '{original_text}'"
                )
            else:
                prompt = original_text

            result = provider.generate(prompt, system_prompt)

        # 检查是否是错误信息
        if result.startswith("[ERROR"):
            return f"[优化失败] {result}"

        return result

    except ImportError as e:
        return f"[配置错误] LLM模块导入失败: {e}"
    except Exception as e:
        return f"[系统错误] 优化过程中发生异常: {e}"


def main():
    """Main function to run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

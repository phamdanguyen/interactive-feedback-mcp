"""
Google Gemini Provider实现

使用OpenAI兼容的API端点，支持最新的gemini-2.0-flash模型
"""

import time
import random
from typing import Optional
from .base import LLMProvider
from .utils import (
    create_openai_client,
    handle_api_error,
    create_chat_completion,
    validate_api_key,
    validate_model,
)


class GeminiProvider(LLMProvider):
    """Google Gemini API适配器（使用OpenAI兼容接口）"""

    def __init__(
        self, api_key: str, model: str = "gemini-2.0-flash", base_url: str = None
    ):
        """
        初始化Gemini Provider

        Args:
            api_key: Google Gemini API密钥
            model: 使用的模型名称
            base_url: API基础URL，如果不提供则使用默认值
        """
        self.api_key = api_key
        self.model = model
        # 使用配置文件中的base_url，如果没有则使用默认值
        self.base_url = (
            base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        self._client = None
        self.last_request_time = 0
        self.min_interval = 2.0  # 减少间隔，因为使用OpenAI兼容接口

    @property
    def client(self):
        """延迟初始化OpenAI兼容的Gemini客户端"""
        if self._client is None:
            self._client = create_openai_client(self.api_key, self.base_url)
        return self._client

    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        使用Gemini API生成文本（OpenAI兼容接口）

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词

        Returns:
            str: 生成的文本或错误信息
        """
        # 实现请求间隔控制
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)

        # 记录请求时间
        self.last_request_time = time.time()

        # 简单重试机制（仅针对频率限制）
        max_retries = 3
        for attempt in range(max_retries):
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ]
                return create_chat_completion(self.client, self.model, messages)

            except Exception as e:
                error_str = str(e).lower()

                # 如果是频率限制，进行重试
                if (
                    "quota" in error_str or "rate" in error_str or "429" in error_str
                ) and attempt < max_retries - 1:
                    wait_time = (2**attempt) + random.uniform(0, 1)  # 指数退避
                    time.sleep(wait_time)
                    continue

                # 使用统一的错误处理
                return handle_api_error(e, "Gemini", self.model)

        return "[ERROR:RATE] Gemini API重试次数已用完，请稍后再试"

    def validate_config(self) -> tuple[bool, str]:
        """
        验证Gemini配置

        Returns:
            tuple[bool, str]: (是否有效, 状态信息)
        """
        # 验证API密钥
        is_valid, message = validate_api_key("gemini", self.api_key)
        if not is_valid:
            return False, message

        # 验证模型
        is_valid, message = validate_model("gemini", self.model)
        if not is_valid:
            return False, message

        return True, "配置有效"

    def test_connection(self) -> tuple[bool, str]:
        """
        测试Gemini API连接

        Returns:
            tuple[bool, str]: (是否成功, 状态信息)
        """
        try:
            # 发送一个简单的测试请求
            test_response = self.generate("你好", "你是一个AI助手，请简短回复。")

            if test_response.startswith("[ERROR:"):
                return False, f"连接测试失败: {test_response}"
            else:
                return True, "Gemini API连接成功"

        except Exception as e:
            return False, f"连接测试异常: {str(e)}"

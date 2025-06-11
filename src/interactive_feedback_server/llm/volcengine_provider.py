"""
火山引擎（豆包）Provider实现

封装火山引擎API调用，提供统一的LLM接口
"""

from typing import Optional
from .base import LLMProvider
from .utils import (
    create_openai_client,
    handle_api_error,
    create_chat_completion,
    validate_api_key,
    validate_model,
)


class VolcEngineProvider(LLMProvider):
    """火山引擎（豆包）API适配器"""

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-v3-250324",
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
    ):
        """
        初始化火山引擎 Provider

        Args:
            api_key: 火山引擎API密钥
            model: 使用的模型名称
            base_url: API基础URL
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None

    @property
    def client(self):
        """延迟初始化火山引擎客户端（使用OpenAI兼容接口）"""
        if self._client is None:
            self._client = create_openai_client(self.api_key, self.base_url)
        return self._client

    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        使用火山引擎API生成文本

        Args:
            prompt: 用户输入
            system_prompt: 系统提示词

        Returns:
            str: 生成的文本或错误信息
        """
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
            return create_chat_completion(self.client, self.model, messages)

        except Exception as e:
            return handle_api_error(e, "火山引擎", self.model)

    def validate_config(self) -> tuple[bool, str]:
        """
        验证火山引擎配置

        Returns:
            tuple[bool, str]: (是否有效, 状态信息)
        """
        # 验证API密钥
        is_valid, message = validate_api_key("volcengine", self.api_key)
        if not is_valid:
            return False, message

        # 验证Base URL
        if not self.base_url or not self.base_url.startswith(("http://", "https://")):
            return False, "火山引擎Base URL格式无效"

        # 验证模型
        is_valid, message = validate_model("volcengine", self.model)
        if not is_valid:
            return False, message

        return True, "配置有效"

    def test_connection(self) -> tuple[bool, str]:
        """
        测试火山引擎API连接

        Returns:
            tuple[bool, str]: (是否成功, 状态信息)
        """
        try:
            # 发送一个简单的测试请求
            test_response = self.generate("你好", "你是一个AI助手，请简短回复。")

            if test_response.startswith("[ERROR:"):
                return False, f"连接测试失败: {test_response}"
            else:
                return True, "火山引擎API连接成功"

        except Exception as e:
            return False, f"连接测试异常: {str(e)}"

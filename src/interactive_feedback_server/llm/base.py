"""
LLM Provider抽象基类

定义所有LLM提供商必须实现的统一接口
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """定义所有 LLM Provider 必须遵循的接口。"""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        根据给定的 prompt 生成文本。

        Args:
            prompt: 用户的主要输入或问题
            system_prompt: 定义模型角色的系统级指令

        Returns:
            str: 模型生成的文本

        Raises:
            Exception: 当API调用失败时抛出异常
        """
        pass

    @abstractmethod
    def validate_config(self) -> tuple[bool, str]:
        """
        验证当前provider的配置是否有效。

        Returns:
            tuple[bool, str]: (是否有效, 状态信息)
        """
        pass

"""
LLM模块常量定义

统一管理所有LLM相关的常量，避免重复定义
"""

# 默认Provider配置
DEFAULT_PROVIDER_CONFIGS = {
    "openai": {
        "api_key": "",
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    },
    "gemini": {"api_key": "", "model": "gemini-2.0-flash"},
    "deepseek": {
        "api_key": "",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "volcengine": {
        "api_key": "",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "model": "deepseek-v3-250324",
    },
}

# 默认优化器配置 - V4.2 用户友好版本
DEFAULT_OPTIMIZER_CONFIG = {
    "enabled": True,  # V4.2 改为默认启用
    "active_provider": "openai",
    "providers": DEFAULT_PROVIDER_CONFIGS,
}

# 支持的模型列表
SUPPORTED_MODELS = {
    "openai": [
        # OpenAI模型
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        # DeepSeek模型（兼容OpenAI接口）
        "deepseek-chat",
        "deepseek-coder",
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash-preview-04-17",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro",
        "gemini-pro",
    ],
    "deepseek": ["deepseek-chat", "deepseek-coder"],
    "volcengine": [
        "deepseek-v3-250324",
        "doubao-pro-4k",
        "doubao-pro-32k",
        "doubao-pro-128k",
        "doubao-lite-4k",
        "doubao-lite-32k",
    ],
}

# API端点配置
API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "deepseek": "https://api.deepseek.com/v1",
    "volcengine": "https://ark.cn-beijing.volces.com/api/v3",
}

# 通用配置
COMMON_CONFIG = {"timeout": 30, "temperature": 0.7, "max_tokens": 1024}

# 错误消息模板
ERROR_MESSAGES = {
    "auth": "[ERROR:AUTH] {provider} API密钥无效，请检查配置",
    "rate": "[ERROR:RATE] {provider} API调用频率过高，请稍后再试",
    "timeout": "[ERROR:TIMEOUT] {provider} 请求超时，请稍后重试",
    "request": "[ERROR:REQUEST] {provider} 请求参数无效，请检查输入内容",
    "safety": "[ERROR:SAFETY] 内容被{provider}安全过滤器阻止，请修改输入",
    "model": "[ERROR:MODEL] {provider} 模型 {model} 不存在或不支持",
    "unknown": "[ERROR:UNKNOWN] {provider} 服务异常: {error}",
}

# Provider显示名称
PROVIDER_DISPLAY_NAMES = {
    "openai": {"zh_CN": "OpenAI", "en_US": "OpenAI"},
    "gemini": {"zh_CN": "Google Gemini", "en_US": "Google Gemini"},
    "deepseek": {"zh_CN": "DeepSeek", "en_US": "DeepSeek"},
    "volcengine": {"zh_CN": "火山引擎", "en_US": "Huoshan"},
}

# API密钥验证规则
API_KEY_VALIDATION = {
    "openai": {"prefix": "sk-", "min_length": 30},  # 调整为更合理的长度
    "gemini": {"prefix": "AIza", "min_length": 30},
    "deepseek": {"prefix": "sk-", "min_length": 30},
    "volcengine": {"format": "uuid", "min_length": 30, "contains": "-"},  # UUID格式
}

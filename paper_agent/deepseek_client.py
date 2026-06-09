"""DeepSeek API 客户端。"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

from .env_loader import load_env_file


@dataclass(slots=True)
class DeepSeekConfig:
    """调用 DeepSeek API 需要的配置。"""

    # API Key 不写死在代码中，而是从环境变量或外部配置传入。
    api_key: str
    # DeepSeek 的 OpenAI 兼容接口基础地址。
    base_url: str = "https://api.deepseek.com"
    # 默认模型。后续模型变更时，可以通过命令行参数替换。
    model: str = "deepseek-v4-flash"
    # 控制生成内容的随机性。综述任务更适合偏低温度，保证稳定。
    temperature: float = 0.2
    # 限制最大输出 token，避免一次生成过长。
    max_tokens: int = 4000


class DeepSeekClient:
    """使用标准库 urllib 调用 DeepSeek Chat Completions API。"""

    def __init__(self, config: DeepSeekConfig) -> None:
        self.config = config

    @classmethod
    def from_env(cls, base_url: str, model: str) -> "DeepSeekClient":
        """从环境变量创建客户端。"""

        # 先加载本地 .env，再读取环境变量。这样用户不用每次在终端手动 export。
        load_env_file()
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "未找到 DEEPSEEK_API_KEY，请确认项目根目录下的 .env 已填写 DeepSeek API Key。"
            )
        base_url = os.getenv("DEEPSEEK_BASE_URL", base_url).strip() or base_url
        model = os.getenv("DEEPSEEK_MODEL", model).strip() or model
        return cls(DeepSeekConfig(api_key=api_key, base_url=base_url, model=model))

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """发送一次聊天补全请求，并返回模型生成的文本。"""

        url = self.config.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            response_body = response.read().decode("utf-8")
        data = json.loads(response_body)
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"DeepSeek API 返回格式异常：{data}") from exc

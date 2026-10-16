"""LLM 适配层：简历字段提取。协议 + DeepSeek 实现。"""

import json
from typing import Any, Protocol

import httpx

from .config import settings
from .extraction import EXTRACTION_PROMPT


class LLMNotConfiguredError(RuntimeError):
    """未配置 LLM 凭据时抛出。"""


class LLMClient(Protocol):
    def extract_resume_fields(self, text: str) -> dict[str, Any]: ...


class DeepSeekClient:
    """DeepSeek chat completions 客户端，输出简历 13 字段 JSON。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = settings.deepseek_base_url,
        model: str = settings.deepseek_model,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def extract_resume_fields(self, text: str) -> dict[str, Any]:
        if not self._api_key:
            raise LLMNotConfiguredError("未配置 DEEPSEEK_API_KEY，无法进行 AI 简历提取")

        resp = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": text},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM 未返回 JSON 对象")
        return parsed

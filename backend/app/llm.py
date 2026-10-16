"""LLM 适配层：简历字段提取与评分。协议 + DeepSeek 实现。"""

import json
from collections.abc import Sequence
from typing import Any, Protocol

import httpx

from .config import settings
from .extraction import EXTRACTION_PROMPT
from .schemas import ScoringStandardAIn, ScoringStandardBIn
from .scoring import build_scoring_prompt, normalize_match_weights


class LLMNotConfiguredError(RuntimeError):
    """未配置 LLM 凭据时抛出。"""


class LLMClient(Protocol):
    def extract_resume_fields(self, text: str) -> dict[str, Any]: ...

    def score_resume(
        self,
        resume_content: dict[str, Any],
        a_rows: Sequence[ScoringStandardAIn],
        b_rows: Sequence[ScoringStandardBIn],
    ) -> dict[str, float]: ...


class DeepSeekClient:
    """DeepSeek chat completions 客户端。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = settings.deepseek_base_url,
        model: str = settings.deepseek_model,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def _chat_json(self, system: str, user: str) -> dict[str, Any]:
        resp = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
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

    def extract_resume_fields(self, text: str) -> dict[str, Any]:
        if not self._api_key:
            raise LLMNotConfiguredError("未配置 DEEPSEEK_API_KEY，无法进行 AI 简历提取")
        return self._chat_json(EXTRACTION_PROMPT, text)

    def score_resume(
        self,
        resume_content: dict[str, Any],
        a_rows: Sequence[ScoringStandardAIn],
        b_rows: Sequence[ScoringStandardBIn],
    ) -> dict[str, float]:
        if not self._api_key:
            raise LLMNotConfiguredError("未配置 DEEPSEEK_API_KEY，无法进行 AI 简历评分")
        prompt = build_scoring_prompt(a_rows, b_rows)
        parsed = self._chat_json(prompt, json.dumps(resume_content, ensure_ascii=False))
        return normalize_match_weights(parsed)

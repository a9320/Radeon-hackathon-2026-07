"""CodeRisk Agent — LLM 客户端

支持双后端：共享 API（Radeon Cloud）+ 本地 llama.cpp。
统一接口，Agent 层无感知切换。
"""

from __future__ import annotations

import json
import time
from typing import Optional

import httpx
from rich.console import Console

from core.models import LLMBackend, LLMConfig

console = Console()

# 默认配置
DEFAULT_CONFIGS = {
    LLMBackend.SHARED_API: LLMConfig(
        backend=LLMBackend.SHARED_API,
        api_url="https://chat.api.amd.com/v1",
        model="Qwen/Qwen3.6-35B-A3B",
        temperature=0.1,
        max_tokens=4096,
    ),
    LLMBackend.LOCAL: LLMConfig(
        backend=LLMBackend.LOCAL,
        api_url="http://localhost:8080",
        model="qwen2.5-coder-7b-instruct",
        temperature=0.1,
        max_tokens=4096,
    ),
}


class LLMClient:
    """统一 LLM 客户端"""

    def __init__(self, config: Optional[LLMConfig] = None, backend: Optional[LLMBackend] = None):
        if config:
            self.config = config
        else:
            b = backend or LLMBackend.SHARED_API
            self.config = DEFAULT_CONFIGS[b]

        self._client = httpx.Client(timeout=self.config.timeout)
        self._request_count = 0
        self._total_tokens = 0

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> str:
        """发送对话请求，返回文本响应"""
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        url = f"{self.config.api_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        start = time.monotonic()
        try:
            resp = self._client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            console.print(f"[red]LLM API error: {e.response.status_code}[/]")
            raise
        except httpx.RequestError as e:
            console.print(f"[red]LLM connection error: {e}[/]")
            raise

        elapsed_ms = int((time.monotonic() - start) * 1000)
        self._request_count += 1

        # 提取响应
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        self._total_tokens += usage.get("total_tokens", 0)

        console.print(
            f"[dim]LLM [{self.config.backend.value}] "
            f"{elapsed_ms}ms | "
            f"tokens: {usage.get('prompt_tokens', '?')}→{usage.get('completion_tokens', '?')} | "
            f"total: {self._total_tokens}[/]"
        )

        return content

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """发送对话请求，返回 JSON 对象"""
        raw = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        # 尝试提取 JSON
        return _extract_json(raw)

    @property
    def stats(self) -> dict:
        return {
            "backend": self.config.backend.value,
            "model": self.config.model,
            "requests": self._request_count,
            "total_tokens": self._total_tokens,
        }

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _extract_json(text: str) -> dict:
    """从 LLM 响应中提取 JSON（容错处理）"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 ```json ... ``` 块
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        try:
            return json.loads(text[start:end].strip())
        except json.JSONDecodeError:
            pass

    # 尝试提取第一个 { ... }
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1

    raise ValueError(f"无法从 LLM 响应中提取 JSON:\n{text[:200]}...")

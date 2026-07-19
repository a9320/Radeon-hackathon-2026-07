"""CodeRisk Agent - LLM Client

Three backends:
1. Shared API (Radeon Cloud HTTP)
2. Local llama-server (HTTP)
3. Local llama-cpp-python (direct GGUF load)

Unified interface with auto-retry.
"""

from __future__ import annotations

import json
import time
from typing import Optional

import httpx
from rich.console import Console

from core.models import LLMBackend, LLMConfig

console = Console()

DEFAULT_CONFIGS = {
    LLMBackend.SHARED_API: LLMConfig(
        backend=LLMBackend.SHARED_API,
        api_url="https://developer.amd.com.cn/radeon/api/v1",
        model="Qwen/Qwen3.6-35B-A3B",
        temperature=0.1,
        max_tokens=4096,
    ),
    LLMBackend.LOCAL_HTTP: LLMConfig(
        backend=LLMBackend.LOCAL_HTTP,
        api_url="http://localhost:8080",
        model="qwen2.5-coder-7b-instruct",
        temperature=0.1,
        max_tokens=4096,
    ),
    LLMBackend.LOCAL_LLAMA_CPP: LLMConfig(
        backend=LLMBackend.LOCAL_LLAMA_CPP,
        model_path="/workspace/llama.cpp/models/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        model="qwen2.5-coder-7b-instruct",
        temperature=0.1,
        max_tokens=4096,
    ),
}

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0


class LLMClient:
    """Unified LLM client with retry support."""

    def __init__(self, config: Optional[LLMConfig] = None, backend: Optional[LLMBackend] = None):
        if config:
            self.config = config
        else:
            b = backend or LLMBackend.LOCAL_LLAMA_CPP
            self.config = DEFAULT_CONFIGS[b]

        self._client: Optional[httpx.Client] = None
        self._local_llm = None
        self._request_count = 0
        self._total_tokens = 0

        if self.config.backend in (LLMBackend.SHARED_API, LLMBackend.LOCAL_HTTP):
            self._client = httpx.Client(timeout=self.config.timeout)
        elif self.config.backend == LLMBackend.LOCAL_LLAMA_CPP:
            self._init_llama_cpp()

    def _init_llama_cpp(self):
        try:
            from llama_cpp import Llama
        except ImportError:
            console.print("[red]llama-cpp-python not installed. Run: pip install llama-cpp-python[/]")
            raise

        if not self.config.model_path:
            raise ValueError("LOCAL_LLAMA_CPP requires model_path in config")

        console.print(f"[dim]Loading local model: {self.config.model_path}[/]")
        self._local_llm = Llama(
            model_path=self.config.model_path,
            n_gpu_layers=self.config.n_gpu_layers,
            verbose=False,
            n_ctx=4096,
        )
        console.print("[green]Local model loaded.[/]")

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict] = None,
    ) -> str:
        """Send chat request with auto-retry."""
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        last_err = None
        for attempt in range(MAX_RETRIES):
            try:
                if self.config.backend == LLMBackend.LOCAL_LLAMA_CPP:
                    return self._chat_local(messages, temp, tokens)
                else:
                    return self._chat_http(messages, temp, tokens, response_format)
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY * (2 ** attempt)
                    console.print(
                        f"[yellow]Retry {attempt + 1}/{MAX_RETRIES} after {delay}s: {e}[/]"
                    )
                    time.sleep(delay)
        raise last_err

    def _chat_http(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[dict] = None,
    ) -> str:
        """HTTP API call (shared API or llama-server)."""
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        url = f"{self.config.api_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        start = time.monotonic()
        resp = self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        self._request_count += 1

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        self._total_tokens += usage.get("total_tokens", 0)

        console.print(
            f"[dim]LLM [{self.config.backend.value}] "
            f"{elapsed_ms}ms | "
            f"tokens: {usage.get('prompt_tokens', '?')}->{usage.get('completion_tokens', '?')} | "
            f"total: {self._total_tokens}[/]"
        )
        return content

    def _chat_local(
        self,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        """llama-cpp-python direct inference."""
        prompt = self._messages_to_prompt(messages)

        stop_tokens = ["<|endofassistant|>", "</s>"]

        start = time.monotonic()
        result = self._local_llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_tokens,
        )
        elapsed_ms = int((time.monotonic() - start) * 1000)
        self._request_count += 1

        text = result["choices"][0]["text"]
        tokens_used = result.get("usage", {}).get("total_tokens", 0)
        self._total_tokens += tokens_used

        console.print(
            f"[dim]LLM [local_llama_cpp] "
            f"{elapsed_ms}ms | "
            f"tokens: {tokens_used} | "
            f"total: {self._total_tokens}[/]"
        )
        return text

    def chat_json(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict:
        """Send chat request, parse JSON from response (robust extraction)."""
        raw = self.chat(messages, temperature, max_tokens)
        return _extract_json(raw)

    @property
    def stats(self) -> dict:
        return {
            "backend": self.config.backend.value,
            "model": self.config.model,
            "requests": self._request_count,
            "total_tokens": self._total_tokens,
        }

    @staticmethod
    def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
        """Convert OpenAI-style messages to a single prompt string for llama-cpp."""
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                parts.append(f"<|system|>\n{content}")
            elif role == "user":
                parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}")
        parts.append("<|assistant|>")
        return "\n".join(parts)

    def close(self):
        if self._client:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response with multiple fallback strategies."""
    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: extract from ```json ... ``` block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        try:
            return json.loads(text[start:end].strip())
        except json.JSONDecodeError:
            pass

    # Strategy 3: find first { ... } block
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

    raise ValueError(f"Failed to extract JSON from LLM response:\n{text[:300]}...")

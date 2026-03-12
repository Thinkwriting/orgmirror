"""LLM Backend 抽象层 — 支持多种 LLM 后端"""

from __future__ import annotations

import asyncio
import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """LLM 调用结果"""
    text: str
    input_tokens: int
    output_tokens: int


class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    @abstractmethod
    async def chat(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """调用 LLM 并返回结果"""
        ...


class AnthropicBackend(LLMBackend):
    """Anthropic API 后端（使用 anthropic SDK）"""

    def __init__(self, api_key: Optional[str] = None):
        try:
            import anthropic
        except ImportError:
            raise ImportError("需要安装 anthropic SDK: pip install anthropic")
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
        )

    async def chat(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        response = await self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text if response.content else ""
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


class OpenAIBackend(LLMBackend):
    """OpenAI 兼容 API 后端（支持 Codex/Cursor/GPT 等）"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        try:
            import openai
        except ImportError:
            raise ImportError("需要安装 openai SDK: pip install openai")
        self._client = openai.AsyncOpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
        )

    async def chat(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_message},
            ],
        )
        text = response.choices[0].message.content or "" if response.choices else ""
        usage = response.usage
        return LLMResponse(
            text=text,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )


class ClaudeCodeBackend(LLMBackend):
    """Claude Code subprocess 后端（调用本地 claude CLI，无需 API key）"""

    async def chat(
        self,
        system: str,
        user_message: str,
        model: str,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        # 将 system prompt 和 user message 合并为一个 prompt
        prompt = f"[System]\n{system}\n\n[User]\n{user_message}"

        cmd = ["claude", "-p", prompt, "--model", model]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "unknown error"
            raise RuntimeError(f"claude CLI 调用失败 (exit {proc.returncode}): {error_msg}")

        text = stdout.decode().strip()

        # Token 估算：字符数 / 4
        input_chars = len(system) + len(user_message)
        output_chars = len(text)

        return LLMResponse(
            text=text,
            input_tokens=input_chars // 4,
            output_tokens=output_chars // 4,
        )


def create_backend(
    backend_type: str = "anthropic",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMBackend:
    """工厂函数：根据类型创建 LLM 后端实例"""
    if backend_type == "anthropic":
        return AnthropicBackend(api_key=api_key)
    elif backend_type == "openai":
        return OpenAIBackend(api_key=api_key, base_url=base_url)
    elif backend_type == "claude-code":
        return ClaudeCodeBackend()
    else:
        raise ValueError(f"未知后端类型: {backend_type}，可用: anthropic, openai, claude-code")

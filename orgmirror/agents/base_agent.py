"""BaseAgent — 所有Agent的基类，自动集成 metrics 采集"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

import anthropic

from ..core.metrics import AgentLevel, AgentMetrics, MetricsCollector


class BaseAgent(ABC):
    """Agent基类。子类只需实现 system_prompt 和 process 方法。"""

    def __init__(
        self,
        agent_id: str,
        role: str,
        level: AgentLevel,
        system_prompt: str,
        model: str = "claude-sonnet-4-20250514",
        collector: Optional[MetricsCollector] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.level = level
        self.system_prompt = system_prompt
        self.model = model
        self.collector = collector
        self._client: Optional[anthropic.AsyncAnthropic] = None
        self.upstream: Optional[str] = None
        self.downstream_ids: list[str] = []

    @property
    def client(self) -> anthropic.AsyncAnthropic:
        if self._client is None:
            self._client = anthropic.AsyncAnthropic()
        return self._client

    async def run(self, input_text: str) -> str:
        """执行Agent，自动采集metrics"""
        metrics: Optional[AgentMetrics] = None
        if self.collector:
            metrics = self.collector.start_agent(self.agent_id, self.role, self.level)
            metrics.input_text = input_text
            metrics.upstream_agent = self.upstream
            metrics.downstream_agents = list(self.downstream_ids)

        output = await self._call_llm(input_text, metrics)

        if metrics and self.collector:
            metrics.output_text = output
            self.collector.finish_agent(metrics)

        return output

    async def _call_llm(self, input_text: str, metrics: Optional[AgentMetrics] = None) -> str:
        """调用 LLM 并提取 token 使用信息"""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.system_prompt,
            messages=[{"role": "user", "content": input_text}],
        )

        output = response.content[0].text if response.content else ""

        if metrics:
            metrics.input_tokens = response.usage.input_tokens
            metrics.output_tokens = response.usage.output_tokens

        return output

    def connect_downstream(self, *agents: BaseAgent):
        """建立下游连接关系"""
        for a in agents:
            self.downstream_ids.append(a.agent_id)
            a.upstream = self.agent_id

    def __repr__(self):
        return f"<{self.__class__.__name__} id={self.agent_id} role={self.role}>"

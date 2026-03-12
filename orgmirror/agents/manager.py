"""ManagerAgent — 管理型Agent，审批/汇报/转发"""

from __future__ import annotations

from typing import Optional

from ..core.llm_backend import LLMBackend
from ..core.metrics import AgentLevel, MetricsCollector
from .base_agent import BaseAgent


class ManagerAgent(BaseAgent):
    """管理层Agent：VP、总监、项目经理等。主要做审批、汇报、格式转换。"""

    def __init__(
        self,
        agent_id: str,
        role: str,
        level: AgentLevel,
        system_prompt: str,
        collector: MetricsCollector | None = None,
        model: str = "claude-sonnet-4-20250514",
        backend: Optional[LLMBackend] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            role=role,
            level=level,
            system_prompt=system_prompt,
            model=model,
            collector=collector,
            backend=backend,
        )

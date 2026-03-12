"""ReviewerAgent — 审查型Agent，评审/选择/质量控制"""

from __future__ import annotations

from typing import Optional

from ..core.llm_backend import LLMBackend
from ..core.metrics import AgentLevel, MetricsCollector
from .base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """审查型Agent：政委、总办评审、数据验证等。评估质量，选出赢家。"""

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

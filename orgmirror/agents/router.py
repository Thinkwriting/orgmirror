"""RouterAgent — 路由型Agent，任务分发/调度"""

from __future__ import annotations

from typing import Optional

from ..core.llm_backend import LLMBackend
from ..core.metrics import AgentLevel, MetricsCollector
from .base_agent import BaseAgent


class RouterAgent(BaseAgent):
    """路由型Agent：路由分发、中台调度等。分析任务并分配给合适的下游Agent。"""

    def __init__(
        self,
        agent_id: str,
        role: str,
        system_prompt: str,
        collector: MetricsCollector | None = None,
        model: str = "claude-sonnet-4-20250514",
        backend: Optional[LLMBackend] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            role=role,
            level=AgentLevel.ROUTER,
            system_prompt=system_prompt,
            model=model,
            collector=collector,
            backend=backend,
        )

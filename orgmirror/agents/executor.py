"""ExecutorAgent — 执行型Agent，实际产出内容"""

from ..core.metrics import AgentLevel, MetricsCollector
from .base_agent import BaseAgent


class ExecutorAgent(BaseAgent):
    """执行层Agent：直接产出代码、文档、分析等实际内容"""

    def __init__(
        self,
        agent_id: str,
        role: str,
        system_prompt: str,
        collector: MetricsCollector | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        super().__init__(
            agent_id=agent_id,
            role=role,
            level=AgentLevel.EXECUTION,
            system_prompt=system_prompt,
            model=model,
            collector=collector,
        )

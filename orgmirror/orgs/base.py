"""组织架构基类 — 定义Agent间的拓扑关系和执行流程"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from ..agents.base_agent import BaseAgent
from ..core.analyzer import ContributionAnalyzer
from ..core.llm_backend import LLMBackend
from ..core.metrics import MetricsCollector, TaskMetrics
from ..core.reporter import print_report


class OrgBase(ABC):
    """组织架构基类。每个组织模式（阿里/腾讯/字节）继承此类。"""

    org_mode: str = ""  # alibaba / tencent / bytedance
    org_name: str = ""

    def __init__(self, model: str = "claude-sonnet-4-20250514", backend: Optional[LLMBackend] = None):
        self.model = model
        self.backend = backend
        self.agents: dict[str, BaseAgent] = {}
        self.collector: MetricsCollector | None = None

    @abstractmethod
    def _build_agents(self, collector: MetricsCollector) -> dict[str, BaseAgent]:
        """构建该组织模式的所有Agent，返回 {agent_id: agent}"""
        ...

    @abstractmethod
    async def _execute(self, task: str) -> str:
        """执行任务，按组织架构的流程调度Agent"""
        ...

    async def run(self, task: str, task_id: str | None = None) -> TaskMetrics:
        """运行任务并返回分析后的指标"""
        if task_id is None:
            task_id = uuid.uuid4().hex[:8]

        self.collector = MetricsCollector(task_id, task, self.org_mode)
        self.agents = self._build_agents(self.collector)

        # 建立Agent间连接关系
        self._connect_agents()

        # 执行
        result = await self._execute(task)

        # 分析
        analyzer = ContributionAnalyzer()
        task_metrics = analyzer.analyze_task(self.collector.get_task_metrics())

        # 打印报告
        print_report(task_metrics)

        return task_metrics

    def _connect_agents(self):
        """子类可覆盖，建立Agent间的上下游关系"""
        pass

"""任务编排器 — 管理多组织模式的任务执行和对比"""

from __future__ import annotations

from typing import Optional

from ..core.llm_backend import LLMBackend
from ..core.metrics import TaskMetrics
from ..core.reporter import print_comparison, print_report
from ..orgs.base import OrgBase


class Orchestrator:
    """顶层编排器：选择组织模式，执行任务，生成对比报告"""

    def __init__(self, model: str = "claude-sonnet-4-20250514", backend: Optional[LLMBackend] = None):
        self.model = model
        self.backend = backend
        self._org_registry: dict[str, type[OrgBase]] = {}

    def register(self, org_cls: type[OrgBase]):
        """注册一个组织架构模式"""
        self._org_registry[org_cls.org_mode] = org_cls

    async def run_single(self, org_mode: str, task: str) -> TaskMetrics:
        """用指定的组织模式执行任务"""
        org_cls = self._org_registry.get(org_mode)
        if not org_cls:
            raise ValueError(f"未知组织模式: {org_mode}，可用: {list(self._org_registry.keys())}")

        org = org_cls(model=self.model, backend=self.backend)
        return await org.run(task)

    async def run_comparison(self, task: str, modes: list[str] | None = None) -> list[TaskMetrics]:
        """用多种组织模式执行同一任务，生成对比报告"""
        if modes is None:
            modes = list(self._org_registry.keys())

        results = []
        for mode in modes:
            metrics = await self.run_single(mode, task)
            results.append(metrics)

        if len(results) > 1:
            print_comparison(results)

        return results

    @property
    def available_modes(self) -> list[str]:
        return list(self._org_registry.keys())

"""字节模式 — 网状扁平制（8 Agent）

架构：
[用户] → [路由分发Agent] → 3个[执行Agent]并行
       → [数据验证Agent](AB测试) → [UG增长Agent] → 交付

特点：
- 无审批层，Context not Control
- 推荐算法思维分配任务
- AB测试思维验证产出
- 最扁平，传话筒最少
"""

from __future__ import annotations

import asyncio

from ..agents.executor import ExecutorAgent
from ..agents.reviewer import ReviewerAgent
from ..agents.router import RouterAgent
from ..core.metrics import AgentLevel, MetricsCollector
from .base import OrgBase


class ByteDanceOrg(OrgBase):
    org_mode = "bytedance"
    org_name = "字节模式（网状扁平制）"

    def _build_agents(self, collector: MetricsCollector) -> dict:
        agents = {}

        # 路由分发Agent — 推荐算法思维，直接把任务拆成子任务分配
        agents["router"] = RouterAgent(
            agent_id="router",
            role="路由分发",
            system_prompt=(
                "你是字节跳动的任务路由器。像推荐算法一样，将任务直接分配给最合适的执行者。\n"
                "不需要层层审批。直接将任务拆解为2-3个可并行的子任务。\n"
                "输出格式：\n"
                "子任务A: [描述]\n"
                "子任务B: [描述]\n"
                "子任务C: [描述]\n"
                "简洁、直接、不废话。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        # 3个执行Agent — 并行执行子任务
        for label in ["A", "B", "C"]:
            agents[f"exec_{label}"] = ExecutorAgent(
                agent_id=f"exec_{label}",
                role=f"执行者{label}",
                system_prompt=(
                    f"你是字节跳动的执行者{label}。你有完全的决策权和执行权，不需要请示任何人。\n"
                    "你的工作是完成分配给你的子任务，产出具体的代码、文档或分析。\n"
                    "追求效率和质量。不要写废话，直接给结果。\n"
                    "字节风格：高人才密度下的自我管理，你是Owner而非执行者。"
                ),
                collector=collector,
                model=self.model,
                backend=self.backend,
            )

        # 数据验证Agent — AB测试思维
        agents["validator"] = ReviewerAgent(
            agent_id="validator",
            role="数据验证",
            level=AgentLevel.EXECUTION,
            system_prompt=(
                "你是字节跳动的数据验证Agent。用AB测试思维评估多个执行者的产出。\n"
                "对比各执行者的产出质量，选出最佳方案或整合各方优点。\n"
                "输出：\n"
                "1. 各产出的质量评分\n"
                "2. 最终整合结果\n"
                "数据驱动，不搞人情。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        # UG增长Agent — 优化输出的传播性
        agents["ug"] = ExecutorAgent(
            agent_id="ug",
            role="增长优化",
            system_prompt=(
                "你是字节跳动的UG增长Agent。优化最终产出的传播性和用户体验。\n"
                "让输出更易读、更有吸引力、更有传播价值。\n"
                "但不要过度包装——内容为王。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        return agents

    def _connect_agents(self):
        a = self.agents
        a["router"].connect_downstream(a["exec_A"], a["exec_B"], a["exec_C"])
        a["exec_A"].connect_downstream(a["validator"])
        a["exec_B"].connect_downstream(a["validator"])
        a["exec_C"].connect_downstream(a["validator"])
        a["validator"].connect_downstream(a["ug"])

    async def _execute(self, task: str) -> str:
        a = self.agents

        # Step 1: 路由分发
        subtasks_text = await a["router"].run(f"任务：{task}")

        # Step 2: 3个执行Agent并行
        exec_results = await asyncio.gather(
            a["exec_A"].run(f"你负责的子任务来自以下拆解：\n{subtasks_text}\n\n请完成子任务A部分。"),
            a["exec_B"].run(f"你负责的子任务来自以下拆解：\n{subtasks_text}\n\n请完成子任务B部分。"),
            a["exec_C"].run(f"你负责的子任务来自以下拆解：\n{subtasks_text}\n\n请完成子任务C部分。"),
        )

        # Step 3: 数据验证（AB测试）
        validation_input = (
            f"原始任务：{task}\n\n"
            f"执行者A产出：\n{exec_results[0]}\n\n"
            f"执行者B产出：\n{exec_results[1]}\n\n"
            f"执行者C产出：\n{exec_results[2]}\n\n"
            "请评估并整合。"
        )
        validated = await a["validator"].run(validation_input)

        # Step 4: UG优化
        final = await a["ug"].run(
            f"原始任务：{task}\n\n验证后的产出：\n{validated}\n\n请优化传播性和可读性。"
        )

        return final

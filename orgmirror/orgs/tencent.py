"""腾讯模式 — 联邦赛马制（12 Agent）

架构：
[用户] → [总办共识] → BG-A团队(3人) + BG-B团队(3人) 赛马
       → [TEG底座] 为两队提供基础能力
       → [总办评审] 选出赢家
       → [CDG投资判断] 评估商业价值
       → 交付

特点：
- 赛马机制：同一任务双团队做，一方白干
- 总办共识讨论但不投票
- CDG评估但不执行
- 联邦制，BG高度自治
"""

from __future__ import annotations

import asyncio

from ..agents.executor import ExecutorAgent
from ..agents.manager import ManagerAgent
from ..agents.reviewer import ReviewerAgent
from ..agents.router import RouterAgent
from ..core.metrics import AgentLevel, MetricsCollector
from .base import OrgBase


class TencentOrg(OrgBase):
    org_mode = "tencent"
    org_name = "腾讯模式（联邦赛马制）"

    def _build_agents(self, collector: MetricsCollector) -> dict:
        a = {}

        # === 总办 ===
        a["zonban_consensus"] = ManagerAgent(
            agent_id="zonban_consensus",
            role="总办共识",
            level=AgentLevel.EXECUTIVE,
            system_prompt=(
                "你是腾讯总办。你的职责是：\n"
                "1. 讨论任务的战略价值\n"
                "2. 形成共识但不做具体决策\n"
                "3. 将任务同时下发给两个BG赛马\n"
                "经典风格：充分讨论、温和表态、不明确站队。"
            ),
            collector=collector, model=self.model,
        )

        # === BG-A 团队 ===
        a["bg_a_lead"] = ManagerAgent(
            agent_id="bg_a_lead",
            role="BG-A负责人",
            level=AgentLevel.MIDDLE,
            system_prompt="你是腾讯BG-A的负责人。带领团队完成任务，拿出最好的方案证明你的BG更强。",
            collector=collector, model=self.model,
        )
        a["bg_a_dev"] = ExecutorAgent(
            agent_id="bg_a_dev",
            role="BG-A开发",
            system_prompt="你是腾讯BG-A的开发。根据负责人的指示，产出高质量的实现。竭尽全力，这是赛马！",
            collector=collector, model=self.model,
        )
        a["bg_a_pm"] = ExecutorAgent(
            agent_id="bg_a_pm",
            role="BG-A产品",
            system_prompt="你是腾讯BG-A的产品经理。做需求分析和方案设计，帮团队赢得赛马。",
            collector=collector, model=self.model,
        )

        # === BG-B 团队（赛马对手）===
        a["bg_b_lead"] = ManagerAgent(
            agent_id="bg_b_lead",
            role="BG-B负责人",
            level=AgentLevel.MIDDLE,
            system_prompt="你是腾讯BG-B的负责人。你的团队也在做同样的任务，你必须比BG-A做得更好。",
            collector=collector, model=self.model,
        )
        a["bg_b_dev"] = ExecutorAgent(
            agent_id="bg_b_dev",
            role="BG-B开发",
            system_prompt="你是腾讯BG-B的开发。产出最好的实现，赛过BG-A。",
            collector=collector, model=self.model,
        )
        a["bg_b_pm"] = ExecutorAgent(
            agent_id="bg_b_pm",
            role="BG-B产品",
            system_prompt="你是腾讯BG-B的产品经理。拿出比BG-A更有创意的方案。",
            collector=collector, model=self.model,
        )

        # === TEG 技术底座 ===
        a["teg"] = ExecutorAgent(
            agent_id="teg",
            role="TEG底座",
            system_prompt=(
                "你是腾讯TEG。你的职责是提供基础技术��力（云服务、AI能力、数据处理）。\n"
                "你同时服务BG-A和BG-B，不参与赛马，只提供工具。"
            ),
            collector=collector, model=self.model,
        )
        a["teg"].level = AgentLevel.INFRA

        # === 总办评审 ===
        a["zonban_review"] = ReviewerAgent(
            agent_id="zonban_review",
            role="总办评审",
            level=AgentLevel.EXECUTIVE,
            system_prompt=(
                "你是腾讯总办评审。两个BG的产出都在这里了。\n"
                "1. 从用户价值、技术质量、创新性三个维度评估\n"
                "2. 选出赢家\n"
                "3. 说明选择理由\n"
                "公正评审，用数据说话。"
            ),
            collector=collector, model=self.model,
        )

        # === CDG 投资判断 ===
        a["cdg"] = ReviewerAgent(
            agent_id="cdg",
            role="CDG投资判断",
            level=AgentLevel.EXECUTIVE,
            system_prompt=(
                "你是腾讯CDG。你的职责是：\n"
                "1. 评估赢家方案的商业价值\n"
                "2. 给出投资/投入建议\n"
                "3. 提供市场视角的补充\n"
                "你评估但不执行。"
            ),
            collector=collector, model=self.model,
        )

        return a

    def _connect_agents(self):
        a = self.agents
        a["zonban_consensus"].connect_downstream(a["bg_a_lead"], a["bg_b_lead"])
        a["bg_a_lead"].connect_downstream(a["bg_a_dev"], a["bg_a_pm"])
        a["bg_b_lead"].connect_downstream(a["bg_b_dev"], a["bg_b_pm"])
        a["teg"].connect_downstream(a["bg_a_dev"], a["bg_b_dev"])
        a["zonban_review"].connect_downstream(a["cdg"])

    async def _execute(self, task: str) -> str:
        a = self.agents

        # Step 1: 总办共识
        consensus = await a["zonban_consensus"].run(f"新任务需要评估：{task}")

        # Step 2: TEG准备基础能力
        teg_support = await a["teg"].run(f"两个BG即将赛马，任务是：{task}\n请提供基础技术能力支撑。")

        # Step 3: 两个BG赛马（并行）
        bg_a_result, bg_b_result = await asyncio.gather(
            self._run_bg("a", task, consensus, teg_support),
            self._run_bg("b", task, consensus, teg_support),
        )

        # Step 4: 总办评审选赢家
        review = await a["zonban_review"].run(
            f"原始任务：{task}\n\n"
            f"BG-A产出：\n{bg_a_result}\n\n"
            f"BG-B产出：\n{bg_b_result}\n\n"
            "请评审并选出赢家。"
        )

        # 标记输家的token为赛马浪费（通过agent_id约定）
        self._mark_race_loser(review)

        # Step 5: CDG投资判断
        final = await a["cdg"].run(
            f"总办评审结果：{review}\n\n请给出商业价值评估和投入建议。"
        )

        return final

    async def _run_bg(self, bg: str, task: str, consensus: str, teg_support: str) -> str:
        """运行一个BG的完整流程"""
        a = self.agents
        prefix = f"bg_{bg}"

        lead_result = await a[f"{prefix}_lead"].run(
            f"总办共识：{consensus}\nTEG能力：{teg_support}\n任务：{task}\n请制定团队执行方案。"
        )

        pm_result, dev_result = await asyncio.gather(
            a[f"{prefix}_pm"].run(
                f"负责人方案：{lead_result}\n任务：{task}\n请做产品设计。"
            ),
            a[f"{prefix}_dev"].run(
                f"负责人方案：{lead_result}\nTEG能力：{teg_support}\n任务：{task}\n请做技术实现。"
            ),
        )

        return f"产品方案：{pm_result}\n\n技术实现：{dev_result}"

    def _mark_race_loser(self, review_text: str):
        """根据评审结果标记输家BG的metrics"""
        # 简单启发式：如果评审中提到BG-A赢/BG-B输，标记BG-B相关的agent
        review_lower = review_text.lower()
        loser_prefix = None

        if "bg-a" in review_lower and ("赢" in review_text or "胜" in review_text or "winner" in review_lower):
            loser_prefix = "bg_b"
        elif "bg-b" in review_lower and ("赢" in review_text or "胜" in review_text or "winner" in review_lower):
            loser_prefix = "bg_a"
        else:
            # 默认BG-B是输家（确保赛马浪费总被计算）
            loser_prefix = "bg_b"

        if self.collector and loser_prefix:
            for m in self.collector.task_metrics.agent_metrics:
                if m.agent_id.startswith(loser_prefix):
                    m._is_race_loser = True

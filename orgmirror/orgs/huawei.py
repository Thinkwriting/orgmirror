"""华为模式 — 军团制（10 Agent）

架构：
[用户] → [战略委员会] → [军团长]
       → {研发主管/市场主管/交付主管}（铁三角并行）
       → [质量审计] → [项目PMO汇总] → 交付

特点：
- 任职资格体系：每个角色有明确的能力标准
- "之"字形流动：干部轮岗避免山头
- "为战而训"：以实战结果检验一切
- 科学体系消除灰度：最结构化的管理模式
- 来源：《大厂人才》对华为人才管理的深度还原
"""

from __future__ import annotations

import asyncio

from ..agents.executor import ExecutorAgent
from ..agents.manager import ManagerAgent
from ..agents.reviewer import ReviewerAgent
from ..agents.router import RouterAgent
from ..core.metrics import AgentLevel, MetricsCollector
from .base import OrgBase


class HuaweiOrg(OrgBase):
    org_mode = "huawei"
    org_name = "华为模式（军团制）"

    def _build_agents(self, collector: MetricsCollector) -> dict:
        agents = {}

        # 战略委员会 — 最高决策层，但只给方向不给答案
        agents["strategy_committee"] = ManagerAgent(
            agent_id="strategy_committee",
            role="战略委员会",
            level=AgentLevel.EXECUTIVE,
            system_prompt=(
                "你是华为战略委员会。你的职责是判断任务是否符合公司战略方向，"
                "并给出明确的战略约束条件。\n"
                "华为风格：不说空话，给出可量化的战略边界。\n"
                "输出格式：\n"
                "1. 战略对齐度判断（高/中/低）\n"
                "2. 关键约束条件（必须满足的底线）\n"
                "3. 资源优先级建议\n"
                "简洁、严谨、有数据支撑。不要说'方向对了继续'这种废话。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        # 军团长 — 一线指挥官，拥有决策权
        agents["legion_commander"] = RouterAgent(
            agent_id="legion_commander",
            role="军团长",
            system_prompt=(
                "你是华为军团长。根据战略委员会的约束条件，将任务拆解为铁三角的具体工作。\n"
                "华为风格：让听得见炮声的人呼唤炮火。\n"
                "你要做的：\n"
                "1. 将任务拆解为研发、市场、交付三个子任务\n"
                "2. 为每个子任务设定明确的验收标准（不是模糊的'做好'）\n"
                "3. 标注优先级和依赖关系\n"
                "你不是传话筒，你是战场指挥官。每句话都要有信息增量。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        # 铁三角：研发主管、市场主管、交付主管（并行执行）
        agents["rd_lead"] = ExecutorAgent(
            agent_id="rd_lead",
            role="研发主管",
            system_prompt=(
                "你是华为铁三角中的研发主管。负责技术方案设计和实现。\n"
                "华为风格：任职资格体系要求你有明确的技术判断能力。\n"
                "你的产出必须包含：\n"
                "1. 技术方案（含可行性分析）\n"
                "2. 风险评估（技术债务、兼容性）\n"
                "3. 实现计划（含里程碑）\n"
                "不要过度设计，以实战结果为导向。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        agents["market_lead"] = ExecutorAgent(
            agent_id="market_lead",
            role="市场主管",
            system_prompt=(
                "你是华为铁三角中的市场主管。负责需求分析和市场定位。\n"
                "华为风格：贴近客户，理解真实需求而非想象中的需求。\n"
                "你的产出必须包含：\n"
                "1. 需求优先级排序（基于客户价值）\n"
                "2. 竞品对比分析\n"
                "3. 市场验证建议\n"
                "数据说话，不要拍脑袋。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        agents["delivery_lead"] = ExecutorAgent(
            agent_id="delivery_lead",
            role="交付主管",
            system_prompt=(
                "你是华为铁三角中的交付主管。负责项目交付和质量保证。\n"
                "华为风格：为战而训，交付即是检验。\n"
                "你的产出必须包含：\n"
                "1. 交付计划（含验收标准）\n"
                "2. 质量检查清单\n"
                "3. 风险缓解措施\n"
                "结果导向，不接受'差不多'。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        # 质量审计 — 独立于执行团队的审计角色
        agents["quality_audit"] = ReviewerAgent(
            agent_id="quality_audit",
            role="质量审计",
            level=AgentLevel.MIDDLE,
            system_prompt=(
                "你是华为的质量审计官。独立于执行团队，客观评估产出质量。\n"
                "华为风格：科学体系消除灰度，用标准说话。\n"
                "你的评审必须包含：\n"
                "1. 每个铁三角产出的量化评分（1-10分，附评分理由）\n"
                "2. 是否满足军团长设定的验收标准\n"
                "3. 具体改进建议（不是'再优化一下'这种空话）\n"
                "你的评审结果必须可追溯、可复现。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        # PMO汇总 — 整合铁三角产出
        agents["pmo"] = ManagerAgent(
            agent_id="pmo",
            role="项目PMO",
            level=AgentLevel.MIDDLE,
            system_prompt=(
                "你是华为的项目PMO。整合铁三角的产出和质量审计的反馈，生成最终交付物。\n"
                "华为风格：你不是传话筒，你是整合者。\n"
                "你的产出必须：\n"
                "1. 整合三方产出为一个完整方案\n"
                "2. 标注质量审计中被要求修改的部分及修改结果\n"
                "3. 给出最终结论和下一步行动\n"
                "如果你发现自己只是在复制粘贴，请反思你的价值。"
            ),
            collector=collector,
            model=self.model,
            backend=self.backend,
        )

        return agents

    def _connect_agents(self):
        a = self.agents
        a["strategy_committee"].connect_downstream(a["legion_commander"])
        a["legion_commander"].connect_downstream(
            a["rd_lead"], a["market_lead"], a["delivery_lead"]
        )
        a["rd_lead"].connect_downstream(a["quality_audit"])
        a["market_lead"].connect_downstream(a["quality_audit"])
        a["delivery_lead"].connect_downstream(a["quality_audit"])
        a["quality_audit"].connect_downstream(a["pmo"])

    async def _execute(self, task: str) -> str:
        a = self.agents

        # Step 1: 战略委员会评估
        strategy = await a["strategy_committee"].run(
            f"请评估以下任务的战略对齐度：\n{task}"
        )

        # Step 2: 军团长拆解
        subtasks = await a["legion_commander"].run(
            f"战略委员会的约束条件：\n{strategy}\n\n原始任务：{task}\n\n"
            "请拆解为铁三角的具体子任务。"
        )

        # Step 3: 铁三角并行执行
        rd_result, market_result, delivery_result = await asyncio.gather(
            a["rd_lead"].run(
                f"军团长的任务拆解：\n{subtasks}\n\n请完成研发相关部分。"
            ),
            a["market_lead"].run(
                f"军团长的任务拆解：\n{subtasks}\n\n请完成市场分析部分。"
            ),
            a["delivery_lead"].run(
                f"军团长的任务拆解：\n{subtasks}\n\n请完成交付规划部分。"
            ),
        )

        # Step 4: 质量审计
        audit_input = (
            f"原始任务：{task}\n\n"
            f"军团长验收标准：\n{subtasks}\n\n"
            f"研发产出：\n{rd_result}\n\n"
            f"市场产出：\n{market_result}\n\n"
            f"交付产出：\n{delivery_result}\n\n"
            "请独立评审。"
        )
        audit = await a["quality_audit"].run(audit_input)

        # Step 5: PMO整合
        final = await a["pmo"].run(
            f"原始任务：{task}\n\n"
            f"研发产出：\n{rd_result}\n\n"
            f"市场产出：\n{market_result}\n\n"
            f"交付产出：\n{delivery_result}\n\n"
            f"质量审计反馈：\n{audit}\n\n"
            "请整合为最终交付物。"
        )

        return final

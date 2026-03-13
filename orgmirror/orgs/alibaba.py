"""阿里模式 — 中台制（13 Agent）

架构：
[用户] → [合伙人委员会] → [VP战略] → [中台调度]
       → [数据中台][技术中台][业务中台]
       → [政委审查]
       → [产品][开发][测试][运维] 前台业务
       → [项目经理] → [总监] → 交付

特点：
- 中台共享服务，前台轻量灵活
- 政委/HR文化审查
- 多层审批链
- 预期大量传话筒
"""

from __future__ import annotations

from ..agents.executor import ExecutorAgent
from ..agents.manager import ManagerAgent
from ..agents.reviewer import ReviewerAgent
from ..agents.router import RouterAgent
from ..core.metrics import AgentLevel, MetricsCollector
from .base import OrgBase


class AlibabaOrg(OrgBase):
    org_mode = "alibaba"
    org_name = "阿里模式（中台制）"

    def _build_agents(self, collector: MetricsCollector) -> dict:
        a = {}

        # === 高管层 ===
        a["partner_committee"] = ManagerAgent(
            agent_id="partner_committee",
            role="合伙人委员会",
            level=AgentLevel.EXECUTIVE,
            system_prompt=(
                "你是阿里巴巴合伙人委员会。你的职责是：\n"
                "1. 确认任务与集团战略方向一致\n"
                "2. 给出战略级指导意见\n"
                "3. 将任务授权给VP执行\n"
                "你的输出应该是高层战略视角的指导。"
            ),
            collector=collector, model=self.model, backend=self.backend,
        )

        a["vp"] = ManagerAgent(
            agent_id="vp",
            role="VP战略",
            level=AgentLevel.EXECUTIVE,
            system_prompt=(
                "你是阿里巴巴的VP。你的职责是：\n"
                "1. 将合伙人的战略指导转化为可执行的方案\n"
                "2. 确定需要哪些中台能力支撑\n"
                "3. 将任务传递给中台调度\n"
                "经典口头禅：'方向对了，继续。'"
            ),
            collector=collector, model=self.model, backend=self.backend,
        )

        # === 中台层 ===
        a["zhongtai_dispatch"] = RouterAgent(
            agent_id="zhongtai_dispatch",
            role="中台调度",
            system_prompt=(
                "你是阿里巴巴的中台调度Agent。你的职责是：\n"
                "1. 分析任务需要哪些中台能力（数据/技术/业务）\n"
                "2. 协调各中台提供服务\n"
                "3. 将中台能力打包后交给前台业务团队"
            ),
            collector=collector, model=self.model, backend=self.backend,
        )

        for name, desc in [
            ("data_zhongtai", "数据中台：提供数据分析、用户画像、AB测试等数据能力"),
            ("tech_zhongtai", "技术中台：提供技术架构、基础服务、中间件等技术能力"),
            ("biz_zhongtai", "业务中台：提供通用业务逻辑、支付、营销等业务能力"),
        ]:
            a[name] = ExecutorAgent(
                agent_id=name,
                role=desc.split("：")[0],
                system_prompt=f"你是阿里巴巴的{desc}。根据需求提供你的专业能力支撑。",
                collector=collector, model=self.model, backend=self.backend,
            )
            # 中台是基础设施层
            a[name].level = AgentLevel.INFRA

        # === 政委审查 ===
        a["commissar"] = ReviewerAgent(
            agent_id="commissar",
            role="政委",
            level=AgentLevel.MIDDLE,
            system_prompt=(
                "你是阿里巴巴的政委（HRBP）。你拥有一票否决权。\n"
                "1. 审查方案是否符合阿里价值观（客户第一、团队合作、拥抱变化）\n"
                "2. 如果发现违背价值观，直接否决并要求重做\n"
                "3. 如果通过，明确标注'政委审查通过'并说明理由\n"
                "你不是建议者，你是把门人。你的否决权是真实的。\n"
                "《大厂人才》实证：政委体系在实际运作中常沦为权力寻租工具，"
                "审查结果多为'橄榄型'分布，缺乏区分度。"
            ),
            collector=collector, model=self.model, backend=self.backend,
        )

        # === 前台业务 ===
        for role_id, role_name, prompt in [
            ("product", "产品经理", "你是阿里巴巴的产品经理。将任务转化为产品需求文档，定义功能点和验收标准。"),
            ("developer", "开发工程师", "你是阿里巴巴的开发工程师。根据产品需求和中台能力，编写具体的代码实现。"),
            ("tester", "测试工程师", "你是阿里巴巴的测试工程师。编写测试用例，验证实现是否符合需求。"),
            ("ops", "运维工程师", "你是阿里巴巴的运维工程师。确保部署方案和运维监控完善。"),
        ]:
            a[role_id] = ExecutorAgent(
                agent_id=role_id,
                role=role_name,
                system_prompt=prompt,
                collector=collector, model=self.model, backend=self.backend,
            )

        # === 中层管理 ===
        a["pm"] = ManagerAgent(
            agent_id="pm",
            role="项目经理",
            level=AgentLevel.MIDDLE,
            system_prompt=(
                "你是阿里巴巴的项目经理。你全流程参与协调：\n"
                "1. 跟踪各执行者的进度和产出\n"
                "2. 协调跨团队依赖和资源冲突\n"
                "3. 汇总产出整理成汇报材料提交给总监\n"
                "你是各部门之间的协调者和信息枢纽。\n"
                "《大厂人才》实证：PM常沦为传话筒，真正协调价值被层层汇报消耗。"
            ),
            collector=collector, model=self.model, backend=self.backend,
        )

        a["director"] = ManagerAgent(
            agent_id="director",
            role="总监",
            level=AgentLevel.MIDDLE,
            system_prompt=(
                "你是阿里巴巴的总监。你的职责是：\n"
                "1. 审批项目经理的汇报\n"
                "2. 添加管理层视角的评论\n"
                "3. 将材料转发给VP\n"
                "你的核心价值是'审批通过'。"
            ),
            collector=collector, model=self.model, backend=self.backend,
        )

        return a

    def _connect_agents(self):
        a = self.agents
        a["partner_committee"].connect_downstream(a["vp"])
        a["vp"].connect_downstream(a["zhongtai_dispatch"])
        a["zhongtai_dispatch"].connect_downstream(
            a["data_zhongtai"], a["tech_zhongtai"], a["biz_zhongtai"]
        )
        a["commissar"].connect_downstream(a["product"])
        a["product"].connect_downstream(a["developer"])
        a["developer"].connect_downstream(a["tester"])
        a["tester"].connect_downstream(a["ops"])
        a["ops"].connect_downstream(a["pm"])
        a["pm"].connect_downstream(a["director"])

    async def _execute(self, task: str) -> str:
        a = self.agents

        # Step 1: 合伙人委员会 → VP
        strategy = await a["partner_committee"].run(f"新任务需要战略评估：{task}")
        vp_direction = await a["vp"].run(f"合伙人指示：{strategy}\n\n原始任务：{task}")

        # Step 2: 中台调度 → 三大中台
        dispatch = await a["zhongtai_dispatch"].run(
            f"VP方向：{vp_direction}\n任务：{task}\n请协调中台资源。"
        )
        data_support = await a["data_zhongtai"].run(f"中台调度需求：{dispatch}\n请提供数据能力支撑。")
        tech_support = await a["tech_zhongtai"].run(f"中台调度需求：{dispatch}\n请提供技术能力支撑。")
        biz_support = await a["biz_zhongtai"].run(f"中台调度需求：{dispatch}\n请提供业务能力支撑。")

        zhongtai_combined = f"数据中台：{data_support}\n技术中台：{tech_support}\n业务中台：{biz_support}"

        # Step 3: 政委审查
        commissar_review = await a["commissar"].run(
            f"请审查以下方案的价值观对齐情况：\nVP方向：{vp_direction}\n中台支撑：{zhongtai_combined}"
        )

        # Step 4: 前台业务执行链
        prd = await a["product"].run(
            f"任务：{task}\nVP方向：{vp_direction}\n中台能力：{zhongtai_combined}\n政委意见：{commissar_review}\n\n请输出产品需求。"
        )
        code = await a["developer"].run(f"产品需求：{prd}\n中台技术能力：{tech_support}\n\n请编写实现。")
        test = await a["tester"].run(f"产品需求：{prd}\n开发产出：{code}\n\n请编写测试。")
        deploy = await a["ops"].run(f"开发产出：{code}\n测试结果：{test}\n\n请制定运维方案。")

        # Step 5: 项目经理汇总 → 总监审批
        pm_report = await a["pm"].run(
            f"请汇总项目产出：\n产品需求：{prd}\n开发实现：{code}\n测试结果：{test}\n运维方案：{deploy}"
        )
        final = await a["director"].run(
            f"项目经理汇报：{pm_report}\n\n请审批并提交最终交付物。"
        )

        return final

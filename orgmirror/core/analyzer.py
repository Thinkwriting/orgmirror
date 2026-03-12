"""ContributionAnalyzer — 分析每个Agent的实际贡献度"""

from __future__ import annotations

from difflib import SequenceMatcher

from .metrics import AgentLevel, AgentMetrics, ContributionType, TaskMetrics


class ContributionAnalyzer:
    """分析引擎：计算每个Agent的信息增量、决策影响、可跳过性"""

    def analyze_task(self, task: TaskMetrics) -> TaskMetrics:
        """分析整个任务的所有Agent指标"""
        for m in task.agent_metrics:
            m.info_delta = self.calculate_info_delta(m.input_text, m.output_text)
            m.is_passthrough = m.info_delta < 0.15
            m.contribution_type = self.classify_contribution(m)

        # 计算决策影响（需要全局视角）
        self._calculate_decision_impacts(task)

        # 计算可跳过性
        for m in task.agent_metrics:
            m.skip_score = self._calculate_skip_score(m)

        # 汇总
        self._aggregate(task)
        return task

    @staticmethod
    def calculate_info_delta(input_text: str, output_text: str) -> float:
        """计算信息增量：输出中有多少是新增的 vs 复述的。
        0 = 纯复述，1 = 全新内容。"""
        if not input_text or not output_text:
            return 0.5  # 无法比较时给中间值

        # 使用 SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, input_text, output_text).ratio()
        # 相似度高 → 信息增量低
        delta = 1.0 - similarity
        return round(max(0.0, min(1.0, delta)), 3)

    def _calculate_decision_impacts(self, task: TaskMetrics):
        """计算每个Agent对下游的决策影响"""
        agent_map = {m.agent_id: m for m in task.agent_metrics}

        for m in task.agent_metrics:
            if not m.downstream_agents:
                # 末端Agent，如果是执行层则高影响
                m.decision_impact = 0.8 if m.agent_level == AgentLevel.EXECUTION else 0.3
                continue

            # 检查下游Agent的输出是否受到此Agent的影响
            downstream_deltas = []
            for did in m.downstream_agents:
                dm = agent_map.get(did)
                if dm:
                    # 如果下游Agent的输出跟此Agent的输出差异大，说明下游Agent有自己的贡献
                    # 如果差异小，说明此Agent的输出直接被采用
                    overlap = SequenceMatcher(None, m.output_text, dm.input_text).ratio()
                    downstream_deltas.append(overlap)

            if downstream_deltas:
                # 平均overlap越高，说明此Agent的输出确实被下游使用了
                m.decision_impact = round(sum(downstream_deltas) / len(downstream_deltas), 3)
            else:
                m.decision_impact = 0.3

    @staticmethod
    def _calculate_skip_score(m: AgentMetrics) -> float:
        """可跳过性：移除该Agent后任务能否正常完成。
        1.0 = 完全可以跳过，0.0 = 绝对不能跳过"""
        score = 0.0

        # 传话筒 → 高可跳过性
        if m.is_passthrough:
            score += 0.4

        # 信息增量低 → 可跳过
        score += (1.0 - m.info_delta) * 0.3

        # 决策影响低 → 可跳过
        score += (1.0 - m.decision_impact) * 0.3

        return round(max(0.0, min(1.0, score)), 3)

    @staticmethod
    def classify_contribution(m: AgentMetrics) -> ContributionType:
        """分类：核心贡献者/辅助者/传话筒/纯开销"""
        # 传话筒：信息增量极低
        if m.info_delta < 0.15:
            return ContributionType.PASSTHROUGH

        # 执行层 + 高信息增量 = 核心
        if m.agent_level == AgentLevel.EXECUTION and m.info_delta > 0.4:
            return ContributionType.CORE

        # 高管/中层但信息增量高 = 辅助
        if m.info_delta > 0.3:
            return ContributionType.HELPER

        # 其余 = 开销
        return ContributionType.OVERHEAD

    @staticmethod
    def _aggregate(task: TaskMetrics):
        """计算任务级汇总指标"""
        if not task.agent_metrics:
            return

        task.total_tokens = sum(m.total_tokens for m in task.agent_metrics)
        task.total_wall_time_ms = sum(m.wall_time_ms for m in task.agent_metrics)
        task.passthrough_count = sum(1 for m in task.agent_metrics if m.is_passthrough)

        if task.total_tokens == 0:
            return

        # 按层级计算token占比
        level_tokens = {}
        for m in task.agent_metrics:
            level_tokens.setdefault(m.agent_level, 0)
            level_tokens[m.agent_level] += m.total_tokens

        task.executive_token_ratio = round(
            level_tokens.get(AgentLevel.EXECUTIVE, 0) / task.total_tokens, 3
        )
        task.middle_token_ratio = round(
            level_tokens.get(AgentLevel.MIDDLE, 0) / task.total_tokens, 3
        )
        task.execution_token_ratio = round(
            level_tokens.get(AgentLevel.EXECUTION, 0) / task.total_tokens, 3
        )

        # 赛马浪费率（腾讯模式专用 — 被淘汰的BG的token占比）
        if task.org_mode == "tencent":
            loser_tokens = sum(
                m.total_tokens for m in task.agent_metrics
                if "loser" in m.agent_id.lower() or (
                    hasattr(m, '_is_race_loser') and m._is_race_loser
                )
            )
            task.waste_ratio = round(loser_tokens / task.total_tokens, 3) if task.total_tokens else 0.0

"""AgentMetrics 数据采集层 — 每个Agent调用自动记录效率数据"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AgentLevel(str, Enum):
    EXECUTIVE = "executive"    # 高管层（VP、合伙人、总办）
    MIDDLE = "middle"          # 中层（总监、项目经理、政委）
    EXECUTION = "execution"    # 执行层（开发、测试、运维）
    INFRA = "infra"            # 基础设施（中台、TEG底座）
    ROUTER = "router"          # 路由/分发


class ContributionType(str, Enum):
    CORE = "core"              # 核心贡献者 — 产出实质内容
    HELPER = "helper"          # 辅助者 — 有增值但非核心
    PASSTHROUGH = "passthrough" # 传话筒 — 输入≈输出
    OVERHEAD = "overhead"      # 纯开销 — 消耗token但无产出


@dataclass
class AgentMetrics:
    """单次Agent调用的效率数据"""
    agent_id: str
    agent_role: str
    agent_level: AgentLevel
    org_mode: str  # alibaba / tencent / bytedance

    # Token 消耗
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # 内容指纹
    input_content_hash: str = ""
    output_content_hash: str = ""

    # 效率指标
    info_delta: float = 0.0          # 信息增量 0~1
    decision_impact: float = 0.0     # 决策影响 0~1
    skip_score: float = 0.0          # 可跳过性 0~1
    contribution_type: ContributionType = ContributionType.OVERHEAD

    # 时间
    wall_time_ms: int = 0
    start_time: float = 0.0
    end_time: float = 0.0

    # 传话筒检测
    is_passthrough: bool = False

    # 上下文
    input_text: str = ""
    output_text: str = ""
    upstream_agent: Optional[str] = None
    downstream_agents: list[str] = field(default_factory=list)

    def finalize(self):
        """在Agent执行完毕后计算衍生指标"""
        self.total_tokens = self.input_tokens + self.output_tokens
        self.wall_time_ms = int((self.end_time - self.start_time) * 1000)
        self.input_content_hash = _content_hash(self.input_text)
        self.output_content_hash = _content_hash(self.output_text)


@dataclass
class TaskMetrics:
    """整个任务的汇总指标"""
    task_id: str
    task_description: str
    org_mode: str
    agent_metrics: list[AgentMetrics] = field(default_factory=list)

    # 汇总指标（由 analyzer 填充）
    total_tokens: int = 0
    total_wall_time_ms: int = 0
    executive_token_ratio: float = 0.0
    middle_token_ratio: float = 0.0
    execution_token_ratio: float = 0.0
    passthrough_count: int = 0
    waste_ratio: float = 0.0  # 腾讯赛马浪费率

    def add(self, m: AgentMetrics):
        self.agent_metrics.append(m)


class MetricsCollector:
    """全局指标收集器 — 管理一次任务运行中所有Agent的指标"""

    def __init__(self, task_id: str, task_description: str, org_mode: str):
        self.task_metrics = TaskMetrics(
            task_id=task_id,
            task_description=task_description,
            org_mode=org_mode,
        )

    def start_agent(self, agent_id: str, agent_role: str, agent_level: AgentLevel) -> AgentMetrics:
        """开始记录一个Agent的执行"""
        m = AgentMetrics(
            agent_id=agent_id,
            agent_role=agent_role,
            agent_level=agent_level,
            org_mode=self.task_metrics.org_mode,
            start_time=time.time(),
        )
        return m

    def finish_agent(self, m: AgentMetrics):
        """结束一个Agent的执行并归档"""
        m.end_time = time.time()
        m.finalize()
        self.task_metrics.add(m)

    def get_task_metrics(self) -> TaskMetrics:
        return self.task_metrics


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16] if text else ""

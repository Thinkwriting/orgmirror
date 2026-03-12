"""效率审计报告生成器 — 终端版"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .metrics import AgentLevel, ContributionType, TaskMetrics

console = Console()

# 贡献类型的 emoji 和颜色
CONTRIB_STYLE = {
    ContributionType.CORE: ("🟢", "green", "核心贡献者"),
    ContributionType.HELPER: ("🟡", "yellow", "辅助者"),
    ContributionType.PASSTHROUGH: ("🟠", "dark_orange", "传话筒"),
    ContributionType.OVERHEAD: ("🔴", "red", "纯开销"),
}

LEVEL_LABEL = {
    AgentLevel.EXECUTIVE: "高管层",
    AgentLevel.MIDDLE: "中层",
    AgentLevel.EXECUTION: "执行层",
    AgentLevel.INFRA: "基础设施",
    AgentLevel.ROUTER: "路由",
}

ORG_LABEL = {
    "alibaba": "阿里模式（中台制）",
    "tencent": "腾讯模式（联邦赛马制）",
    "bytedance": "字节模式（网状扁平制）",
}


def print_report(task: TaskMetrics):
    """打印完整的效率审计报告"""
    console.print()
    console.print(Panel(
        f"[bold]📋 任务[/bold]: {task.task_description}\n"
        f"[bold]🏢 架构[/bold]: {ORG_LABEL.get(task.org_mode, task.org_mode)}\n"
        f"[bold]🎫 总Token[/bold]: {task.total_tokens:,}\n"
        f"[bold]⏱️  总耗时[/bold]: {task.total_wall_time_ms:,}ms",
        title="[bold cyan]🔍 重生之我在大厂当高管 — 效率审计报告[/bold cyan]",
        border_style="cyan",
    ))

    _print_contribution_ranking(task)
    _print_management_overhead(task)
    _print_passthrough_detection(task)
    _print_what_if_cut(task)

    if task.org_mode == "tencent":
        _print_race_waste(task)
    if task.org_mode == "alibaba":
        _print_zhongtai_delay(task)

    console.print()


def _print_contribution_ranking(task: TaskMetrics):
    """Agent 贡献排行榜"""
    table = Table(title="📊 Agent 贡献排行榜", show_header=True, header_style="bold")
    table.add_column("排名", style="dim", width=4)
    table.add_column("角色", width=16)
    table.add_column("层级", width=8)
    table.add_column("Token", justify="right", width=8)
    table.add_column("信息增量", justify="right", width=8)
    table.add_column("决策影响", justify="right", width=8)
    table.add_column("可跳过性", justify="right", width=8)
    table.add_column("评级", width=12)

    # 按信息增量*决策影响降序排列
    sorted_agents = sorted(
        task.agent_metrics,
        key=lambda m: m.info_delta * m.decision_impact,
        reverse=True,
    )

    for i, m in enumerate(sorted_agents, 1):
        emoji, color, label = CONTRIB_STYLE[m.contribution_type]
        table.add_row(
            str(i),
            m.agent_role,
            LEVEL_LABEL.get(m.agent_level, str(m.agent_level)),
            str(m.total_tokens),
            f"{m.info_delta:.1%}",
            f"{m.decision_impact:.1%}",
            f"{m.skip_score:.1%}",
            Text(f"{emoji} {label}", style=color),
        )

    console.print(table)


def _print_management_overhead(task: TaskMetrics):
    """管理层开销率"""
    console.print()
    overhead = task.executive_token_ratio + task.middle_token_ratio
    color = "green" if overhead < 0.3 else "yellow" if overhead < 0.5 else "red"
    console.print(Panel(
        f"高管层 Token 占比: [bold]{task.executive_token_ratio:.1%}[/bold]\n"
        f"中层 Token 占比:   [bold]{task.middle_token_ratio:.1%}[/bold]\n"
        f"执行层 Token 占比: [bold]{task.execution_token_ratio:.1%}[/bold]\n"
        f"──────────────────\n"
        f"管理层总开销:      [bold {color}]{overhead:.1%}[/bold {color}]",
        title="[bold]🏢 管理层开销率[/bold]",
    ))


def _print_passthrough_detection(task: TaskMetrics):
    """传话筒检测"""
    passthroughs = [m for m in task.agent_metrics if m.is_passthrough]
    if not passthroughs:
        console.print(Panel(
            "[green]未检测到传话筒Agent ✓[/green]",
            title="[bold]📢 传话筒检测[/bold]",
        ))
        return

    lines = []
    for m in passthroughs:
        lines.append(
            f"[red]⚠️  {m.agent_role}[/red] — "
            f"信息增量仅 {m.info_delta:.1%}，消耗 {m.total_tokens} tokens"
        )
    console.print(Panel(
        "\n".join(lines),
        title=f"[bold]📢 传话筒检测 — 发现 {len(passthroughs)} 个[/bold]",
    ))


def _print_what_if_cut(task: TaskMetrics):
    """如果砍掉XX — 模拟移除高可跳过性Agent"""
    skippable = [m for m in task.agent_metrics if m.skip_score > 0.6]
    if not skippable:
        return

    saved_tokens = sum(m.total_tokens for m in skippable)
    saved_pct = saved_tokens / task.total_tokens if task.total_tokens else 0

    lines = []
    for m in sorted(skippable, key=lambda x: x.skip_score, reverse=True):
        lines.append(f"  砍掉 [{m.agent_role}] → 节省 {m.total_tokens} tokens（可跳过性 {m.skip_score:.0%}）")

    console.print(Panel(
        "\n".join(lines) + f"\n\n[bold]💰 合计可节省: {saved_tokens:,} tokens ({saved_pct:.1%})[/bold]",
        title="[bold]✂️  如果砍掉这些Agent…[/bold]",
    ))


def _print_race_waste(task: TaskMetrics):
    """腾讯专属：赛马浪费率"""
    console.print(Panel(
        f"赛马浪费率: [bold red]{task.waste_ratio:.1%}[/bold red]\n"
        f"（被淘汰的BG的Token消耗占总消耗比例）",
        title="[bold]🏇 赛马浪费率（腾讯模式专属）[/bold]",
    ))


def _print_zhongtai_delay(task: TaskMetrics):
    """阿里专属：中台响应延迟"""
    infra_agents = [m for m in task.agent_metrics if m.agent_level == AgentLevel.INFRA]
    if not infra_agents:
        return
    infra_time = sum(m.wall_time_ms for m in infra_agents)
    ratio = infra_time / task.total_wall_time_ms if task.total_wall_time_ms else 0
    console.print(Panel(
        f"中台Agent总耗时: [bold]{infra_time:,}ms[/bold]\n"
        f"占总耗时比例:     [bold yellow]{ratio:.1%}[/bold yellow]",
        title="[bold]🏗️  中台响应延迟（阿里模式专属）[/bold]",
    ))


def print_comparison(tasks: list[TaskMetrics]):
    """打印多架构对比报告"""
    console.print()
    table = Table(title="⚔️ 架构效率对比", show_header=True, header_style="bold cyan")
    table.add_column("指标", width=20)
    for t in tasks:
        table.add_column(ORG_LABEL.get(t.org_mode, t.org_mode), width=20)

    table.add_row("总Token",
                  *[f"{t.total_tokens:,}" for t in tasks])
    table.add_row("总耗时(ms)",
                  *[f"{t.total_wall_time_ms:,}" for t in tasks])
    table.add_row("Agent数量",
                  *[str(len(t.agent_metrics)) for t in tasks])
    table.add_row("传话筒数量",
                  *[f"[red]{t.passthrough_count}[/red]" if t.passthrough_count else "[green]0[/green]"
                    for t in tasks])
    table.add_row("管理层开销",
                  *[f"{t.executive_token_ratio + t.middle_token_ratio:.1%}" for t in tasks])
    table.add_row("执行层占比",
                  *[f"{t.execution_token_ratio:.1%}" for t in tasks])

    console.print(table)

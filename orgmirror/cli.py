"""OrgMirror CLI — 命令行入口"""

from __future__ import annotations

import argparse
import asyncio

from .core.orchestrator import Orchestrator
from .orgs.alibaba import AlibabaOrg
from .orgs.bytedance import ByteDanceOrg
from .orgs.tencent import TencentOrg


def build_orchestrator(model: str = "claude-sonnet-4-20250514") -> Orchestrator:
    orch = Orchestrator(model=model)
    orch.register(ByteDanceOrg)
    orch.register(AlibabaOrg)
    orch.register(TencentOrg)
    return orch


async def async_main(args: argparse.Namespace):
    orch = build_orchestrator(model=args.model)

    if args.compare:
        await orch.run_comparison(args.task, modes=args.modes or None)
    else:
        mode = (args.modes or ["bytedance"])[0]
        await orch.run_single(mode, args.task)


def main():
    parser = argparse.ArgumentParser(
        description="OrgMirror — 大厂效率审计 AI Multi-Agent 组织效率照妖镜"
    )
    parser.add_argument("task", help="要执行的任务描述")
    parser.add_argument(
        "-m", "--modes", nargs="+",
        choices=["bytedance", "alibaba", "tencent"],
        help="组织模式（可多选）",
    )
    parser.add_argument(
        "--compare", action="store_true",
        help="对比模式：用所有指定架构跑同一任务",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-20250514",
        help="LLM 模型名称",
    )
    args = parser.parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()

"""Demo: 三种架构跑同一任务，生成对比报告"""

import asyncio

from orgmirror.cli import build_orchestrator


async def main():
    orch = build_orchestrator()

    # 简单任务测试
    task = "写一个Python函数，实现快速排序算法，包含注释和复杂度分析"

    print("=" * 60)
    print(f"📋 任务: {task}")
    print("=" * 60)

    # 方式1: 只跑字节模式
    # await orch.run_single("bytedance", task)

    # 方式2: 三种架构对比
    await orch.run_comparison(task)


if __name__ == "__main__":
    asyncio.run(main())

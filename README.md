# 🔍 OrgMirror — 大厂效率审计 AI Agent 照妖镜

> **大厂到底有多少中层是不干活的？让 AI Agent 替你算清楚。**

OrgMirror 将阿里、腾讯、字节三大互联网公司的组织架构映射为 AI Multi-Agent 系统，用同一个任务跑三套架构，自动生成**效率审计报告**——哪些 Agent 真干活了，哪些只是传话筒。

## 🎯 核心卖点

不是又一个 Multi-Agent 框架。核心是**组织效率的照妖镜**：

- 📊 **贡献度报告** — 每个 Agent 的信息增量、决策影响、可跳过性一目了然
- 🏇 **赛马浪费率** — 腾讯模式下，被淘汰的 BG 浪费了多少 token？
- 🏗️ **中台响应延迟** — 阿里模式下，中台到底帮忙还是添乱？
- ✂️ **如果砍掉 XX** — 模拟裁掉某个 Agent，效率能提升多少？
- ⚔️ **三架构对比** — 同一任务，三种组织模式的效率 PK

## 🏢 三套组织架构

### 字节模式（网状扁平制）— 8 Agent
```
用户 → 路由分发 → 执行者A/B/C（并行）→ 数据验证（AB测试）→ UG增长 → 交付
```
**最扁平**。无审批层，Context not Control。预期传话筒最少。

### 阿里模式（中台制）— 13 Agent
```
用户 → 合伙人委员会 → VP → 中台调度 → 三大中台
     → 政委审查 → 产品/开发/测试/运维 → 项目经理 → 总监 → 交付
```
**最层级化**。中台共享 + 政委文化审查 + 多层审批链。预期传话筒最多。

### 腾讯模式（联邦赛马制）— 12 Agent
```
用户 → 总办共识 → BG-A团队 + BG-B团队（赛马）→ TEG底座
     → 总办评审（选赢家）→ CDG投资判断 → 交付
```
**最浪费**。赛马机制 = 同一任务做两遍，一方全部白干。但可能出更好的结果。

## 📊 效率审计报告示例

```
🔍 效率审计报告 — OrgMirror
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 任务: 写一个快速排序算法
🏢 架构: 阿里模式（中台制）
🎫 总Token: 12,847
⏱️  总耗时: 34,200ms

📊 Agent 贡献排行榜
┌──┬──────────────┬──────────┬────────┬────────┬────────┬──────────┐
│# │ Agent        │ 信息增量  │ 决策影响│ 可跳过性│ Token  │ 评级     │
├──┼──────────────┼──────────┼────────┼────────┼────────┼──────────┤
│1 │ developer    │ 72.3%    │ 85.0%  │ 12.0%  │ 2,341  │ 🟢核心   │
│2 │ tester       │ 65.1%    │ 70.0%  │ 18.0%  │ 1,856  │ 🟢核心   │
│3 │ product      │ 48.7%    │ 60.0%  │ 25.0%  │ 1,423  │ 🟡辅助   │
│..│ ...          │          │        │        │        │          │
│11│ director     │ 8.2%     │ 15.0%  │ 82.0%  │ 890    │ 🟠传话筒  │
│12│ commissar    │ 5.1%     │ 5.0%   │ 91.0%  │ 756    │ 🔴纯开销  │
│13│ vp           │ 3.4%     │ 10.0%  │ 88.0%  │ 1,102  │ 🟠传话筒  │
└──┴──────────────┴──────────┴────────┴────────┴────────┴──────────┘

🏢 管理层开销率
  高管层 Token 占比: 23.4%
  中层 Token 占比:   19.8%
  执行层 Token 占比: 41.2%
  管理层总开销:      43.2% ⚠️

📢 传话筒检测 — 发现 3 个
  ⚠️ director (总监) — 信息增量仅 8.2%，消耗 890 tokens
  ⚠️ vp (VP战略) — 信息增量仅 3.4%，消耗 1,102 tokens
  ⚠️ commissar (政委) — 信息增量仅 5.1%，消耗 756 tokens

✂️ 如果砍掉这些Agent…
  砍掉 [commissar] → 节省 756 tokens（可跳过性 91%）
  砍掉 [vp] → 节省 1,102 tokens（可跳过性 88%）
  砍掉 [director] → 节省 890 tokens（可跳过性 82%）
  💰 合计可节省: 2,748 tokens (21.4%)
```

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/yourname/orgmirror.git
cd orgmirror
pip install -e .
```

需要设置 Anthropic API Key：
```bash
export ANTHROPIC_API_KEY=your-key-here
```

### 使用

```bash
# 用字节模式跑一个任务
orgmirror "写一个Python快速排序" -m bytedance

# 用阿里模式
orgmirror "设计一个用户注册API" -m alibaba

# 三种架构对比（核心玩法）
orgmirror "做一个竞品分析报告" --compare

# 指定多种架构对比
orgmirror "写一个排序函数" -m bytedance alibaba --compare
```

### Python API

```python
import asyncio
from orgmirror.cli import build_orchestrator

async def main():
    orch = build_orchestrator()

    # 单架构
    metrics = await orch.run_single("bytedance", "写一个快速排序")

    # 三架构对比
    results = await orch.run_comparison("写一个快速排序")

asyncio.run(main())
```

## ⚔️ 三架构对比结果（预期）

| 指标 | 字节（扁平） | 阿里（中台） | 腾讯（赛马） |
|------|------------|------------|------------|
| Agent 数量 | 8 | 13 | 12 |
| 总 Token | ⭐ 最少 | 最多 | 中等 |
| 传话筒数量 | 0-1 | 3-5 | 1-2 |
| 管理层开销 | <15% | >40% | ~25% |
| 赛马浪费 | 0% | 0% | ~30% |
| 执行效率 | ⭐ 最高 | 最低 | 中等 |
| 产出质量 | 高 | 高 | ⭐ 可能最高 |

**核心发现**：字节模式在简单任务上碾压，但复杂任务中腾讯的赛马可能产出更好的结果——代价是 30% 的 token 浪费。阿里模式的政委和多层审批在任何任务中都是纯开销。

## 🏗️ 架构

```
orgmirror/
├── core/
│   ├── metrics.py      # 数据采集层 — AgentMetrics
│   ├── analyzer.py     # 分析引擎 — ContributionAnalyzer
│   ├── reporter.py     # 报告生成（Rich终端版）
│   └── orchestrator.py # 任务编排器
├── agents/
│   ├── base_agent.py   # Agent基类（自动metrics采集）
│   ├── executor.py     # 执行型（开发、产品等）
│   ├── manager.py      # 管理型（VP、总监等）
│   ├── reviewer.py     # 审查型（政委、评审等）
│   └── router.py       # 路由型（分发、调度等）
├── orgs/
│   ├── base.py         # 组织架构基类
│   ├── bytedance.py    # 字节模式 — 8 Agent
│   ├── alibaba.py      # 阿里模式 — 13 Agent
│   └── tencent.py      # 腾讯模式 — 12 Agent
└── cli.py              # 命令行入口
```

## 🎭 灵感来源

- [edict](https://github.com/cft0808/edict) — 用三省六部制映射 AI Agent，古今对照
- **OrgMirror** — 用大厂组织架构映射 AI Agent，效率照妖

核心差异：edict 卖的是文化自豪感，我们卖的是**对中层管理的不满共鸣**。

## 📅 Roadmap

- [x] Phase 1: 项目基础 + 三种组织模式
- [ ] Phase 2: OpenClaw 平台集成
- [ ] Phase 3: 实时看板（军机处升级版）
- [ ] Phase 4: 传播优化（自动生成可分享内容）
- [ ] Phase 5: 自定义组织架构（输入你公司的org chart）

## License

MIT

"""端到端测试 — 用 mock LLM 验证整个流程"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from orgmirror.cli import build_orchestrator
from orgmirror.core.metrics import ContributionType


def make_mock_response(text: str, input_tokens: int = 100, output_tokens: int = 200):
    """创建模拟的 Anthropic API 响应"""
    resp = MagicMock()
    content_block = MagicMock()
    content_block.text = text
    resp.content = [content_block]
    resp.usage = MagicMock()
    resp.usage.input_tokens = input_tokens
    resp.usage.output_tokens = output_tokens
    return resp


class TestByteDanceE2E(unittest.TestCase):
    """字节模式端到端测试"""

    @patch("orgmirror.agents.base_agent.anthropic.AsyncAnthropic")
    def test_bytedance_full_run(self, mock_anthropic_cls):
        mock_client = MagicMock()

        # 模拟不同角色的不同输出
        responses = {
            "路由": make_mock_response(
                "子任务A: 实现partition函数\n子任务B: 实现递归主体\n子任务C: 编写测试用例",
                50, 80
            ),
            "子任务A": make_mock_response(
                "def partition(arr, low, high):\n    pivot = arr[high]\n    i = low - 1\n    for j in range(low, high):\n        if arr[j] <= pivot:\n            i += 1\n            arr[i], arr[j] = arr[j], arr[i]\n    arr[i+1], arr[high] = arr[high], arr[i+1]\n    return i + 1",
                100, 300
            ),
            "子任务B": make_mock_response(
                "def quicksort(arr, low=0, high=None):\n    if high is None:\n        high = len(arr) - 1\n    if low < high:\n        pi = partition(arr, low, high)\n        quicksort(arr, low, pi - 1)\n        quicksort(arr, pi + 1, high)\n    return arr",
                100, 250
            ),
            "子任务C": make_mock_response(
                "import pytest\ndef test_quicksort():\n    assert quicksort([3,1,2]) == [1,2,3]\n    assert quicksort([]) == []\n    assert quicksort([1]) == [1]",
                100, 200
            ),
            "评估": make_mock_response(
                "评分：A=9/10 B=8/10 C=7/10\n整合结果：完整的快速排序实现含partition、递归主体和测试用例。时间复杂度O(nlogn)平均。",
                500, 400
            ),
            "优化": make_mock_response(
                "# 快速排序实现\n## 核心代码\n```python\ndef quicksort(arr)...\n```\n## 复杂度\n- 时间：O(nlogn) 平均\n- 空间：O(logn)",
                600, 350
            ),
        }

        call_count = [0]
        async def mock_create(**kwargs):
            call_count[0] += 1
            msg = kwargs.get("messages", [{}])[0].get("content", "")
            if "拆解" in kwargs.get("system", "") or "路由" in kwargs.get("system", ""):
                return responses["路由"]
            elif "子任务A" in msg:
                return responses["子任务A"]
            elif "子任务B" in msg:
                return responses["子任务B"]
            elif "子任务C" in msg:
                return responses["子任务C"]
            elif "评估" in kwargs.get("system", "") or "验证" in kwargs.get("system", ""):
                return responses["评估"]
            else:
                return responses["优化"]

        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=mock_create)
        mock_anthropic_cls.return_value = mock_client

        orch = build_orchestrator()
        metrics = asyncio.run(orch.run_single("bytedance", "写一个快速排序"))

        # 验证基本结构
        assert metrics.org_mode == "bytedance"
        assert len(metrics.agent_metrics) == 6  # router + 3 exec + validator + ug
        assert metrics.total_tokens > 0

        # 验证有执行层Agent
        exec_agents = [m for m in metrics.agent_metrics if m.agent_id.startswith("exec_")]
        assert len(exec_agents) == 3

        print(f"\n✅ ByteDance E2E: {len(metrics.agent_metrics)} agents, {metrics.total_tokens} tokens")
        print(f"   传话筒: {metrics.passthrough_count}")
        print(f"   管理层开销: {metrics.executive_token_ratio + metrics.middle_token_ratio:.1%}")


class TestAlibabaE2E(unittest.TestCase):
    """阿里模式端到端测试"""

    @patch("orgmirror.agents.base_agent.anthropic.AsyncAnthropic")
    def test_alibaba_full_run(self, mock_anthropic_cls):
        mock_client = MagicMock()

        # 阿里模式的关键：高管层和中层的输出应该跟输入很像（传话筒）
        async def mock_create(**kwargs):
            system = kwargs.get("system", "")
            msg = kwargs.get("messages", [{}])[0].get("content", "")

            if "合伙人" in system:
                return make_mock_response(
                    f"战略批准。该任务符合集团方向。请VP落实。原始任务：{msg[:100]}",
                    80, 120
                )
            elif "VP" in system:
                return make_mock_response(
                    f"方向对了，继续。请中台配合。{msg[:100]}",
                    150, 100  # 输入多输出少 — 典型传话筒
                )
            elif "调度" in system:
                return make_mock_response("需要数据中台做分析，技术中台提供框架，业务中台对接接口。", 200, 150)
            elif "数据中台" in system:
                return make_mock_response("数据分析结论：用户行为数据建议采用快速排序优化查询效率。", 100, 180)
            elif "技术中台" in system:
                return make_mock_response("技术方案：Python3.11+，使用Hoare partition scheme。", 100, 160)
            elif "业务中台" in system:
                return make_mock_response("业务接口：排序服务API，支持POST /sort 入参为数组。", 100, 140)
            elif "政委" in system:
                return make_mock_response(
                    "价值观审查通过。方案体现了客户第一和拥抱变化。建议加强团队协作精神。",
                    300, 120  # 大量输入，很少有用输出
                )
            elif "产品" in system:
                return make_mock_response(
                    "PRD: 功能-快速排序函数，输入-整数数组，输出-排序后数组，验收标准-时间O(nlogn)。",
                    200, 250
                )
            elif "开发" in system:
                return make_mock_response(
                    "def quicksort(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[len(arr)//2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quicksort(left) + middle + quicksort(right)",
                    300, 400
                )
            elif "测试" in system:
                return make_mock_response(
                    "测试用例：\n1. 空数组→[]\n2. 单元素→[1]\n3. 已排序→不变\n4. 逆序→正确排序\n5. 重复元素→正确处理\n全部PASS。",
                    400, 300
                )
            elif "运维" in system:
                return make_mock_response("部署方案：Docker容器化，K8s编排，Prometheus监控。", 300, 180)
            elif "项目经理" in system:
                return make_mock_response(
                    f"周报汇总：各模块进展顺利。产品需求已完成，开发已交付，测试全部通过，运维方案就绪。{msg[:50]}",
                    500, 200  # 大量输入，输出就是换个格式
                )
            elif "总监" in system:
                return make_mock_response(
                    f"审批通过。同意项目经理的汇报。建议持续优化。{msg[:80]}",
                    300, 100  # 典型传话筒
                )
            else:
                return make_mock_response("默认输出", 50, 50)

        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=mock_create)
        mock_anthropic_cls.return_value = mock_client

        orch = build_orchestrator()
        metrics = asyncio.run(orch.run_single("alibaba", "写一个快速排序"))

        assert metrics.org_mode == "alibaba"
        assert len(metrics.agent_metrics) == 13
        assert metrics.passthrough_count >= 1  # 至少总监应该被检测为传话筒

        print(f"\n✅ Alibaba E2E: {len(metrics.agent_metrics)} agents, {metrics.total_tokens} tokens")
        print(f"   传话筒: {metrics.passthrough_count}")
        print(f"   管理层开销: {metrics.executive_token_ratio + metrics.middle_token_ratio:.1%}")


class TestTencentE2E(unittest.TestCase):
    """腾讯模式端到端测试"""

    @patch("orgmirror.agents.base_agent.anthropic.AsyncAnthropic")
    def test_tencent_full_run(self, mock_anthropic_cls):
        mock_client = MagicMock()

        async def mock_create(**kwargs):
            system = kwargs.get("system", "")
            if "总办" in system and "评审" not in system:
                return make_mock_response("共识：该任务有价值，建议两个BG都试试看。不明确谁更合适。", 80, 130)
            elif "TEG" in system:
                return make_mock_response("基础能力：Python运行环境、CI/CD、性能测试工具已就绪。", 100, 150)
            elif "BG-A负责人" in system:
                return make_mock_response("BG-A方案：采用经典Lomuto partition，代码简洁易懂。", 200, 180)
            elif "BG-A开发" in system:
                return make_mock_response(
                    "def quicksort_a(arr, low, high):\n    if low < high:\n        pi = partition(arr, low, high)\n        quicksort_a(arr, low, pi-1)\n        quicksort_a(arr, pi+1, high)",
                    250, 350
                )
            elif "BG-A产品" in system:
                return make_mock_response("BG-A PRD：专注性能优化，支持大数据量���序。", 200, 220)
            elif "BG-B负责人" in system:
                return make_mock_response("BG-B方案：采用三路快排(Dutch National Flag)，处理重复元素更优。", 200, 200)
            elif "BG-B开发" in system:
                return make_mock_response(
                    "def quicksort_b(arr):\n    if len(arr) <= 1: return arr\n    pivot = arr[0]\n    less = [x for x in arr[1:] if x < pivot]\n    equal = [x for x in arr if x == pivot]\n    greater = [x for x in arr[1:] if x > pivot]\n    return quicksort_b(less) + equal + quicksort_b(greater)",
                    250, 380
                )
            elif "BG-B产品" in system:
                return make_mock_response("BG-B PRD：专注代码可读性和Pythonic风格，面向初学者友好。", 200, 210)
            elif "评审" in system:
                return make_mock_response(
                    "评审结果：BG-B赢。三路快排更Pythonic，处理重复元素性能更好。BG-A的in-place方案虽然内存更优但可读性不足。",
                    600, 300
                )
            elif "CDG" in system:
                return make_mock_response(
                    "投资评估：该排序方案可作为内部工具库一部分。建议投入2人月打磨。市场对排序库需求一般。",
                    400, 250
                )
            else:
                return make_mock_response("默认输出", 50, 50)

        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=mock_create)
        mock_anthropic_cls.return_value = mock_client

        orch = build_orchestrator()
        metrics = asyncio.run(orch.run_single("tencent", "写一个快速排序"))

        assert metrics.org_mode == "tencent"
        assert len(metrics.agent_metrics) == 10  # 总办+TEG+BG-A(3)+BG-B(3)+评审+CDG
        assert metrics.waste_ratio > 0  # 应该有赛马浪费

        print(f"\n✅ Tencent E2E: {len(metrics.agent_metrics)} agents, {metrics.total_tokens} tokens")
        print(f"   赛马浪费率: {metrics.waste_ratio:.1%}")
        print(f"   传话筒: {metrics.passthrough_count}")


class TestComparison(unittest.TestCase):
    """三架构对比测试"""

    @patch("orgmirror.agents.base_agent.anthropic.AsyncAnthropic")
    def test_comparison(self, mock_anthropic_cls):
        mock_client = MagicMock()

        async def mock_create(**kwargs):
            return make_mock_response("模拟输出：" + kwargs.get("system", "")[:50], 100, 200)

        mock_client.messages = MagicMock()
        mock_client.messages.create = AsyncMock(side_effect=mock_create)
        mock_anthropic_cls.return_value = mock_client

        orch = build_orchestrator()
        results = asyncio.run(orch.run_comparison("写一个快速排序"))

        assert len(results) == 3
        modes = {r.org_mode for r in results}
        assert modes == {"bytedance", "alibaba", "tencent"}

        print("\n✅ Comparison test passed — 3 architectures compared")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""
CRM-OrchSell 量化评估模块

提供系统化的量化评估工具，从5个核心维度评估Agent系统能力：
1. 任务拆解质量
2. 工具执行准确性
3. 反思验真有效性
4. LLM方案生成质量
5. 端到端性能
"""

from tests.eval.test_dataset import (
    TestCase,
    ReflectionTestCase,
    ToolQuery,
    TEST_CASES,
    REFLECTION_TEST_CASES,
    TOOL_TEST_QUERIES
)

from tests.eval.task_planning_eval import TaskPlanningEvaluator
from tests.eval.tool_accuracy_eval import ToolAccuracyEvaluator
from tests.eval.reflection_eval import ReflectionEvaluator
from tests.eval.proposal_quality_eval import ProposalQualityEvaluator
from tests.eval.e2e_performance_eval import E2EPerformanceEvaluator
from tests.eval.eval_report import EvalReportGenerator

__all__ = [
    "TestCase",
    "ReflectionTestCase",
    "ToolQuery",
    "TEST_CASES",
    "REFLECTION_TEST_CASES",
    "TOOL_TEST_QUERIES",
    "TaskPlanningEvaluator",
    "ToolAccuracyEvaluator",
    "ReflectionEvaluator",
    "ProposalQualityEvaluator",
    "E2EPerformanceEvaluator",
    "EvalReportGenerator"
]

"""
量化评估系统演示脚本

展示如何使用评估系统进行完整的量化评估。
可直接运行: python tests/eval/main_test.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from loguru import logger
logger.remove()
logger.add(sys.stdout, level="WARNING")

from tests.eval.task_planning_eval import TaskPlanningEvaluator
from tests.eval.tool_accuracy_eval import ToolAccuracyEvaluator
from tests.eval.reflection_eval import ReflectionEvaluator
from tests.eval.proposal_quality_eval import ProposalQualityEvaluator
from tests.eval.e2e_performance_eval import E2EPerformanceEvaluator
from tests.eval.eval_report import EvalReportGenerator
from tests.eval.test_dataset import TEST_CASES, REFLECTION_TEST_CASES, TOOL_TEST_QUERIES


async def main():
    print("=" * 60)
    print("  CRM-OrchSell 量化评估系统演示")
    print("=" * 60)
    print()

    # 1. 任务拆解评估
    print("[1/5] 运行任务拆解评估...")
    task_ev = TaskPlanningEvaluator()
    task_report = await task_ev.evaluate(TEST_CASES[:10])
    print(f"  ✓ 完成: {task_report.pass_rate:.1%} 通过率, {task_report.overall_task_type_accuracy:.1%} 类型准确率")

    # 2. 工具准确性评估
    print("[2/5] 运行工具准确性评估...")
    tool_ev = ToolAccuracyEvaluator()
    tool_report = await tool_ev.evaluate_all(TOOL_TEST_QUERIES[:5])
    print(f"  ✓ 完成: {tool_report.pass_rate:.1%} 通过率, {tool_report.overall_field_consistency:.1%} 字段一致率")

    # 3. 反思验真评估
    print("[3/5] 运行反思验真评估...")
    reflection_ev = ReflectionEvaluator()
    reflection_report = await reflection_ev.evaluate(REFLECTION_TEST_CASES)
    print(f"  ✓ 完成: TPR={reflection_report.roc_metrics.true_positive_rate:.1%}, FPR={reflection_report.roc_metrics.false_positive_rate:.1%}")

    # 4. 方案质量评估
    print("[4/5] 运行方案质量评估...")
    proposal_ev = ProposalQualityEvaluator()
    proposal_report = await proposal_ev.evaluate(TEST_CASES[:5])
    print(f"  ✓ 完成: {proposal_report.pass_rate:.1%} 通过率")

    # 5. 性能评估
    print("[5/5] 运行端到端性能评估...")
    perf_ev = E2EPerformanceEvaluator(num_runs_per_case=1)
    perf_report = await perf_ev.run_benchmark(TEST_CASES[:3])
    print(f"  ✓ 完成: P50={perf_report.latency_metric.p50_latency_ms:.0f}ms, 成功率={perf_report.status_distribution.success_rate:.1%}")

    # 生成综合报告
    print()
    print("-" * 60)
    print("生成综合评估报告...")

    generator = EvalReportGenerator()
    full_report = generator.generate_full_report(
        task_report=task_report,
        tool_report=tool_report,
        reflection_report=reflection_report,
        proposal_report=proposal_report,
        performance_report=perf_report
    )

    # 输出报告
    print()
    print("=" * 60)
    print(f"  综合评分: {full_report.overall_score.total_score}/100")
    print(f"  等级: {full_report.overall_score.grade}")
    print(f"  通过维度: {full_report.overall_score.passed_dimensions}/{full_report.overall_score.total_dimensions}")
    print("=" * 60)

    print()
    print("各维度得分:")
    for ds in full_report.overall_score.dimension_scores:
        status_icon = "✅" if ds["status"] == "passed" else ("⚠️" if ds["status"] == "warning" else "❌")
        status_text = {"passed": "通过", "warning": "警告", "failed": "失败"}.get(ds["status"], "")
        print(f"  {status_icon} {ds['name']}: {ds['score']}分 (权重 {ds['weight']:.0%})")

    if full_report.suggestions:
        print()
        print("改进建议 (Top 5):")
        for i, s in enumerate(full_report.suggestions[:5], 1):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s.priority, "⚪")
            print(f"  {i}. {priority_icon} [{s.dimension}] {s.issue}")
            print(f"     建议: {s.suggestion}")

    print()
    print("结论:")
    for c in full_report.conclusions:
        print(f"  - {c}")

    # 导出报告
    output_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(output_dir, exist_ok=True)

    md_path = os.path.join(output_dir, "demo_report.md")
    generator.export_markdown(full_report, md_path)
    print()
    print(f"报告已保存: {md_path}")

    return full_report


if __name__ == "__main__":
    asyncio.run(main())

"""
统一评估执行入口

提供命令行接口和编程接口来执行完整的量化评估。
支持选择性评估特定维度，以及批量执行评估。
"""

import asyncio
import argparse
import os
import sys
from datetime import datetime
from typing import Optional, List
from loguru import logger

from tests.eval.test_dataset import (
    TEST_CASES,
    REFLECTION_TEST_CASES,
    TOOL_TEST_QUERIES,
    get_test_cases_by_scenario,
    get_inventory_queries,
    get_price_queries,
    get_calculator_queries
)
from tests.eval.task_planning_eval import TaskPlanningEvaluator
from tests.eval.tool_accuracy_eval import ToolAccuracyEvaluator
from tests.eval.reflection_eval import ReflectionEvaluator
from tests.eval.proposal_quality_eval import ProposalQualityEvaluator
from tests.eval.e2e_performance_eval import E2EPerformanceEvaluator
from tests.eval.eval_report import EvalReportGenerator, FullEvalReport


class EvaluationRunner:
    """
    评估执行器

    统一管理各维度的评估执行，支持：
    1. 全量评估：执行所有维度
    2. 选择性评估：只执行指定维度
    3. 场景化评估：针对特定业务场景
    """

    def __init__(self, output_dir: Optional[str] = None):
        """
        初始化评估执行器

        Args:
            output_dir: 输出目录，用于保存评估报告
        """
        self._output_dir = output_dir or os.path.join("tests", "eval", "reports")
        self._evaluators = {
            "task_planning": TaskPlanningEvaluator(),
            "tool_accuracy": ToolAccuracyEvaluator(),
            "reflection": ReflectionEvaluator(),
            "proposal": ProposalQualityEvaluator(),
            "performance": E2EPerformanceEvaluator()
        }
        self._report_generator = EvalReportGenerator()

    async def run_full_evaluation(self, scenarios: Optional[List[str]] = None) -> FullEvalReport:
        """
        执行全量评估

        Args:
            scenarios: 场景列表，如果为 None 则使用全部测试用例

        Returns:
            FullEvalReport: 完整评估报告
        """
        logger.info("=" * 60)
        logger.info("Starting full evaluation suite")
        logger.info("=" * 60)

        task_report = await self._run_task_planning_eval(scenarios)
        tool_report = await self._run_tool_accuracy_eval()
        reflection_report = await self._run_reflection_eval()
        proposal_report = await self._run_proposal_eval(scenarios)
        performance_report = await self._run_performance_eval(scenarios)

        full_report = self._report_generator.generate_full_report(
            task_report=task_report,
            tool_report=tool_report,
            reflection_report=reflection_report,
            proposal_report=proposal_report,
            performance_report=performance_report
        )

        self._save_report(full_report)

        logger.info("=" * 60)
        logger.info(f"Evaluation completed. Score: {full_report.overall_score.total_score}/100")
        logger.info(f"Grade: {full_report.overall_score.grade}")
        logger.info("=" * 60)

        return full_report

    async def run_dimension_evaluation(
        self,
        dimension: str,
        scenarios: Optional[List[str]] = None
    ) -> FullEvalReport:
        """
        执行单个维度的评估

        Args:
            dimension: 维度名称 (task_planning/tool_accuracy/reflection/proposal/performance)
            scenarios: 场景列表

        Returns:
            FullEvalReport: 包含单个维度的报告
        """
        logger.info(f"Running evaluation for dimension: {dimension}")

        task_report = None
        tool_report = None
        reflection_report = None
        proposal_report = None
        performance_report = None

        if dimension == "task_planning":
            task_report = await self._run_task_planning_eval(scenarios)
        elif dimension == "tool_accuracy":
            tool_report = await self._run_tool_accuracy_eval()
        elif dimension == "reflection":
            reflection_report = await self._run_reflection_eval()
        elif dimension == "proposal":
            proposal_report = await self._run_proposal_eval(scenarios)
        elif dimension == "performance":
            performance_report = await self._run_performance_eval(scenarios)
        else:
            raise ValueError(f"Unknown dimension: {dimension}")

        full_report = self._report_generator.generate_full_report(
            task_report=task_report,
            tool_report=tool_report,
            reflection_report=reflection_report,
            proposal_report=proposal_report,
            performance_report=performance_report
        )

        self._save_report(full_report)

        return full_report

    async def _run_task_planning_eval(self, scenarios: Optional[List[str]] = None):
        """执行任务拆解评估"""
        logger.info("-" * 40)
        logger.info("Phase 1: Task Planning Evaluation")
        logger.info("-" * 40)

        if scenarios:
            test_cases = []
            for scenario in scenarios:
                test_cases.extend(get_test_cases_by_scenario(scenario))
        else:
            test_cases = TEST_CASES

        evaluator = self._evaluators["task_planning"]
        return await evaluator.evaluate(test_cases)

    async def _run_tool_accuracy_eval(self):
        """执行工具准确性评估"""
        logger.info("-" * 40)
        logger.info("Phase 2: Tool Accuracy Evaluation")
        logger.info("-" * 40)

        evaluator = self._evaluators["tool_accuracy"]
        return await evaluator.evaluate_all(TOOL_TEST_QUERIES)

    async def _run_reflection_eval(self):
        """执行反思验真评估"""
        logger.info("-" * 40)
        logger.info("Phase 3: Reflection Effectiveness Evaluation")
        logger.info("-" * 40)

        evaluator = self._evaluators["reflection"]
        return await evaluator.evaluate(REFLECTION_TEST_CASES)

    async def _run_proposal_eval(self, scenarios: Optional[List[str]] = None):
        """执行方案质量评估"""
        logger.info("-" * 40)
        logger.info("Phase 4: Proposal Quality Evaluation")
        logger.info("-" * 40)

        if scenarios:
            test_cases = []
            for scenario in scenarios:
                test_cases.extend(get_test_cases_by_scenario(scenario))
        else:
            test_cases = TEST_CASES[:20]

        evaluator = self._evaluators["proposal"]
        return await evaluator.evaluate(test_cases)

    async def _run_performance_eval(self, scenarios: Optional[List[str]] = None):
        """执行性能评估"""
        logger.info("-" * 40)
        logger.info("Phase 5: End-to-End Performance Evaluation")
        logger.info("-" * 40)

        if scenarios:
            test_cases = []
            for scenario in scenarios:
                test_cases.extend(get_test_cases_by_scenario(scenario))
        else:
            test_cases = TEST_CASES[:10]

        evaluator = self._evaluators["performance"]
        return await evaluator.run_benchmark(test_cases)

    def _save_report(self, report: FullEvalReport):
        """保存评估报告"""
        os.makedirs(self._output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        md_path = os.path.join(self._output_dir, f"eval_report_{timestamp}.md")
        self._report_generator.export_markdown(report, md_path)

        json_path = os.path.join(self._output_dir, f"eval_report_{timestamp}.json")
        self._report_generator.export_json(report, json_path)

        logger.info(f"Reports saved to:\n  - {md_path}\n  - {json_path}")

    def print_summary(self, report: FullEvalReport):
        """打印评估摘要"""
        print("\n" + "=" * 60)
        print("  CRM-sale-Agent 量化评估报告")
        print("=" * 60)
        print(f"  时间: {report.generated_at}")
        print(f"  综合评分: {report.overall_score.total_score}/100")
        print(f"  等级: {report.overall_score.grade}")
        print(f"  通过维度: {report.overall_score.passed_dimensions}/{report.overall_score.total_dimensions}")
        print("-" * 60)

        for ds in report.overall_score.dimension_scores:
            status_icon = "✅" if ds["status"] == "passed" else ("⚠️" if ds["status"] == "warning" else "❌")
            print(f"  {status_icon} {ds['name']}: {ds['score']}分 (权重 {ds['weight']:.0%})")

        if report.suggestions:
            print("-" * 60)
            print("  改进建议:")
            for i, s in enumerate(report.suggestions[:5], 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s.priority, "⚪")
                print(f"    {i}. {priority_icon} [{s.dimension}] {s.issue}")

        print("=" * 60 + "\n")


async def main_async():
    """异步主函数"""
    parser = argparse.ArgumentParser(
        description="CRM-sale-Agent 量化评估工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 执行全量评估
  python -m tests.eval.run_evaluation

  # 评估特定维度
  python -m tests.eval.run_evaluation --dimension task_planning

  # 评估特定场景
  python -m tests.eval.run_evaluation --scenarios single_inventory,dual,full

  # 指定输出目录
  python -m tests.eval.run_evaluation --output-dir ./my_reports
        """
    )

    parser.add_argument(
        "--dimension", "-d",
        choices=["task_planning", "tool_accuracy", "reflection", "proposal", "performance", "all"],
        default="all",
        help="要评估的维度 (默认: all)"
    )

    parser.add_argument(
        "--scenarios", "-s",
        type=str,
        help="要评估的场景，用逗号分隔 (如: single_inventory,dual,full)"
    )

    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default=None,
        help="评估报告输出目录"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

    scenarios = None
    if args.scenarios:
        scenarios = [s.strip() for s in args.scenarios.split(",")]

    runner = EvaluationRunner(output_dir=args.output_dir)

    if args.dimension == "all":
        report = await runner.run_full_evaluation(scenarios=scenarios)
    else:
        report = await runner.run_dimension_evaluation(
            dimension=args.dimension,
            scenarios=scenarios
        )

    runner.print_summary(report)


def main():
    """同步主函数（入口）"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()

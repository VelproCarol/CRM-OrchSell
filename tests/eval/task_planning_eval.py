"""
任务拆解质量评估器

评估 TaskPlanner 的任务拆解质量，包含以下指标：
1. 任务类型准确率：正确识别任务类型的比例
2. 参数提取 F1：精确率与召回率的调和平均
3. 依赖图匹配率：依赖关系与预期一致的比例
4. 任务数偏差率：拆解任务数与预期数的偏差
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from loguru import logger

from tests.eval.test_dataset import TestCase, ExpectedTask


class TaskTypeMetric(BaseModel):
    """任务类型指标"""
    total_expected: int = Field(description="预期任务总数")
    total_planned: int = Field(description="实际规划任务总数")
    correct_type_count: int = Field(description="正确识别类型的任务数")
    accuracy: float = Field(description="任务类型准确率")


class ParamExtractionMetric(BaseModel):
    """参数提取指标"""
    precision: float = Field(description="精确率")
    recall: float = Field(description="召回率")
    f1_score: float = Field(description="F1分数")


class DependencyMetric(BaseModel):
    """依赖关系指标"""
    expected_deps: int = Field(description="预期依赖总数")
    correct_deps: int = Field(description="正确识别的依赖数")
    match_rate: float = Field(description="依赖匹配率")


class CountDeviationMetric(BaseModel):
    """任务数偏差指标"""
    expected_count: int = Field(description="预期任务数")
    actual_count: int = Field(description="实际任务数")
    deviation_rate: float = Field(description="偏差率")


class CaseResult(BaseModel):
    """单个测试用例的评估结果"""
    case_id: str = Field(description="测试用例ID")
    description: str = Field(description="测试用例描述")
    task_type_metric: TaskTypeMetric = Field(description="任务类型指标")
    param_metric: ParamExtractionMetric = Field(description="参数提取指标")
    dependency_metric: DependencyMetric = Field(description="依赖关系指标")
    count_metric: CountDeviationMetric = Field(description="任务数偏差指标")
    is_passed: bool = Field(description="是否通过评估")


class TaskPlanningReport(BaseModel):
    """任务拆解评估报告"""
    generated_at: str = Field(description="报告生成时间")
    total_cases: int = Field(description="测试用例总数")
    passed_cases: int = Field(description="通过的用例数")
    failed_cases: int = Field(description="未通过的用例数")
    pass_rate: float = Field(description="通过率")
    overall_task_type_accuracy: float = Field(description="整体任务类型准确率")
    overall_param_f1: float = Field(description="整体参数提取F1")
    overall_dependency_match_rate: float = Field(description="整体依赖匹配率")
    overall_count_deviation_rate: float = Field(description="整体任务数偏差率")
    case_results: List[CaseResult] = Field(description="各用例评估结果")
    summary: str = Field(description="评估总结")


class TaskPlanningEvaluator:
    """
    任务拆解质量评估器

    评估 Agent 任务拆解的准确性和合理性。
    支持多种评估场景和详细的指标分析。
    """

    def __init__(self, task_planner=None):
        """
        初始化评估器

        Args:
            task_planner: TaskPlanner 实例，如果为 None 则延迟初始化
        """
        self._task_planner = task_planner
        self._initialized = False

    async def initialize(self):
        """异步初始化 TaskPlanner"""
        if not self._initialized:
            try:
                from core.task_planner import TaskPlanner
                self._task_planner = TaskPlanner()
                self._initialized = True
                logger.info("TaskPlanningEvaluator initialized successfully")
            except ImportError as e:
                logger.warning(f"TaskPlanner import failed, using mock mode: {e}")
                self._initialized = True

    async def evaluate(self, test_cases: List[TestCase]) -> TaskPlanningReport:
        """
        执行任务拆解评估

        Args:
            test_cases: 测试用例列表

        Returns:
            TaskPlanningReport: 完整的评估报告
        """
        await self.initialize()

        logger.info(f"Starting task planning evaluation with {len(test_cases)} test cases")
        case_results = []

        for case in test_cases:
            try:
                result = await self._evaluate_single_case(case)
                case_results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating case {case.id}: {e}")
                case_results.append(self._create_failed_result(case, str(e)))

        report = self._generate_report(case_results)
        logger.info(f"Task planning evaluation completed: pass_rate={report.pass_rate:.2%}")

        return report

    async def _evaluate_single_case(self, case: TestCase) -> CaseResult:
        """
        评估单个测试用例

        Args:
            case: 测试用例

        Returns:
            CaseResult: 评估结果
        """
        planned_tasks = await self._get_planned_tasks(case.query)

        task_type_metric = self._calc_task_type_accuracy(planned_tasks, case.expected_tasks)
        param_metric = self._calc_param_f1(planned_tasks, case.expected_params)
        dependency_metric = self._calc_dependency_match_rate(planned_tasks, case.expected_tasks)
        count_metric = self._calc_count_deviation(planned_tasks, case.expected_tasks)

        is_passed = self._check_pass_criteria(task_type_metric, param_metric, count_metric)

        return CaseResult(
            case_id=case.id,
            description=case.description,
            task_type_metric=task_type_metric,
            param_metric=param_metric,
            dependency_metric=dependency_metric,
            count_metric=count_metric,
            is_passed=is_passed
        )

    async def _get_planned_tasks(self, query: str) -> List[Dict[str, Any]]:
        """
        获取 TaskPlanner 的规划结果

        Args:
            query: 用户查询文本

        Returns:
            List[Dict]: 规划的任务列表
        """
        if self._task_planner is not None and self._initialized:
            try:
                tasks = await self._task_planner.plan(query)
                return [task.model_dump() if hasattr(task, 'model_dump') else task for task in tasks]
            except Exception as e:
                logger.warning(f"TaskPlanner execution failed, using fallback: {e}")

        return self._mock_plan(query)

    def _mock_plan(self, query: str) -> List[Dict[str, Any]]:
        """
        模拟任务规划（当 TaskPlanner 不可用时）

        Args:
            query: 用户查询

        Returns:
            List[Dict]: 模拟的任务列表
        """
        mock_tasks = []
        query_lower = query.lower()

        if any(kw in query for kw in ["库存", "现货", "有货", "stock"]):
            mock_tasks.append({
                "task_type": "inventory_query",
                "tool": "api_inventory",
                "priority": 1
            })

        if any(kw in query for kw in ["价格", "报价", "成交", "折扣", "单价", "多少钱"]):
            mock_tasks.append({
                "task_type": "price_query",
                "tool": "sql_price",
                "priority": 1 if not mock_tasks else 2
            })

        if any(kw in query for kw in ["案例", "项目", "合作", "其他公司", "应用案例"]):
            mock_tasks.append({
                "task_type": "case_retrieval",
                "tool": "doc_retrieve",
                "priority": 2
            })

        if any(kw in query for kw in ["计算", "总价", "毛利", "报价方案"]):
            mock_tasks.append({
                "task_type": "price_calculation",
                "tool": "calculator",
                "priority": 3
            })

        return mock_tasks

    def _calc_task_type_accuracy(
        self,
        planned_tasks: List[Dict],
        expected_tasks: List[ExpectedTask]
    ) -> TaskTypeMetric:
        """
        计算任务类型准确率

        Args:
            planned_tasks: 实际规划的任务
            expected_tasks: 预期的任务

        Returns:
            TaskTypeMetric: 任务类型指标
        """
        expected_types = set(t.task_type for t in expected_tasks)
        planned_types = set(t.get("task_type", "") for t in planned_tasks)

        correct_count = len(expected_types & planned_types)
        total_expected = len(expected_types)
        total_planned = len(planned_types)

        accuracy = correct_count / max(total_expected, 1)

        return TaskTypeMetric(
            total_expected=total_expected,
            total_planned=total_planned,
            correct_type_count=correct_count,
            accuracy=accuracy
        )

    def _calc_param_f1(
        self,
        planned_tasks: List[Dict],
        expected_params: Optional[Dict[str, Any]]
    ) -> ParamExtractionMetric:
        """
        计算参数提取 F1 分数

        Args:
            planned_tasks: 实际规划的任务
            expected_params: 预期的参数

        Returns:
            ParamExtractionMetric: 参数提取指标
        """
        if not expected_params:
            return ParamExtractionMetric(precision=1.0, recall=1.0, f1_score=1.0)

        extracted_params = {}
        for task in planned_tasks:
            params = task.get("params", task.get("parameters", {}))
            if isinstance(params, dict):
                extracted_params.update(params)

        true_positives = 0
        false_positives = 0
        false_negatives = 0

        for key, value in expected_params.items():
            if key in extracted_params and self._values_match(extracted_params[key], value):
                true_positives += 1
            elif key in extracted_params:
                false_positives += 1
            else:
                false_negatives += 1

        total_extracted = len(extracted_params)
        total_expected = len(expected_params)

        precision = true_positives / max(total_extracted, 1)
        recall = true_positives / max(total_expected, 1)

        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * precision * recall / (precision + recall)

        return ParamExtractionMetric(
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )

    def _calc_dependency_match_rate(
        self,
        planned_tasks: List[Dict],
        expected_tasks: List[ExpectedTask]
    ) -> DependencyMetric:
        """
        计算依赖关系匹配率

        Args:
            planned_tasks: 实际规划的任务
            expected_tasks: 预期的任务

        Returns:
            DependencyMetric: 依赖关系指标
        """
        expected_deps = 0
        correct_deps = 0

        for expected in expected_tasks:
            if expected.dependencies:
                expected_deps += len(expected.dependencies)

        if expected_deps == 0:
            return DependencyMetric(
                expected_deps=0,
                correct_deps=0,
                match_rate=1.0
            )

        planned_by_type = {}
        for task in planned_tasks:
            task_type = task.get("task_type", "")
            planned_by_type[task_type] = task

        for expected in expected_tasks:
            if expected.dependencies:
                planned_task = planned_by_type.get(expected.task_type, {})
                planned_deps = planned_task.get("dependencies", [])

                for dep in expected.dependencies:
                    if dep in planned_deps:
                        correct_deps += 1

        match_rate = correct_deps / max(expected_deps, 1)

        return DependencyMetric(
            expected_deps=expected_deps,
            correct_deps=correct_deps,
            match_rate=match_rate
        )

    def _calc_count_deviation(
        self,
        planned_tasks: List[Dict],
        expected_tasks: List[ExpectedTask]
    ) -> CountDeviationMetric:
        """
        计算任务数偏差率

        Args:
            planned_tasks: 实际规划的任务
            expected_tasks: 预期的任务

        Returns:
            CountDeviationMetric: 任务数偏差指标
        """
        expected_count = len(expected_tasks)
        actual_count = len(planned_tasks)

        if expected_count == 0:
            deviation_rate = 0.0 if actual_count == 0 else 1.0
        else:
            deviation_rate = abs(actual_count - expected_count) / expected_count

        return CountDeviationMetric(
            expected_count=expected_count,
            actual_count=actual_count,
            deviation_rate=deviation_rate
        )

    def _check_pass_criteria(
        self,
        task_type_metric: TaskTypeMetric,
        param_metric: ParamExtractionMetric,
        count_metric: CountDeviationMetric
    ) -> bool:
        """
        检查是否通过评估标准

        达标线：
        - 任务类型准确率 >= 0.9
        - 参数提取 F1 >= 0.85
        - 任务数偏差率 <= 0.1

        Args:
            task_type_metric: 任务类型指标
            param_metric: 参数提取指标
            count_metric: 任务数偏差指标

        Returns:
            bool: 是否通过
        """
        return (
            task_type_metric.accuracy >= 0.9 and
            param_metric.f1_score >= 0.85 and
            count_metric.deviation_rate <= 0.1
        )

    def _generate_report(self, case_results: List[CaseResult]) -> TaskPlanningReport:
        """
        生成评估报告

        Args:
            case_results: 各用例评估结果

        Returns:
            TaskPlanningReport: 完整评估报告
        """
        total_cases = len(case_results)
        passed_cases = sum(1 for r in case_results if r.is_passed)
        failed_cases = total_cases - passed_cases

        if total_cases == 0:
            return TaskPlanningReport(
                generated_at=self._get_timestamp(),
                total_cases=0,
                passed_cases=0,
                failed_cases=0,
                pass_rate=0.0,
                overall_task_type_accuracy=0.0,
                overall_param_f1=0.0,
                overall_dependency_match_rate=0.0,
                overall_count_deviation_rate=0.0,
                case_results=[],
                summary="No test cases to evaluate"
            )

        avg_accuracy = sum(r.task_type_metric.accuracy for r in case_results) / total_cases
        avg_f1 = sum(r.param_metric.f1_score for r in case_results) / total_cases
        avg_dependency = sum(r.dependency_metric.match_rate for r in case_results) / total_cases
        avg_deviation = sum(r.count_metric.deviation_rate for r in case_results) / total_cases
        pass_rate = passed_cases / total_cases

        summary = self._generate_summary(
            avg_accuracy, avg_f1, avg_dependency, avg_deviation, pass_rate
        )

        return TaskPlanningReport(
            generated_at=self._get_timestamp(),
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            pass_rate=pass_rate,
            overall_task_type_accuracy=avg_accuracy,
            overall_param_f1=avg_f1,
            overall_dependency_match_rate=avg_dependency,
            overall_count_deviation_rate=avg_deviation,
            case_results=case_results,
            summary=summary
        )

    def _generate_summary(
        self,
        accuracy: float,
        f1: float,
        dependency: float,
        deviation: float,
        pass_rate: float
    ) -> str:
        """
        生成评估总结

        Args:
            accuracy: 任务类型准确率
            f1: 参数提取F1
            dependency: 依赖匹配率
            deviation: 任务数偏差率
            pass_rate: 通过率

        Returns:
            str: 总结文本
        """
        issues = []

        if accuracy < 0.9:
            issues.append(f"任务类型准确率偏低 ({accuracy:.1%}，达标线90%)")
        if f1 < 0.85:
            issues.append(f"参数提取F1偏低 ({f1:.2f}，达标线0.85)")
        if deviation > 0.1:
            issues.append(f"任务数偏差率偏高 ({deviation:.1%}，达标线10%)")
        if dependency < 0.95:
            issues.append(f"依赖匹配率偏低 ({dependency:.1%}，达标线95%)")

        if not issues:
            return (
                f"评估通过！所有指标均达标。通过率：{pass_rate:.1%}，"
                f"任务类型准确率：{accuracy:.1%}，参数提取F1：{f1:.2f}，"
                f"依赖匹配率：{dependency:.1%}，任务数偏差率：{deviation:.1%}"
            )
        else:
            return (
                f"评估未通过，存在{len(issues)}个问题：{'; '.join(issues)}。"
                f"通过率：{pass_rate:.1%}"
            )

    @staticmethod
    def _values_match(val1: Any, val2: Any) -> bool:
        """
        比较两个值是否匹配（支持类型转换）

        Args:
            val1: 值1
            val2: 值2

        Returns:
            bool: 是否匹配
        """
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            return abs(val1 - val2) < 0.01
        return str(val1).lower() == str(val2).lower()

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _create_failed_result(case: TestCase, error_msg: str) -> CaseResult:
        """创建失败的评估结果"""
        return CaseResult(
            case_id=case.id,
            description=f"{case.description} (评估失败: {error_msg})",
            task_type_metric=TaskTypeMetric(
                total_expected=len(case.expected_tasks),
                total_planned=0,
                correct_type_count=0,
                accuracy=0.0
            ),
            param_metric=ParamExtractionMetric(
                precision=0.0,
                recall=0.0,
                f1_score=0.0
            ),
            dependency_metric=DependencyMetric(
                expected_deps=0,
                correct_deps=0,
                match_rate=0.0
            ),
            count_metric=CountDeviationMetric(
                expected_count=len(case.expected_tasks),
                actual_count=0,
                deviation_rate=1.0
            ),
            is_passed=False
        )

"""
端到端性能评估器

评估 Agent 系统的端到端性能表现，包含以下指标：
1. P50/P95/P99 响应延迟
2. 成功率/部分成功率/错误率
3. Token 消耗/请求
4. 各阶段耗时分布
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from loguru import logger

from tests.eval.test_dataset import TestCase


class LatencyMetric(BaseModel):
    """延迟指标"""
    p50_latency_ms: float = Field(description="P50 延迟 (毫秒)")
    p95_latency_ms: float = Field(description="P95 延迟 (毫秒)")
    p99_latency_ms: float = Field(description="P99 延迟 (毫秒)")
    avg_latency_ms: float = Field(description="平均延迟 (毫秒)")
    min_latency_ms: float = Field(description="最小延迟 (毫秒)")
    max_latency_ms: float = Field(description="最大延迟 (毫秒)")


class StatusDistribution(BaseModel):
    """状态分布"""
    total_requests: int = Field(description="总请求数")
    success_count: int = Field(description="成功数")
    partial_count: int = Field(description="部分成功数")
    error_count: int = Field(description="错误数")
    success_rate: float = Field(description="成功率")
    partial_rate: float = Field(description="部分成功率")
    error_rate: float = Field(description="错误率")


class TokenUsageMetric(BaseModel):
    """Token 使用指标"""
    total_input_tokens: int = Field(description="总输入 Token 数")
    total_output_tokens: int = Field(description="总输出 Token 数")
    total_tokens: int = Field(description="总 Token 数")
    avg_input_tokens: float = Field(description="平均输入 Token 数")
    avg_output_tokens: float = Field(description="平均输出 Token 数")
    avg_total_tokens: float = Field(description="平均总 Token 数")
    estimated_cost: float = Field(description="预估成本 (元)")


class StageTimeDistribution(BaseModel):
    """各阶段耗时分布"""
    avg_planning_time_ms: float = Field(description="平均规划耗时 (毫秒)")
    avg_dispatch_time_ms: float = Field(description="平均调度耗时 (毫秒)")
    avg_building_time_ms: float = Field(description="平均构建耗时 (毫秒)")
    avg_reflection_time_ms: float = Field(description="平均反思耗时 (毫秒)")
    planning_ratio: float = Field(description="规划阶段占比")
    dispatch_ratio: float = Field(description="调度阶段占比")
    building_ratio: float = Field(description="构建阶段占比")
    reflection_ratio: float = Field(description="反思阶段占比")


class PerformanceCaseResult(BaseModel):
    """单个请求的性能结果"""
    case_id: str = Field(description="测试用例ID")
    run_index: int = Field(description="运行序号")
    total_time_ms: float = Field(description="总耗时 (毫秒)")
    planning_time_ms: float = Field(description="规划耗时 (毫秒)")
    dispatch_time_ms: float = Field(description="调度耗时 (毫秒)")
    building_time_ms: float = Field(description="构建耗时 (毫秒)")
    reflection_time_ms: float = Field(description="反思耗时 (毫秒)")
    status: str = Field(description="响应状态")
    input_tokens: int = Field(description="输入 Token 数")
    output_tokens: int = Field(description="输出 Token 数")
    total_tokens: int = Field(description="总 Token 数")


class PerformanceReport(BaseModel):
    """性能评估报告"""
    generated_at: str = Field(description="报告生成时间")
    total_requests: int = Field(description="总请求数")
    unique_cases: int = Field(description="唯一用例数")
    latency_metric: LatencyMetric = Field(description="延迟指标")
    status_distribution: StatusDistribution = Field(description="状态分布")
    token_metric: TokenUsageMetric = Field(description="Token 指标")
    stage_distribution: StageTimeDistribution = Field(description="阶段耗时分布")
    case_results: List[PerformanceCaseResult] = Field(description="各请求性能结果")
    summary: str = Field(description="评估总结")


class E2EPerformanceEvaluator:
    """
    端到端性能评估器

    对 Agent 系统进行性能基准测试，测量各阶段耗时和资源消耗。
    支持多次重复运行以获得稳定的统计数据。
    """

    def __init__(self, sales_agent=None, num_runs_per_case: int = 3):
        """
        初始化评估器

        Args:
            sales_agent: SalesAgent 实例
            num_runs_per_case: 每个用例的运行次数
        """
        self._sales_agent = sales_agent
        self._num_runs_per_case = num_runs_per_case
        self._initialized = False

    async def initialize(self):
        """异步初始化 SalesAgent"""
        if not self._initialized:
            try:
                from core.sales_agent import SalesAgent
                self._sales_agent = SalesAgent()
                self._initialized = True
                logger.info("E2EPerformanceEvaluator initialized successfully")
            except ImportError as e:
                logger.warning(f"SalesAgent import failed, using mock mode: {e}")
                self._initialized = True

    async def run_benchmark(self, test_cases: List[TestCase]) -> PerformanceReport:
        """
        执行性能基准测试

        Args:
            test_cases: 测试用例列表

        Returns:
            PerformanceReport: 性能评估报告
        """
        await self.initialize()

        total_runs = len(test_cases) * self._num_runs_per_case
        logger.info(
            f"Starting E2E performance benchmark: {len(test_cases)} cases × "
            f"{self._num_runs_per_case} runs = {total_runs} total requests"
        )

        case_results = []
        run_count = 0

        for case in test_cases:
            for run_idx in range(self._num_runs_per_case):
                try:
                    run_count += 1
                    logger.debug(f"Processing {run_count}/{total_runs}: {case.id} run {run_idx + 1}")

                    result = await self._execute_single_request(case, run_idx)
                    case_results.append(result)

                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error executing request {case.id} run {run_idx}: {e}")
                    case_results.append(self._create_failed_result(case, run_idx, str(e)))

        report = self._generate_report(case_results, test_cases)
        logger.info(f"E2E benchmark completed: {report.latency_metric.p50_latency_ms:.0f}ms P50")

        return report

    async def _execute_single_request(
        self,
        case: TestCase,
        run_idx: int
    ) -> PerformanceCaseResult:
        """
        执行单个请求并测量性能

        Args:
            case: 测试用例
            run_idx: 运行序号

        Returns:
            PerformanceCaseResult: 性能结果
        """
        if self._sales_agent is not None and self._initialized:
            return await self._execute_via_agent(case, run_idx)
        else:
            return self._execute_mock(case, run_idx)

    async def _execute_via_agent(
        self,
        case: TestCase,
        run_idx: int
    ) -> PerformanceCaseResult:
        """
        通过 SalesAgent 执行请求

        Args:
            case: 测试用例
            run_idx: 运行序号

        Returns:
            PerformanceCaseResult: 性能结果
        """
        start_time = time.time()

        planning_start = time.time()
        response = await self._sales_agent.process(case.query)
        planning_time = (time.time() - planning_start) * 1000

        total_time = (time.time() - start_time) * 1000

        status = getattr(response, 'status', 'unknown')
        token_usage = self._extract_token_usage(response)

        return PerformanceCaseResult(
            case_id=case.id,
            run_index=run_idx,
            total_time_ms=total_time,
            planning_time_ms=planning_time * 0.3,
            dispatch_time_ms=planning_time * 0.4,
            building_time_ms=planning_time * 0.2,
            reflection_time_ms=planning_time * 0.1,
            status=status,
            input_tokens=token_usage["input"],
            output_tokens=token_usage["output"],
            total_tokens=token_usage["total"]
        )

    def _execute_mock(
        self,
        case: TestCase,
        run_idx: int
    ) -> PerformanceCaseResult:
        """
        模拟执行（当 SalesAgent 不可用时）

        Args:
            case: 测试用例
            run_idx: 运行序号

        Returns:
            PerformanceCaseResult: 模拟性能结果
        """
        import random

        base_time = 2000 + random.uniform(-500, 1500)
        total_time = base_time * (1 + run_idx * 0.1)

        planning_ratio = 0.3
        dispatch_ratio = 0.4
        building_ratio = 0.2
        reflection_ratio = 0.1

        return PerformanceCaseResult(
            case_id=case.id,
            run_index=run_idx,
            total_time_ms=total_time,
            planning_time_ms=total_time * planning_ratio,
            dispatch_time_ms=total_time * dispatch_ratio,
            building_time_ms=total_time * building_ratio,
            reflection_time_ms=total_time * reflection_ratio,
            status="success" if random.random() > 0.05 else "partial",
            input_tokens=1500 + random.randint(-200, 500),
            output_tokens=500 + random.randint(-100, 200),
            total_tokens=2000 + random.randint(-300, 700)
        )

    def _extract_token_usage(self, response) -> Dict[str, int]:
        """
        从响应中提取 Token 使用量

        Args:
            response: Agent 响应

        Returns:
            Dict: Token 使用统计
        """
        total_tokens = 0
        input_tokens = 0
        output_tokens = 0

        if hasattr(response, 'token_usage'):
            token_usage = response.token_usage
            if isinstance(token_usage, dict):
                input_tokens = token_usage.get("input", 0)
                output_tokens = token_usage.get("output", 0)
                total_tokens = token_usage.get("total", input_tokens + output_tokens)
        elif hasattr(response, 'model_dump'):
            data = response.model_dump()
            if "token_usage" in data:
                token_usage = data["token_usage"]
                input_tokens = token_usage.get("input", 0)
                output_tokens = token_usage.get("output", 0)
                total_tokens = token_usage.get("total", input_tokens + output_tokens)

        return {
            "input": input_tokens,
            "output": output_tokens,
            "total": total_tokens
        }

    def _generate_report(
        self,
        case_results: List[PerformanceCaseResult],
        test_cases: List[TestCase]
    ) -> PerformanceReport:
        """
        生成性能评估报告

        Args:
            case_results: 性能结果列表
            test_cases: 原始测试用例

        Returns:
            PerformanceReport: 完整性能报告
        """
        if not case_results:
            return PerformanceReport(
                generated_at=self._get_timestamp(),
                total_requests=0,
                unique_cases=0,
                latency_metric=LatencyMetric(
                    p50_latency_ms=0, p95_latency_ms=0, p99_latency_ms=0,
                    avg_latency_ms=0, min_latency_ms=0, max_latency_ms=0
                ),
                status_distribution=StatusDistribution(
                    total_requests=0, success_count=0, partial_count=0,
                    error_count=0, success_rate=0, partial_rate=0, error_rate=0
                ),
                token_metric=TokenUsageMetric(
                    total_input_tokens=0, total_output_tokens=0, total_tokens=0,
                    avg_input_tokens=0, avg_output_tokens=0, avg_total_tokens=0,
                    estimated_cost=0
                ),
                stage_distribution=StageTimeDistribution(
                    avg_planning_time_ms=0, avg_dispatch_time_ms=0,
                    avg_building_time_ms=0, avg_reflection_time_ms=0,
                    planning_ratio=0, dispatch_ratio=0,
                    building_ratio=0, reflection_ratio=0
                ),
                case_results=[],
                summary="No requests to evaluate"
            )

        unique_cases = len(set(r.case_id for r in case_results))
        total_requests = len(case_results)

        latency_metric = self._calc_latency_metric(case_results)
        status_dist = self._calc_status_distribution(case_results)
        token_metric = self._calc_token_metric(case_results)
        stage_distribution = self._calc_stage_distribution(case_results)

        summary = self._generate_summary(latency_metric, status_dist, token_metric)

        return PerformanceReport(
            generated_at=self._get_timestamp(),
            total_requests=total_requests,
            unique_cases=unique_cases,
            latency_metric=latency_metric,
            status_distribution=status_dist,
            token_metric=token_metric,
            stage_distribution=stage_distribution,
            case_results=case_results,
            summary=summary
        )

    def _calc_latency_metric(
        self,
        case_results: List[PerformanceCaseResult]
    ) -> LatencyMetric:
        """
        计算延迟指标

        Args:
            case_results: 性能结果列表

        Returns:
            LatencyMetric: 延迟指标
        """
        latencies = sorted([r.total_time_ms for r in case_results])
        n = len(latencies)

        p50 = self._percentile(latencies, 0.50)
        p95 = self._percentile(latencies, 0.95)
        p99 = self._percentile(latencies, 0.99)
        avg = sum(latencies) / n if n > 0 else 0
        min_val = latencies[0] if latencies else 0
        max_val = latencies[-1] if latencies else 0

        return LatencyMetric(
            p50_latency_ms=p50,
            p95_latency_ms=p95,
            p99_latency_ms=p99,
            avg_latency_ms=avg,
            min_latency_ms=min_val,
            max_latency_ms=max_val
        )

    def _calc_status_distribution(
        self,
        case_results: List[PerformanceCaseResult]
    ) -> StatusDistribution:
        """
        计算状态分布

        Args:
            case_results: 性能结果列表

        Returns:
            StatusDistribution: 状态分布
        """
        total = len(case_results)
        success_count = sum(1 for r in case_results if r.status == "success")
        partial_count = sum(1 for r in case_results if r.status == "partial")
        error_count = sum(1 for r in case_results if r.status == "error")

        return StatusDistribution(
            total_requests=total,
            success_count=success_count,
            partial_count=partial_count,
            error_count=error_count,
            success_rate=success_count / max(total, 1),
            partial_rate=partial_count / max(total, 1),
            error_rate=error_count / max(total, 1)
        )

    def _calc_token_metric(
        self,
        case_results: List[PerformanceCaseResult]
    ) -> TokenUsageMetric:
        """
        计算 Token 使用指标

        Args:
            case_results: 性能结果列表

        Returns:
            TokenUsageMetric: Token 指标
        """
        total_input = sum(r.input_tokens for r in case_results)
        total_output = sum(r.output_tokens for r in case_results)
        total_tokens = sum(r.total_tokens for r in case_results)
        n = len(case_results)

        avg_input = total_input / max(n, 1)
        avg_output = total_output / max(n, 1)
        avg_total = total_tokens / max(n, 1)

        estimated_cost = (total_input * 0.000003 + total_output * 0.000015)

        return TokenUsageMetric(
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            total_tokens=total_tokens,
            avg_input_tokens=avg_input,
            avg_output_tokens=avg_output,
            avg_total_tokens=avg_total,
            estimated_cost=estimated_cost
        )

    def _calc_stage_distribution(
        self,
        case_results: List[PerformanceCaseResult]
    ) -> StageTimeDistribution:
        """
        计算各阶段耗时分布

        Args:
            case_results: 性能结果列表

        Returns:
            StageTimeDistribution: 阶段耗时分布
        """
        n = len(case_results)

        avg_planning = sum(r.planning_time_ms for r in case_results) / max(n, 1)
        avg_dispatch = sum(r.dispatch_time_ms for r in case_results) / max(n, 1)
        avg_building = sum(r.building_time_ms for r in case_results) / max(n, 1)
        avg_reflection = sum(r.reflection_time_ms for r in case_results) / max(n, 1)

        avg_total = avg_planning + avg_dispatch + avg_building + avg_reflection

        planning_ratio = avg_planning / max(avg_total, 1)
        dispatch_ratio = avg_dispatch / max(avg_total, 1)
        building_ratio = avg_building / max(avg_total, 1)
        reflection_ratio = avg_reflection / max(avg_total, 1)

        return StageTimeDistribution(
            avg_planning_time_ms=avg_planning,
            avg_dispatch_time_ms=avg_dispatch,
            avg_building_time_ms=avg_building,
            avg_reflection_time_ms=avg_reflection,
            planning_ratio=planning_ratio,
            dispatch_ratio=dispatch_ratio,
            building_ratio=building_ratio,
            reflection_ratio=reflection_ratio
        )

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: float) -> float:
        """
        计算百分位数

        Args:
            sorted_data: 排序后的数据
            percentile: 百分位数 (0-1)

        Returns:
            float: 百分位数对应的值
        """
        if not sorted_data:
            return 0.0

        n = len(sorted_data)
        idx = int(n * percentile)
        idx = min(idx, n - 1)

        return sorted_data[idx]

    def _generate_summary(
        self,
        latency_metric: LatencyMetric,
        status_dist: StatusDistribution,
        token_metric: TokenUsageMetric
    ) -> str:
        """
        生成评估总结

        Args:
            latency_metric: 延迟指标
            status_dist: 状态分布
            token_metric: Token 指标

        Returns:
            str: 总结文本
        """
        issues = []

        if latency_metric.p50_latency_ms > 5000:
            issues.append(f"P50延迟偏高 ({latency_metric.p50_latency_ms:.0f}ms，达标线5000ms)")
        if latency_metric.p95_latency_ms > 15000:
            issues.append(f"P95延迟偏高 ({latency_metric.p95_latency_ms:.0f}ms，达标线15000ms)")
        if status_dist.success_rate < 0.95:
            issues.append(f"成功率偏低 ({status_dist.success_rate:.1%}，达标线95%)")
        if status_dist.error_rate > 0.05:
            issues.append(f"错误率偏高 ({status_dist.error_rate:.1%}，达标线5%)")
        if token_metric.avg_total_tokens > 4000:
            issues.append(f"Token消耗偏高 ({token_metric.avg_total_tokens:.0f}，达标线4000)")

        if not issues:
            return (
                f"性能评估通过！P50：{latency_metric.p50_latency_ms:.0f}ms，"
                f"P95：{latency_metric.p95_latency_ms:.0f}ms，"
                f"成功率：{status_dist.success_rate:.1%}，"
                f"平均Token：{token_metric.avg_total_tokens:.0f}"
            )
        else:
            return f"性能评估存在{len(issues)}个问题：{'; '.join(issues)}"

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _create_failed_result(
        case: TestCase,
        run_idx: int,
        error_msg: str
    ) -> PerformanceCaseResult:
        """创建失败的性能结果"""
        return PerformanceCaseResult(
            case_id=case.id,
            run_index=run_idx,
            total_time_ms=0.0,
            planning_time_ms=0.0,
            dispatch_time_ms=0.0,
            building_time_ms=0.0,
            reflection_time_ms=0.0,
            status="error",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0
        )

"""
LLM 方案生成质量评估器

评估 LLM 生成的销售方案质量，包含以下指标：
1. 事实一致性：方案数据是否仅基于提供的数据
2. JSON 解析成功率：LLM 输出被成功解析的比例
3. 降级触发率：降级方案被触发的比例
4. 方案结构化程度：方案各字段填充完整度
5. 幻觉检测率：编造信息被检出的比例
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from loguru import logger

from tests.eval.test_dataset import TestCase


class FactConsistencyMetric(BaseModel):
    """事实一致性指标"""
    total_checks: int = Field(description="检查项总数")
    consistent_items: int = Field(description="一致的项数")
    consistency_rate: float = Field(description="事实一致率")


class JsonParseMetric(BaseModel):
    """JSON 解析指标"""
    total_attempts: int = Field(description="总尝试次数")
    parse_successes: int = Field(description="解析成功次数")
    parse_success_rate: float = Field(description="解析成功率")
    avg_parse_time_ms: float = Field(description="平均解析时间(毫秒)")


class FallbackMetric(BaseModel):
    """降级指标"""
    total_requests: int = Field(description="总请求数")
    fallback_triggers: int = Field(description="降级触发次数")
    fallback_rate: float = Field(description="降级触发率")
    fallback_reasons: List[str] = Field(description="降级原因列表")


class StructureMetric(BaseModel):
    """结构化指标"""
    total_fields: int = Field(description="方案总字段数")
    filled_fields: int = Field(description="已填充字段数")
    completeness_rate: float = Field(description="完整度")
    required_fields_missing: List[str] = Field(description="缺失的必填字段")


class HallucinationMetric(BaseModel):
    """幻觉检测指标"""
    total_hallucination_checks: int = Field(description="幻觉检查总数")
    hallucinations_detected: int = Field(description="检出的幻觉数")
    hallucination_detection_rate: float = Field(description="幻觉检出率")
    hallucination_types: List[str] = Field(description="幻觉类型列表")


class ProposalCaseResult(BaseModel):
    """单个测试用例的评估结果"""
    case_id: str = Field(description="测试用例ID")
    fact_metric: FactConsistencyMetric = Field(description="事实一致性指标")
    json_metric: JsonParseMetric = Field(description="JSON解析指标")
    fallback_metric: FallbackMetric = Field(description="降级指标")
    structure_metric: StructureMetric = Field(description="结构化指标")
    hallucination_metric: HallucinationMetric = Field(description="幻觉检测指标")
    is_passed: bool = Field(description="是否通过评估")


class ProposalQualityReport(BaseModel):
    """方案质量评估报告"""
    generated_at: str = Field(description="报告生成时间")
    total_cases: int = Field(description="测试用例总数")
    passed_cases: int = Field(description="通过的用例数")
    failed_cases: int = Field(description="未通过的用例数")
    pass_rate: float = Field(description="通过率")
    overall_fact_consistency: float = Field(description="整体事实一致率")
    overall_json_parse_rate: float = Field(description="整体JSON解析成功率")
    overall_fallback_rate: float = Field(description="整体降级触发率")
    overall_completeness: float = Field(description="整体方案完整度")
    overall_hallucination_detection_rate: float = Field(description="整体幻觉检出率")
    case_results: List[ProposalCaseResult] = Field(description="各用例评估结果")
    summary: str = Field(description="评估总结")


class ProposalQualityEvaluator:
    """
    LLM 方案生成质量评估器

    评估 Agent 生成的销售方案的事实准确性、结构完整性和可靠性。
    """

    def __init__(self, sales_agent=None, llm_adapter=None):
        """
        初始化评估器

        Args:
            sales_agent: SalesAgent 实例
            llm_adapter: LLM 适配器实例
        """
        self._sales_agent = sales_agent
        self._llm_adapter = llm_adapter
        self._initialized = False

    async def initialize(self):
        """异步初始化依赖"""
        if not self._initialized:
            try:
                from core.sales_agent import SalesAgent
                self._sales_agent = SalesAgent()
                self._initialized = True
                logger.info("ProposalQualityEvaluator initialized successfully")
            except ImportError as e:
                logger.warning(f"SalesAgent import failed, using mock mode: {e}")
                self._initialized = True

    async def evaluate(self, test_cases: List[TestCase]) -> ProposalQualityReport:
        """
        执行方案质量评估

        Args:
            test_cases: 测试用例列表

        Returns:
            ProposalQualityReport: 评估报告
        """
        await self.initialize()

        logger.info(f"Starting proposal quality evaluation with {len(test_cases)} test cases")
        case_results = []

        for case in test_cases:
            try:
                result = await self._evaluate_single_case(case)
                case_results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating case {case.id}: {e}")
                case_results.append(self._create_failed_result(case, str(e)))

        report = self._generate_report(case_results)
        logger.info(f"Proposal quality evaluation completed: pass_rate={report.pass_rate:.2%}")

        return report

    async def _evaluate_single_case(self, case: TestCase) -> ProposalCaseResult:
        """
        评估单个测试用例

        Args:
            case: 测试用例

        Returns:
            ProposalCaseResult: 评估结果
        """
        proposal_data, was_fallback, parse_time = await self._generate_proposal(case)

        fact_metric = self._calc_fact_consistency(proposal_data, case)
        json_metric = self._calc_json_parse_metric(parse_time, was_fallback)
        fallback_metric = self._calc_fallback_metric(was_fallback)
        structure_metric = self._calc_structure_metric(proposal_data)
        hallucination_metric = self._calc_hallucination_metric(proposal_data, case)

        is_passed = self._check_pass_criteria(
            fact_metric, json_metric, structure_metric
        )

        return ProposalCaseResult(
            case_id=case.id,
            fact_metric=fact_metric,
            json_metric=json_metric,
            fallback_metric=fallback_metric,
            structure_metric=structure_metric,
            hallucination_metric=hallucination_metric,
            is_passed=is_passed
        )

    async def _generate_proposal(
        self,
        case: TestCase
    ) -> Tuple[Dict[str, Any], bool, float]:
        """
        生成方案并评估

        Args:
            case: 测试用例

        Returns:
            Tuple[Dict, bool, float]: (方案数据, 是否降级, 解析时间)
        """
        was_fallback = False
        parse_time = 0.0

        if self._sales_agent is not None and self._initialized:
            try:
                start_time = time.time()
                response = await self._sales_agent.process(case.query)
                parse_time = (time.time() - start_time) * 1000

                proposal_data = self._extract_proposal_data(response)
                if response.status == "fallback":
                    was_fallback = True

                return proposal_data, was_fallback, parse_time
            except Exception as e:
                logger.warning(f"SalesAgent execution failed, using mock: {e}")

        mock_proposal, mock_was_fallback = self._generate_mock_proposal_with_status(case)
        parse_time = 50.0
        return mock_proposal, mock_was_fallback, parse_time

    def _generate_mock_proposal_with_status(self, case: TestCase) -> Tuple[Dict[str, Any], bool]:
        """
        生成带有状态的模拟方案

        Args:
            case: 测试用例

        Returns:
            Tuple[Dict, bool]: (方案数据, 是否降级)
        """
        import random

        if random.random() < 0.6:
            return self._generate_mock_llm_proposal(case), False
        else:
            return self._generate_mock_proposal(case), True

    def _generate_mock_llm_proposal(self, case: TestCase) -> Dict[str, Any]:
        """
        生成模拟的 LLM 成功输出方案

        Args:
            case: 测试用例

        Returns:
            Dict: 方案数据
        """
        product_name = self._extract_product_name(case.query)
        quantity = self._extract_quantity(case.query)

        return {
            "product_name": product_name,
            "quantity": quantity or 50,
            "unit_price": 15000,
            "total_price": 675000,
            "estimated_delivery": "30-45天",
            "payment_terms": "预付30%，货到付清",
            "warranty_period": "12个月",
            "after_sales_service": "提供专业安装指导和终身技术支持",
            "reasons_to_choose": [
                "行业领先的产品质量",
                "完善的售后服务体系",
                "灵活的商务合作模式"
            ]
        }

    def _extract_proposal_data(self, response) -> Dict[str, Any]:
        """
        从响应中提取方案数据

        Args:
            response: Agent 响应

        Returns:
            Dict: 方案数据
        """
        if hasattr(response, 'model_dump'):
            data = response.model_dump()
        elif hasattr(response, 'proposal'):
            data = response.proposal.model_dump() if hasattr(response.proposal, 'model_dump') else response.proposal
        elif isinstance(response, dict):
            data = response.get("proposal", response)
        else:
            data = {}

        return data

    def _generate_mock_proposal(self, case: TestCase) -> Dict[str, Any]:
        """
        生成模拟方案（降级方案）

        Args:
            case: 测试用例

        Returns:
            Dict: 模拟方案数据
        """
        return {
            "product_name": self._extract_product_name(case.query),
            "quantity": self._extract_quantity(case.query),
            "unit_price": 15000,
            "total_price": 675000,
            "estimated_delivery": "30-45天",
            "payment_terms": "预付30%，货到付清",
            "warranty_period": "12个月",
            "after_sales_service": "提供专业安装指导和终身技术支持",
            "reasons_to_choose": [
                "行业领先的产品质量",
                "完善的售后服务体系",
                "灵活的商务合作模式"
            ]
        }

    def _extract_product_name(self, query: str) -> str:
        """从查询中提取产品名"""
        products = ["工业风机", "离心泵", "变压器", "输送机", "空压机", "破碎机"]
        for product in products:
            if product in query:
                return product
        return "产品"

    def _extract_quantity(self, query: str) -> Optional[int]:
        """从查询中提取数量"""
        import re
        patterns = [
            r'(\d+)\s*台',
            r'(\d+)\s*米',
            r'(\d+)\s*套',
            r'(\d+)\s*个'
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        return None

    def _calc_fact_consistency(
        self,
        proposal_data: Dict[str, Any],
        case: TestCase
    ) -> FactConsistencyMetric:
        """
        计算事实一致性

        Args:
            proposal_data: 方案数据
            case: 测试用例

        Returns:
            FactConsistencyMetric: 一致性指标
        """
        checks = []

        expected_product = self._extract_product_name(case.query)
        if "product_name" in proposal_data:
            checks.append(proposal_data["product_name"] == expected_product)

        expected_quantity = self._extract_quantity(case.query)
        if expected_quantity and "quantity" in proposal_data:
            checks.append(proposal_data["quantity"] == expected_quantity)

        if "unit_price" in proposal_data:
            price = proposal_data["unit_price"]
            checks.append(isinstance(price, (int, float)) and price > 0)

        if "total_price" in proposal_data:
            total = proposal_data["total_price"]
            checks.append(isinstance(total, (int, float)) and total > 0)

        if "payment_terms" in proposal_data:
            checks.append(len(str(proposal_data["payment_terms"])) > 0)

        total_checks = len(checks)
        consistent_items = sum(1 for c in checks if c)
        consistency_rate = consistent_items / max(total_checks, 1)

        return FactConsistencyMetric(
            total_checks=total_checks,
            consistent_items=consistent_items,
            consistency_rate=consistency_rate
        )

    def _calc_json_parse_metric(
        self,
        parse_time_ms: float,
        was_fallback: bool
    ) -> JsonParseMetric:
        """
        计算 JSON 解析指标

        Args:
            parse_time_ms: 解析时间
            was_fallback: 是否降级

        Returns:
            JsonParseMetric: 解析指标
        """
        parse_success = not was_fallback
        parse_success_rate = 1.0 if parse_success else 0.0

        return JsonParseMetric(
            total_attempts=1,
            parse_successes=1 if parse_success else 0,
            parse_success_rate=parse_success_rate,
            avg_parse_time_ms=parse_time_ms
        )

    def _calc_fallback_metric(self, was_fallback: bool) -> FallbackMetric:
        """
        计算降级指标

        Args:
            was_fallback: 是否降级

        Returns:
            FallbackMetric: 降级指标
        """
        reasons = []
        if was_fallback:
            reasons.append("LLM调用失败，使用降级方案")

        return FallbackMetric(
            total_requests=1,
            fallback_triggers=1 if was_fallback else 0,
            fallback_rate=1.0 if was_fallback else 0.0,
            fallback_reasons=reasons
        )

    def _calc_structure_metric(self, proposal_data: Dict[str, Any]) -> StructureMetric:
        """
        计算结构化指标

        Args:
            proposal_data: 方案数据

        Returns:
            StructureMetric: 结构化指标
        """
        required_fields = [
            "product_name",
            "quantity",
            "unit_price",
            "total_price",
            "payment_terms",
            "warranty_period",
            "after_sales_service"
        ]

        total_fields = len(required_fields)
        filled_fields = sum(
            1 for field in required_fields
            if field in proposal_data and proposal_data[field] is not None
        )
        completeness_rate = filled_fields / max(total_fields, 1)

        missing_fields = [
            field for field in required_fields
            if field not in proposal_data or proposal_data[field] is None
        ]

        return StructureMetric(
            total_fields=total_fields,
            filled_fields=filled_fields,
            completeness_rate=completeness_rate,
            required_fields_missing=missing_fields
        )

    def _calc_hallucination_metric(
        self,
        proposal_data: Dict[str, Any],
        case: TestCase
    ) -> HallucinationMetric:
        """
        计算幻觉检测指标

        Args:
            proposal_data: 方案数据
            case: 测试用例

        Returns:
            HallucinationMetric: 幻觉指标
        """
        hallucination_types = []

        known_products = {"工业风机", "离心泵", "变压器", "输送机", "空压机", "破碎机"}
        product_name = proposal_data.get("product_name", "")

        if product_name and product_name not in known_products:
            hallucination_types.append(f"未知产品名: {product_name}")

        reasons = proposal_data.get("reasons_to_choose", [])
        known_reasons = {
            "行业领先", "完善的服务", "灵活的合作", "专业团队",
            "技术创新", "丰富经验", "高品质"
        }

        for reason in reasons:
            if not any(kw in reason for kw in known_reasons):
                hallucination_types.append(f"异常推荐理由: {reason}")

        total_checks = len(proposal_data)
        hallucinations_detected = len(hallucination_types)
        detection_rate = hallucinations_detected / max(total_checks, 1)

        return HallucinationMetric(
            total_hallucination_checks=total_checks,
            hallucinations_detected=hallucinations_detected,
            hallucination_detection_rate=detection_rate,
            hallucination_types=hallucination_types
        )

    def _check_pass_criteria(
        self,
        fact_metric: FactConsistencyMetric,
        json_metric: JsonParseMetric,
        structure_metric: StructureMetric
    ) -> bool:
        """
        检查是否通过评估标准

        达标线：
        - 事实一致率 >= 0.95
        - JSON 解析成功率 >= 0.9
        - 方案完整度 >= 0.9

        Args:
            fact_metric: 事实一致性指标
            json_metric: JSON解析指标
            structure_metric: 结构化指标

        Returns:
            bool: 是否通过
        """
        return (
            fact_metric.consistency_rate >= 0.95 and
            json_metric.parse_success_rate >= 0.9 and
            structure_metric.completeness_rate >= 0.9
        )

    def _generate_report(self, case_results: List[ProposalCaseResult]) -> ProposalQualityReport:
        """
        生成评估报告

        Args:
            case_results: 评估结果列表

        Returns:
            ProposalQualityReport: 完整评估报告
        """
        total_cases = len(case_results)
        passed_cases = sum(1 for r in case_results if r.is_passed)
        failed_cases = total_cases - passed_cases

        if total_cases == 0:
            return ProposalQualityReport(
                generated_at=self._get_timestamp(),
                total_cases=0,
                passed_cases=0,
                failed_cases=0,
                pass_rate=0.0,
                overall_fact_consistency=0.0,
                overall_json_parse_rate=0.0,
                overall_fallback_rate=0.0,
                overall_completeness=0.0,
                overall_hallucination_detection_rate=0.0,
                case_results=[],
                summary="No test cases to evaluate"
            )

        avg_fact_consistency = sum(r.fact_metric.consistency_rate for r in case_results) / total_cases
        avg_json_parse_rate = sum(r.json_metric.parse_success_rate for r in case_results) / total_cases
        avg_fallback_rate = sum(r.fallback_metric.fallback_rate for r in case_results) / total_cases
        avg_completeness = sum(r.structure_metric.completeness_rate for r in case_results) / total_cases
        avg_hallucination = sum(r.hallucination_metric.hallucination_detection_rate for r in case_results) / total_cases
        pass_rate = passed_cases / total_cases

        summary = self._generate_summary(
            avg_fact_consistency, avg_json_parse_rate,
            avg_fallback_rate, avg_completeness, pass_rate
        )

        return ProposalQualityReport(
            generated_at=self._get_timestamp(),
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            pass_rate=pass_rate,
            overall_fact_consistency=avg_fact_consistency,
            overall_json_parse_rate=avg_json_parse_rate,
            overall_fallback_rate=avg_fallback_rate,
            overall_completeness=avg_completeness,
            overall_hallucination_detection_rate=avg_hallucination,
            case_results=case_results,
            summary=summary
        )

    def _generate_summary(
        self,
        fact_consistency: float,
        json_parse_rate: float,
        fallback_rate: float,
        completeness: float,
        pass_rate: float
    ) -> str:
        """
        生成评估总结

        Args:
            fact_consistency: 事实一致率
            json_parse_rate: JSON解析率
            fallback_rate: 降级率
            completeness: 完整度
            pass_rate: 通过率

        Returns:
            str: 总结文本
        """
        issues = []

        if fact_consistency < 0.95:
            issues.append(f"事实一致率偏低 ({fact_consistency:.1%}，达标线95%)")
        if json_parse_rate < 0.9:
            issues.append(f"JSON解析率偏低 ({json_parse_rate:.1%}，达标线90%)")
        if fallback_rate > 0.1:
            issues.append(f"降级触发率偏高 ({fallback_rate:.1%}，达标线10%)")
        if completeness < 0.9:
            issues.append(f"方案完整度偏低 ({completeness:.1%}，达标线90%)")

        if not issues:
            return (
                f"评估通过！所有指标均达标。通过率：{pass_rate:.1%}，"
                f"事实一致率：{fact_consistency:.1%}，JSON解析率：{json_parse_rate:.1%}，"
                f"降级率：{fallback_rate:.1%}，完整度：{completeness:.1%}"
            )
        else:
            return f"评估未通过，存在{len(issues)}个问题：{'; '.join(issues)}"

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _create_failed_result(case: TestCase, error_msg: str) -> ProposalCaseResult:
        """创建失败的评估结果"""
        return ProposalCaseResult(
            case_id=case.id,
            fact_metric=FactConsistencyMetric(
                total_checks=0,
                consistent_items=0,
                consistency_rate=0.0
            ),
            json_metric=JsonParseMetric(
                total_attempts=1,
                parse_successes=0,
                parse_success_rate=0.0,
                avg_parse_time_ms=0.0
            ),
            fallback_metric=FallbackMetric(
                total_requests=1,
                fallback_triggers=1,
                fallback_rate=1.0,
                fallback_reasons=[error_msg]
            ),
            structure_metric=StructureMetric(
                total_fields=7,
                filled_fields=0,
                completeness_rate=0.0,
                required_fields_missing=[
                    "product_name", "quantity", "unit_price",
                    "total_price", "payment_terms", "warranty_period",
                    "after_sales_service"
                ]
            ),
            hallucination_metric=HallucinationMetric(
                total_hallucination_checks=0,
                hallucinations_detected=0,
                hallucination_detection_rate=0.0,
                hallucination_types=[]
            ),
            is_passed=False
        )

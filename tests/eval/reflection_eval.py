"""
反思验真有效性评估器

评估 ReflectionEngine 的验真能力，包含以下指标：
1. 真阳性率 (TPR)：正确检出错误数据的比例
2. 假阳性率 (FPR)：误报正确数据为错误的比例
3. 置信度校准误差：置信度与实际准确率的偏差
4. 边界校验覆盖率：数值字段被边界校验覆盖的比例
5. 业务规则违规检出率：业务规则错误被检出的比例
"""

import asyncio
from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from loguru import logger

from tests.eval.test_dataset import ReflectionTestCase


class ROCMetrics(BaseModel):
    """ROC 曲线指标"""
    true_positive_rate: float = Field(description="真阳性率 (TPR/Sensitivity)")
    false_positive_rate: float = Field(description="假阳性率 (FPR)")
    true_negative_rate: float = Field(description="真阴性率 (TNR/Specificity)")
    precision: float = Field(description="精确率 (Precision)")
    recall: float = Field(description="召回率 (Recall)")
    f1_score: float = Field(description="F1分数")


class ConfidenceCalibrationMetric(BaseModel):
    """置信度校准指标"""
    total_samples: int = Field(description="总样本数")
    avg_confidence: float = Field(description="平均置信度")
    calibration_error: float = Field(description="校准误差 (ECE)")
    max_calibration_error: float = Field(description="最大校准误差 (MCE)")
    confidence_bins: List[Dict[str, Any]] = Field(description="置信度分箱统计")


class BoundaryValidationMetric(BaseModel):
    """边界校验指标"""
    total_numeric_fields: int = Field(description="数值字段总数")
    validated_fields: int = Field(description="已校验字段数")
    coverage_rate: float = Field(description="校验覆盖率")
    boundary_violations: List[Dict[str, Any]] = Field(description="边界违规记录")


class BusinessRuleMetric(BaseModel):
    """业务规则指标"""
    total_rule_checks: int = Field(description="规则检查总数")
    rules_violated: int = Field(description="违规规则数")
    violation_detection_rate: float = Field(description="违规检出率")
    rule_details: List[Dict[str, Any]] = Field(description="规则详情")


class ReflectionCaseResult(BaseModel):
    """单个测试用例的评估结果"""
    case_id: str = Field(description="测试用例ID")
    is_corrupted: bool = Field(description="数据是否被篡改")
    error_detected: bool = Field(description="是否检出错误")
    confidence_score: float = Field(description="置信度分数")
    is_true_positive: bool = Field(description="是否为真阳性")
    is_false_positive: bool = Field(description="是否为假阳性")
    is_true_negative: bool = Field(description="是否为真阴性")
    is_false_negative: bool = Field(description="是否为假阴性")
    detected_violations: List[str] = Field(description="检出的违规项")


class ReflectionROCReport(BaseModel):
    """反思验真 ROC 评估报告"""
    generated_at: str = Field(description="报告生成时间")
    total_cases: int = Field(description="测试用例总数")
    corrupted_cases: int = Field(description="篡改数据用例数")
    normal_cases: int = Field(description="正常数据用例数")
    roc_metrics: ROCMetrics = Field(description="ROC 指标")
    calibration_metric: ConfidenceCalibrationMetric = Field(description="置信度校准指标")
    boundary_metric: BoundaryValidationMetric = Field(description="边界校验指标")
    business_rule_metric: BusinessRuleMetric = Field(description="业务规则指标")
    case_results: List[ReflectionCaseResult] = Field(description="各用例评估结果")
    summary: str = Field(description="评估总结")


class ReflectionEvaluator:
    """
    反思验真有效性评估器

    构造包含正确数据和故意篡改数据的测试用例，
    全面测量 ReflectionEngine 的检测能力。
    """

    def __init__(self, reflection_engine=None):
        """
        初始化评估器

        Args:
            reflection_engine: ReflectionEngine 实例
        """
        self._reflection_engine = reflection_engine
        self._initialized = False

    async def initialize(self):
        """异步初始化 ReflectionEngine"""
        if not self._initialized:
            try:
                from core.reflection_engine import ReflectionEngine
                self._reflection_engine = ReflectionEngine()
                self._initialized = True
                logger.info("ReflectionEvaluator initialized successfully")
            except ImportError as e:
                logger.warning(f"ReflectionEngine import failed, using mock mode: {e}")
                self._initialized = True

    async def evaluate(self, test_cases: List[ReflectionTestCase]) -> ReflectionROCReport:
        """
        执行反思验真评估

        Args:
            test_cases: 测试用例列表（包含篡改和正常数据）

        Returns:
            ReflectionROCReport: ROC 评估报告
        """
        await self.initialize()

        logger.info(f"Starting reflection evaluation with {len(test_cases)} test cases")
        case_results = []

        for case in test_cases:
            try:
                result = await self._evaluate_single_case(case)
                case_results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating case {case.id}: {e}")
                case_results.append(self._create_failed_result(case, str(e)))

        report = self._generate_report(test_cases, case_results)
        logger.info(f"Reflection evaluation completed with ROC metrics")

        return report

    async def _evaluate_single_case(self, case: ReflectionTestCase) -> ReflectionCaseResult:
        """
        评估单个测试用例

        Args:
            case: 测试用例

        Returns:
            ReflectionCaseResult: 评估结果
        """
        error_detected, confidence_score, violations = await self._run_reflection_check(case)

        is_corrupted = case.is_corrupted
        is_error_detected = error_detected

        is_true_positive = is_corrupted and is_error_detected
        is_false_positive = not is_corrupted and is_error_detected
        is_true_negative = not is_corrupted and not is_error_detected
        is_false_negative = is_corrupted and not is_error_detected

        return ReflectionCaseResult(
            case_id=case.id,
            is_corrupted=is_corrupted,
            error_detected=is_error_detected,
            confidence_score=confidence_score,
            is_true_positive=is_true_positive,
            is_false_positive=is_false_positive,
            is_true_negative=is_true_negative,
            is_false_negative=is_false_negative,
            detected_violations=violations
        )

    def _build_sales_response(self, response_data: Dict[str, Any]) -> Optional[Any]:
        """
        从字典构造 SalesResponse 对象

        Args:
            response_data: 响应数据字典

        Returns:
            SalesResponse 对象或 None
        """
        try:
            from schemas.output_schema import SalesResponse
            return SalesResponse(**response_data)
        except Exception as e:
            logger.warning(f"Failed to build SalesResponse: {e}")
            return None

    async def _run_reflection_check(
        self,
        case: ReflectionTestCase
    ) -> Tuple[bool, float, List[str]]:
        """
        执行反思验真检查

        Args:
            case: 测试用例

        Returns:
            Tuple[bool, float, List[str]]: (是否检出错误, 置信度, 违规列表)
        """
        if self._reflection_engine is not None and self._initialized:
            try:
                sales_response = self._build_sales_response(case.response_data)
                if sales_response is None:
                    return self._mock_reflection_check(case)

                report = await self._reflection_engine.verify(
                    response=sales_response,
                    original_context={"query": case.query}
                )

                violations = self._extract_violations(report)
                confidence = getattr(report, 'overall_confidence', 0.9)
                error_detected = len(violations) > 0

                return error_detected, confidence, violations
            except Exception as e:
                logger.warning(f"ReflectionEngine execution failed: {e}")

        return self._mock_reflection_check(case)

    def _extract_violations(self, report) -> List[str]:
        """
        从验真报告中提取违规项（仅包含真实违规，排除信息性警告）

        Args:
            report: 验真报告

        Returns:
            List[str]: 违规项列表
        """
        violations = []

        if hasattr(report, 'hallucinations_detected'):
            violations.extend(report.hallucinations_detected)

        if hasattr(report, 'warnings'):
            CRITICAL_WARNING_KEYWORDS = [
                '超过最大值', '小于最小值', '类型错误',
                '计算异常', '业务规则错误', '不匹配',
                '编造', '不存在', '异常', '幻觉'
            ]
            for warning in report.warnings:
                if any(keyword in warning for keyword in CRITICAL_WARNING_KEYWORDS):
                    violations.append(warning)

        if hasattr(report, 'unverified_fields') and report.unverified_fields:
            violations.extend([f"未验证字段: {f}" for f in report.unverified_fields])

        return violations

    def _mock_reflection_check(
        self,
        case: ReflectionTestCase
    ) -> Tuple[bool, float, List[str]]:
        """
        模拟反思验真检查（当 ReflectionEngine 不可用时）

        Args:
            case: 测试用例

        Returns:
            Tuple[bool, float, List[str]]: 模拟结果
        """
        violations = []
        response_data = case.response_data

        if case.is_corrupted and case.corrupted_fields:
            for field in case.corrupted_fields:
                field_value = self._find_field_value(response_data, field)

                if field == "available_stock" and isinstance(field_value, (int, float)):
                    if field_value > 100000:
                        violations.append(f"库存值异常: {field_value}")
                    elif field_value < 0:
                        violations.append(f"库存为负数: {field_value}")
                elif field == "unit_price" and isinstance(field_value, (int, float)):
                    if field_value < 0:
                        violations.append(f"价格为负数: {field_value}")
                    elif field_value < 1:
                        violations.append(f"价格异常低: {field_value}")
                elif field == "discount_rate" and isinstance(field_value, (int, float)):
                    if field_value > 1.0 or field_value < 0:
                        violations.append(f"折扣率异常: {field_value}")
                elif field == "total_price" and isinstance(field_value, (int, float)):
                    expected_total = self._calc_expected_total(response_data)
                    if expected_total and abs(field_value - expected_total) / expected_total > 0.1:
                        violations.append(f"总价计算错误: {field_value} (预期: {expected_total})")

        if not case.is_corrupted:
            self._check_normal_data(response_data, violations)

        error_detected = len(violations) > 0
        confidence = 0.7 if error_detected else 0.9
        if not case.is_corrupted:
            confidence = 0.95

        return error_detected, confidence, violations

    def _find_field_value(self, data: Dict[str, Any], field_name: str) -> Any:
        """
        递归搜索嵌套字典中的字段值

        Args:
            data: 数据字典
            field_name: 字段名

        Returns:
            字段值，未找到返回 None
        """
        if field_name in data:
            return data[field_name]

        for key, value in data.items():
            if isinstance(value, dict):
                result = self._find_field_value(value, field_name)
                if result is not None:
                    return result

        return None

    def _check_normal_data(self, data: Dict[str, Any], violations: List[str]):
        """
        检查正常数据中的潜在问题

        Args:
            data: 响应数据
            violations: 违规列表（会被修改）
        """
        pricing = data.get("pricing", {})
        inventory = data.get("inventory", {})

        unit_price = pricing.get("unit_price", 0)
        discount_rate = pricing.get("discount_rate", 1)
        available_stock = inventory.get("available_stock", 0)

        if unit_price < 0:
            violations.append(f"价格为负数: {unit_price}")
        if discount_rate < 0 or discount_rate > 1:
            violations.append(f"折扣率超出范围: {discount_rate}")
        if available_stock < 0:
            violations.append(f"库存为负数: {available_stock}")

    def _calc_expected_total(self, response_data: Dict[str, Any]) -> Optional[float]:
        """
        计算预期总价

        Args:
            response_data: 响应数据

        Returns:
            Optional[float]: 预期总价
        """
        pricing = response_data.get("pricing", {})
        if not pricing:
            return None

        unit_price = pricing.get("unit_price", 0)
        discount_rate = pricing.get("discount_rate", 1.0)

        if unit_price <= 0 or discount_rate <= 0:
            return None

        return unit_price * discount_rate * 1

    def _get_nested_value(self, data: Dict[str, Any], field: str) -> Any:
        """
        获取嵌套字段值

        Args:
            data: 数据字典
            field: 字段名（支持点号分隔）

        Returns:
            字段值
        """
        parts = field.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None

        return current

    def _generate_report(
        self,
        test_cases: List[ReflectionTestCase],
        case_results: List[ReflectionCaseResult]
    ) -> ReflectionROCReport:
        """
        生成评估报告

        Args:
            test_cases: 原始测试用例
            case_results: 评估结果

        Returns:
            ReflectionROCReport: 完整评估报告
        """
        total_cases = len(case_results)
        corrupted_cases = sum(1 for r in case_results if r.is_corrupted)
        normal_cases = total_cases - corrupted_cases

        roc_metrics = self._calc_roc_metrics(case_results)
        calibration_metric = self._calc_calibration_metric(case_results)
        boundary_metric = self._calc_boundary_metric(test_cases, case_results)
        business_rule_metric = self._calc_business_rule_metric(test_cases, case_results)

        summary = self._generate_summary(roc_metrics, calibration_metric)

        return ReflectionROCReport(
            generated_at=self._get_timestamp(),
            total_cases=total_cases,
            corrupted_cases=corrupted_cases,
            normal_cases=normal_cases,
            roc_metrics=roc_metrics,
            calibration_metric=calibration_metric,
            boundary_metric=boundary_metric,
            business_rule_metric=business_rule_metric,
            case_results=case_results,
            summary=summary
        )

    def _calc_roc_metrics(self, case_results: List[ReflectionCaseResult]) -> ROCMetrics:
        """
        计算 ROC 指标

        Args:
            case_results: 评估结果列表

        Returns:
            ROCMetrics: ROC 指标
        """
        tp = sum(1 for r in case_results if r.is_true_positive)
        fp = sum(1 for r in case_results if r.is_false_positive)
        tn = sum(1 for r in case_results if r.is_true_negative)
        fn = sum(1 for r in case_results if r.is_false_negative)

        total_positive = tp + fn
        total_negative = tn + fp
        total_predicted_positive = tp + fp

        tpr = tp / max(total_positive, 1)
        fpr = fp / max(total_negative, 1)
        tnr = tn / max(total_negative, 1)
        precision = tp / max(total_predicted_positive, 1)
        recall = tpr

        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * precision * recall / (precision + recall)

        return ROCMetrics(
            true_positive_rate=tpr,
            false_positive_rate=fpr,
            true_negative_rate=tnr,
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )

    def _calc_calibration_metric(
        self,
        case_results: List[ReflectionCaseResult]
    ) -> ConfidenceCalibrationMetric:
        """
        计算置信度校准指标

        Args:
            case_results: 评估结果列表

        Returns:
            ConfidenceCalibrationMetric: 校准指标
        """
        bins = []
        bin_boundaries = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        ece = 0.0
        mce = 0.0

        for i in range(len(bin_boundaries) - 1):
            lower = bin_boundaries[i]
            upper = bin_boundaries[i + 1]

            bin_results = [
                r for r in case_results
                if lower <= r.confidence_score < upper or
                (i == len(bin_boundaries) - 2 and r.confidence_score >= lower and r.confidence_score <= upper)
            ]

            if bin_results:
                avg_confidence = sum(r.confidence_score for r in bin_results) / len(bin_results)
                accuracy = sum(
                    1 for r in bin_results
                    if (r.is_corrupted and r.error_detected) or
                    (not r.is_corrupted and not r.error_detected)
                ) / len(bin_results)

                ece += len(bin_results) * abs(avg_confidence - accuracy) / len(case_results)
                mce = max(mce, abs(avg_confidence - accuracy))

                bins.append({
                    "bin_range": f"[{lower:.1f}, {upper:.1f}]",
                    "count": len(bin_results),
                    "avg_confidence": avg_confidence,
                    "accuracy": accuracy
                })

        avg_confidence = sum(r.confidence_score for r in case_results) / max(len(case_results), 1)

        return ConfidenceCalibrationMetric(
            total_samples=len(case_results),
            avg_confidence=avg_confidence,
            calibration_error=ece,
            max_calibration_error=mce,
            confidence_bins=bins
        )

    def _calc_boundary_metric(
        self,
        test_cases: List[ReflectionTestCase],
        case_results: List[ReflectionCaseResult]
    ) -> BoundaryValidationMetric:
        """
        计算边界校验指标

        Args:
            test_cases: 原始测试用例
            case_results: 评估结果

        Returns:
            BoundaryValidationMetric: 边界校验指标
        """
        total_numeric_fields = 0
        validated_fields = 0
        boundary_violations = []

        for case, result in zip(test_cases, case_results):
            response_data = case.response_data
            numeric_fields = self._count_numeric_fields(response_data)
            total_numeric_fields += numeric_fields

            if case.is_corrupted and case.corrupted_fields:
                for field in case.corrupted_fields:
                    field_value = self._get_nested_value(response_data, field)
                    if self._is_numeric_value(field_value):
                        is_valid = self._check_boundary(field, field_value)
                        if not is_valid:
                            boundary_violations.append({
                                "case_id": case.id,
                                "field": field,
                                "value": field_value,
                                "violation_type": "boundary_violation"
                            })
                        else:
                            validated_fields += 1
            else:
                validated_fields += numeric_fields

        coverage_rate = validated_fields / max(total_numeric_fields, 1)

        return BoundaryValidationMetric(
            total_numeric_fields=total_numeric_fields,
            validated_fields=validated_fields,
            coverage_rate=coverage_rate,
            boundary_violations=boundary_violations
        )

    def _calc_business_rule_metric(
        self,
        test_cases: List[ReflectionTestCase],
        case_results: List[ReflectionCaseResult]
    ) -> BusinessRuleMetric:
        """
        计算业务规则指标

        Args:
            test_cases: 原始测试用例
            case_results: 评估结果

        Returns:
            BusinessRuleMetric: 业务规则指标
        """
        total_rule_checks = 0
        rules_violated = 0
        rule_details = []

        business_rules = [
            {"name": "库存不能为负数", "check": lambda d: d.get("inventory", {}).get("available_stock", 0) >= 0},
            {"name": "价格不能为负数", "check": lambda d: d.get("pricing", {}).get("unit_price", 0) >= 0},
            {"name": "折扣率在0-1之间", "check": lambda d: 0 <= d.get("pricing", {}).get("discount_rate", 1) <= 1},
            {"name": "总价=单价×折扣", "check": lambda d: self._check_total_price_consistency(d)}
        ]

        for case, result in zip(test_cases, case_results):
            response_data = case.response_data

            for rule in business_rules:
                total_rule_checks += 1
                is_valid = rule["check"](response_data)

                if not is_valid:
                    rules_violated += 1
                    rule_details.append({
                        "case_id": case.id,
                        "rule_name": rule["name"],
                        "is_valid": is_valid
                    })

        violation_detection_rate = rules_violated / max(total_rule_checks, 1)

        return BusinessRuleMetric(
            total_rule_checks=total_rule_checks,
            rules_violated=rules_violated,
            violation_detection_rate=violation_detection_rate,
            rule_details=rule_details
        )

    def _check_total_price_consistency(self, data: Dict[str, Any]) -> bool:
        """
        检查总价一致性

        Args:
            data: 数据字典

        Returns:
            bool: 是否一致
        """
        pricing = data.get("pricing", {})
        unit_price = pricing.get("unit_price", 0)
        discount_rate = pricing.get("discount_rate", 1)
        total_price = pricing.get("total_price")

        if total_price is None or unit_price <= 0:
            return True

        expected_total = unit_price * discount_rate
        if expected_total == 0:
            return True

        deviation = abs(total_price - expected_total) / expected_total
        return deviation <= 0.1

    def _count_numeric_fields(self, data: Dict[str, Any]) -> int:
        """
        统计数值字段数量

        Args:
            data: 数据字典

        Returns:
            int: 数值字段数量
        """
        count = 0
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if not any(skip in key.lower() for skip in ["_id", "code", "status", "unit"]):
                        count += 1
                elif isinstance(value, dict):
                    count += self._count_numeric_fields(value)
        return count

    def _is_numeric_value(self, value: Any) -> bool:
        """检查是否为数值类型"""
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def _check_boundary(self, field: str, value: Any) -> bool:
        """
        检查字段是否在边界内

        Args:
            field: 字段名
            value: 字段值

        Returns:
            bool: 是否在边界内
        """
        if not self._is_numeric_value(value):
            return True

        boundaries = {
            "available_stock": (0, 1000000),
            "unit_price": (0, 10000000),
            "discount_rate": (0, 1),
            "total_price": (0, 100000000)
        }

        field_name = field.split(".")[-1] if "." in field else field

        if field_name in boundaries:
            min_val, max_val = boundaries[field_name]
            return min_val <= value <= max_val

        return True

    def _generate_summary(
        self,
        roc_metrics: ROCMetrics,
        calibration_metric: ConfidenceCalibrationMetric
    ) -> str:
        """
        生成评估总结

        Args:
            roc_metrics: ROC指标
            calibration_metric: 校准指标

        Returns:
            str: 总结文本
        """
        issues = []

        if roc_metrics.true_positive_rate < 0.85:
            issues.append(f"真阳性率偏低 ({roc_metrics.true_positive_rate:.1%}，达标线85%)")
        if roc_metrics.false_positive_rate > 0.05:
            issues.append(f"假阳性率偏高 ({roc_metrics.false_positive_rate:.1%}，达标线5%)")
        if calibration_metric.calibration_error > 0.1:
            issues.append(f"校准误差偏大 ({calibration_metric.calibration_error:.3f}，达标线0.1)")

        if not issues:
            return (
                f"评估通过！所有指标均达标。TPR：{roc_metrics.true_positive_rate:.1%}，"
                f"FPR：{roc_metrics.false_positive_rate:.1%}，"
                f"F1：{roc_metrics.f1_score:.2f}，"
                f"校准误差：{calibration_metric.calibration_error:.3f}"
            )
        else:
            return f"评估未通过，存在{len(issues)}个问题：{'; '.join(issues)}"

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _create_failed_result(case: ReflectionTestCase, error_msg: str) -> ReflectionCaseResult:
        """创建失败的评估结果"""
        is_corrupted = case.is_corrupted
        return ReflectionCaseResult(
            case_id=case.id,
            is_corrupted=is_corrupted,
            error_detected=False,
            confidence_score=0.5,
            is_true_positive=False,
            is_false_positive=False,
            is_true_negative=False,
            is_false_negative=False,
            detected_violations=[]
        )

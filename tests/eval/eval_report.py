"""
评估报告生成器

汇总所有评估维度的结果，生成完整的综合评估报告。
支持生成 Markdown 格式的报告文件。
"""

import json
from typing import Optional
from pydantic import BaseModel, Field
from loguru import logger

from tests.eval.task_planning_eval import TaskPlanningReport
from tests.eval.tool_accuracy_eval import ToolAccuracyReport
from tests.eval.reflection_eval import ReflectionROCReport
from tests.eval.proposal_quality_eval import ProposalQualityReport
from tests.eval.e2e_performance_eval import PerformanceReport


class DimensionScore(BaseModel):
    """维度评分"""
    name: str = Field(description="维度名称")
    score: float = Field(description="得分 (0-100)")
    weight: float = Field(description="权重")
    weighted_score: float = Field(description="加权得分")
    status: str = Field(description="状态: passed/warning/failed")
    key_metrics: dict = Field(description="关键指标")


class OverallScore(BaseModel):
    """综合评分"""
    total_score: float = Field(description="总得分 (0-100)")
    dimension_scores: list = Field(description="各维度得分")
    grade: str = Field(description="等级: A/B/C/D/E")
    passed_dimensions: int = Field(description="通过的维度数")
    total_dimensions: int = Field(description="总维度数")


class ImprovementSuggestion(BaseModel):
    """改进建议"""
    dimension: str = Field(description="所属维度")
    priority: str = Field(description="优先级: high/medium/low")
    issue: str = Field(description="问题描述")
    suggestion: str = Field(description="改进建议")


class FullEvalReport(BaseModel):
    """完整评估报告"""
    generated_at: str = Field(description="报告生成时间")
    overall_score: OverallScore = Field(description="综合评分")
    task_planning_report: Optional[TaskPlanningReport] = Field(None, description="任务拆解报告")
    tool_accuracy_report: Optional[ToolAccuracyReport] = Field(None, description="工具准确性报告")
    reflection_report: Optional[ReflectionROCReport] = Field(None, description="反思验真报告")
    proposal_quality_report: Optional[ProposalQualityReport] = Field(None, description="方案质量报告")
    performance_report: Optional[PerformanceReport] = Field(None, description="性能报告")
    suggestions: list = Field(default_factory=list, description="改进建议列表")
    conclusions: list = Field(default_factory=list, description="结论列表")


class EvalReportGenerator:
    """
    评估报告生成器

    将各维度的评估结果汇总为统一的综合报告，
    计算加权评分并生成改进建议。
    """

    # 各维度权重配置
    DIMENSION_WEIGHTS = {
        "task_planning": 0.20,
        "tool_accuracy": 0.25,
        "reflection": 0.20,
        "proposal": 0.15,
        "performance": 0.20
    }

    # 达标线配置
    PASS_THRESHOLDS = {
        "task_planning": {
            "overall_task_type_accuracy": 0.90,
            "overall_param_f1": 0.85,
            "overall_count_deviation_rate": 0.10
        },
        "tool_accuracy": {
            "overall_field_consistency": 0.98,
            "overall_numeric_deviation": 0.02,
            "overall_success_rate": 0.99
        },
        "reflection": {
            "true_positive_rate": 0.85,
            "false_positive_rate": 0.05,
            "calibration_error": 0.10
        },
        "proposal": {
            "overall_fact_consistency": 0.95,
            "overall_json_parse_rate": 0.90,
            "overall_completeness": 0.90
        },
        "performance": {
            "p50_latency_ms": 5000,
            "p95_latency_ms": 15000,
            "success_rate": 0.95,
            "error_rate": 0.05,
            "avg_total_tokens": 4000
        }
    }

    def generate_full_report(
        self,
        task_report: Optional[TaskPlanningReport] = None,
        tool_report: Optional[ToolAccuracyReport] = None,
        reflection_report: Optional[ReflectionROCReport] = None,
        proposal_report: Optional[ProposalQualityReport] = None,
        performance_report: Optional[PerformanceReport] = None
    ) -> FullEvalReport:
        """
        生成完整评估报告

        Args:
            task_report: 任务拆解报告
            tool_report: 工具准确性报告
            reflection_report: 反思验真报告
            proposal_report: 方案质量报告
            performance_report: 性能报告

        Returns:
            FullEvalReport: 完整评估报告
        """
        logger.info("Generating full evaluation report")

        dimension_scores = []

        if task_report:
            task_score = self._calc_task_planning_score(task_report)
            dimension_scores.append(task_score)

        if tool_report:
            tool_score = self._calc_tool_accuracy_score(tool_report)
            dimension_scores.append(tool_score)

        if reflection_report:
            reflection_score = self._calc_reflection_score(reflection_report)
            dimension_scores.append(reflection_score)

        if proposal_report:
            proposal_score = self._calc_proposal_score(proposal_report)
            dimension_scores.append(proposal_score)

        if performance_report:
            performance_score = self._calc_performance_score(performance_report)
            dimension_scores.append(performance_score)

        overall_score = self._calc_overall_score(dimension_scores)

        suggestions = self._generate_suggestions(
            task_report, tool_report, reflection_report,
            proposal_report, performance_report
        )

        conclusions = self._generate_conclusions(overall_score, dimension_scores)

        return FullEvalReport(
            generated_at=self._get_timestamp(),
            overall_score=overall_score,
            task_planning_report=task_report,
            tool_accuracy_report=tool_report,
            reflection_report=reflection_report,
            proposal_quality_report=proposal_report,
            performance_report=performance_report,
            suggestions=suggestions,
            conclusions=conclusions
        )

    def _calc_task_planning_score(self, report: TaskPlanningReport) -> DimensionScore:
        """计算任务拆解维度得分"""
        score = 0.0
        key_metrics = {}

        accuracy = report.overall_task_type_accuracy * 100
        score += accuracy * 0.35
        key_metrics["任务类型准确率"] = f"{report.overall_task_type_accuracy:.1%}"

        f1 = report.overall_param_f1 * 100
        score += f1 * 0.35
        key_metrics["参数提取F1"] = f"{report.overall_param_f1:.2f}"

        deviation_penalty = min(report.overall_count_deviation_rate, 0.2) * 50
        score += (100 - deviation_penalty) * 0.30
        key_metrics["任务数偏差率"] = f"{report.overall_count_deviation_rate:.1%}"

        score = max(0, min(100, score))
        passed = self._check_task_planning_pass(report)

        return DimensionScore(
            name="任务拆解质量",
            score=round(score, 1),
            weight=self.DIMENSION_WEIGHTS["task_planning"],
            weighted_score=round(score * self.DIMENSION_WEIGHTS["task_planning"], 2),
            status="passed" if passed else ("warning" if score >= 70 else "failed"),
            key_metrics=key_metrics
        )

    def _calc_tool_accuracy_score(self, report: ToolAccuracyReport) -> DimensionScore:
        """计算工具准确性维度得分"""
        score = 0.0
        key_metrics = {}

        consistency = report.overall_field_consistency * 100
        score += consistency * 0.40
        key_metrics["字段一致率"] = f"{report.overall_field_consistency:.1%}"

        deviation = (1 - min(report.overall_numeric_deviation, 0.1)) * 100
        score += deviation * 0.35
        key_metrics["数值偏差率"] = f"{report.overall_numeric_deviation:.2%}"

        success = report.overall_success_rate * 100
        score += success * 0.25
        key_metrics["工具成功率"] = f"{report.overall_success_rate:.1%}"

        score = max(0, min(100, score))
        passed = self._check_tool_accuracy_pass(report)

        return DimensionScore(
            name="工具执行准确性",
            score=round(score, 1),
            weight=self.DIMENSION_WEIGHTS["tool_accuracy"],
            weighted_score=round(score * self.DIMENSION_WEIGHTS["tool_accuracy"], 2),
            status="passed" if passed else ("warning" if score >= 70 else "failed"),
            key_metrics=key_metrics
        )

    def _calc_reflection_score(self, report: ReflectionROCReport) -> DimensionScore:
        """计算反思验真维度得分"""
        score = 0.0
        key_metrics = {}

        tpr = report.roc_metrics.true_positive_rate * 100
        score += tpr * 0.40
        key_metrics["真阳性率(TPR)"] = f"{report.roc_metrics.true_positive_rate:.1%}"

        fpr_penalty = report.roc_metrics.false_positive_rate * 200
        score += max(0, 100 - fpr_penalty) * 0.35
        key_metrics["假阳性率(FPR)"] = f"{report.roc_metrics.false_positive_rate:.1%}"

        calibration_penalty = min(report.calibration_metric.calibration_error * 200, 100)
        score += (100 - calibration_penalty) * 0.25
        key_metrics["校准误差"] = f"{report.calibration_metric.calibration_error:.3f}"

        score = max(0, min(100, score))
        passed = self._check_reflection_pass(report)

        return DimensionScore(
            name="反思验真有效性",
            score=round(score, 1),
            weight=self.DIMENSION_WEIGHTS["reflection"],
            weighted_score=round(score * self.DIMENSION_WEIGHTS["reflection"], 2),
            status="passed" if passed else ("warning" if score >= 70 else "failed"),
            key_metrics=key_metrics
        )

    def _calc_proposal_score(self, report: ProposalQualityReport) -> DimensionScore:
        """计算方案质量维度得分"""
        score = 0.0
        key_metrics = {}

        consistency = report.overall_fact_consistency * 100
        score += consistency * 0.35
        key_metrics["事实一致率"] = f"{report.overall_fact_consistency:.1%}"

        parse_rate = report.overall_json_parse_rate * 100
        score += parse_rate * 0.30
        key_metrics["JSON解析率"] = f"{report.overall_json_parse_rate:.1%}"

        completeness = report.overall_completeness * 100
        score += completeness * 0.25
        key_metrics["方案完整度"] = f"{report.overall_completeness:.1%}"

        fallback_penalty = min(report.overall_fallback_rate * 100, 100)
        score += (100 - fallback_penalty) * 0.10
        key_metrics["降级触发率"] = f"{report.overall_fallback_rate:.1%}"

        score = max(0, min(100, score))
        passed = self._check_proposal_pass(report)

        return DimensionScore(
            name="LLM方案生成质量",
            score=round(score, 1),
            weight=self.DIMENSION_WEIGHTS["proposal"],
            weighted_score=round(score * self.DIMENSION_WEIGHTS["proposal"], 2),
            status="passed" if passed else ("warning" if score >= 70 else "failed"),
            key_metrics=key_metrics
        )

    def _calc_performance_score(self, report: PerformanceReport) -> DimensionScore:
        """计算端到端性能维度得分"""
        score = 0.0
        key_metrics = {}

        p50 = min(report.latency_metric.p50_latency_ms / 5000, 1.0) * 100
        score += p50 * 0.20
        key_metrics["P50延迟"] = f"{report.latency_metric.p50_latency_ms:.0f}ms"

        p95 = max(0, (1 - report.latency_metric.p95_latency_ms / 15000)) * 100
        score += p95 * 0.20
        key_metrics["P95延迟"] = f"{report.latency_metric.p95_latency_ms:.0f}ms"

        success_rate = report.status_distribution.success_rate * 100
        score += success_rate * 0.25
        key_metrics["成功率"] = f"{report.status_distribution.success_rate:.1%}"

        token_penalty = max(0, (report.token_metric.avg_total_tokens - 2000) / 2000) * 50
        score += max(0, 100 - token_penalty) * 0.20
        key_metrics["平均Token"] = f"{report.token_metric.avg_total_tokens:.0f}"

        stage_balance = self._calc_stage_balance_score(report.stage_distribution)
        score += stage_balance * 0.15
        key_metrics["阶段分布均衡"] = f"{stage_balance:.0f}/100"

        score = max(0, min(100, score))
        passed = self._check_performance_pass(report)

        return DimensionScore(
            name="端到端性能",
            score=round(score, 1),
            weight=self.DIMENSION_WEIGHTS["performance"],
            weighted_score=round(score * self.DIMENSION_WEIGHTS["performance"], 2),
            status="passed" if passed else ("warning" if score >= 70 else "failed"),
            key_metrics=key_metrics
        )

    def _calc_stage_balance_score(self, stage_dist) -> float:
        """计算阶段分布均衡得分"""
        expected_ratios = {"planning": 0.3, "dispatch": 0.4, "building": 0.2, "reflection": 0.1}

        actual = {
            "planning": stage_dist.planning_ratio,
            "dispatch": stage_dist.dispatch_ratio,
            "building": stage_dist.building_ratio,
            "reflection": stage_dist.reflection_ratio
        }

        deviation = sum(abs(actual[k] - v) for k, v in expected_ratios.items())
        return max(0, 100 - deviation * 200)

    def _calc_overall_score(self, dimension_scores: list) -> OverallScore:
        """计算综合评分"""
        if not dimension_scores:
            return OverallScore(
                total_score=0,
                dimension_scores=[],
                grade="E",
                passed_dimensions=0,
                total_dimensions=0
            )

        total_weight = sum(d.weight for d in dimension_scores)
        if total_weight == 0:
            total_weight = 1

        weighted_total = sum(d.weighted_score for d in dimension_scores)
        final_score = weighted_total / total_weight

        grade = self._score_to_grade(final_score)
        passed = sum(1 for d in dimension_scores if d.status == "passed")

        return OverallScore(
            total_score=round(final_score, 1),
            dimension_scores=[d.model_dump() for d in dimension_scores],
            grade=grade,
            passed_dimensions=passed,
            total_dimensions=len(dimension_scores)
        )

    def _score_to_grade(self, score: float) -> str:
        """将得分转换为等级"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "E"

    def _check_task_planning_pass(self, report: TaskPlanningReport) -> bool:
        """检查任务拆解是否达标"""
        thresholds = self.PASS_THRESHOLDS["task_planning"]
        return (
            report.overall_task_type_accuracy >= thresholds["overall_task_type_accuracy"] and
            report.overall_param_f1 >= thresholds["overall_param_f1"] and
            report.overall_count_deviation_rate <= thresholds["overall_count_deviation_rate"]
        )

    def _check_tool_accuracy_pass(self, report: ToolAccuracyReport) -> bool:
        """检查工具准确性是否达标"""
        thresholds = self.PASS_THRESHOLDS["tool_accuracy"]
        return (
            report.overall_field_consistency >= thresholds["overall_field_consistency"] and
            report.overall_numeric_deviation <= thresholds["overall_numeric_deviation"] and
            report.overall_success_rate >= thresholds["overall_success_rate"]
        )

    def _check_reflection_pass(self, report: ReflectionROCReport) -> bool:
        """检查反思验真是否达标"""
        thresholds = self.PASS_THRESHOLDS["reflection"]
        return (
            report.roc_metrics.true_positive_rate >= thresholds["true_positive_rate"] and
            report.roc_metrics.false_positive_rate <= thresholds["false_positive_rate"] and
            report.calibration_metric.calibration_error <= thresholds["calibration_error"]
        )

    def _check_proposal_pass(self, report: ProposalQualityReport) -> bool:
        """检查方案质量是否达标"""
        thresholds = self.PASS_THRESHOLDS["proposal"]
        return (
            report.overall_fact_consistency >= thresholds["overall_fact_consistency"] and
            report.overall_json_parse_rate >= thresholds["overall_json_parse_rate"] and
            report.overall_completeness >= thresholds["overall_completeness"]
        )

    def _check_performance_pass(self, report: PerformanceReport) -> bool:
        """检查性能是否达标"""
        thresholds = self.PASS_THRESHOLDS["performance"]
        return (
            report.latency_metric.p50_latency_ms <= thresholds["p50_latency_ms"] and
            report.latency_metric.p95_latency_ms <= thresholds["p95_latency_ms"] and
            report.status_distribution.success_rate >= thresholds["success_rate"] and
            report.status_distribution.error_rate <= thresholds["error_rate"]
        )

    def _generate_suggestions(
        self,
        task_report: Optional[TaskPlanningReport],
        tool_report: Optional[ToolAccuracyReport],
        reflection_report: Optional[ReflectionROCReport],
        proposal_report: Optional[ProposalQualityReport],
        performance_report: Optional[PerformanceReport]
    ) -> list:
        """生成改进建议"""
        suggestions = []

        if task_report and not self._check_task_planning_pass(task_report):
            if task_report.overall_task_type_accuracy < 0.9:
                suggestions.append(ImprovementSuggestion(
                    dimension="任务拆解",
                    priority="high",
                    issue=f"任务类型准确率偏低 ({task_report.overall_task_type_accuracy:.1%})",
                    suggestion="优化 TaskPlanner 的 prompt，增加任务类型识别的示例和规则"
                ))
            if task_report.overall_param_f1 < 0.85:
                suggestions.append(ImprovementSuggestion(
                    dimension="任务拆解",
                    priority="medium",
                    issue=f"参数提取 F1 偏低 ({task_report.overall_param_f1:.2f})",
                    suggestion="增强参数提取的正则表达式和模式匹配能力"
                ))

        if tool_report and not self._check_tool_accuracy_pass(tool_report):
            if tool_report.overall_field_consistency < 0.98:
                suggestions.append(ImprovementSuggestion(
                    dimension="工具准确性",
                    priority="high",
                    issue=f"字段一致率偏低 ({tool_report.overall_field_consistency:.1%})",
                    suggestion="检查数据映射逻辑，确保字段名和格式一致"
                ))

        if reflection_report and not self._check_reflection_pass(reflection_report):
            if reflection_report.roc_metrics.true_positive_rate < 0.85:
                suggestions.append(ImprovementSuggestion(
                    dimension="反思验真",
                    priority="high",
                    issue=f"真阳性率偏低 ({reflection_report.roc_metrics.true_positive_rate:.1%})",
                    suggestion="扩展业务规则库，增加更多异常检测模式"
                ))

        if proposal_report and not self._check_proposal_pass(proposal_report):
            if proposal_report.overall_json_parse_rate < 0.9:
                suggestions.append(ImprovementSuggestion(
                    dimension="方案生成",
                    priority="high",
                    issue=f"JSON 解析率偏低 ({proposal_report.overall_json_parse_rate:.1%})",
                    suggestion="增强 LLM 输出格式约束，添加 JSON 校验和修复逻辑"
                ))

        if performance_report and not self._check_performance_pass(performance_report):
            if performance_report.latency_metric.p95_latency_ms > 15000:
                suggestions.append(ImprovementSuggestion(
                    dimension="性能",
                    priority="high",
                    issue=f"P95 延迟偏高 ({performance_report.latency_metric.p95_latency_ms:.0f}ms)",
                    suggestion="优化缓存策略，减少重复的数据库查询和 LLM 调用"
                ))

        return suggestions

    def _generate_conclusions(
        self,
        overall_score: OverallScore,
        dimension_scores: list
    ) -> list:
        """生成结论"""
        conclusions = []

        conclusions.append(
            f"综合评分：{overall_score.total_score}/100 (等级 {overall_score.grade})"
        )
        conclusions.append(
            f"通过维度：{overall_score.passed_dimensions}/{overall_score.total_dimensions}"
        )

        best = max(dimension_scores, key=lambda d: d.score) if dimension_scores else None
        worst = min(dimension_scores, key=lambda d: d.score) if dimension_scores else None

        if best:
            conclusions.append(f"最强维度：{best.name} ({best.score}分)")
        if worst:
            conclusions.append(f"待提升维度：{worst.name} ({worst.score}分)")

        return conclusions

    def export_markdown(self, report: FullEvalReport, filepath: Optional[str] = None) -> str:
        """
        导出 Markdown 格式的报告

        Args:
            report: 完整评估报告
            filepath: 输出文件路径（可选）

        Returns:
            str: Markdown 格式的报告内容
        """
        md_lines = []

        md_lines.append("# Agent 系统量化评估报告\n")
        md_lines.append(f"**评估时间**: {report.generated_at}\n")

        md_lines.append(f"## 综合评分: {report.overall_score.total_score} / 100\n")
        md_lines.append(f"**等级**: {report.overall_score.grade}\n")
        md_lines.append(f"**通过维度**: {report.overall_score.passed_dimensions}/{report.overall_score.total_dimensions}\n")

        md_lines.append("\n## 各维度得分\n")
        md_lines.append("| 维度 | 得分 | 权重 | 加权得分 | 状态 |")
        md_lines.append("|------|------|------|---------|------|")

        for ds in report.overall_score.dimension_scores:
            status_icon = "✅" if ds["status"] == "passed" else ("⚠️" if ds["status"] == "warning" else "❌")
            status_text = {"passed": "通过", "warning": "警告", "failed": "失败"}.get(ds["status"], "")
            md_lines.append(
                f"| {ds['name']} | {ds['score']} | {ds['weight']:.0%} | {ds['weighted_score']:.2f} | {status_icon} {status_text} |"
            )

        md_lines.append("\n## 详细指标\n")

        if report.task_planning_report:
            md_lines.append("### 1. 任务拆解质量\n")
            md_lines.append(f"- 任务类型准确率: **{report.task_planning_report.overall_task_type_accuracy:.1%}**")
            md_lines.append(f"- 参数提取 F1: **{report.task_planning_report.overall_param_f1:.2f}**")
            md_lines.append(f"- 任务数偏差率: **{report.task_planning_report.overall_count_deviation_rate:.1%}**")
            md_lines.append(f"- {report.task_planning_report.summary}\n")

        if report.tool_accuracy_report:
            md_lines.append("### 2. 工具执行准确性\n")
            md_lines.append(f"- 字段一致率: **{report.tool_accuracy_report.overall_field_consistency:.1%}**")
            md_lines.append(f"- 数值偏差率: **{report.tool_accuracy_report.overall_numeric_deviation:.2%}**")
            md_lines.append(f"- 工具成功率: **{report.tool_accuracy_report.overall_success_rate:.1%}**")
            md_lines.append(f"- {report.tool_accuracy_report.summary}\n")

        if report.reflection_report:
            md_lines.append("### 3. 反思验真有效性\n")
            md_lines.append(f"- 真阳性率 (TPR): **{report.reflection_report.roc_metrics.true_positive_rate:.1%}**")
            md_lines.append(f"- 假阳性率 (FPR): **{report.reflection_report.roc_metrics.false_positive_rate:.1%}**")
            md_lines.append(f"- F1 分数: **{report.reflection_report.roc_metrics.f1_score:.2f}**")
            md_lines.append(f"- {report.reflection_report.summary}\n")

        if report.proposal_quality_report:
            md_lines.append("### 4. LLM 方案生成质量\n")
            md_lines.append(f"- 事实一致率: **{report.proposal_quality_report.overall_fact_consistency:.1%}**")
            md_lines.append(f"- JSON 解析率: **{report.proposal_quality_report.overall_json_parse_rate:.1%}**")
            md_lines.append(f"- 方案完整度: **{report.proposal_quality_report.overall_completeness:.1%}**")
            md_lines.append(f"- {report.proposal_quality_report.summary}\n")

        if report.performance_report:
            md_lines.append("### 5. 端到端性能\n")
            md_lines.append(f"- P50 延迟: **{report.performance_report.latency_metric.p50_latency_ms:.0f}ms**")
            md_lines.append(f"- P95 延迟: **{report.performance_report.latency_metric.p95_latency_ms:.0f}ms**")
            md_lines.append(f"- 成功率: **{report.performance_report.status_distribution.success_rate:.1%}**")
            md_lines.append(f"- 平均 Token: **{report.performance_report.token_metric.avg_total_tokens:.0f}**")
            md_lines.append(f"- {report.performance_report.summary}\n")

        if report.suggestions:
            md_lines.append("## 改进建议\n")
            for i, s in enumerate(report.suggestions, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s.priority, "⚪")
                md_lines.append(f"{i}. {priority_icon} **[{s.dimension}]** {s.issue}")
                md_lines.append(f"   - 建议：{s.suggestion}\n")

        md_lines.append("## 结论\n")
        for c in report.conclusions:
            md_lines.append(f"- {c}")

        md_lines.append("")

        markdown_content = "\n".join(md_lines)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            logger.info(f"Report saved to {filepath}")

        return markdown_content

    def export_json(self, report: FullEvalReport, filepath: Optional[str] = None) -> str:
        """
        导出 JSON 格式的报告

        Args:
            report: 完整评估报告
            filepath: 输出文件路径（可选）

        Returns:
            str: JSON 格式的报告
        """
        report_dict = report.model_dump()
        json_content = json.dumps(report_dict, ensure_ascii=False, indent=2)

        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(json_content)
            logger.info(f"JSON report saved to {filepath}")

        return json_content

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

"""
反思验真引擎模块
复刻纷享工程验真 RAG 策略，对 Agent 输出进行事实验真
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from config.settings import settings, Constants
from core.output_schema import (
    ReflectionReport,
    ReflectionField,
    SalesResponse,
    InventoryInfo,
    PricingInfo,
    CaseInfo
)


class ReflectionEngine:
    """
    反思验真引擎
    提取 Agent 输出内所有事实字段，反向比对数据源做二次核验
    """
    
    def __init__(self):
        """初始化反思验真引擎"""
        self.enabled = settings.REFLECTION_ENABLED
        self.confidence_threshold = settings.REFLECTION_CONFIDENCE_THRESHOLD
        self._data_sources: Dict[str, Any] = {}
        logger.info(f"反思验真引擎初始化，启用状态: {self.enabled}")
    
    def register_data_source(self, source_name: str, source_instance: Any):
        """
        注册数据源实例
        
        Args:
            source_name: 数据源名称
            source_instance: 数据源实例
        """
        self._data_sources[source_name] = source_instance
        logger.info(f"注册数据源: {source_name}")
    
    async def verify(
        self,
        response: SalesResponse,
        original_context: Optional[Dict[str, Any]] = None
    ) -> ReflectionReport:
        """
        验证 Agent 输出的真实性
        
        Args:
            response: Agent 响应
            original_context: 原始上下文（工具返回的真实数据）
            
        Returns:
            反思验真报告
        """
        if not self.enabled:
            logger.info("反思验真未启用，跳过验证")
            return ReflectionReport(
                enabled=False,
                overall_confidence=1.0,
                verified_fields=[],
                warnings=["反思验真未启用"]
            )
        
        logger.info("开始反思验真...")
        
        original_context = original_context or {}
        field_details: List[ReflectionField] = []
        verified_fields: List[str] = []
        unverified_fields: List[str] = []
        warnings: List[str] = []
        hallucinations: List[str] = []
        corrections: List[str] = []
        
        # 验证库存信息
        if response.inventory:
            inventory_verification = await self._verify_inventory(
                response.inventory,
                original_context.get(Constants.TASK_INVENTORY_QUERY)
            )
            field_details.extend(inventory_verification["fields"])
            verified_fields.extend(inventory_verification["verified"])
            unverified_fields.extend(inventory_verification["unverified"])
            warnings.extend(inventory_verification["warnings"])
            hallucinations.extend(inventory_verification["hallucinations"])
            corrections.extend(inventory_verification["corrections"])
        
        # 验证价格信息
        if response.pricing:
            pricing_verification = await self._verify_pricing(
                response.pricing,
                original_context.get(Constants.TASK_PRICE_QUERY)
            )
            field_details.extend(pricing_verification["fields"])
            verified_fields.extend(pricing_verification["verified"])
            unverified_fields.extend(pricing_verification["unverified"])
            warnings.extend(pricing_verification["warnings"])
            hallucinations.extend(pricing_verification["hallucinations"])
            corrections.extend(pricing_verification["corrections"])
        
        # 验证案例信息
        if response.cases:
            cases_verification = await self._verify_cases(
                response.cases,
                original_context.get(Constants.TASK_CASE_RETRIEVAL)
            )
            field_details.extend(cases_verification["fields"])
            verified_fields.extend(cases_verification["verified"])
            unverified_fields.extend(cases_verification["unverified"])
            warnings.extend(cases_verification["warnings"])
            hallucinations.extend(cases_verification["hallucinations"])
            corrections.extend(cases_verification["corrections"])
        
        # 计算整体置信度
        total_fields = len(verified_fields) + len(unverified_fields)
        overall_confidence = (
            len(verified_fields) / total_fields if total_fields > 0 else 1.0
        )
        
        # 如果置信度过低，添加警告
        if overall_confidence < self.confidence_threshold:
            warnings.append(
                f"整体置信度 {overall_confidence:.2%} 低于阈值 {self.confidence_threshold:.2%}"
            )
        
        logger.info(
            f"反思验真完成，置信度: {overall_confidence:.2%}, "
            f"已验证: {len(verified_fields)}, 未验证: {len(unverified_fields)}"
        )
        
        return ReflectionReport(
            enabled=True,
            overall_confidence=overall_confidence,
            verified_fields=verified_fields,
            unverified_fields=unverified_fields,
            field_details=field_details,
            warnings=warnings,
            hallucinations_detected=hallucinations,
            corrections_applied=corrections
        )
    
    async def _verify_inventory(
        self,
        inventory: InventoryInfo,
        source_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证库存信息
        
        Args:
            inventory: 库存信息
            source_data: 数据源数据
            
        Returns:
            验证结果字典
        """
        fields: List[ReflectionField] = []
        verified: List[str] = []
        unverified: List[str] = []
        warnings: List[str] = []
        hallucinations: List[str] = []
        corrections: List[str] = []
        
        if not source_data:
            warnings.append("库存数据源不可用，无法验证")
            return {
                "fields": fields,
                "verified": verified,
                "unverified": unverified,
                "warnings": warnings,
                "hallucinations": hallucinations,
                "corrections": corrections
            }
        
        # 验证库存数量
        if "stock_quantity" in source_data:
            is_match = inventory.stock_quantity == source_data["stock_quantity"]
            fields.append(ReflectionField(
                field_name="stock_quantity",
                field_value=inventory.stock_quantity,
                is_verified=is_match,
                confidence=1.0 if is_match else 0.0,
                source="inventory_query"
            ))
            if is_match:
                verified.append("stock_quantity")
            else:
                unverified.append("stock_quantity")
                hallucinations.append(
                    f"库存数量不匹配: 输出 {inventory.stock_quantity}, 实际 {source_data['stock_quantity']}"
                )
        
        # 验证可用数量
        if "available_quantity" in source_data:
            is_match = inventory.available_quantity == source_data["available_quantity"]
            fields.append(ReflectionField(
                field_name="available_quantity",
                field_value=inventory.available_quantity,
                is_verified=is_match,
                confidence=1.0 if is_match else 0.0,
                source="inventory_query"
            ))
            if is_match:
                verified.append("available_quantity")
            else:
                unverified.append("available_quantity")
        
        return {
            "fields": fields,
            "verified": verified,
            "unverified": unverified,
            "warnings": warnings,
            "hallucinations": hallucinations,
            "corrections": corrections
        }
    
    async def _verify_pricing(
        self,
        pricing: PricingInfo,
        source_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证价格信息
        
        Args:
            pricing: 价格信息
            source_data: 数据源数据
            
        Returns:
            验证结果字典
        """
        fields: List[ReflectionField] = []
        verified: List[str] = []
        unverified: List[str] = []
        warnings: List[str] = []
        hallucinations: List[str] = []
        corrections: List[str] = []
        
        if not source_data:
            warnings.append("价格数据源不可用，无法验证")
            return {
                "fields": fields,
                "verified": verified,
                "unverified": unverified,
                "warnings": warnings,
                "hallucinations": hallucinations,
                "corrections": corrections
            }
        
        # 验证单价
        if "unit_price" in source_data:
            # 允许一定误差范围
            source_price = source_data["unit_price"]
            price_diff = abs(pricing.unit_price - source_price)
            # 防止除零错误
            if source_price > 0:
                tolerance = source_price * 0.05  # 5% 误差容忍
                is_match = price_diff <= tolerance
                confidence = 1.0 - (price_diff / source_price) if is_match else 0.0
            else:
                # 如果源价格为0，只有当输出价格也为0时才匹配
                is_match = pricing.unit_price == 0
                confidence = 1.0 if is_match else 0.0
            
            fields.append(ReflectionField(
                field_name="unit_price",
                field_value=pricing.unit_price,
                is_verified=is_match,
                confidence=confidence,
                source="price_query"
            ))
            if is_match:
                verified.append("unit_price")
            else:
                unverified.append("unit_price")
                hallucinations.append(
                    f"单价不匹配: 输出 {pricing.unit_price}, 实际 {source_data['unit_price']}"
                )
        
        # 验证折扣率
        if "discount_rate" in source_data:
            is_match = abs(pricing.discount_rate - source_data["discount_rate"]) < 0.01
            fields.append(ReflectionField(
                field_name="discount_rate",
                field_value=pricing.discount_rate,
                is_verified=is_match,
                confidence=1.0 if is_match else 0.0,
                source="price_query"
            ))
            if is_match:
                verified.append("discount_rate")
            else:
                unverified.append("discount_rate")
        
        return {
            "fields": fields,
            "verified": verified,
            "unverified": unverified,
            "warnings": warnings,
            "hallucinations": hallucinations,
            "corrections": corrections
        }
    
    async def _verify_cases(
        self,
        cases: List[CaseInfo],
        source_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证案例信息
        
        Args:
            cases: 案例信息列表
            source_data: 数据源数据
            
        Returns:
            验证结果字典
        """
        fields: List[ReflectionField] = []
        verified: List[str] = []
        unverified: List[str] = []
        warnings: List[str] = []
        hallucinations: List[str] = []
        corrections: List[str] = []
        
        if not source_data or not source_data.get("cases"):
            warnings.append("案例数据源不可用，无法验证")
            return {
                "fields": fields,
                "verified": verified,
                "unverified": unverified,
                "warnings": warnings,
                "hallucinations": hallucinations,
                "corrections": corrections
            }
        
        source_cases = source_data.get("cases", [])
        
        # 验证每个案例
        for i, case in enumerate(cases):
            # 查找匹配的源案例
            matched_source = None
            for source_case in source_cases:
                if case.case_id == source_case.get("case_id"):
                    matched_source = source_case
                    break
            
            if matched_source:
                # 验证案例字段
                if "quantity" in matched_source:
                    is_match = case.quantity == matched_source["quantity"]
                    fields.append(ReflectionField(
                        field_name=f"case_{i}_quantity",
                        field_value=case.quantity,
                        is_verified=is_match,
                        confidence=1.0 if is_match else 0.0,
                        source="case_retrieval"
                    ))
                    if is_match:
                        verified.append(f"case_{i}_quantity")
                    else:
                        unverified.append(f"case_{i}_quantity")
                
                if "deal_price" in matched_source:
                    price_diff = abs(case.deal_price - matched_source["deal_price"])
                    tolerance = matched_source["deal_price"] * 0.05
                    is_match = price_diff <= tolerance
                    fields.append(ReflectionField(
                        field_name=f"case_{i}_deal_price",
                        field_value=case.deal_price,
                        is_verified=is_match,
                        confidence=1.0 if is_match else 0.0,
                        source="case_retrieval"
                    ))
                    if is_match:
                        verified.append(f"case_{i}_deal_price")
                    else:
                        unverified.append(f"case_{i}_deal_price")
            else:
                # 未找到匹配的源案例，可能是幻觉
                hallucinations.append(f"案例 {case.case_id} 未在数据源中找到")
                unverified.append(f"case_{i}_existence")
        
        return {
            "fields": fields,
            "verified": verified,
            "unverified": unverified,
            "warnings": warnings,
            "hallucinations": hallucinations,
            "corrections": corrections
        }
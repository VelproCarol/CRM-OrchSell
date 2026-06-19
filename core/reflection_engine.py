"""
反思验真引擎模块
复刻纷享工程验真 RAG 策略，对 Agent 输出进行事实验真
增强版：添加数值边界校验和业务规则校验
"""
from typing import Dict, Any, List, Optional
from loguru import logger

from config.settings import settings, Constants
from schemas.output_schema import (
    ReflectionReport,
    ReflectionField,
    SalesResponse,
    InventoryInfo,
    PricingInfo,
    CaseInfo
)


class BoundaryValidator:
    """
    数值边界校验器
    校验数值字段是否在合理的业务范围内
    """
    
    # 库存数量边界
    MIN_STOCK_QUANTITY = 0
    MAX_STOCK_QUANTITY = 1000000  # 最大库存数量
    
    # 价格边界
    MIN_PRICE = 0.0
    MAX_PRICE = 10000000.0  # 最高单价（1000万）
    
    # 折扣率边界
    MIN_DISCOUNT_RATE = 0.0
    MAX_DISCOUNT_RATE = 1.0  # 折扣率应在 0-1 之间
    
    # 数量边界
    MIN_QUANTITY = 0
    MAX_QUANTITY = 100000  # 最大采购数量
    
    # 相似度边界
    MIN_SIMILARITY = 0.0
    MAX_SIMILARITY = 1.0
    
    @classmethod
    def validate_stock_quantity(cls, value: int, field_name: str) -> Dict[str, Any]:
        """
        验证库存数量
        
        Args:
            value: 库存数量
            field_name: 字段名称
            
        Returns:
            校验结果
        """
        if not isinstance(value, int):
            return {
                "is_valid": False,
                "error": f"{field_name} 类型错误，应为整数",
                "confidence": 0.0
            }
        
        if value < cls.MIN_STOCK_QUANTITY:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 小于最小值 {cls.MIN_STOCK_QUANTITY}",
                "confidence": 0.0
            }
        
        if value > cls.MAX_STOCK_QUANTITY:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 超过最大值 {cls.MAX_STOCK_QUANTITY}",
                "confidence": 0.5
            }
        
        return {
            "is_valid": True,
            "error": None,
            "confidence": 1.0
        }
    
    @classmethod
    def validate_price(cls, value: float, field_name: str) -> Dict[str, Any]:
        """
        验证价格
        
        Args:
            value: 价格值
            field_name: 字段名称
            
        Returns:
            校验结果
        """
        if not isinstance(value, (int, float)):
            return {
                "is_valid": False,
                "error": f"{field_name} 类型错误，应为数值",
                "confidence": 0.0
            }
        
        if value < cls.MIN_PRICE:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 小于最小值 {cls.MIN_PRICE}",
                "confidence": 0.0
            }
        
        if value > cls.MAX_PRICE:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 超过最大值 {cls.MAX_PRICE}",
                "confidence": 0.5
            }
        
        return {
            "is_valid": True,
            "error": None,
            "confidence": 1.0
        }
    
    @classmethod
    def validate_discount_rate(cls, value: float, field_name: str) -> Dict[str, Any]:
        """
        验证折扣率
        
        Args:
            value: 折扣率
            field_name: 字段名称
            
        Returns:
            校验结果
        """
        if not isinstance(value, (int, float)):
            return {
                "is_valid": False,
                "error": f"{field_name} 类型错误，应为数值",
                "confidence": 0.0
            }
        
        if value < cls.MIN_DISCOUNT_RATE:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 小于最小值 {cls.MIN_DISCOUNT_RATE}",
                "confidence": 0.0
            }
        
        if value > cls.MAX_DISCOUNT_RATE:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 超过最大值 {cls.MAX_DISCOUNT_RATE}",
                "confidence": 0.0
            }
        
        return {
            "is_valid": True,
            "error": None,
            "confidence": 1.0
        }
    
    @classmethod
    def validate_quantity(cls, value: int, field_name: str) -> Dict[str, Any]:
        """
        验证采购数量
        
        Args:
            value: 数量
            field_name: 字段名称
            
        Returns:
            校验结果
        """
        if not isinstance(value, int):
            return {
                "is_valid": False,
                "error": f"{field_name} 类型错误，应为整数",
                "confidence": 0.0
            }
        
        if value < cls.MIN_QUANTITY:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 小于最小值 {cls.MIN_QUANTITY}",
                "confidence": 0.0
            }
        
        if value > cls.MAX_QUANTITY:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 超过最大值 {cls.MAX_QUANTITY}",
                "confidence": 0.5
            }
        
        return {
            "is_valid": True,
            "error": None,
            "confidence": 1.0
        }
    
    @classmethod
    def validate_similarity(cls, value: float, field_name: str) -> Dict[str, Any]:
        """
        验证相似度得分
        
        Args:
            value: 相似度
            field_name: 字段名称
            
        Returns:
            校验结果
        """
        if not isinstance(value, (int, float)):
            return {
                "is_valid": False,
                "error": f"{field_name} 类型错误，应为数值",
                "confidence": 0.0
            }
        
        if value < cls.MIN_SIMILARITY or value > cls.MAX_SIMILARITY:
            return {
                "is_valid": False,
                "error": f"{field_name} 值 {value} 不在有效范围 [{cls.MIN_SIMILARITY}, {cls.MAX_SIMILARITY}]",
                "confidence": 0.0
            }
        
        return {
            "is_valid": True,
            "error": None,
            "confidence": 1.0
        }


class BusinessRuleValidator:
    """
    业务规则校验器
    校验业务逻辑是否合理
    """
    
    @classmethod
    def validate_inventory_logic(cls, inventory: InventoryInfo) -> List[str]:
        """
        验证库存业务逻辑
        
        Args:
            inventory: 库存信息
            
        Returns:
            错误列表
        """
        errors = []
        
        # 可用库存不能超过总库存
        if inventory.available_quantity > inventory.stock_quantity:
            errors.append(
                f"可用库存 {inventory.available_quantity} 超过总库存 {inventory.stock_quantity}"
            )
        
        # 预留库存不能超过总库存
        if inventory.reserved_quantity and inventory.reserved_quantity > inventory.stock_quantity:
            errors.append(
                f"预留库存 {inventory.reserved_quantity} 超过总库存 {inventory.stock_quantity}"
            )
        
        # 可用库存 + 预留库存不能超过总库存
        if inventory.reserved_quantity:
            total_allocated = inventory.available_quantity + inventory.reserved_quantity
            if total_allocated > inventory.stock_quantity:
                errors.append(
                    f"可用库存 + 预留库存 ({total_allocated}) 超过总库存 {inventory.stock_quantity}"
                )
        
        return errors
    
    @classmethod
    def validate_pricing_logic(cls, pricing: PricingInfo, quantity: int = 1) -> List[str]:
        """
        验证价格业务逻辑
        
        Args:
            pricing: 价格信息
            quantity: 采购数量
            
        Returns:
            错误列表
        """
        errors = []
        
        # 总价应该等于单价乘以数量（考虑折扣）
        expected_total = pricing.unit_price * quantity * (1 - pricing.discount_rate)
        if pricing.total_price != 0:
            diff = abs(pricing.total_price - expected_total)
            tolerance = expected_total * 0.01 if expected_total > 0 else 0.01
            if diff > tolerance:
                errors.append(
                    f"总价计算异常: 计算值 {expected_total:.2f} vs 实际值 {pricing.total_price:.2f}"
                )
        
        return errors
    
    @classmethod
    def validate_case_logic(cls, case: CaseInfo) -> List[str]:
        """
        验证案例业务逻辑
        
        Args:
            case: 案例信息
            
        Returns:
            错误列表
        """
        errors = []
        
        # 总金额应该等于单价乘以数量
        if case.total_amount and case.deal_price > 0 and case.quantity > 0:
            expected_total = case.deal_price * case.quantity
            diff = abs(case.total_amount - expected_total)
            tolerance = expected_total * 0.01
            if diff > tolerance:
                errors.append(
                    f"案例 {case.case_id} 总金额计算异常: 计算值 {expected_total:.2f} vs 实际值 {case.total_amount:.2f}"
                )
        
        return errors


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
        验证库存信息（增强版：添加边界校验和业务规则校验）
        
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
        
        # 第一步：边界校验（无需数据源）
        logger.info("开始库存边界校验...")
        
        # 校验库存数量边界
        stock_quantity_validation = BoundaryValidator.validate_stock_quantity(
            inventory.stock_quantity, "stock_quantity"
        )
        fields.append(ReflectionField(
            field_name="stock_quantity_boundary",
            field_value=inventory.stock_quantity,
            is_verified=stock_quantity_validation["is_valid"],
            confidence=stock_quantity_validation["confidence"],
            source="boundary_validation"
        ))
        if not stock_quantity_validation["is_valid"]:
            unverified.append("stock_quantity_boundary")
            warnings.append(stock_quantity_validation["error"])
        
        # 校验可用数量边界
        available_validation = BoundaryValidator.validate_stock_quantity(
            inventory.available_quantity, "available_quantity"
        )
        fields.append(ReflectionField(
            field_name="available_quantity_boundary",
            field_value=inventory.available_quantity,
            is_verified=available_validation["is_valid"],
            confidence=available_validation["confidence"],
            source="boundary_validation"
        ))
        if not available_validation["is_valid"]:
            unverified.append("available_quantity_boundary")
            warnings.append(available_validation["error"])
        
        # 第二步：业务规则校验
        logger.info("开始库存业务规则校验...")
        logic_errors = BusinessRuleValidator.validate_inventory_logic(inventory)
        for error in logic_errors:
            warnings.append(f"业务规则错误: {error}")
            unverified.append("inventory_logic")
        
        # 第三步：数据源比对（如果数据源可用）
        if source_data:
            logger.info("开始库存数据源比对...")
            
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
        else:
            warnings.append("库存数据源不可用，跳过数据源比对")
        
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
        验证价格信息（增强版：添加边界校验和业务规则校验）
        
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
        
        # 第一步：边界校验（无需数据源）
        logger.info("开始价格边界校验...")
        
        # 校验单价边界
        price_validation = BoundaryValidator.validate_price(
            pricing.unit_price, "unit_price"
        )
        fields.append(ReflectionField(
            field_name="unit_price_boundary",
            field_value=pricing.unit_price,
            is_verified=price_validation["is_valid"],
            confidence=price_validation["confidence"],
            source="boundary_validation"
        ))
        if not price_validation["is_valid"]:
            unverified.append("unit_price_boundary")
            warnings.append(price_validation["error"])
        
        # 校验折扣率边界
        discount_validation = BoundaryValidator.validate_discount_rate(
            pricing.discount_rate, "discount_rate"
        )
        fields.append(ReflectionField(
            field_name="discount_rate_boundary",
            field_value=pricing.discount_rate,
            is_verified=discount_validation["is_valid"],
            confidence=discount_validation["confidence"],
            source="boundary_validation"
        ))
        if not discount_validation["is_valid"]:
            unverified.append("discount_rate_boundary")
            warnings.append(discount_validation["error"])
        
        # 第二步：业务规则校验
        logger.info("开始价格业务规则校验...")
        logic_errors = BusinessRuleValidator.validate_pricing_logic(pricing)
        for error in logic_errors:
            warnings.append(f"业务规则错误: {error}")
            unverified.append("pricing_logic")
        
        # 第三步：数据源比对（如果数据源可用）
        if source_data:
            logger.info("开始价格数据源比对...")
            
            # 验证单价
            if "unit_price" in source_data:
                source_price = source_data["unit_price"]
                price_diff = abs(pricing.unit_price - source_price)
                if source_price > 0:
                    tolerance = source_price * 0.05
                    is_match = price_diff <= tolerance
                    confidence = 1.0 - (price_diff / source_price) if is_match else 0.0
                else:
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
        else:
            warnings.append("价格数据源不可用，跳过数据源比对")
        
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
        验证案例信息（增强版：添加边界校验和业务规则校验）
        
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
        
        # 第一步：边界校验和业务规则校验（无需数据源）
        logger.info("开始案例边界校验...")
        for i, case in enumerate(cases):
            # 校验数量边界
            quantity_validation = BoundaryValidator.validate_quantity(
                case.quantity, f"case_{i}_quantity"
            )
            fields.append(ReflectionField(
                field_name=f"case_{i}_quantity_boundary",
                field_value=case.quantity,
                is_verified=quantity_validation["is_valid"],
                confidence=quantity_validation["confidence"],
                source="boundary_validation"
            ))
            if not quantity_validation["is_valid"]:
                unverified.append(f"case_{i}_quantity_boundary")
                warnings.append(quantity_validation["error"])
            
            # 校验价格边界
            price_validation = BoundaryValidator.validate_price(
                case.deal_price, f"case_{i}_deal_price"
            )
            fields.append(ReflectionField(
                field_name=f"case_{i}_deal_price_boundary",
                field_value=case.deal_price,
                is_verified=price_validation["is_valid"],
                confidence=price_validation["confidence"],
                source="boundary_validation"
            ))
            if not price_validation["is_valid"]:
                unverified.append(f"case_{i}_deal_price_boundary")
                warnings.append(price_validation["error"])
            
            # 校验相似度边界（如果有）
            if case.similarity_score is not None:
                similarity_validation = BoundaryValidator.validate_similarity(
                    case.similarity_score, f"case_{i}_similarity"
                )
                fields.append(ReflectionField(
                    field_name=f"case_{i}_similarity_boundary",
                    field_value=case.similarity_score,
                    is_verified=similarity_validation["is_valid"],
                    confidence=similarity_validation["confidence"],
                    source="boundary_validation"
                ))
                if not similarity_validation["is_valid"]:
                    unverified.append(f"case_{i}_similarity_boundary")
                    warnings.append(similarity_validation["error"])
            
            # 业务规则校验
            logic_errors = BusinessRuleValidator.validate_case_logic(case)
            for error in logic_errors:
                warnings.append(f"案例 {case.case_id} 业务规则错误: {error}")
                unverified.append(f"case_{i}_logic")
        
        # 第二步：数据源比对（如果数据源可用）
        if source_data and source_data.get("cases"):
            logger.info("开始案例数据源比对...")
            source_cases = source_data.get("cases", [])
            
            for i, case in enumerate(cases):
                matched_source = None
                for source_case in source_cases:
                    if case.case_id == source_case.get("case_id"):
                        matched_source = source_case
                        break
                
                if matched_source:
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
                    hallucinations.append(f"案例 {case.case_id} 未在数据源中找到")
                    unverified.append(f"case_{i}_existence")
        else:
            warnings.append("案例数据源不可用，跳过数据源比对")
        
        return {
            "fields": fields,
            "verified": verified,
            "unverified": unverified,
            "warnings": warnings,
            "hallucinations": hallucinations,
            "corrections": corrections
        }
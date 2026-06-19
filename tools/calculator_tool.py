"""
计算器工具
高精度数值计算（阶梯报价、毛利、账期成本）
"""
from typing import Dict, Any, Optional, List
from decimal import Decimal
from loguru import logger

from tools.base_tool import BaseTool
from config.settings import Constants


class CalculatorTool(BaseTool):
    """
    计算器工具
    用于计算报价、毛利、账期成本等数值
    """
    
    def __init__(self):
        """初始化计算器工具"""
        super().__init__(
            name=Constants.TOOL_CALCULATOR,
            description="高精度数值计算工具，支持阶梯报价、毛利计算、账期成本核算"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行计算
        
        Args:
            quantity: 采购数量
            unit_price: 单价（可选，如果未提供则从 context 获取）
            discount_rate: 折扣率（可选）
            payment_terms: 付款条件（可选）
            base_cost: 基础成本（可选，用于计算毛利）
            quantity_ranges: 阶梯数量区间（可选）
            discount_ranges: 阶梯折扣区间（可选）
            
        Returns:
            计算结果字典
        """
        try:
            logger.info(f"计算器工具开始执行，参数: {kwargs}")
            
            # 参数验证
            quantity = kwargs.get("quantity", 0)
            if quantity <= 0:
                return self._handle_error(ValueError("采购数量必须大于0"))
            
            # 获取单价（可能从 context 传入）
            unit_price = kwargs.get("unit_price", 0)
            if unit_price <= 0:
                # 从 context 获取（工具调度器会传入前序任务结果）
                price_context = kwargs.get(Constants.TASK_PRICE_QUERY) or {}
                if isinstance(price_context, dict):
                    unit_price = price_context.get("unit_price", 0)
            
            if unit_price <= 0:
                return self._handle_error(ValueError("单价必须大于0，请确认价格查询任务已成功完成"))
            
            # 计算阶梯折扣
            discount_rate = self._calculate_discount(
                quantity=quantity,
                discount_rate=kwargs.get("discount_rate"),
                quantity_ranges=kwargs.get("quantity_ranges"),
                discount_ranges=kwargs.get("discount_ranges")
            )
            
            # 计算总价
            total_price = self._calculate_total_price(
                quantity=quantity,
                unit_price=unit_price,
                discount_rate=discount_rate
            )
            
            # 计算毛利
            base_cost = kwargs.get("base_cost", unit_price * 0.7)  # 默认成本为70%
            gross_profit = self._calculate_gross_profit(
                total_price=total_price,
                base_cost=base_cost,
                quantity=quantity
            )
            
            # 计算账期成本
            payment_terms = kwargs.get("payment_terms", "款到发货")
            payment_cost = self._calculate_payment_cost(
                total_price=total_price,
                payment_terms=payment_terms
            )
            
            result = {
                "unit_price": float(unit_price),
                "quantity": quantity,
                "discount_rate": float(discount_rate),
                "total_price": float(total_price),
                "gross_profit": float(gross_profit),
                "gross_profit_rate": float(gross_profit / total_price) if total_price > 0 else 0,
                "payment_terms": payment_terms,
                "payment_cost": float(payment_cost),
                "net_profit": float(total_price - base_cost * quantity - payment_cost)
            }
            
            logger.info(f"计算器工具执行成功，总价: {result['total_price']}")
            return self._success_response(result)
            
        except Exception as e:
            return self._handle_error(e)
    
    def _calculate_discount(
        self,
        quantity: int,
        discount_rate: Optional[float] = None,
        quantity_ranges: Optional[List[int]] = None,
        discount_ranges: Optional[List[float]] = None
    ) -> Decimal:
        """
        计算阶梯折扣
        
        Args:
            quantity: 采购数量
            discount_rate: 固定折扣率
            quantity_ranges: 阶梯数量区间
            discount_ranges: 阶梯折扣区间
            
        Returns:
            折扣率
        """
        # 如果提供了固定折扣率，直接使用
        if discount_rate is not None:
            return Decimal(str(discount_rate))
        
        # 默认阶梯折扣规则
        if quantity_ranges is None:
            quantity_ranges = [10, 30, 50, 100]
        
        if discount_ranges is None:
            discount_ranges = [0.0, 0.03, 0.05, 0.08, 0.10]
        
        # 根据数量匹配折扣率
        for i, threshold in enumerate(quantity_ranges):
            if quantity < threshold:
                return Decimal(str(discount_ranges[i]))
        
        # 超过最大区间，使用最高折扣
        return Decimal(str(discount_ranges[-1]))
    
    def _calculate_total_price(
        self,
        quantity: int,
        unit_price: float,
        discount_rate: Decimal
    ) -> Decimal:
        """
        计算总价
        
        Args:
            quantity: 采购数量
            unit_price: 单价
            discount_rate: 折扣率
            
        Returns:
            总价
        """
        base_price = Decimal(str(unit_price)) * Decimal(str(quantity))
        discounted_price = base_price * (Decimal("1") - discount_rate)
        return discounted_price
    
    def _calculate_gross_profit(
        self,
        total_price: Decimal,
        base_cost: float,
        quantity: int
    ) -> Decimal:
        """
        计算毛利
        
        Args:
            total_price: 总价
            base_cost: 单位成本
            quantity: 采购数量
            
        Returns:
            毛利
        """
        total_cost = Decimal(str(base_cost)) * Decimal(str(quantity))
        return total_price - total_cost
    
    def _calculate_payment_cost(
        self,
        total_price: Decimal,
        payment_terms: str
    ) -> Decimal:
        """
        计算账期成本
        
        Args:
            total_price: 总价
            payment_terms: 付款条件
            
        Returns:
            账期成本
        """
        # 解析账期天数
        import re
        
        # 默认年化利率 6%
        annual_rate = Decimal("0.06")
        
        # 提取账期天数
        days_match = re.search(r"(\d+)天", payment_terms)
        if days_match:
            days = int(days_match.group(1))
        else:
            days = 0
        
        # 计算账期成本（简单利息计算）
        if days > 0:
            daily_rate = annual_rate / Decimal("365")
            payment_cost = total_price * daily_rate * Decimal(str(days))
            return payment_cost
        
        return Decimal("0")
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数 Schema
        
        Returns:
            参数 Schema 字典
        """
        return {
            "type": "object",
            "properties": {
                "quantity": {
                    "type": "integer",
                    "description": "采购数量"
                },
                "unit_price": {
                    "type": "number",
                    "description": "单价（可选）"
                },
                "discount_rate": {
                    "type": "number",
                    "description": "折扣率（可选）"
                },
                "payment_terms": {
                    "type": "string",
                    "description": "付款条件"
                },
                "base_cost": {
                    "type": "number",
                    "description": "基础成本（可选）"
                }
            },
            "required": ["quantity"]
        }
"""
工具测试模块
测试各个工具的独立功能
"""
import pytest
from tools import (
    CalculatorTool,
    ApiInventoryTool,
    SqlPriceTool,
    DocRetrieveTool
)
from config.settings import Constants


@pytest.mark.asyncio
class TestCalculatorTool:
    """
    计算器工具测试
    """
    
    async def test_basic_calculation(self):
        """
        测试基本计算功能
        """
        tool = CalculatorTool()
        
        result = await tool.execute(
            quantity=50,
            unit_price=8500.0,
            discount_rate=0.05
        )
        
        assert result["success"] is True
        assert result["quantity"] == 50
        assert result["unit_price"] == 8500.0
        assert result["discount_rate"] == 0.05
        assert result["total_price"] == 50 * 8500.0 * 0.95
    
    async def test_ladder_discount(self):
        """
        测试阶梯折扣计算
        """
        tool = CalculatorTool()
        
        # 小批量（无折扣）
        result1 = await tool.execute(quantity=5, unit_price=1000.0)
        assert result1["discount_rate"] == 0.0
        
        # 中批量（3%折扣）
        result2 = await tool.execute(quantity=20, unit_price=1000.0)
        assert result2["discount_rate"] == 0.03
        
        # 大批量（5%折扣）
        result3 = await tool.execute(quantity=50, unit_price=1000.0)
        assert result3["discount_rate"] == 0.05
        
        # 超大批量（8%折扣）
        result4 = await tool.execute(quantity=100, unit_price=1000.0)
        assert result4["discount_rate"] == 0.08
    
    async def test_payment_cost(self):
        """
        测试账期成本计算
        """
        tool = CalculatorTool()
        
        result = await tool.execute(
            quantity=50,
            unit_price=8500.0,
            payment_terms="30天账期"
        )
        
        assert result["success"] is True
        assert result["payment_terms"] == "30天账期"
        assert result["payment_cost"] > 0
    
    async def test_gross_profit(self):
        """
        测试毛利计算
        """
        tool = CalculatorTool()
        
        result = await tool.execute(
            quantity=50,
            unit_price=8500.0,
            base_cost=6000.0
        )
        
        assert result["success"] is True
        assert result["gross_profit"] > 0
        assert result["gross_profit_rate"] > 0
    
    async def test_invalid_quantity(self):
        """
        测试无效数量
        """
        tool = CalculatorTool()
        
        result = await tool.execute(quantity=0, unit_price=1000.0)
        
        assert result["success"] is False
        assert "error" in result
    
    async def test_get_schema(self):
        """
        测试获取工具 Schema
        """
        tool = CalculatorTool()
        
        schema = tool.get_tool_schema()
        
        assert schema["name"] == Constants.TOOL_CALCULATOR
        assert "parameters" in schema


@pytest.mark.asyncio
class TestApiInventoryTool:
    """
    库存查询工具测试
    """
    
    async def test_query_existing_product(self):
        """
        测试查询现有产品库存
        """
        tool = ApiInventoryTool()
        
        result = await tool.execute(product_name="工业风机")
        
        assert result["success"] is True
        assert "product_name" in result
        assert "stock_quantity" in result
        assert "available_quantity" in result
    
    async def test_query_with_quantity(self):
        """
        测试带数量需求的库存查询
        """
        tool = ApiInventoryTool()
        
        result = await tool.execute(
            product_name="工业风机",
            quantity=50
        )
        
        assert result["success"] is True
        assert "can_supply" in result
    
    async def test_query_nonexistent_product(self):
        """
        测试查询不存在的产品
        """
        tool = ApiInventoryTool()
        
        result = await tool.execute(product_name="不存在的产品")
        
        assert result["success"] is True
        assert result["stock_quantity"] == 0
        assert "warning" in result
    
    async def test_missing_product_name(self):
        """
        测试缺少产品名称
        """
        tool = ApiInventoryTool()
        
        result = await tool.execute()
        
        assert result["success"] is False
        assert "error" in result


@pytest.mark.asyncio
class TestSqlPriceTool:
    """
    价格查询工具测试
    """
    
    async def test_query_product_price(self):
        """
        测试查询产品价格
        """
        tool = SqlPriceTool()
        
        result = await tool.execute(product_name="工业风机")
        
        assert result["success"] is True
        assert "unit_price" in result
        assert "price_range" in result
    
    async def test_query_with_quantity_range(self):
        """
        测试带数量范围的价格查询
        """
        tool = SqlPriceTool()
        
        result = await tool.execute(
            product_name="工业风机",
            quantity_range=[40, 60]
        )
        
        assert result["success"] is True
    
    async def test_query_with_payment_terms(self):
        """
        测试带付款条件的价格查询
        """
        tool = SqlPriceTool()
        
        result = await tool.execute(
            product_name="工业风机",
            payment_terms="30天账期"
        )
        
        assert result["success"] is True
    
    async def test_missing_product_name(self):
        """
        测试缺少产品名称
        """
        tool = SqlPriceTool()
        
        result = await tool.execute()
        
        assert result["success"] is False


@pytest.mark.asyncio
class TestDocRetrieveTool:
    """
    文档检索工具测试
    """
    
    async def test_retrieve_cases(self):
        """
        测试检索案例
        """
        tool = DocRetrieveTool()
        
        result = await tool.execute(product_name="工业风机")
        
        assert result["success"] is True
        assert "cases" in result
        assert len(result["cases"]) > 0
    
    async def test_retrieve_with_quantity_range(self):
        """
        测试带数量范围的案例检索
        """
        tool = DocRetrieveTool()
        
        result = await tool.execute(
            product_name="工业风机",
            quantity_range=[40, 60],
            payment_terms="30天账期"
        )
        
        assert result["success"] is True
        assert "query_text" in result
    
    async def test_retrieve_with_top_k(self):
        """
        测试指定返回数量
        """
        tool = DocRetrieveTool()
        
        result = await tool.execute(
            product_name="工业风机",
            top_k=2
        )
        
        assert result["success"] is True
        assert len(result["cases"]) <= 2
    
    async def test_missing_product_name(self):
        """
        测试缺少产品名称
        """
        tool = DocRetrieveTool()
        
        result = await tool.execute()
        
        assert result["success"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
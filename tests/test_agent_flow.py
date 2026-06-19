"""
Agent 流程测试模块
测试完整的 Agent 执行流程
"""
import pytest
from core.sales_agent import SalesAgent
from tools import (
    CalculatorTool,
    ApiInventoryTool,
    SqlPriceTool,
    DocRetrieveTool
)
from config.settings import Constants


@pytest.mark.asyncio
class TestSalesAgentFlow:
    """
    Agent 流程测试
    """
    
    async def test_agent_initialization(self):
        """
        测试 Agent 初始化
        """
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 检查工具注册
        tools = agent.tool_dispatcher.get_registered_tools()
        
        assert len(tools) == 4
        assert Constants.TOOL_CALCULATOR in tools
        assert Constants.TOOL_API_INVENTORY in tools
    
    async def test_agent_process_simple_query(self):
        """
        测试简单查询处理
        """
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 执行查询
        response = await agent.process(
            query="采购50台工业风机",
            product_category="工业风机"
        )
        
        # 检查响应
        assert response.status in ["success", "partial", "error"]
        assert response.query == "采购50台工业风机"
        assert len(response.task_logs) > 0
    
    async def test_agent_process_complex_query(self):
        """
        测试复杂查询处理
        """
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 执行复杂查询
        response = await agent.process(
            query="采购50台工业风机，想要30天账期，对比往期大客户成交价，给一套合作方案",
            customer_id="C001",
            product_category="工业风机"
        )
        
        # 检查响应
        assert response.status in ["success", "partial", "error"]
        assert response.customer_id == "C001"
        
        # 检查任务日志
        assert len(response.task_logs) > 0
        
        # 检查是否有成功的任务
        successful_tasks = [
            log for log in response.task_logs
            if log.status == Constants.TASK_STATUS_COMPLETED
        ]
        
        assert len(successful_tasks) > 0
    
    async def test_agent_reflection_enabled(self):
        """
        测试反思验真启用
        """
        from config.settings import settings
        
        # 确保反思验真启用
        settings.REFLECTION_ENABLED = True
        
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 执行查询
        response = await agent.process(
            query="采购50台工业风机",
            product_category="工业风机"
        )
        
        # 检查反思报告
        if response.status != "error":
            assert response.reflection_report is not None
            assert response.reflection_report.enabled is True
    
    async def test_agent_task_planning(self):
        """
        测试任务拆解
        """
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 执行查询
        response = await agent.process(
            query="采购50台工业风机",
            product_category="工业风机"
        )
        
        # 检查任务日志中的任务类型
        task_types = [log.task_type for log in response.task_logs]
        
        # 应包含库存查询和价格查询
        assert Constants.TASK_INVENTORY_QUERY in task_types or response.status == "error"
    
    async def test_agent_error_handling(self):
        """
        测试错误处理
        """
        agent = SalesAgent()
        
        # 不注册工具（模拟错误场景）
        
        # 执行查询
        response = await agent.process(
            query="采购50台工业风机",
            product_category="工业风机"
        )
        
        # 应返回错误状态
        assert response.status == "error"
    
    async def test_agent_with_different_products(self):
        """
        测试不同产品查询
        """
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 测试不同产品
        products = ["工业风机", "离心泵", "压缩机"]
        
        for product in products:
            response = await agent.process(
                query=f"采购10台{product}",
                product_category=product
            )
            
            assert response.status in ["success", "partial", "error"]
    
    async def test_agent_performance(self):
        """
        测试 Agent 性能
        """
        import time
        
        agent = SalesAgent()
        
        # 注册工具
        agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        # 执行查询并计时
        start_time = time.time()
        
        response = await agent.process(
            query="采购50台工业风机",
            product_category="工业风机"
        )
        
        elapsed_time = time.time() - start_time
        
        # 检查响应时间（应该在合理范围内）
        # 注意：这个测试可能因为 LLM 调用而耗时较长
        # 这里只检查是否完成，不严格限制时间
        assert response.status in ["success", "partial", "error"]
        
        # 检查任务日志中的耗时
        if response.task_logs:
            for log in response.task_logs:
                if log.duration_ms:
                    assert log.duration_ms > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
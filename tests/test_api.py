"""
API 接口测试模块
测试 FastAPI 接口功能
"""
import pytest
from fastapi.testclient import TestClient
from api.chat_route import create_app


# 创建测试客户端
app = create_app()
client = TestClient(app)


class TestHealthEndpoint:
    """
    健康检查接口测试
    """
    
    def test_health_check(self):
        """
        测试健康检查接口
        """
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "llm_mode" in response.json()
    
    def test_stats_endpoint(self):
        """
        测试统计信息接口
        """
        response = client.get("/api/stats")
        
        assert response.status_code == 200
        assert "total_requests" in response.json()
        assert "successful_requests" in response.json()


class TestToolsEndpoint:
    """
    工具接口测试
    """
    
    def test_get_tools(self):
        """
        测试获取工具列表
        """
        response = client.get("/api/tools")
        
        assert response.status_code == 200
        assert "tools" in response.json()
        assert response.json()["count"] > 0


class TestSalesChatEndpoint:
    """
    销售咨询接口测试
    """
    
    def test_sales_chat_basic(self):
        """
        测试基本销售咨询
        """
        response = client.post(
            "/api/chat/sales",
            json={
                "query": "采购50台工业风机",
                "product_category": "工业风机"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert data["status"] in ["success", "partial", "error"]
    
    def test_sales_chat_with_customer_id(self):
        """
        测试带客户ID的销售咨询
        """
        response = client.post(
            "/api/chat/sales",
            json={
                "customer_id": "C001",
                "query": "采购50台工业风机，想要30天账期",
                "product_category": "工业风机"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["customer_id"] == "C001"
    
    def test_sales_chat_empty_query(self):
        """
        测试空查询
        """
        response = client.post(
            "/api/chat/sales",
            json={
                "query": ""
            }
        )
        
        # 应该返回 422（参数验证失败）
        assert response.status_code == 422
    
    def test_sales_chat_complex_query(self):
        """
        测试复杂查询
        """
        response = client.post(
            "/api/chat/sales",
            json={
                "query": "采购50台工业风机，想要30天账期，对比往期大客户成交价，给一套合作方案",
                "product_category": "工业风机"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应结构
        assert "inventory" in data or data["status"] == "error"
        assert "pricing" in data or data["status"] == "error"
        assert "cases" in data
        assert "task_logs" in data


class TestInitEndpoint:
    """
    初始化接口测试
    """
    
    def test_init_database(self):
        """
        测试数据库初始化
        """
        response = client.post("/api/init")
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestErrorHandling:
    """
    错误处理测试
    """
    
    def test_invalid_endpoint(self):
        """
        测试无效端点
        """
        response = client.get("/api/invalid")
        
        assert response.status_code == 404
    
    def test_invalid_method(self):
        """
        测试无效方法
        """
        response = client.get("/api/chat/sales")
        
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
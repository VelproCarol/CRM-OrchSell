"""
库存查询工具
模拟 CRM 库存 HTTP 接口查询
"""
from typing import Dict, Any, Optional
import random
from loguru import logger

from tools.base_tool import BaseTool
from config.settings import settings, Constants


class ApiInventoryTool(BaseTool):
    """
    库存查询工具
    模拟调用 CRM 库存接口，返回库存信息
    """
    
    # 模拟产品库存数据（个人项目使用模拟数据）
    MOCK_INVENTORY_DATA = {
        "工业风机": {
            "product_sku": "IF-2024-001",
            "stock_quantity": 120,
            "available_quantity": 50,
            "reserved_quantity": 70,
            "lead_time": "7天",
            "warehouse_location": "华东仓库",
            "unit": "台"
        },
        "离心泵": {
            "product_sku": "CP-2024-002",
            "stock_quantity": 80,
            "available_quantity": 30,
            "reserved_quantity": 50,
            "lead_time": "10天",
            "warehouse_location": "华南仓库",
            "unit": "台"
        },
        "压缩机": {
            "product_sku": "CM-2024-003",
            "stock_quantity": 45,
            "available_quantity": 20,
            "reserved_quantity": 25,
            "lead_time": "15天",
            "warehouse_location": "华北仓库",
            "unit": "台"
        },
        "电机": {
            "product_sku": "EM-2024-004",
            "stock_quantity": 200,
            "available_quantity": 150,
            "reserved_quantity": 50,
            "lead_time": "5天",
            "warehouse_location": "华东仓库",
            "unit": "台"
        },
        "阀门": {
            "product_sku": "VL-2024-005",
            "stock_quantity": 500,
            "available_quantity": 400,
            "reserved_quantity": 100,
            "lead_time": "3天",
            "warehouse_location": "华南仓库",
            "unit": "个"
        }
    }
    
    def __init__(self):
        """初始化库存查询工具"""
        super().__init__(
            name=Constants.TOOL_API_INVENTORY,
            description="CRM库存接口查询工具，返回产品实时库存、备货周期等信息"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行库存查询
        
        Args:
            product_name: 产品名称
            quantity: 需求数量（可选）
            
        Returns:
            库存信息字典
        """
        try:
            logger.info(f"库存查询工具开始执行，参数: {kwargs}")
            
            # 参数验证
            product_name = kwargs.get("product_name")
            if not product_name:
                return self._handle_error(ValueError("产品名称不能为空"))
            
            # 模拟调用 CRM 库存接口
            if settings.USE_MOCK_DATA:
                inventory_data = self._mock_api_call(product_name)
            else:
                # 实际 API 调用（需要配置真实 CRM 接口）
                inventory_data = await self._real_api_call(product_name)
            
            # 检查库存是否满足需求
            required_quantity = kwargs.get("quantity", 0)
            if required_quantity > 0:
                available = inventory_data.get("available_quantity", 0)
                if available < required_quantity:
                    inventory_data["stock_warning"] = f"库存不足，当前可用 {available}，需求 {required_quantity}"
                    inventory_data["can_supply"] = False
                else:
                    inventory_data["can_supply"] = True
            
            logger.info(f"库存查询成功，产品: {product_name}, 可用库存: {inventory_data.get('available_quantity')}")
            return self._success_response(inventory_data)
            
        except Exception as e:
            return self._handle_error(e)
    
    def _mock_api_call(self, product_name: str) -> Dict[str, Any]:
        """
        模拟 API 调用
        
        Args:
            product_name: 产品名称
            
        Returns:
            模拟库存数据
        """
        # 查找匹配的产品
        for key, data in self.MOCK_INVENTORY_DATA.items():
            if key in product_name or product_name in key:
                # 添加随机波动（模拟实时库存）
                result = data.copy()
                result["product_name"] = key
                result["stock_quantity"] = data["stock_quantity"] + random.randint(-5, 5)
                result["available_quantity"] = data["available_quantity"] + random.randint(-3, 3)
                result["query_time"] = "2024-01-15 10:30:00"
                return result
        
        # 未找到产品，返回默认数据
        logger.warning(f"未找到产品 {product_name} 的库存数据，返回默认值")
        return {
            "product_name": product_name,
            "product_sku": "UNKNOWN",
            "stock_quantity": 0,
            "available_quantity": 0,
            "reserved_quantity": 0,
            "lead_time": "需询价",
            "warehouse_location": "未知",
            "unit": "未知",
            "query_time": "2024-01-15 10:30:00",
            "warning": "产品未在库存系统中找到"
        }
    
    async def _real_api_call(self, product_name: str) -> Dict[str, Any]:
        """
        实际 API 调用（需要配置真实 CRM 接口）
        
        Args:
            product_name: 产品名称
            
        Returns:
            API 返回的库存数据
        """
        # TODO: 实现真实 CRM 接口调用
        # 示例代码（需要配置 CRM_API_URL 和 CRM_API_KEY）
        """
        import httpx
        
        api_url = settings.CRM_API_URL
        api_key = settings.CRM_API_KEY
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{api_url}/inventory",
                params={"product_name": product_name},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API调用失败: {response.status_code}")
        """
        
        # 当前返回模拟数据
        return self._mock_api_call(product_name)
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数 Schema
        
        Returns:
            参数 Schema 字典
        """
        return {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "产品名称"
                },
                "quantity": {
                    "type": "integer",
                    "description": "需求数量（可选）"
                }
            },
            "required": ["product_name"]
        }
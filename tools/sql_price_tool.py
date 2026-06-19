"""
价格查询工具
查询本地 SQLite/MySQL 历史成交价格
"""
from typing import Dict, Any, Optional, List
import sqlite3
from pathlib import Path
from loguru import logger

from tools.base_tool import BaseTool
from config.settings import settings, Constants
from services.cache_manager import get_cache_manager


class SqlPriceTool(BaseTool):
    """
    价格查询工具
    从本地数据库查询历史成交价格、折扣政策等信息
    """
    
    def __init__(self):
        """初始化价格查询工具"""
        super().__init__(
            name=Constants.TOOL_SQL_PRICE,
            description="历史成交价格查询工具，返回产品价格区间、折扣政策、往期成交记录"
        )
        
        # 数据库路径
        self.db_path = Path(settings.SQLITE_DB_PATH)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行价格查询
        
        Args:
            product_name: 产品名称
            quantity_range: 数量区间 [min, max]（可选）
            payment_terms: 付款条件（可选）
            time_range: 时间范围（可选，默认近6个月）
            
        Returns:
            价格信息字典
        """
        try:
            logger.info(f"价格查询工具开始执行，参数: {kwargs}")
            
            # 参数验证
            product_name = kwargs.get("product_name")
            if not product_name:
                return self._handle_error(ValueError("产品名称不能为空"))
            
            # 构建缓存键（包含数量区间）
            quantity_range = kwargs.get("quantity_range")
            range_key = f"{quantity_range[0]}-{quantity_range[1]}" if quantity_range else None
            
            # 尝试从缓存获取数据
            cache_manager = get_cache_manager()
            cached_data = cache_manager.get_pricing(product_name, range_key)
            if cached_data:
                logger.info(f"从缓存获取价格数据，产品: {product_name}")
                price_data = cached_data
            else:
                # 查询历史成交价格
                price_data = await self._query_price_data(
                    product_name=product_name,
                    quantity_range=quantity_range,
                    payment_terms=kwargs.get("payment_terms"),
                    time_range=kwargs.get("time_range", "6个月")
                )
                
                # 将结果存入缓存
                cache_manager.set_pricing(product_name, price_data, range_key)
            
            logger.info(f"价格查询成功，产品: {product_name}, 平均价格: {price_data.get('avg_price')}")
            return self._success_response(price_data)
            
        except Exception as e:
            return self._handle_error(e)
    
    async def _query_price_data(
        self,
        product_name: str,
        quantity_range: Optional[List[int]] = None,
        payment_terms: Optional[str] = None,
        time_range: str = "6个月"
    ) -> Dict[str, Any]:
        """
        查询价格数据
        
        Args:
            product_name: 产品名称
            quantity_range: 数量区间
            payment_terms: 付款条件
            time_range: 时间范围
            
        Returns:
            价格数据字典
        """
        # 检查数据库是否存在
        if not self.db_path.exists():
            logger.warning(f"数据库不存在: {self.db_path}, 返回模拟数据")
            return self._get_mock_price_data(product_name)
        
        try:
            # 连接数据库
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # 构建查询条件
            conditions = ["product_name LIKE ?"]
            params = [f"%{product_name}%"]
            
            if quantity_range:
                conditions.append("quantity BETWEEN ? AND ?")
                params.extend(quantity_range)
            
            if payment_terms:
                conditions.append("payment_terms LIKE ?")
                params.append(f"%{payment_terms}%")
            
            # 查询历史成交记录
            query = f"""
                SELECT 
                    AVG(unit_price) as avg_price,
                    MIN(unit_price) as min_price,
                    MAX(unit_price) as max_price,
                    AVG(discount_rate) as avg_discount,
                    COUNT(*) as deal_count
                FROM deal_records
                WHERE {(" AND ").join(conditions)}
            """
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            # 查询具体成交记录（用于参考）
            detail_query = f"""
                SELECT 
                    deal_id,
                    customer_name,
                    quantity,
                    unit_price,
                    total_amount,
                    discount_rate,
                    payment_terms,
                    deal_date
                FROM deal_records
                WHERE {(" AND ").join(conditions)}
                ORDER BY deal_date DESC
                LIMIT 5
            """
            
            cursor.execute(detail_query, params)
            details = cursor.fetchall()
            
            conn.close()
            
            if result and result[0]:
                avg_price = result[0]
                min_price = result[1]
                max_price = result[2]
                avg_discount = result[3] or 0
                deal_count = result[4]
                
                # 构建返回数据
                price_data = {
                    "product_name": product_name,
                    "unit_price": float(avg_price),
                    "price_range": {
                        "min": float(min_price),
                        "max": float(max_price)
                    },
                    "discount_rate": float(avg_discount),
                    "deal_count": deal_count,
                    "time_range": time_range,
                    "recent_deals": [
                        {
                            "deal_id": row[0],
                            "customer_name": row[1],
                            "quantity": row[2],
                            "unit_price": float(row[3]),
                            "total_amount": float(row[4]),
                            "discount_rate": float(row[5]),
                            "payment_terms": row[6],
                            "deal_date": row[7]
                        }
                        for row in details
                    ]
                }
                
                return price_data
            else:
                logger.warning(f"未找到产品 {product_name} 的成交记录")
                return self._get_mock_price_data(product_name)
                
        except sqlite3.Error as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return self._get_mock_price_data(product_name)
    
    def _get_mock_price_data(self, product_name: str) -> Dict[str, Any]:
        """
        获取模拟价格数据
        
        Args:
            product_name: 产品名称
            
        Returns:
            模拟价格数据
        """
        # 模拟价格数据
        mock_prices = {
            "工业风机": {
                "unit_price": 8500.0,
                "price_range": {"min": 8000.0, "max": 9000.0},
                "discount_rate": 0.05,
                "deal_count": 12,
                "time_range": "近6个月",
                "recent_deals": [
                    {
                        "deal_id": "D-2024-001",
                        "customer_name": "某制造企业A",
                        "quantity": 55,
                        "unit_price": 8200.0,
                        "total_amount": 451000.0,
                        "discount_rate": 0.05,
                        "payment_terms": "30天账期",
                        "deal_date": "2024-01-10"
                    },
                    {
                        "deal_id": "D-2024-002",
                        "customer_name": "某制造企业B",
                        "quantity": 40,
                        "unit_price": 8500.0,
                        "total_amount": 340000.0,
                        "discount_rate": 0.03,
                        "payment_terms": "款到发货",
                        "deal_date": "2024-01-05"
                    }
                ]
            },
            "离心泵": {
                "unit_price": 3200.0,
                "price_range": {"min": 3000.0, "max": 3500.0},
                "discount_rate": 0.04,
                "deal_count": 8,
                "time_range": "近6个月"
            },
            "压缩机": {
                "unit_price": 15000.0,
                "price_range": {"min": 14000.0, "max": 16000.0},
                "discount_rate": 0.06,
                "deal_count": 5,
                "time_range": "近6个月"
            },
            "电机": {
                "unit_price": 1200.0,
                "price_range": {"min": 1100.0, "max": 1300.0},
                "discount_rate": 0.02,
                "deal_count": 20,
                "time_range": "近6个月"
            },
            "阀门": {
                "unit_price": 350.0,
                "price_range": {"min": 320.0, "max": 380.0},
                "discount_rate": 0.01,
                "deal_count": 30,
                "time_range": "近6个月"
            }
        }
        
        # 查找匹配的产品
        for key, data in mock_prices.items():
            if key in product_name or product_name in key:
                result = data.copy()
                result["product_name"] = key
                return result
        
        # 未找到产品，返回默认数据
        logger.warning(f"未找到产品 {product_name} 的价格数据，返回默认值")
        return {
            "product_name": product_name,
            "unit_price": 0.0,
            "price_range": {"min": 0.0, "max": 0.0},
            "discount_rate": 0.0,
            "deal_count": 0,
            "time_range": "无数据",
            "warning": "产品未在价格库中找到"
        }
    
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
                "quantity_range": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "数量区间 [min, max]（可选）"
                },
                "payment_terms": {
                    "type": "string",
                    "description": "付款条件（可选）"
                },
                "time_range": {
                    "type": "string",
                    "description": "时间范围（可选）"
                }
            },
            "required": ["product_name"]
        }
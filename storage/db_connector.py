"""
数据库连接器模块
支持 SQLite/MySQL/PostgreSQL 多数据库类型连接
提供统一的数据库查询接口
"""
from typing import Dict, Any, Optional, List
import sqlite3
from pathlib import Path
from loguru import logger

from config.settings import settings


class DatabaseConnector:
    """
    数据库连接器
    统一管理不同类型数据库的连接和查询
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化数据库连接器"""
        self.db_type = settings.DB_TYPE
        self.connection = None
        self._connect()
    
    def _connect(self):
        """建立数据库连接"""
        try:
            if self.db_type == "sqlite":
                db_path = Path(settings.SQLITE_DB_PATH)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                self.connection = sqlite3.connect(str(db_path))
                self.connection.row_factory = sqlite3.Row
            elif self.db_type == "mysql":
                import pymysql
                self.connection = pymysql.connect(
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DB,
                    charset="utf8mb4"
                )
            elif self.db_type == "postgresql":
                import psycopg2
                self.connection = psycopg2.connect(
                    host=settings.POSTGRES_HOST,
                    port=settings.POSTGRES_PORT,
                    user=settings.POSTGRES_USER,
                    password=settings.POSTGRES_PASSWORD,
                    dbname=settings.POSTGRES_DB
                )
            
            logger.info(f"数据库连接成功，类型: {self.db_type}")
            
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
    
    def _ensure_connection(self):
        """确保连接有效"""
        if not self.connection:
            self._connect()
        
        try:
            if self.db_type == "mysql":
                self.connection.ping(reconnect=True)
            elif self.db_type == "postgresql":
                self.connection.cursor().execute("SELECT 1")
        except Exception:
            logger.warning("数据库连接已断开，重新连接...")
            self._connect()
    
    def query(self, sql: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        
        Args:
            sql: SQL查询语句
            params: 查询参数列表
            
        Returns:
            查询结果列表，每条记录为字典
        """
        self._ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if self.db_type == "sqlite":
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            elif self.db_type == "mysql":
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            elif self.db_type == "postgresql":
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
            
            cursor.close()
            
            result = []
            for row in rows:
                record = {}
                for i, col in enumerate(columns):
                    record[col] = row[i]
                result.append(record)
            
            return result
            
        except Exception as e:
            logger.error(f"数据库查询失败: {str(e)}, SQL: {sql}")
            raise
    
    def execute(self, sql: str, params: Optional[List] = None) -> int:
        """
        执行非查询语句（INSERT/UPDATE/DELETE）
        
        Args:
            sql: SQL语句
            params: 参数列表
            
        Returns:
            受影响的行数
        """
        self._ensure_connection()
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            affected_rows = cursor.rowcount
            self.connection.commit()
            cursor.close()
            
            return affected_rows
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"数据库执行失败: {str(e)}, SQL: {sql}")
            raise
    
    def get_inventory(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        查询产品库存信息
        
        Args:
            product_name: 产品名称
            
        Returns:
            库存信息字典
        """
        try:
            sql = """
                SELECT product_name, product_sku, stock_quantity, 
                       available_quantity, reserved_quantity, 
                       lead_time, warehouse_location, unit
                FROM inventory
                WHERE product_name LIKE ?
                LIMIT 1
            """
            
            results = self.query(sql, [f"%{product_name}%"])
            
            if results:
                return results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"库存查询失败: {str(e)}")
            return None
    
    def get_price_info(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        查询产品价格信息
        
        Args:
            product_name: 产品名称
            
        Returns:
            价格信息字典
        """
        try:
            sql = """
                SELECT AVG(unit_price) as avg_price,
                       MIN(unit_price) as min_price,
                       MAX(unit_price) as max_price,
                       AVG(discount_rate) as avg_discount,
                       COUNT(*) as deal_count
                FROM deal_records
                WHERE product_name LIKE ?
            """
            
            results = self.query(sql, [f"%{product_name}%"])
            
            if results and results[0]["avg_price"] is not None:
                return {
                    "avg_price": float(results[0]["avg_price"]),
                    "min_price": float(results[0]["min_price"]),
                    "max_price": float(results[0]["max_price"]),
                    "avg_discount": float(results[0]["avg_discount"] or 0),
                    "deal_count": results[0]["deal_count"]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"价格查询失败: {str(e)}")
            return None
    
    def get_product_list(self) -> List[Dict[str, Any]]:
        """
        获取产品列表
        
        Returns:
            产品列表
        """
        try:
            sql = """
                SELECT product_sku, product_name, category, 
                       base_price, unit, description
                FROM products
                ORDER BY category, product_name
            """
            
            return self.query(sql)
            
        except Exception as e:
            logger.error(f"产品列表查询失败: {str(e)}")
            return []
    
    def get_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        查询客户信息
        
        Args:
            customer_id: 客户ID
            
        Returns:
            客户信息字典
        """
        try:
            sql = """
                SELECT customer_id, customer_name, industry, 
                       contact_person, contact_phone, address, credit_level
                FROM customers
                WHERE customer_id = ?
                LIMIT 1
            """
            
            results = self.query(sql, [customer_id])
            
            if results:
                return results[0]
            
            return None
            
        except Exception as e:
            logger.error(f"客户查询失败: {str(e)}")
            return None
    
    def get_recent_deals(self, product_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近成交记录
        
        Args:
            product_name: 产品名称
            limit: 返回数量限制
            
        Returns:
            成交记录列表
        """
        try:
            sql = """
                SELECT deal_id, customer_name, quantity, unit_price, 
                       total_amount, discount_rate, payment_terms, deal_date
                FROM deal_records
                WHERE product_name LIKE ?
                ORDER BY deal_date DESC
                LIMIT ?
            """
            
            return self.query(sql, [f"%{product_name}%", limit])
            
        except Exception as e:
            logger.error(f"成交记录查询失败: {str(e)}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")


def get_db_connector() -> DatabaseConnector:
    """
    获取数据库连接器实例
    
    Returns:
        DatabaseConnector 实例
    """
    return DatabaseConnector()

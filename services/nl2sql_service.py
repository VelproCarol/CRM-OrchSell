"""
NL2SQL 服务模块
使用大模型将自然语言转换为 SQL 语句并执行查询
"""
from typing import List, Dict, Any, Optional
from loguru import logger
import sqlite3
import re
from pathlib import Path

from config.settings import settings
from core.llm_adapter import get_llm_adapter


class NL2SQLService:
    """
    NL2SQL 服务类
    负责将自然语言查询转换为 SQL 并安全执行
    """
    
    def __init__(self):
        """初始化 NL2SQL 服务"""
        self.db_path = Path(settings.SQLITE_DB_PATH)
        self.llm_adapter = get_llm_adapter()
        self._schema_cache = None
        
        # 危险 SQL 关键词（禁止使用）
        self.dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'TRUNCATE', 
            'ALTER', 'CREATE', 'DROP TABLE', 'DROP DATABASE',
            'EXEC', 'EXECUTE', 'SP_', 'XP_'
        ]
        
        # 允许的表名白名单
        self.allowed_tables = [
            'products', 'customers', 'deal_records'
        ]
        
    def _get_database_schema(self) -> str:
        """
        获取数据库 schema 信息（缓存）
        
        Returns:
            数据库表结构描述
        """
        if self._schema_cache is not None:
            return self._schema_cache
            
        if not self.db_path.exists():
            return ""
            
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_info = []
        for table in tables:
            if table.startswith('sqlite_'):
                continue
                
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            
            column_descriptions = []
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                column_descriptions.append(f"- {col_name}: {col_type}")
            
            schema_info.append(f"表名: {table}")
            schema_info.append("列:")
            schema_info.extend(column_descriptions)
            schema_info.append("")
        
        conn.close()
        
        self._schema_cache = "\n".join(schema_info)
        return self._schema_cache
    
    def _validate_sql(self, sql: str) -> bool:
        """
        验证 SQL 语句安全性
        
        Args:
            sql: SQL 语句
            
        Returns:
            是否安全
        """
        upper_sql = sql.strip().upper()
        
        # 检查是否包含危险关键词
        for keyword in self.dangerous_keywords:
            if keyword in upper_sql:
                logger.warning(f"检测到危险 SQL 关键词: {keyword}")
                return False
        
        # 检查是否以 SELECT 开头
        if not upper_sql.startswith('SELECT'):
            logger.warning(f"只允许 SELECT 查询，当前 SQL: {sql[:50]}")
            return False
            
        # 检查查询的表是否在白名单中（忽略大小写）
        # 提取 FROM 后面的表名
        from_match = re.search(r'FROM\s+(\w+)', upper_sql)
        if from_match:
            table_name = from_match.group(1).lower()  # 转换为小写比较
            if table_name not in self.allowed_tables:
                logger.warning(f"表 {table_name} 不在白名单中")
                return False
                
        return True
    
    def _parse_sql_result(self, cursor: sqlite3.Cursor) -> Dict[str, Any]:
        """
        解析 SQL 查询结果
        
        Args:
            cursor: 数据库游标
            
        Returns:
            包含列名和数据的字典
        """
        # 获取列名
        column_names = [desc[0] for desc in cursor.description]
        # 获取数据
        rows = cursor.fetchall()
        
        # 转换为字典列表
        result = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            result.append(row_dict)
        
        return {
            'columns': column_names,
            'data': result,
            'count': len(result)
        }
    
    async def generate_sql(self, natural_query: str) -> str:
        """
        使用大模型将自然语言转换为 SQL 语句
        
        Args:
            natural_query: 自然语言查询
            
        Returns:
            生成的 SQL 语句
        """
        schema = self._get_database_schema()
        
        if not schema:
            return "SELECT * FROM products LIMIT 10"
        
        # 构建提示词
        prompt = f"""
你是一个 SQL 专家，需要根据用户的自然语言查询生成正确的 SQLite SQL 语句。

数据库 schema 如下：
{schema}

用户查询：{natural_query}

请只返回 SQL 语句，不要包含其他解释。SQL 语句必须是有效的 SQLite 语法。

注意：
1. 只使用 SELECT 查询
2. 使用中文列名时保持原样
3. 避免使用复杂的 JOIN，尽量使用简单查询
4. 如果不确定表名或列名，可以查询 products 表获取产品信息

例如：
用户：查询所有产品
SQL：SELECT * FROM products

用户：工业风机的库存是多少
SQL：SELECT * FROM products WHERE product_name = '工业风机'

用户：A级客户有哪些
SQL：SELECT * FROM customers WHERE credit_level = 'A级'
        """.strip()
        
        messages = [
            {"role": "system", "content": "你是一个专业的 SQL 生成助手，只输出 SQL 语句。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.llm_adapter.chat(messages, temperature=0.1)
            logger.debug(f"生成的 SQL: {response.strip()}")
            return response.strip()
        except Exception as e:
            logger.error(f"大模型调用失败: {str(e)}")
            # 失败时返回默认查询
            return "SELECT * FROM products LIMIT 10"
    
    async def query(self, natural_query: str) -> Dict[str, Any]:
        """
        执行自然语言查询
        
        Args:
            natural_query: 自然语言查询
            
        Returns:
            查询结果字典
        """
        # 生成 SQL
        sql = await self.generate_sql(natural_query)
        
        # 验证 SQL
        if not self._validate_sql(sql):
            return {
                'status': 'error',
                'message': 'SQL 语句不安全，已被拒绝执行',
                'generated_sql': sql
            }
        
        # 执行查询
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 设置查询超时（通过限制执行时间）
            cursor.execute("PRAGMA query_only = ON;")
            cursor.execute(sql)
            
            result = self._parse_sql_result(cursor)
            conn.close()
            
            logger.info(f"NL2SQL 查询成功: {natural_query}, 返回 {result['count']} 条记录")
            
            return {
                'status': 'success',
                'query_text': natural_query,
                'generated_sql': sql,
                'columns': result['columns'],
                'data': result['data'],
                'count': result['count']
            }
            
        except sqlite3.Error as e:
            logger.error(f"SQL 执行失败: {str(e)}, SQL: {sql}")
            return {
                'status': 'error',
                'message': f'SQL 执行失败: {str(e)}',
                'generated_sql': sql
            }
        except Exception as e:
            logger.error(f"查询异常: {str(e)}")
            return {
                'status': 'error',
                'message': f'查询异常: {str(e)}',
                'generated_sql': sql
            }
    
    async def explain_intent(self, natural_query: str) -> str:
        """
        使用大模型解析用户查询意图
        
        Args:
            natural_query: 自然语言查询
            
        Returns:
            意图解析结果
        """
        prompt = f"""
分析用户的查询意图：

用户查询：{natural_query}

请分析：
1. 用户想要查询的对象（产品/客户/成交记录/库存）
2. 查询的条件或筛选要求
3. 期望的输出格式

请用简洁的中文描述，不超过100字。
        """.strip()
        
        messages = [
            {"role": "system", "content": "你是一个意图分析专家，帮助分析用户的查询意图。"},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.llm_adapter.chat(messages, temperature=0.3)
            return response.strip()
        except Exception as e:
            logger.error(f"意图分析失败: {str(e)}")
            return "无法解析查询意图"


# 创建单例服务
_nl2sql_service = None

def get_nl2sql_service() -> NL2SQLService:
    """
    获取 NL2SQL 服务实例（单例）
    
    Returns:
        NL2SQLService 实例
    """
    global _nl2sql_service
    if _nl2sql_service is None:
        _nl2sql_service = NL2SQLService()
    return _nl2sql_service
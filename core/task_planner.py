"""
任务拆解器模块
基于大模型将客户咨询拆解为标准化子任务队列
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from loguru import logger

from config.settings import settings, Constants
from core.llm_adapter import get_llm
from schemas.output_schema import TaskPlan


class TaskPlanner:
    """
    任务拆解器
    根据客户咨询文本自主拆分销售子任务队列
    """
    
    # 系统提示词：角色层 + 任务规则层 + 输出约束层
    SYSTEM_PROMPT = """你是一个专业的销售任务拆解助手，专门负责分析客户咨询并拆解为标准化的销售子任务。

## 角色定位
你是一个数据驱动的销售助理，只能基于真实数据源（库存系统、价格数据库、案例文档库）提供信息。
你绝对不能编造任何库存、价格、案例数据。

## 任务拆解规则
根据客户咨询，你需要拆解以下4类标准任务：

1. **库存查询任务** (inventory_query)
   - 触发条件：客户提及具体产品、数量、交期需求
   - 执行工具：api_inventory
   - 输出：产品库存量、可用量、备货周期

2. **价格查询任务** (price_query)
   - 触发条件：客户提及价格、折扣、往期成交价对比
   - 执行工具：sql_price
   - 输出：历史成交价格、价格区间、折扣政策

3. **案例检索任务** (case_retrieval)
   - 触发条件：客户提及案例参考、相似客户、合作方案
   - 执行工具：doc_retrieve
   - 输出：相似成交案例、客户画像、合作模式

4. **价格计算任务** (price_calculation)
   - 触发条件：客户需要报价、毛利计算、账期成本
   - 执行工具：calculator
   - 输出：最终报价、毛利区间、付款方案

## 任务优先级规则
1. 库存查询任务优先级最高（priority=1）
2. 价格查询和案例检索可并行执行（priority=2）
3. 价格计算依赖前序任务结果（priority=3）

## 任务依赖关系
- price_calculation 依赖 inventory_query 和 price_query 的结果

## 输出格式要求
你必须严格按照 JSON 格式输出任务列表，格式如下：
```json
{
  "tasks": [
    {
      "task_type": "任务类型（如 inventory_query, price_query 等）",
      "tool_name": "工具名称",
      "description": "任务描述",
      "parameters": {
        "参数名": "参数值"
      },
      "priority": 优先级数字,
      "dependencies": ["依赖的任务类型（如 inventory_query）"]
    }
  ]
}
```

**重要**：dependencies 数组中必须填写任务类型（task_type），如 `["inventory_query", "price_query"]`，不能填写 task_id。
```

## 示例
客户咨询："采购50台工业风机，想要30天账期，对比往期大客户成交价，给一套合作方案"

输出：
```json
{
  "tasks": [
    {
      "task_type": "inventory_query",
      "tool_name": "api_inventory",
      "description": "查询工业风机库存情况",
      "parameters": {
        "product_name": "工业风机",
        "quantity": 50
      },
      "priority": 1,
      "dependencies": []
    },
    {
      "task_type": "price_query",
      "tool_name": "sql_price",
      "description": "查询工业风机历史成交价格",
      "parameters": {
        "product_name": "工业风机",
        "quantity_range": [40, 60]
      },
      "priority": 2,
      "dependencies": []
    },
    {
      "task_type": "case_retrieval",
      "tool_name": "doc_retrieve",
      "description": "检索相似采购量和账期的成交案例",
      "parameters": {
        "product_name": "工业风机",
        "quantity_range": [40, 60],
        "payment_terms": "30天账期"
      },
      "priority": 2,
      "dependencies": []
    },
    {
      "task_type": "price_calculation",
      "tool_name": "calculator",
      "description": "计算最终报价和毛利",
      "parameters": {
        "quantity": 50,
        "payment_terms": "30天账期"
      },
      "priority": 3,
      "dependencies": ["inventory_query", "price_query"]
    }
  ]
}
```

现在，请根据客户的咨询内容，拆解任务并输出 JSON 格式的任务列表。"""
    
    def __init__(self):
        """初始化任务拆解器"""
        self.llm = get_llm()
        logger.info("任务拆解器初始化完成")
    
    async def plan(
        self,
        query: str,
        customer_id: Optional[str] = None,
        product_category: Optional[str] = None
    ) -> List[TaskPlan]:
        """
        拆解客户咨询为任务列表
        
        Args:
            query: 客户咨询文本
            customer_id: 客户ID
            product_category: 产品品类
            
        Returns:
            任务计划列表
        """
        logger.info(f"开始拆解任务，查询: {query[:50]}...")
        
        # 构建用户消息
        user_message = f"""客户咨询：{query}

客户ID：{customer_id or '未提供'}
产品品类：{product_category or '未明确'}

请拆解任务并输出 JSON 格式的任务列表。"""
        
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # 调用大模型拆解任务
            response = await self.llm.chat(
                messages=messages,
                temperature=0.3  # 低温度保证输出稳定性
            )
            
            logger.debug(f"任务拆解响应: {response[:200]}...")
            
            # 解析响应
            tasks = self._parse_response(response)
            
            # 为每个任务分配唯一ID
            task_plans = []
            for idx, task in enumerate(tasks):
                task_id = f"task_{uuid.uuid4().hex[:8]}"
                task_plan = TaskPlan(
                    task_id=task_id,
                    task_type=task.get("task_type", "unknown"),
                    tool_name=task.get("tool_name", "unknown"),
                    description=task.get("description", ""),
                    parameters=task.get("parameters", {}),
                    priority=task.get("priority", idx + 1),
                    dependencies=task.get("dependencies", [])
                )
                task_plans.append(task_plan)
            
            logger.info(f"任务拆解完成，共 {len(task_plans)} 个任务")
            return task_plans
            
        except Exception as e:
            logger.error(f"任务拆解失败: {str(e)}")
            # 返回默认任务列表
            return self._get_default_tasks(query, product_category)
    
    def _parse_response(self, response: str) -> List[Dict[str, Any]]:
        """
        解析大模型响应，提取任务列表
        
        Args:
            response: 大模型响应文本
            
        Returns:
            任务字典列表
        """
        import json
        import re
        
        try:
            # 尝试提取 JSON 块
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = response
            
            data = json.loads(json_str)
            tasks = data.get("tasks", [])
            
            if not tasks:
                logger.warning("响应中未找到任务列表")
                return []
            
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {str(e)}")
            return []
    
    def _get_default_tasks(
        self,
        query: str,
        product_category: Optional[str] = None
    ) -> List[TaskPlan]:
        """
        获取默认任务列表（降级方案）
        
        Args:
            query: 客户咨询
            product_category: 产品品类
            
        Returns:
            默认任务列表
        """
        logger.warning("使用默认任务列表")
        
        product = product_category or "产品"
        
        return [
            TaskPlan(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                task_type=Constants.TASK_INVENTORY_QUERY,
                tool_name=Constants.TOOL_API_INVENTORY,
                description=f"查询{product}库存情况",
                parameters={"product_name": product},
                priority=1,
                dependencies=[]
            ),
            TaskPlan(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                task_type=Constants.TASK_PRICE_QUERY,
                tool_name=Constants.TOOL_SQL_PRICE,
                description=f"查询{product}历史成交价格",
                parameters={"product_name": product},
                priority=2,
                dependencies=[]
            ),
            TaskPlan(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                task_type=Constants.TASK_CASE_RETRIEVAL,
                tool_name=Constants.TOOL_DOC_RETRIEVE,
                description=f"检索{product}相似成交案例",
                parameters={"product_name": product},
                priority=2,
                dependencies=[]
            ),
            TaskPlan(
                task_id=f"task_{uuid.uuid4().hex[:8]}",
                task_type=Constants.TASK_PRICE_CALCULATION,
                tool_name=Constants.TOOL_CALCULATOR,
                description="计算最终报价和毛利",
                parameters={},
                priority=3,
                dependencies=["inventory_query", "price_query"]
            )
        ]
"""
CRM-OrchSell 量化测试数据集

包含覆盖不同业务场景的标注测试样本，用于评估Agent系统的各项能力。
数据集分为三类：
1. TEST_CASES: 任务拆解测试用例
2. REFLECTION_TEST_CASES: 反思验真测试用例（含故意篡改数据）
3. TOOL_TEST_QUERIES: 工具准确性测试查询
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExpectedTask(BaseModel):
    """预期任务定义"""
    task_type: str = Field(description="任务类型: inventory_query, price_query, case_retrieval, price_calculation")
    tool: str = Field(description="使用的工具名称")
    priority: int = Field(description="任务优先级 1-4")
    dependencies: Optional[List[str]] = Field(default=None, description="依赖的任务ID列表")


class TestCase(BaseModel):
    """任务拆解测试用例"""
    id: str = Field(description="测试用例唯一标识")
    query: str = Field(description="用户输入的客户咨询文本")
    expected_tasks: List[ExpectedTask] = Field(description="预期的任务列表")
    expected_keywords: Optional[List[str]] = Field(default=None, description="预期提取的关键词")
    expected_params: Optional[Dict[str, Any]] = Field(default=None, description="预期提取的参数")
    description: str = Field(description="测试场景描述")


class ReflectionTestCase(BaseModel):
    """反思验真测试用例"""
    id: str = Field(description="测试用例唯一标识")
    query: str = Field(description="用户输入的客户咨询文本")
    response_data: Dict[str, Any] = Field(description="Agent生成的响应数据")
    is_corrupted: bool = Field(description="数据是否被故意篡改: True=篡改, False=正常")
    corrupted_fields: Optional[List[str]] = Field(default=None, description="被篡改的字段列表")
    description: str = Field(description="测试场景描述")


class ToolQuery(BaseModel):
    """工具测试查询"""
    id: str = Field(description="查询唯一标识")
    tool_name: str = Field(description="工具名称")
    params: Dict[str, Any] = Field(description="工具调用参数")
    expected_result: Dict[str, Any] = Field(description="预期的查询结果（真值）")
    description: str = Field(description="测试场景描述")


TEST_CASES: List[TestCase] = [
    # ==================== 单任务：库存查询 ====================
    TestCase(
        id="TC-001",
        query="查询工业风机的库存情况",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1)
        ],
        expected_keywords=["工业风机"],
        description="单任务：纯库存查询"
    ),
    TestCase(
        id="TC-002",
        query="现在离心泵还有多少现货？",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1)
        ],
        expected_keywords=["离心泵", "现货"],
        description="单任务：库存+现货查询"
    ),
    TestCase(
        id="TC-003",
        query="输送机库存够100米吗？",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1)
        ],
        expected_keywords=["输送机", "100米"],
        description="单任务：带数量的库存查询"
    ),
    TestCase(
        id="TC-004",
        query="变压器当前库存",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1)
        ],
        expected_keywords=["变压器"],
        description="单任务：简化库存查询"
    ),
    TestCase(
        id="TC-005",
        query="空压机有货吗？",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1)
        ],
        expected_keywords=["空压机"],
        description="单任务：库存有无查询"
    ),

    # ==================== 单任务：价格查询 ====================
    TestCase(
        id="TC-006",
        query="我想了解离心泵最近的成交价格",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["离心泵", "成交价"],
        description="单任务：历史成交价查询"
    ),
    TestCase(
        id="TC-007",
        query="工业风机现在什么价？",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["工业风机", "价格"],
        description="单任务：当前价格查询"
    ),
    TestCase(
        id="TC-008",
        query="100千伏安变压器报价",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["100千伏安", "变压器", "报价"],
        description="单任务：规格产品报价"
    ),
    TestCase(
        id="TC-009",
        query="你们的空压机最低能给到多少折扣？",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["空压机", "折扣"],
        description="单任务：折扣查询"
    ),
    TestCase(
        id="TC-010",
        query="大型破碎机的单价是多少？",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["大型破碎机", "单价"],
        description="单任务：单价查询"
    ),

    # ==================== 单任务：案例检索 ====================
    TestCase(
        id="TC-011",
        query="有没有其他公司采购工业风机的合作案例？",
        expected_tasks=[
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=1)
        ],
        expected_keywords=["工业风机", "合作案例"],
        description="单任务：案例检索"
    ),
    TestCase(
        id="TC-012",
        query="想看一些离心泵的应用案例",
        expected_tasks=[
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=1)
        ],
        expected_keywords=["离心泵", "应用案例"],
        description="单任务：应用案例检索"
    ),
    TestCase(
        id="TC-013",
        query="你们有没有做过化工行业的项目案例？",
        expected_tasks=[
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=1)
        ],
        expected_keywords=["化工行业", "项目案例"],
        description="单任务：行业案例检索"
    ),

    # ==================== 双任务组合 ====================
    TestCase(
        id="TC-014",
        query="工业风机库存还有多少？另外价格怎么样？",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2)
        ],
        expected_keywords=["工业风机", "库存", "价格"],
        description="双任务：库存+价格"
    ),
    TestCase(
        id="TC-015",
        query="我想买50台离心泵，先看看库存和类似的合作案例",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["50台", "离心泵", "库存", "合作案例"],
        expected_params={"quantity": 50, "product_name": "离心泵"},
        description="双任务：库存+案例"
    ),
    TestCase(
        id="TC-016",
        query="工业风机多少钱一台？有没有其他企业采购的案例？",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["工业风机", "价格", "采购案例"],
        description="双任务：价格+案例"
    ),
    TestCase(
        id="TC-017",
        query="输送机定位于化工行业，想了解库存和成交价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["输送机", "化工行业", "库存", "成交价"],
        description="双任务：并行库存+价格"
    ),
    TestCase(
        id="TC-018",
        query="帮我查下变压器的库存和折扣政策",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2)
        ],
        expected_keywords=["变压器", "库存", "折扣"],
        description="双任务：库存+折扣"
    ),
    TestCase(
        id="TC-019",
        query="我采购空压机，想看一下同行业案例和价格",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["空压机", "同行业案例", "价格"],
        description="双任务：价格+案例"
    ),
    TestCase(
        id="TC-020",
        query="破碎机现货有多少？最近成交价是多少？",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1)
        ],
        expected_keywords=["破碎机", "现货", "成交价"],
        description="双任务：并行库存+价格"
    ),
    TestCase(
        id="TC-021",
        query="想买工业风机，先看下库存，再给我报个价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=2,
                         dependencies=["inventory_query"])
        ],
        expected_keywords=["工业风机", "库存", "报价"],
        description="双任务：库存+计算报价"
    ),

    # ==================== 三任务组合 ====================
    TestCase(
        id="TC-022",
        query="采购30台离心泵，想了解库存情况、历史成交价和类似案例",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["30台", "离心泵", "库存", "成交价", "案例"],
        expected_params={"quantity": 30, "product_name": "离心泵"},
        description="三任务：库存+价格+案例"
    ),
    TestCase(
        id="TC-023",
        query="想采购输送机用于矿山，需要查看库存、价格和行业案例",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["输送机", "矿山", "库存", "价格", "案例"],
        expected_params={"product_name": "输送机", "industry": "矿山"},
        description="三任务：带行业库存+价格+案例"
    ),
    TestCase(
        id="TC-024",
        query="我需要500kVA变压器，先看库存，再查成交价，最后做个报价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["500kVA变压器", "库存", "成交价", "报价"],
        expected_params={"product_name": "500kVA变压器"},
        description="三任务：库存+价格+计算"
    ),
    TestCase(
        id="TC-025",
        query="采购一批空压机，看库存、查案例、算下总价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query"])
        ],
        expected_keywords=["空压机", "库存", "案例", "总价"],
        description="三任务：库存+案例+计算"
    ),
    TestCase(
        id="TC-026",
        query="需要采购工业风机，了解库存、对比价格、看看其他客户案例",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["工业风机", "库存", "价格", "客户案例"],
        description="三任务：库存+价格+案例"
    ),
    TestCase(
        id="TC-027",
        query="破碎机采购，先看库存和价格，然后给我做个带折扣的报价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=2,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["破碎机", "库存", "价格", "折扣", "报价"],
        description="三任务：并行库存+价格+计算"
    ),

    # ==================== 四任务全链路 ====================
    TestCase(
        id="TC-028",
        query="采购50台工业风机，想要30天账期，对比往期大客户成交价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["50台", "工业风机", "30天账期", "大客户成交价"],
        expected_params={"quantity": 50, "payment_terms": "30天账期", "product_name": "工业风机"},
        description="四任务：完整销售全链路"
    ),
    TestCase(
        id="TC-029",
        query="想采购100台离心泵用于污水处理项目，需要了解库存、价格、案例并做完整报价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["100台", "离心泵", "污水处理", "库存", "价格", "案例", "报价"],
        expected_params={"quantity": 100, "project_type": "污水处理", "product_name": "离心泵"},
        description="四任务：项目采购全链路"
    ),
    TestCase(
        id="TC-030",
        query="需要20台大型破碎机，要60天账期，想看历史成交价和矿山行业案例",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["20台", "大型破碎机", "60天账期", "矿山", "成交价", "案例"],
        expected_params={"quantity": 20, "payment_terms": "60天账期", "industry": "矿山", "product_name": "大型破碎机"},
        description="四任务：矿山采购全链路"
    ),
    TestCase(
        id="TC-031",
        query="采购10台500kVA变压器，用于新能源项目，需了解库存、历史成交、参考案例并计算总价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["10台", "500kVA变压器", "新能源", "库存", "成交", "案例", "总价"],
        expected_params={"quantity": 10, "project_type": "新能源", "product_name": "500kVA变压器"},
        description="四任务：新能源项目采购"
    ),
    TestCase(
        id="TC-032",
        query="工业风机批量采购30台，要了解库存、查近期成交价、看化工行业案例、给我算个带折扣的报价方案",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["30台", "工业风机", "库存", "成交价", "化工", "案例", "折扣", "报价"],
        expected_params={"quantity": 30, "industry": "化工", "product_name": "工业风机"},
        description="四任务：批量采购全链路"
    ),

    # ==================== 边界场景 ====================
    TestCase(
        id="TC-033",
        query="你们有什么产品可以推荐吗？",
        expected_tasks=[],
        expected_keywords=[],
        description="边界场景：模糊需求，无明确任务"
    ),
    TestCase(
        id="TC-034",
        query="我想了解一下",
        expected_tasks=[],
        expected_keywords=[],
        description="边界场景：极度模糊需求"
    ),
    TestCase(
        id="TC-035",
        query="输送机和破碎机各50台，都要报价",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1),
            ExpectedTask(task_type="price_query", tool="sql_price", priority=2),
            ExpectedTask(task_type="price_calculation", tool="calculator", priority=3,
                         dependencies=["inventory_query", "price_query"])
        ],
        expected_keywords=["输送机", "破碎机", "50台", "报价"],
        expected_params={"products": ["输送机", "破碎机"], "quantity": 50},
        description="边界场景：多产品混合需求"
    ),
    TestCase(
        id="TC-036",
        query="库存怎么样？",
        expected_tasks=[
            ExpectedTask(task_type="inventory_query", tool="api_inventory", priority=1)
        ],
        expected_keywords=["库存"],
        description="边界场景：无产品名的库存查询"
    ),
    TestCase(
        id="TC-037",
        query="帮我看看价格和案例",
        expected_tasks=[
            ExpectedTask(task_type="price_query", tool="sql_price", priority=1),
            ExpectedTask(task_type="case_retrieval", tool="doc_retrieve", priority=2)
        ],
        expected_keywords=["价格", "案例"],
        description="边界场景：无产品名的价格+案例"
    ),
]

REFLECTION_TEST_CASES: List[ReflectionTestCase] = [
    # ==================== 正常数据测试用例 ====================
    ReflectionTestCase(
        id="REF-001",
        query="工业风机采购50台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "工业风机",
                "stock_quantity": 200,
                "available_quantity": 200,
                "lead_time": "7天"
            },
            "pricing": {
                "unit_price": 15000,
                "quantity": 50,
                "total_price": 675000,
                "discount_rate": 0.1,
                "payment_terms": "30天账期"
            }
        },
        is_corrupted=False,
        description="正常数据：库存充足，价格合理"
    ),
    ReflectionTestCase(
        id="REF-002",
        query="离心泵采购30台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "离心泵",
                "stock_quantity": 500,
                "available_quantity": 500,
                "lead_time": "5天"
            },
            "pricing": {
                "unit_price": 8500,
                "quantity": 30,
                "total_price": 216750,
                "discount_rate": 0.15,
                "payment_terms": "15天账期"
            }
        },
        is_corrupted=False,
        description="正常数据：离心泵库存价格"
    ),
    ReflectionTestCase(
        id="REF-003",
        query="变压器采购10台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "500kVA变压器",
                "stock_quantity": 50,
                "available_quantity": 50,
                "lead_time": "14天"
            },
            "pricing": {
                "unit_price": 85000,
                "quantity": 10,
                "total_price": 748000,
                "discount_rate": 0.12,
                "payment_terms": "60天账期"
            }
        },
        is_corrupted=False,
        description="正常数据：变压器库存价格"
    ),

    # ==================== 数据篡改测试用例 ====================
    ReflectionTestCase(
        id="REF-004",
        query="工业风机采购50台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "工业风机",
                "stock_quantity": 999999,
                "available_quantity": 999999,
                "lead_time": "7天"
            },
            "pricing": {
                "unit_price": 15000,
                "quantity": 50,
                "total_price": 13500000,
                "discount_rate": 0.1,
                "payment_terms": "30天账期"
            }
        },
        is_corrupted=True,
        corrupted_fields=["stock_quantity", "total_price"],
        description="篡改数据：库存异常夸大"
    ),
    ReflectionTestCase(
        id="REF-005",
        query="离心泵采购30台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "离心泵",
                "stock_quantity": 500,
                "available_quantity": 500,
                "lead_time": "5天"
            },
            "pricing": {
                "unit_price": 0.01,
                "quantity": 30,
                "total_price": 0.3,
                "discount_rate": 0.15,
                "payment_terms": "15天账期"
            }
        },
        is_corrupted=True,
        corrupted_fields=["unit_price"],
        description="篡改数据：价格异常偏低"
    ),
    ReflectionTestCase(
        id="REF-006",
        query="输送机采购500米",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "输送机",
                "stock_quantity": 300,
                "available_quantity": 300,
                "lead_time": "3天"
            },
            "pricing": {
                "unit_price": 500,
                "quantity": 500,
                "total_price": 375000,
                "discount_rate": 2.5,
                "payment_terms": "款到发货"
            }
        },
        is_corrupted=True,
        corrupted_fields=["discount_rate"],
        description="篡改数据：折扣率异常（>1）"
    ),
    ReflectionTestCase(
        id="REF-007",
        query="空压机采购100台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "空压机",
                "stock_quantity": 100,
                "available_quantity": 100,
                "lead_time": "10天"
            },
            "pricing": {
                "unit_price": -5000,
                "quantity": 100,
                "total_price": -450000,
                "discount_rate": 0.1,
                "payment_terms": "30天账期"
            }
        },
        is_corrupted=True,
        corrupted_fields=["unit_price"],
        description="篡改数据：价格为负数"
    ),
    ReflectionTestCase(
        id="REF-008",
        query="破碎机采购30台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "破碎机",
                "stock_quantity": 30,
                "available_quantity": 30,
                "lead_time": "20天"
            },
            "pricing": {
                "unit_price": 50000,
                "quantity": 30,
                "total_price": 100000,
                "discount_rate": 0.3,
                "payment_terms": "90天账期"
            }
        },
        is_corrupted=True,
        corrupted_fields=["total_price"],
        description="篡改数据：总价计算错误（50000*30*0.3≠100000）"
    ),
    ReflectionTestCase(
        id="REF-009",
        query="变压器采购10台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "100kVA变压器",
                "stock_quantity": 5,
                "available_quantity": 5,
                "lead_time": "14天"
            },
            "pricing": {
                "unit_price": 25000,
                "quantity": 10,
                "total_price": 237500,
                "discount_rate": 0.05,
                "payment_terms": "60天账期"
            }
        },
        is_corrupted=True,
        corrupted_fields=["stock_quantity"],
        description="篡改数据：库存低于采购量但未标记"
    ),
    ReflectionTestCase(
        id="REF-010",
        query="工业风机采购50台",
        response_data={
            "status": "success",
            "inventory": {
                "product_name": "工业风机",
                "stock_quantity": 200,
                "available_quantity": 200,
                "lead_time": "7天"
            },
            "pricing": {
                "unit_price": 15000,
                "quantity": 50,
                "total_price": 675000,
                "discount_rate": 0.1,
                "payment_terms": "30天账期"
            },
            "cases": [
                {
                    "case_id": "CASE-FAKE-001",
                    "customer_name": "虚构公司A",
                    "industry": "不存在的行业",
                    "quantity": 100,
                    "deal_price": 14000,
                    "payment_terms": "预付款",
                    "similarity_score": 0.95
                }
            ]
        },
        is_corrupted=True,
        corrupted_fields=["cases"],
        description="篡改数据：编造不存在的案例"
    ),
]

TOOL_TEST_QUERIES: List[ToolQuery] = [
    # ==================== ApiInventoryTool 测试 ====================
    ToolQuery(
        id="INV-001",
        tool_name="api_inventory",
        params={"product_name": "工业风机"},
        expected_result={"product_name": "工业风机", "available_stock": 200, "unit": "台"},
        description="工业风机库存查询"
    ),
    ToolQuery(
        id="INV-002",
        tool_name="api_inventory",
        params={"product_name": "离心泵"},
        expected_result={"product_name": "离心泵", "available_stock": 500, "unit": "台"},
        description="离心泵库存查询"
    ),
    ToolQuery(
        id="INV-003",
        tool_name="api_inventory",
        params={"product_name": "500kVA变压器"},
        expected_result={"product_name": "500kVA变压器", "available_stock": 50, "unit": "台"},
        description="变压器库存查询"
    ),
    ToolQuery(
        id="INV-004",
        tool_name="api_inventory",
        params={"product_name": "输送机"},
        expected_result={"product_name": "输送机", "available_stock": 300, "unit": "米"},
        description="输送机库存查询"
    ),
    ToolQuery(
        id="INV-005",
        tool_name="api_inventory",
        params={"product_name": "空压机"},
        expected_result={"product_name": "空压机", "available_stock": 100, "unit": "台"},
        description="空压机库存查询"
    ),

    # ==================== SqlPriceTool 测试 ====================
    ToolQuery(
        id="PRC-001",
        tool_name="sql_price",
        params={"product_name": "工业风机"},
        expected_result={"product_name": "工业风机", "unit_price": 15000, "avg_discount": 0.88},
        description="工业风机价格查询"
    ),
    ToolQuery(
        id="PRC-002",
        tool_name="sql_price",
        params={"product_name": "离心泵"},
        expected_result={"product_name": "离心泵", "unit_price": 8500, "avg_discount": 0.85},
        description="离心泵价格查询"
    ),
    ToolQuery(
        id="PRC-003",
        tool_name="sql_price",
        params={"product_name": "500kVA变压器"},
        expected_result={"product_name": "500kVA变压器", "unit_price": 85000, "avg_discount": 0.88},
        description="变压器价格查询"
    ),
    ToolQuery(
        id="PRC-004",
        tool_name="sql_price",
        params={"product_name": "大型破碎机"},
        expected_result={"product_name": "大型破碎机", "unit_price": 120000, "avg_discount": 0.82},
        description="破碎机价格查询"
    ),
    ToolQuery(
        id="PRC-005",
        tool_name="sql_price",
        params={"product_name": "输送机"},
        expected_result={"product_name": "输送机", "unit_price": 500, "avg_discount": 0.9},
        description="输送机价格查询"
    ),

    # ==================== CalculatorTool 测试 ====================
    ToolQuery(
        id="CAL-001",
        tool_name="calculator",
        params={
            "unit_price": 15000,
            "quantity": 50,
            "discount_rate": 0.9
        },
        expected_result={
            "total_price": 75000,
            "unit_price": 15000,
            "quantity": 50
        },
        description="工业风机50台90%折扣计算"
    ),
    ToolQuery(
        id="CAL-002",
        tool_name="calculator",
        params={
            "unit_price": 8500,
            "quantity": 30,
            "discount_rate": 0.85
        },
        expected_result={
            "total_price": 38250,
            "unit_price": 8500,
            "quantity": 30
        },
        description="离心泵30台85%折扣计算"
    ),
    ToolQuery(
        id="CAL-003",
        tool_name="calculator",
        params={
            "unit_price": 85000,
            "quantity": 10,
            "discount_rate": 0.88
        },
        expected_result={
            "total_price": 102000,
            "unit_price": 85000,
            "quantity": 10
        },
        description="变压器10台88%折扣计算"
    ),
]


def get_test_cases_by_scenario(scenario: str) -> List[TestCase]:
    """
    按场景类型获取测试用例

    Args:
        scenario: 场景类型 (single_inventory, single_price, single_case, dual, triple, full, boundary)

    Returns:
        List[TestCase]: 匹配的测试用例列表
    """
    scenario_map = {
        "single_inventory": [tc for tc in TEST_CASES if tc.id.startswith("TC-00") and int(tc.id.split("-")[1]) <= 5],
        "single_price": [tc for tc in TEST_CASES if tc.id.startswith("TC-00") and 6 <= int(tc.id.split("-")[1]) <= 10],
        "single_case": [tc for tc in TEST_CASES if tc.id.startswith("TC-01") and 11 <= int(tc.id.split("-")[1]) <= 13],
        "dual": [tc for tc in TEST_CASES if tc.id.startswith("TC-01") and 14 <= int(tc.id.split("-")[1]) <= 21],
        "triple": [tc for tc in TEST_CASES if tc.id.startswith("TC-02") and 22 <= int(tc.id.split("-")[1]) <= 27],
        "full": [tc for tc in TEST_CASES if tc.id.startswith("TC-02") and 28 <= int(tc.id.split("-")[1]) <= 32],
        "boundary": [tc for tc in TEST_CASES if tc.id.startswith("TC-03") and int(tc.id.split("-")[1]) >= 33],
    }
    return scenario_map.get(scenario, TEST_CASES)


def get_inventory_queries() -> List[ToolQuery]:
    """获取库存查询测试用例"""
    return [q for q in TOOL_TEST_QUERIES if q.tool_name == "api_inventory"]


def get_price_queries() -> List[ToolQuery]:
    """获取价格查询测试用例"""
    return [q for q in TOOL_TEST_QUERIES if q.tool_name == "sql_price"]


def get_calculator_queries() -> List[ToolQuery]:
    """获取计算器测试用例"""
    return [q for q in TOOL_TEST_QUERIES if q.tool_name == "calculator"]

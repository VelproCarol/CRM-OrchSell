"""
FastAPI 路由定义
对外暴露 HTTP 接口，对接企业 CRM/ERP 系统
"""
from typing import Optional, Dict, List
from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from loguru import logger
import time
from pathlib import Path

from config.settings import settings, Constants
from core.sales_agent import SalesAgent
from schemas.output_schema import SalesResponse, ErrorResponse
from tools import (
    CalculatorTool,
    ApiInventoryTool,
    SqlPriceTool,
    DocRetrieveTool
)


# ==================== 请求模型 ====================

class SalesQueryRequest(BaseModel):
    """
    销售咨询请求模型
    """
    customer_id: Optional[str] = Field(None, description="客户ID")
    query: str = Field(..., description="客户咨询文本", min_length=1)
    product_category: Optional[str] = Field(None, description="产品品类")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "C001",
                "query": "采购50台工业风机，想要30天账期，对比往期大客户成交价，给一套合作方案",
                "product_category": "工业风机"
            }
        }


# ==================== 响应模型 ====================

class HealthResponse(BaseModel):
    """
    健康检查响应模型
    """
    status: str = Field(default="ok", description="服务状态")
    version: str = Field(default="1.0.0", description="版本号")
    llm_mode: str = Field(..., description="当前LLM模式")
    timestamp: float = Field(..., description="时间戳")


class StatsResponse(BaseModel):
    """
    统计信息响应模型
    """
    total_requests: int = Field(..., description="总请求数")
    successful_requests: int = Field(..., description="成功请求数")
    failed_requests: int = Field(..., description="失败请求数")
    avg_response_time: float = Field(..., description="平均响应时间(ms)")


class DbQueryRequest(BaseModel):
    """
    数据库查询请求模型（只读）
    """
    query_text: str = Field(..., description="查询描述文本，如'查一下工业风机的库存'", min_length=1)
    query_type: Optional[str] = Field(None, description="查询类型：inventory|product|price|customer|deal")


class ProductListItem(BaseModel):
    """
    产品列表项
    """
    product_sku: str
    product_name: str
    category: str
    base_price: float
    unit: str
    description: Optional[str] = None


class InventoryItem(BaseModel):
    """
    库存查询项
    """
    product_name: str
    product_sku: str
    stock_quantity: int
    available_quantity: int
    reserved_quantity: int
    lead_time: str
    warehouse_location: str
    unit: str


# ==================== 全局变量 ====================

# Agent 实例（延迟初始化）
_agent: Optional[SalesAgent] = None

# 统计信息
_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_time": 0.0
}


# ==================== 创建应用 ====================

def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    Returns:
        FastAPI 应用实例
    """
    app = FastAPI(
        title="可编排多工具销售任务拆解 Agent",
        description="面向 B2B 实体产品销售场景的智能 Agent 系统",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(router)
    
    # 异常处理
    app.add_exception_handler(Exception, global_exception_handler)
    
    logger.info("FastAPI 应用创建完成")
    return app


# ==================== 路由定义 ====================

router = APIRouter(tags=["销售Agent"])


def get_agent() -> SalesAgent:
    """
    获取 Agent 实例（单例模式）
    
    Returns:
        SalesAgent 实例
    """
    global _agent
    if _agent is None:
        logger.info("初始化 SalesAgent...")
        _agent = SalesAgent()
        
        # 注册工具
        _agent.register_tool(Constants.TOOL_CALCULATOR, CalculatorTool())
        _agent.register_tool(Constants.TOOL_API_INVENTORY, ApiInventoryTool())
        _agent.register_tool(Constants.TOOL_SQL_PRICE, SqlPriceTool())
        _agent.register_tool(Constants.TOOL_DOC_RETRIEVE, DocRetrieveTool())
        
        logger.info("SalesAgent 初始化完成，已注册4个工具")
    
    return _agent


@router.post("/api/chat/sales", response_model=SalesResponse)
async def sales_chat(request: SalesQueryRequest):
    """
    销售咨询接口
    
    接收客户咨询，拆解任务，调度工具，生成销售方案
    
    Args:
        request: 销售咨询请求
        
    Returns:
        销售方案响应
    """
    start_time = time.time()
    
    logger.info(f"收到销售咨询请求: {request.query[:50]}...")
    
    # 更新统计
    _stats["total_requests"] += 1
    
    try:
        # 获取 Agent
        agent = get_agent()
        
        # 处理咨询
        response = await agent.process(
            query=request.query,
            customer_id=request.customer_id,
            product_category=request.product_category
        )
        
        # 更新统计
        elapsed_time = (time.time() - start_time) * 1000
        _stats["successful_requests"] += 1
        _stats["total_time"] += elapsed_time
        
        logger.info(f"销售方案生成成功，耗时: {elapsed_time:.2f}ms")
        
        return response
        
    except Exception as e:
        # 更新统计
        _stats["failed_requests"] += 1
        
        logger.error(f"销售方案生成失败: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口
    
    Returns:
        健康状态信息
    """
    from core.llm_adapter import get_llm
    
    llm = get_llm()
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        llm_mode=llm.mode,
        timestamp=time.time()
    )


@router.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    获取统计信息接口
    
    Returns:
        统计信息
    """
    avg_time = (
        _stats["total_time"] / _stats["total_requests"]
        if _stats["total_requests"] > 0
        else 0.0
    )
    
    return StatsResponse(
        total_requests=_stats["total_requests"],
        successful_requests=_stats["successful_requests"],
        failed_requests=_stats["failed_requests"],
        avg_response_time=avg_time
    )


@router.get("/api/tools")
async def get_tools():
    """
    获取已注册工具列表
    
    Returns:
        工具列表
    """
    agent = get_agent()
    tools = agent.tool_dispatcher.get_registered_tools()
    
    return {
        "tools": tools,
        "count": len(tools)
    }


# ==================== 数据库只读查询接口 ====================

@router.get("/api/db/products", response_model=list[ProductListItem])
async def get_product_list():
    """
    获取产品列表接口（只读）
    
    Returns:
        产品列表
    """
    try:
        import sqlite3
        from config.settings import settings
        
        db_path = Path(settings.SQLITE_DB_PATH)
        if not db_path.exists():
            raise HTTPException(status_code=404, detail="数据库文件不存在，请先初始化")
        
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT product_sku, product_name, category, base_price, unit, description
            FROM products
            ORDER BY category, product_name
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        products = [
            ProductListItem(
                product_sku=row["product_sku"],
                product_name=row["product_name"],
                category=row["category"],
                base_price=row["base_price"],
                unit=row["unit"],
                description=row["description"]
            )
            for row in rows
        ]
        
        logger.info(f"产品列表查询成功，共 {len(products)} 条记录")
        return products
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"产品列表查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/api/db/inventory/{product_name}", response_model=InventoryItem)
async def get_inventory(product_name: str):
    """
    获取产品库存接口（只读）
    
    Args:
        product_name: 产品名称
        
    Returns:
        库存信息
    """
    try:
        from tools.api_inventory_tool import ApiInventoryTool
        
        tool = ApiInventoryTool()
        result = await tool.execute(product_name=product_name)
        
        if result.get("success") is False:
            raise HTTPException(status_code=404, detail=result.get("error", "库存查询失败"))
        
        logger.info(f"库存查询成功: {product_name}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"库存查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/api/db/query")
async def query_database(request: DbQueryRequest):
    """
    数据库自然语言查询接口（只读）
    使用大模型解析意图并生成 SQL 语句执行查询
    
    Args:
        request: 查询请求
        
    Returns:
        查询结果
    """
    try:
        from services.nl2sql_service import get_nl2sql_service
        
        nl2sql_service = get_nl2sql_service()
        
        # 解析意图
        intent = await nl2sql_service.explain_intent(request.query_text)
        logger.info(f"用户查询意图: {intent}")
        
        # 生成并执行 SQL
        result = await nl2sql_service.query(request.query_text)
        
        # 添加意图信息到结果
        result['intent'] = intent
        
        return result
        
    except Exception as e:
        logger.error(f"NL2SQL 查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 模型切换接口 ====================

class ModelSwitchRequest(BaseModel):
    """模型切换请求模型"""
    mode: str = Field(..., description="目标模式: openai 或 qwen")
    model_name: Optional[str] = Field(None, description="可选，指定模型名称")


class ModelInfoResponse(BaseModel):
    """模型信息响应模型"""
    mode: str = Field(..., description="当前模式")
    model_name: str = Field(..., description="当前模型名称")
    available_models: Dict[str, List[str]] = Field(..., description="可用模型列表")


@router.get("/api/model", response_model=ModelInfoResponse)
async def get_model_info():
    """
    获取当前模型信息

    Returns:
        当前模型信息
    """
    from core.llm_adapter import get_llm

    llm = get_llm()

    return ModelInfoResponse(
        mode=llm.mode,
        model_name=llm.model_name,
        available_models={
            "openai": ["glm-4", "glm-3-turbo", "glm-4-flash"],
            "qwen": ["qwen2:7b-instruct-q4_K_M", "qwen:7b", "qwen2:14b-instruct-q4_K_M"]
        }
    )


@router.post("/api/model/switch")
async def switch_model(request: ModelSwitchRequest):
    """
    切换大模型

    Args:
        request: 切换请求

    Returns:
        切换结果
    """
    from core.llm_adapter import get_llm

    llm = get_llm()

    try:
        # 如果切换到 qwen 且未指定模型，使用用户指定的 qwen2:7b-instruct-q4_K_M
        target_model = request.model_name
        if request.mode.lower() == "qwen" and not target_model:
            target_model = "qwen2:7b-instruct-q4_K_M"

        result = llm.switch_model(request.mode, target_model)

        return {
            "status": "success",
            "message": f"模型切换成功: {result['old_mode']}/{result['old_model']} -> {result['new_mode']}/{result['new_model']}",
            "new_mode": result["new_mode"],
            "new_model": result["new_model"]
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"模型切换失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"切换失败: {str(e)}")


# ==================== 异常处理 ====================

async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    
    Args:
        request: 请求对象
        exc: 异常对象
        
    Returns:
        错误响应
    """
    logger.error(f"全局异常: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            error_code="INTERNAL_ERROR",
            error_message=str(exc),
            details={"path": request.url.path}
        ).model_dump()
    )

"""
Pydantic 输出 Schema 定义
强制约束 Agent 输出为标准化 JSON 格式
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class InventoryInfo(BaseModel):
    """
    库存信息模型
    """
    product_name: str = Field(..., description="产品名称")
    product_sku: Optional[str] = Field(None, description="产品SKU编码")
    stock_quantity: int = Field(..., description="库存总量")
    available_quantity: int = Field(..., description="可用库存量")
    reserved_quantity: Optional[int] = Field(None, description="预留库存量")
    lead_time: str = Field(..., description="备货周期")
    warehouse_location: Optional[str] = Field(None, description="仓库位置")


class PricingInfo(BaseModel):
    """
    价格信息模型
    """
    unit_price: float = Field(..., description="单价")
    total_price: float = Field(..., description="总价")
    discount_rate: float = Field(default=0.0, description="折扣率")
    discount_reason: Optional[str] = Field(None, description="折扣原因")
    payment_terms: str = Field(..., description="付款条件")
    currency: str = Field(default="CNY", description="货币单位")
    valid_until: Optional[str] = Field(None, description="报价有效期")


class CaseInfo(BaseModel):
    """
    成交案例信息模型
    """
    case_id: str = Field(..., description="案例编号")
    customer_name: Optional[str] = Field(None, description="客户名称（脱敏）")
    industry: Optional[str] = Field(None, description="行业类型")
    quantity: int = Field(..., description="采购数量")
    deal_price: float = Field(..., description="成交单价")
    total_amount: Optional[float] = Field(None, description="成交总金额")
    payment_terms: str = Field(..., description="付款条件")
    deal_date: Optional[str] = Field(None, description="成交日期")
    similarity_score: Optional[float] = Field(None, description="相似度得分")


class CustomerProfile(BaseModel):
    """
    客户画像信息模型
    """
    customer_id: str = Field(..., description="客户ID")
    customer_name: Optional[str] = Field(None, description="客户名称")
    industry: Optional[str] = Field(None, description="所属行业")
    company_size: Optional[str] = Field(None, description="公司规模")
    customer_level: Optional[str] = Field(None, description="客户等级(A/B/C/D)")
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址")
    total_purchase_amount: float = Field(default=0.0, description="累计采购金额")
    purchase_count: int = Field(default=0, description="采购次数")
    last_purchase_date: Optional[str] = Field(None, description="最近采购日期")
    credit_rating: Optional[str] = Field(None, description="信用评级")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class FollowUpRecord(BaseModel):
    """
    跟进记录信息模型
    """
    record_id: str = Field(..., description="记录ID")
    customer_id: str = Field(..., description="客户ID")
    follow_up_type: str = Field(..., description="跟进类型(call/meeting/email/wechat/other)")
    content: str = Field(..., description="跟进内容")
    result: Optional[str] = Field(None, description="跟进结果")
    next_follow_up_date: Optional[str] = Field(None, description="下次跟进日期")
    created_by: Optional[str] = Field(None, description="创建人")
    created_at: Optional[str] = Field(None, description="创建时间")


class ProposalInfo(BaseModel):
    """
    销售方案信息模型
    """
    summary: str = Field(..., description="方案摘要")
    pricing_strategy: str = Field(..., description="定价策略说明")
    inventory_assurance: str = Field(..., description="库存保障说明")
    payment_recommendation: str = Field(..., description="付款方式建议")
    competitive_advantage: str = Field(..., description="竞争优势说明")
    next_steps: List[str] = Field(default_factory=list, description="后续行动建议")
    risk_warnings: List[str] = Field(default_factory=list, description="风险提示")


class ReflectionField(BaseModel):
    """
    反思验真字段模型
    """
    field_name: str = Field(..., description="字段名称")
    field_value: Any = Field(..., description="字段值")
    is_verified: bool = Field(..., description="是否已验证")
    confidence: float = Field(..., description="置信度")
    source: Optional[str] = Field(None, description="数据来源")
    correction: Optional[Any] = Field(None, description="修正后的值")


class ReflectionReport(BaseModel):
    """
    反思验真报告模型
    """
    enabled: bool = Field(..., description="是否启用反思验真")
    overall_confidence: float = Field(..., description="整体置信度")
    verified_fields: List[str] = Field(default_factory=list, description="已验证字段列表")
    unverified_fields: List[str] = Field(default_factory=list, description="未验证字段列表")
    field_details: List[ReflectionField] = Field(default_factory=list, description="字段验证详情")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    hallucinations_detected: List[str] = Field(default_factory=list, description="检测到的幻觉")
    corrections_applied: List[str] = Field(default_factory=list, description="应用的修正")


class TaskLog(BaseModel):
    """
    任务执行日志模型
    """
    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    tool_name: str = Field(..., description="工具名称")
    status: str = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_ms: Optional[int] = Field(None, description="执行耗时(毫秒)")
    input_params: Dict[str, Any] = Field(default_factory=dict, description="输入参数")
    output_result: Optional[Dict[str, Any]] = Field(None, description="输出结果")
    error_message: Optional[str] = Field(None, description="错误信息")


class SalesResponse(BaseModel):
    """
    销售方案响应模型
    这是 Agent 的最终输出格式，100% 固定 JSON 结构
    """
    # 响应状态
    status: str = Field(..., description="响应状态: success/error/partial")
    message: Optional[str] = Field(None, description="响应消息")
    
    # 核心业务数据
    inventory: Optional[InventoryInfo] = Field(None, description="库存信息")
    pricing: Optional[PricingInfo] = Field(None, description="价格信息")
    cases: List[CaseInfo] = Field(default_factory=list, description="相似案例列表")
    proposal: Optional[ProposalInfo] = Field(None, description="销售方案")
    
    # 客户画像信息
    customer_profile: Optional[CustomerProfile] = Field(None, description="客户画像")
    recent_follow_ups: List[FollowUpRecord] = Field(default_factory=list, description="最近跟进记录")
    
    # 反思验真报告
    reflection_report: Optional[ReflectionReport] = Field(None, description="反思验真报告")
    
    # 任务执行日志
    task_logs: List[TaskLog] = Field(default_factory=list, description="任务执行日志")
    
    # 元数据
    customer_id: Optional[str] = Field(None, description="客户ID")
    query: Optional[str] = Field(None, description="原始查询")
    product_category: Optional[str] = Field(None, description="产品品类")
    timestamp: datetime = Field(default_factory=datetime.now, description="生成时间戳")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "销售方案生成成功",
                "inventory": {
                    "product_name": "工业风机",
                    "product_sku": "IF-2024-001",
                    "stock_quantity": 120,
                    "available_quantity": 50,
                    "lead_time": "7天"
                },
                "pricing": {
                    "unit_price": 8500.00,
                    "total_price": 425000.00,
                    "discount_rate": 0.05,
                    "payment_terms": "30天账期"
                },
                "cases": [
                    {
                        "case_id": "CASE-2024-001",
                        "customer_name": "某制造企业",
                        "quantity": 55,
                        "deal_price": 8200.00,
                        "payment_terms": "30天账期"
                    }
                ],
                "proposal": {
                    "summary": "基于当前库存和往期成交案例，为您推荐...",
                    "pricing_strategy": "参考近6个月成交均价...",
                    "inventory_assurance": "当前库存充足...",
                    "payment_recommendation": "建议采用30天账期...",
                    "competitive_advantage": "相比竞品...",
                    "next_steps": ["确认订单", "签订合同"],
                    "risk_warnings": []
                },
                "reflection_report": {
                    "enabled": True,
                    "overall_confidence": 0.92,
                    "verified_fields": ["stock_quantity", "unit_price"],
                    "warnings": []
                },
                "task_logs": []
            }
        }


class TaskPlan(BaseModel):
    """
    任务拆解计划模型
    """
    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    tool_name: str = Field(..., description="执行工具名称")
    description: str = Field(..., description="任务描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任务参数")
    priority: int = Field(default=1, description="优先级")
    dependencies: List[str] = Field(default_factory=list, description="依赖任务ID")


class ErrorResponse(BaseModel):
    """
    错误响应模型
    """
    status: str = Field(default="error", description="状态")
    error_code: str = Field(..., description="错误码")
    error_message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
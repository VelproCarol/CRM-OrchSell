"""
销售 Agent 主入口类
串联全流程，组装数据源生成销售方案
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from loguru import logger

from config.settings import settings, Constants
from core.llm_adapter import get_llm, LLMAdapter
from core.task_planner import TaskPlanner
from core.tool_dispatcher import ToolDispatcher
from core.reflection_engine import ReflectionEngine
from schemas.output_schema import (
    SalesResponse,
    InventoryInfo,
    PricingInfo,
    CaseInfo,
    ProposalInfo,
    TaskLog,
    CustomerProfile,
    FollowUpRecord
)
from services.customer_service import get_customer_service, CustomerService


class SalesAgent:
    """
    销售 Agent 主类
    串联任务拆解、工具调度、反思验真、方案生成全流程
    """
    
    # 方案生成提示词
    PROPOSAL_PROMPT = """你是一个专业的销售方案撰写助手。基于以下真实数据，为客户撰写一份定制化的销售合作方案。

## 重要约束
1. 你必须严格基于提供的数据撰写方案，绝对不能编造任何库存、价格、案例信息
2. 如果某项数据缺失，请明确标注"数据缺失"，不要编造填充
3. 方案必须专业、清晰、有说服力
4. 必须使用提供的 JSON 格式输出

## 提供的真实数据

### 库存信息
{inventory_data}

### 价格信息
{pricing_data}

### 相似案例
{cases_data}

### 客户需求
- 客户ID: {customer_id}
- 咨询内容: {query}
- 产品品类: {product_category}

## 输出格式要求
请严格按照以下 JSON 格式输出销售方案：

```json
{{
  "summary": "方案摘要（2-3句话概括核心方案）",
  "pricing_strategy": "定价策略说明（基于历史价格和当前库存情况）",
  "inventory_assurance": "库存保障说明（库存是否充足、备货周期）",
  "payment_recommendation": "付款方式建议（账期、付款方式）",
  "competitive_advantage": "竞争优势说明（相比竞品的优势）",
  "next_steps": ["后续行动建议1", "后续行动建议2"],
  "risk_warnings": ["风险提示1", "风险提示2"]
}}
```

现在请基于以上数据撰写销售方案。"""
    
    def __init__(self):
        """初始化销售 Agent"""
        self.llm: LLMAdapter = get_llm()
        self.task_planner = TaskPlanner()
        self.tool_dispatcher = ToolDispatcher()
        self.reflection_engine = ReflectionEngine()
        
        logger.info("销售 Agent 初始化完成")
    
    def register_tool(self, tool_name: str, tool_instance: Any):
        """
        注册工具到调度器
        
        Args:
            tool_name: 工具名称
            tool_instance: 工具实例
        """
        self.tool_dispatcher.register_tool(tool_name, tool_instance)
        logger.info(f"销售 Agent 注册工具: {tool_name}")
    
    def register_data_source(self, source_name: str, source_instance: Any):
        """
        注册数据源到反思引擎
        
        Args:
            source_name: 数据源名称
            source_instance: 数据源实例
        """
        self.reflection_engine.register_data_source(source_name, source_instance)
        logger.info(f"销售 Agent 注册数据源: {source_name}")
    
    async def process(
        self,
        query: str,
        customer_id: Optional[str] = None,
        product_category: Optional[str] = None
    ) -> SalesResponse:
        """
        处理客户咨询，生成销售方案
        
        Args:
            query: 客户咨询文本
            customer_id: 客户ID
            product_category: 产品品类
            
        Returns:
            销售方案响应
        """
        request_id = uuid.uuid4().hex[:8]
        logger.info(f"[{request_id}] 开始处理客户咨询: {query[:50]}...")
        
        try:
            # 1. 任务拆解
            logger.info(f"[{request_id}] 步骤1: 任务拆解")
            tasks = await self.task_planner.plan(
                query=query,
                customer_id=customer_id,
                product_category=product_category
            )
            
            if not tasks:
                logger.warning(f"[{request_id}] 任务拆解失败，返回错误响应")
                return SalesResponse(
                    status=Constants.API_STATUS_ERROR,
                    message="无法理解客户需求，请提供更详细的信息",
                    customer_id=customer_id,
                    query=query,
                    product_category=product_category
                )
            
            # 2. 工具调度执行
            logger.info(f"[{request_id}] 步骤2: 工具调度执行")
            task_logs = await self.tool_dispatcher.dispatch(tasks)
            
            # 提取工具返回结果
            context = {}
            for log in task_logs:
                if log.status == Constants.TASK_STATUS_COMPLETED and log.output_result:
                    context[log.task_type] = log.output_result
            
            # 3. 构建响应数据
            logger.info(f"[{request_id}] 步骤3: 构建响应数据")
            response = await self._build_response(
                context=context,
                customer_id=customer_id,
                query=query,
                product_category=product_category
            )
            
            # 4. 反思验真
            if settings.REFLECTION_ENABLED:
                logger.info(f"[{request_id}] 步骤4: 反思验真")
                reflection_report = await self.reflection_engine.verify(response, context)
                response.reflection_report = reflection_report
                
                # 如果置信度过低，标记为部分成功
                if reflection_report.overall_confidence < settings.REFLECTION_CONFIDENCE_THRESHOLD:
                    response.status = Constants.API_STATUS_PARTIAL
                    response.message = "方案生成成功，但部分数据验证失败，请谨慎参考"
            
            # 5. 添加任务日志
            response.task_logs = task_logs
            
            logger.info(f"[{request_id}] 处理完成，状态: {response.status}")
            return response
            
        except Exception as e:
            logger.error(f"[{request_id}] 处理失败: {str(e)}")
            return SalesResponse(
                status=Constants.API_STATUS_ERROR,
                message=f"处理失败: {str(e)}",
                customer_id=customer_id,
                query=query,
                product_category=product_category
            )
    
    async def _build_response(
        self,
        context: Dict[str, Any],
        customer_id: Optional[str],
        query: str,
        product_category: Optional[str]
    ) -> SalesResponse:
        """
        构建响应数据（增强版：添加客户画像和跟进记录）
        
        Args:
            context: 工具返回的上下文数据
            customer_id: 客户ID
            query: 客户咨询
            product_category: 产品品类
            
        Returns:
            销售响应
        """
        # 获取客户服务
        customer_service = get_customer_service()
        
        # 构建库存信息
        inventory_info = None
        if Constants.TASK_INVENTORY_QUERY in context:
            inv_data = context[Constants.TASK_INVENTORY_QUERY]
            inventory_info = InventoryInfo(
                product_name=inv_data.get("product_name", product_category or "未知产品"),
                product_sku=inv_data.get("product_sku"),
                stock_quantity=inv_data.get("stock_quantity", 0),
                available_quantity=inv_data.get("available_quantity", 0),
                lead_time=inv_data.get("lead_time", "未知"),
                warehouse_location=inv_data.get("warehouse_location")
            )
        
        # 构建价格信息
        pricing_info = None
        if Constants.TASK_PRICE_QUERY in context:
            price_data = context[Constants.TASK_PRICE_QUERY]
            # 从计算器工具获取总价（如果有）
            calc_data = context.get(Constants.TASK_PRICE_CALCULATION, {})
            
            pricing_info = PricingInfo(
                unit_price=price_data.get("unit_price", 0.0),
                quantity=calc_data.get("quantity", 1),
                total_price=calc_data.get("total_price", price_data.get("total_price", 0.0)),
                discount_rate=calc_data.get("discount_rate", price_data.get("discount_rate", 0.0)),
                discount_reason=price_data.get("discount_reason"),
                payment_terms=calc_data.get("payment_terms", price_data.get("payment_terms", "款到发货"))
            )
        
        # 构建案例信息
        cases_info: List[CaseInfo] = []
        if Constants.TASK_CASE_RETRIEVAL in context:
            cases_data = context[Constants.TASK_CASE_RETRIEVAL].get("cases", [])
            for case in cases_data:
                cases_info.append(CaseInfo(
                    case_id=case.get("case_id", ""),
                    customer_name=case.get("customer_name"),
                    industry=case.get("industry"),
                    quantity=case.get("quantity", 0),
                    deal_price=case.get("deal_price", 0.0),
                    total_amount=case.get("total_amount"),
                    payment_terms=case.get("payment_terms", ""),
                    deal_date=case.get("deal_date"),
                    similarity_score=case.get("similarity_score")
                ))
        
        # 获取客户画像信息
        customer_profile_info = None
        recent_follow_ups_info: List[FollowUpRecord] = []
        
        if customer_id:
            logger.info(f"获取客户画像信息: {customer_id}")
            customer_summary = customer_service.get_customer_summary(customer_id)
            if customer_summary:
                # 构建客户画像
                profile_data = customer_summary.get("profile", {})
                customer_profile_info = CustomerProfile(
                    customer_id=profile_data.get("customer_id", ""),
                    customer_name=profile_data.get("customer_name"),
                    industry=profile_data.get("industry"),
                    company_size=profile_data.get("company_size"),
                    customer_level=profile_data.get("customer_level"),
                    contact_person=profile_data.get("contact_person"),
                    contact_phone=profile_data.get("contact_phone"),
                    email=profile_data.get("email"),
                    address=profile_data.get("address"),
                    total_purchase_amount=profile_data.get("total_purchase_amount", 0.0),
                    purchase_count=profile_data.get("purchase_count", 0),
                    last_purchase_date=profile_data.get("last_purchase_date"),
                    credit_rating=profile_data.get("credit_rating"),
                    tags=profile_data.get("tags", []),
                    created_at=profile_data.get("created_at"),
                    updated_at=profile_data.get("updated_at")
                )
                
                # 构建跟进记录
                follow_up_records = customer_summary.get("recent_follow_ups", [])
                for record in follow_up_records[:5]:  # 最多取5条
                    recent_follow_ups_info.append(FollowUpRecord(
                        record_id=record.get("record_id", ""),
                        customer_id=record.get("customer_id", ""),
                        follow_up_type=record.get("follow_up_type", ""),
                        content=record.get("content", ""),
                        result=record.get("result"),
                        next_follow_up_date=record.get("next_follow_up_date"),
                        created_by=record.get("created_by"),
                        created_at=record.get("created_at")
                    ))
        
        # 生成销售方案（降级方案确保始终有结果）
        proposal = await self._generate_proposal(
            inventory_info=inventory_info,
            pricing_info=pricing_info,
            cases_info=cases_info,
            customer_id=customer_id,
            query=query,
            product_category=product_category,
            customer_profile=customer_profile_info
        )
        
        return SalesResponse(
            status=Constants.API_STATUS_SUCCESS,
            message="销售方案生成成功",
            inventory=inventory_info,
            pricing=pricing_info,
            cases=cases_info,
            proposal=proposal,
            customer_profile=customer_profile_info,
            recent_follow_ups=recent_follow_ups_info,
            customer_id=customer_id,
            query=query,
            product_category=product_category
        )
    
    async def _generate_proposal(
        self,
        inventory_info: Optional[InventoryInfo],
        pricing_info: Optional[PricingInfo],
        cases_info: List[CaseInfo],
        customer_id: Optional[str],
        query: str,
        product_category: Optional[str],
        customer_profile: Optional[CustomerProfile] = None
    ) -> ProposalInfo:
        """
        生成销售方案
        
        Args:
            inventory_info: 库存信息
            pricing_info: 价格信息
            cases_info: 案例信息
            customer_id: 客户ID
            query: 客户咨询
            product_category: 产品品类
            
        Returns:
            销售方案（始终返回，不会为None）
        """
        try:
            # 格式化数据
            inventory_data = inventory_info.model_dump_json(indent=2) if inventory_info else "库存数据缺失"
            pricing_data = pricing_info.model_dump_json(indent=2) if pricing_info else "价格数据缺失"
            cases_data = "\n".join([
                case.model_dump_json(indent=2) for case in cases_info
            ]) if cases_info else "案例数据缺失"
            
            # 构建提示词
            prompt = self.PROPOSAL_PROMPT.format(
                inventory_data=inventory_data,
                pricing_data=pricing_data,
                cases_data=cases_data,
                customer_id=customer_id or "未提供",
                query=query,
                product_category=product_category or "未明确"
            )
            
            # 调用大模型生成方案
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.chat(messages, temperature=0.7)
            
            # 解析响应
            proposal = self._parse_proposal(response)
            if proposal:
                return proposal
                
            logger.warning("LLM返回数据解析失败，使用降级方案")
            return self._generate_fallback_proposal(
                inventory_info, pricing_info, cases_info, customer_id, query, product_category
            )
            
        except Exception as e:
            logger.error(f"生成销售方案失败: {str(e)}")
            # 降级方案：基于已有数据生成简单的销售方案
            return self._generate_fallback_proposal(
                inventory_info, pricing_info, cases_info, customer_id, query, product_category
            )
    
    def _generate_fallback_proposal(
        self,
        inventory_info: Optional[InventoryInfo],
        pricing_info: Optional[PricingInfo],
        cases_info: List[CaseInfo],
        customer_id: Optional[str],
        query: str,
        product_category: Optional[str]
    ) -> ProposalInfo:
        """
        生成降级销售方案（当LLM调用失败时使用）
        
        Args:
            inventory_info: 库存信息
            pricing_info: 价格信息
            cases_info: 案例信息
            customer_id: 客户ID
            query: 客户咨询
            product_category: 产品品类
            
        Returns:
            降级销售方案
        """
        logger.info("生成降级销售方案")
        
        product_name = product_category or "产品"
        
        # 生成方案摘要
        summary_parts = []
        if inventory_info:
            summary_parts.append(f"产品库存充足，当前可用库存 {inventory_info.available_quantity} 单位")
        if pricing_info:
            summary_parts.append(f"建议单价 {pricing_info.unit_price} 元，总价 {pricing_info.total_price} 元")
            if pricing_info.discount_rate > 0:
                summary_parts.append(f"已提供 {pricing_info.discount_rate * 100:.1f}% 折扣")
        if cases_info:
            summary_parts.append(f"参考了 {len(cases_info)} 个相似成交案例")
        
        summary = "基于当前数据，为您生成以下销售方案：" + "；".join(summary_parts) if summary_parts else \
                  f"针对您关于{product_name}的采购需求，我们提供以下合作方案。"
        
        # 生成定价策略
        pricing_strategy_parts = []
        if pricing_info:
            pricing_strategy_parts.append(f"基准单价：{pricing_info.unit_price} 元")
            pricing_strategy_parts.append(f"采购数量：{pricing_info.quantity} 单位")
            pricing_strategy_parts.append(f"总价：{pricing_info.total_price} 元")
            if pricing_info.discount_rate > 0:
                pricing_strategy_parts.append(f"折扣率：{pricing_info.discount_rate * 100:.1f}%")
                pricing_strategy_parts.append(f"折扣原因：{pricing_info.discount_reason or '大客户优惠'}")
            pricing_strategy_parts.append(f"付款条件：{pricing_info.payment_terms}")
        
        pricing_strategy = "\n".join(pricing_strategy_parts) if pricing_strategy_parts else \
                          "定价策略需根据具体采购数量和付款条件进一步确认，请联系销售顾问获取详细报价。"
        
        # 生成库存保障
        inventory_assurance_parts = []
        if inventory_info:
            inventory_assurance_parts.append(f"产品名称：{inventory_info.product_name}")
            inventory_assurance_parts.append(f"库存总量：{inventory_info.stock_quantity} 单位")
            inventory_assurance_parts.append(f"可用库存：{inventory_info.available_quantity} 单位")
            inventory_assurance_parts.append(f"备货周期：{inventory_info.lead_time}")
            if inventory_info.warehouse_location:
                inventory_assurance_parts.append(f"发货仓库：{inventory_info.warehouse_location}")
            
            if inventory_info.available_quantity > 0:
                inventory_assurance_parts.append("库存充足，可立即发货")
            else:
                inventory_assurance_parts.append("当前库存紧张，需安排生产")
        
        inventory_assurance = "\n".join(inventory_assurance_parts) if inventory_assurance_parts else \
                             "库存信息暂不可用，请联系销售顾问确认。"
        
        # 生成付款建议
        if pricing_info:
            payment_recommendation = f"建议采用{pricing_info.payment_terms}方式结算。"
            if "30天" in pricing_info.payment_terms:
                payment_recommendation += "此方案适合长期合作客户，可享受30天账期。"
            elif "60天" in pricing_info.payment_terms:
                payment_recommendation += "此方案适合信用评级较高的客户。"
            else:
                payment_recommendation += "如需账期服务，请提供客户资质证明进行信用评估。"
        else:
            payment_recommendation = "付款方式可协商，支持款到发货、月结等多种方式。建议根据您的财务周期选择合适的付款条件。"
        
        # 生成竞争优势
        competitive_advantage_parts = []
        if inventory_info and inventory_info.available_quantity > 0:
            competitive_advantage_parts.append("库存充足，交货周期短")
        if pricing_info and pricing_info.discount_rate > 0:
            competitive_advantage_parts.append("价格优惠，折扣力度大")
        if cases_info:
            competitive_advantage_parts.append("丰富的行业经验，成功案例多")
        
        competitive_advantage = "\n".join(competitive_advantage_parts) if competitive_advantage_parts else \
                              "我们拥有专业的销售团队和完善的售后服务体系，可为您提供优质的产品和服务支持。"
        
        # 生成后续行动
        next_steps = [
            "确认采购数量和配置要求",
            "签订正式采购合同",
            "支付预付款或按约定方式结算",
            "安排发货并提供物流跟踪信息",
            "到货验收及售后服务"
        ]
        
        # 生成风险提示
        risk_warnings = []
        if inventory_info and inventory_info.available_quantity < 10:
            risk_warnings.append("当前库存较少，建议尽快确认订单")
        if pricing_info and pricing_info.discount_rate > 0.15:
            risk_warnings.append("折扣力度较大，需上级审批确认")
        
        return ProposalInfo(
            summary=summary,
            pricing_strategy=pricing_strategy,
            inventory_assurance=inventory_assurance,
            payment_recommendation=payment_recommendation,
            competitive_advantage=competitive_advantage,
            next_steps=next_steps,
            risk_warnings=risk_warnings
        )
    
    def _parse_proposal(self, response: str) -> Optional[ProposalInfo]:
        """
        解析大模型生成的方案
        
        Args:
            response: 大模型响应
            
        Returns:
            销售方案
        """
        import json
        import re
        
        try:
            # 提取 JSON 块
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response
            
            data = json.loads(json_str)
            
            return ProposalInfo(
                summary=data.get("summary", ""),
                pricing_strategy=data.get("pricing_strategy", ""),
                inventory_assurance=data.get("inventory_assurance", ""),
                payment_recommendation=data.get("payment_recommendation", ""),
                competitive_advantage=data.get("competitive_advantage", ""),
                next_steps=data.get("next_steps", []),
                risk_warnings=data.get("risk_warnings", [])
            )
            
        except Exception as e:
            logger.error(f"解析方案失败: {str(e)}")
            return None
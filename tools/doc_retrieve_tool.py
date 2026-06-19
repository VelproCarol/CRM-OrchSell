"""
文档检索工具
使用 LlamaIndex + Chroma 向量库检索成交案例文档
"""
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

from tools.base_tool import BaseTool
from config.settings import settings, Constants
from services.cache_manager import get_cache_manager


class DocRetrieveTool(BaseTool):
    """
    文档检索工具
    从 Chroma 向量库检索成交案例、销售话术等文档
    """
    
    def __init__(self):
        """初始化文档检索工具"""
        super().__init__(
            name=Constants.TOOL_DOC_RETRIEVE,
            description="成交案例文档检索工具，返回相似采购量和账期的客户合作案例"
        )
        
        self.chroma_path = Path(settings.CHROMA_DB_PATH)
        self.docs_path = Path(settings.DOCS_PATH)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行文档检索
        
        Args:
            product_name: 产品名称
            quantity_range: 数量区间 [min, max]（可选）
            payment_terms: 付款条件（可选）
            top_k: 返回案例数量（可选，默认3）
            
        Returns:
            案例信息字典
        """
        try:
            logger.info(f"文档检索工具开始执行，参数: {kwargs}")
            
            # 参数验证
            product_name = kwargs.get("product_name")
            if not product_name:
                return self._handle_error(ValueError("产品名称不能为空"))
            
            top_k = kwargs.get("top_k", 3)
            
            # 构建查询文本
            query_text = self._build_query_text(
                product_name=product_name,
                quantity_range=kwargs.get("quantity_range"),
                payment_terms=kwargs.get("payment_terms")
            )
            
            # 尝试从缓存获取数据
            cache_manager = get_cache_manager()
            cached_data = cache_manager.get_case(query_text)
            if cached_data:
                logger.info(f"从缓存获取案例数据，查询: {query_text}")
                return self._success_response(cached_data)
            
            # 检索相似案例
            cases = await self._retrieve_cases(query_text, top_k)
            
            result = {
                "product_name": product_name,
                "query_text": query_text,
                "cases": cases,
                "total_count": len(cases)
            }
            
            # 将结果存入缓存
            cache_manager.set_case(query_text, result)
            
            logger.info(f"文档检索成功，产品: {product_name}, 找到 {len(cases)} 个案例")
            return self._success_response(result)
            
        except Exception as e:
            return self._handle_error(e)
    
    def _build_query_text(
        self,
        product_name: str,
        quantity_range: Optional[List[int]] = None,
        payment_terms: Optional[str] = None
    ) -> str:
        """
        构建查询文本
        
        Args:
            product_name: 产品名称
            quantity_range: 数量区间
            payment_terms: 付款条件
            
        Returns:
            查询文本
        """
        query_parts = [f"{product_name}采购案例"]
        
        if quantity_range:
            query_parts.append(f"采购量{quantity_range[0]}-{quantity_range[1]}")
        
        if payment_terms:
            query_parts.append(f"{payment_terms}")
        
        return " ".join(query_parts)
    
    async def _retrieve_cases(
        self,
        query_text: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        检索相似案例
        
        Args:
            query_text: 查询文本
            top_k: 返回数量
            
        Returns:
            案例列表
        """
        # 检查向量库是否存在
        if not self.chroma_path.exists():
            logger.warning(f"向量库不存在: {self.chroma_path}, 返回模拟数据")
            return self._get_mock_cases(query_text)
        
        try:
            # 使用 LlamaIndex 检索
            from llama_index.core import VectorStoreIndex, StorageContext
            from llama_index.vector_stores.chroma import ChromaVectorStore
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding
            import chromadb
            
            # 加载 Chroma 向量库
            chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
            chroma_collection = chroma_client.get_collection("sales_cases")
            
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # 使用本地嵌入模型
            embed_model = HuggingFaceEmbedding(
                model_name=settings.EMBEDDING_MODEL_PATH,
                trust_remote_code=True
            )
            
            # 加载索引
            index = VectorStoreIndex.from_vector_store(
                vector_store=vector_store,
                embed_model=embed_model
            )
            
            # 创建检索器
            retriever = index.as_retriever(similarity_top_k=top_k)
            
            # 执行检索
            nodes = retriever.retrieve(query_text)
            
            # 解析检索结果
            cases = []
            for node in nodes:
                case_data = self._parse_case_node(node)
                cases.append(case_data)
            
            return cases
            
        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            return self._get_mock_cases(query_text)
    
    def _parse_case_node(self, node: Any) -> Dict[str, Any]:
        """
        解析案例节点
        
        Args:
            node: LlamaIndex 节点
            
        Returns:
            案例数据字典
        """
        import json
        
        try:
            # 尝试从节点元数据中提取案例信息
            metadata = node.metadata or {}
            
            # 尝试从文本中提取 JSON
            text = node.text or ""
            
            # 如果文本包含 JSON，尝试解析
            if "{" in text and "}" in text:
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    case_data = json.loads(json_match.group())
                    case_data["similarity_score"] = node.score if hasattr(node, "score") else 0.8
                    return case_data
            
            # 返回基本案例信息
            return {
                "case_id": metadata.get("case_id", "CASE-UNKNOWN"),
                "customer_name": metadata.get("customer_name", "未知客户"),
                "industry": metadata.get("industry", "未知行业"),
                "quantity": metadata.get("quantity", 0),
                "deal_price": metadata.get("deal_price", 0.0),
                "payment_terms": metadata.get("payment_terms", "未知"),
                "deal_date": metadata.get("deal_date", "未知"),
                "similarity_score": node.score if hasattr(node, "score") else 0.8,
                "content": text[:200]  # 截取部分内容
            }
            
        except Exception as e:
            logger.error(f"解析案例节点失败: {str(e)}")
            return {
                "case_id": "CASE-ERROR",
                "similarity_score": 0.0,
                "error": str(e)
            }
    
    def _get_mock_cases(self, query_text: str) -> List[Dict[str, Any]]:
        """
        获取模拟案例数据
        
        Args:
            query_text: 查询文本
            
        Returns:
            模拟案例列表
        """
        # 模拟案例数据
        mock_cases = [
            {
                "case_id": "CASE-2024-001",
                "customer_name": "某大型制造企业",
                "industry": "汽车制造",
                "quantity": 55,
                "deal_price": 8200.0,
                "total_amount": 451000.0,
                "payment_terms": "30天账期",
                "deal_date": "2024-01-10",
                "similarity_score": 0.92,
                "summary": "客户采购55台工业风机用于生产线升级，采用30天账期，享受5%折扣"
            },
            {
                "case_id": "CASE-2024-002",
                "customer_name": "某化工企业",
                "industry": "化工",
                "quantity": 48,
                "deal_price": 8400.0,
                "total_amount": 403200.0,
                "payment_terms": "30天账期",
                "deal_date": "2024-01-05",
                "similarity_score": 0.88,
                "summary": "客户采购48台工业风机用于通风系统改造，采用30天账期"
            },
            {
                "case_id": "CASE-2023-003",
                "customer_name": "某电力公司",
                "industry": "电力",
                "quantity": 60,
                "deal_price": 8000.0,
                "total_amount": 480000.0,
                "payment_terms": "30天账期",
                "deal_date": "2023-12-20",
                "similarity_score": 0.85,
                "summary": "客户采购60台工业风机用于电厂通风，采用30天账期，享受8%折扣"
            }
        ]
        
        logger.info(f"返回 {len(mock_cases)} 个模拟案例")
        return mock_cases
    
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
                "top_k": {
                    "type": "integer",
                    "description": "返回案例数量（可选，默认3）"
                }
            },
            "required": ["product_name"]
        }
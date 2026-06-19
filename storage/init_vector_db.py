"""
Chroma 向量数据库初始化脚本
批量加载成交案例文档至 Chroma 向量库
"""
from pathlib import Path
from typing import List, Dict, Any
import json
from loguru import logger

from config.settings import settings
from llama_index.core import Document


def init_vector_database():
    """
    初始化 Chroma 向量数据库
    加载成交案例文档并创建向量索引
    """
    chroma_path = Path(settings.CHROMA_DB_PATH)
    docs_path = Path(settings.DOCS_PATH)
    
    # 确保目录存在
    chroma_path.mkdir(parents=True, exist_ok=True)
    docs_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"开始初始化 Chroma 向量数据库: {chroma_path}")
    
    try:
        # 导入必要库
        import chromadb
        from llama_index.core import Document, VectorStoreIndex, StorageContext
        from llama_index.vector_stores.chroma import ChromaVectorStore
        
        # 创建 Chroma 客户端
        chroma_client = chromadb.PersistentClient(path=str(chroma_path))
        
        # 创建或获取集合
        try:
            chroma_collection = chroma_client.get_collection("sales_cases")
            logger.info("使用现有向量集合")
        except:
            chroma_collection = chroma_client.create_collection("sales_cases")
            logger.info("创建新向量集合")
        
        # 检查是否已有数据
        existing_count = chroma_collection.count()
        if existing_count > 0:
            logger.info(f"向量库已有 {existing_count} 条数据，跳过初始化")
            return
        
        # 加载文档
        documents = load_documents(docs_path)
        
        if not documents:
            logger.warning("未找到文档，使用模拟数据")
            documents = generate_mock_documents()
        
        # 创建向量存储
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # 使用 embedding 模型
        embed_model = _create_embedding_model()
        
        # 创建索引
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model,
            show_progress=True
        )
        
        logger.info(f"向量数据库初始化完成，共 {len(documents)} 个文档")
        
    except ImportError as e:
        logger.warning(f"缺少依赖库: {str(e)}, 使用模拟数据")
        # 创建模拟文档文件
        create_mock_doc_files(docs_path)
        logger.info("已创建模拟文档文件")


def load_documents(docs_path: Path) -> List[Document]:
    """
    加载文档文件
    
    Args:
        docs_path: 文档目录路径
        
    Returns:
        Document 列表
    """
    
    documents = []
    
    # 支持的文件格式
    supported_formats = ["*.md", "*.txt", "*.json"]
    
    for pattern in supported_formats:
        for file_path in docs_path.glob(pattern):
            try:
                # 读取文件内容
                content = file_path.read_text(encoding="utf-8")
                
                # 创建 Document
                doc = Document(
                    text=content,
                    metadata={
                        "file_name": file_path.name,
                        "file_path": str(file_path)
                    }
                )
                
                documents.append(doc)
                logger.debug(f"加载文档: {file_path.name}")
                
            except Exception as e:
                logger.error(f"加载文档失败: {file_path.name}, {str(e)}")
    
    return documents


def generate_mock_documents() -> List[Document]:
    """
    生成模拟文档数据
    
    Returns:
        Document 列表
    """
    
    # 模拟案例数据
    mock_cases = [
        {
            "case_id": "CASE-2024-001",
            "title": "某大型制造企业工业风机采购案例",
            "customer": "某大型制造企业",
            "industry": "汽车制造",
            "product": "工业风机",
            "quantity": 55,
            "deal_price": 8200.0,
            "payment_terms": "30天账期",
            "deal_date": "2024-01-10",
            "summary": "客户采购55台工业风机用于生产线升级，采用30天账期，享受5%折扣",
            "details": "该客户为大型汽车制造企业，生产线升级需要增加通风设备。经过多次沟通，最终确定采购55台工业风机，单价8200元，总价451000元。付款方式为30天账期，客户信用等级为A级。",
            "lessons": "大客户采购需要提供详细的技术方案和售后服务承诺，账期政策是关键谈判点。"
        },
        {
            "case_id": "CASE-2024-002",
            "title": "某化工企业离心泵采购案例",
            "customer": "某化工企业",
            "industry": "化工",
            "product": "离心泵",
            "quantity": 20,
            "deal_price": 3100.0,
            "payment_terms": "款到发货",
            "deal_date": "2024-01-05",
            "summary": "客户采购20台离心泵用于化工流程改造，款到发货",
            "details": "化工企业需要更换老旧离心泵，采购20台新型离心泵。单价3100元，总价62000元。付款方式为款到发货，客户要求快速交货。",
            "lessons": "化工行业对设备质量要求高，需要提供详细的技术参数和质量认证。"
        },
        {
            "case_id": "CASE-2024-003",
            "title": "某电力公司压缩机采购案例",
            "customer": "某电力公司",
            "industry": "电力",
            "product": "压缩机",
            "quantity": 8,
            "deal_price": 14500.0,
            "payment_terms": "60天账期",
            "deal_date": "2024-01-15",
            "summary": "电力公司采购8台压缩机用于发电设备维护，60天账期",
            "details": "电力公司发电设备需要定期维护，采购8台高压压缩机。单价14500元，总价116000元。付款方式为60天账期，客户为长期合作伙伴。",
            "lessons": "电力行业客户通常有较长的账期需求，需要做好资金规划。"
        },
        {
            "case_id": "CASE-2024-004",
            "title": "某钢铁企业电机批量采购案例",
            "customer": "某钢铁企业",
            "industry": "钢铁",
            "product": "电机",
            "quantity": 100,
            "deal_price": 1100.0,
            "payment_terms": "30天账期",
            "deal_date": "2024-02-01",
            "summary": "钢铁企业批量采购100台电机用于生产线改造，享受8%折扣",
            "details": "钢铁企业生产线改造需要大量电机，采购100台高效节能电机。单价1100元，总价110000元，享受8%批量折扣。付款方式为30天账期。",
            "lessons": "批量采购客户对价格敏感，需要提供阶梯折扣政策。"
        },
        {
            "case_id": "CASE-2024-005",
            "title": "某纺织企业阀门采购案例",
            "customer": "某纺织企业",
            "industry": "纺织",
            "product": "阀门",
            "quantity": 200,
            "deal_price": 330.0,
            "payment_terms": "分期付款",
            "deal_date": "2024-02-10",
            "summary": "纺织企业采购200个阀门用于管道系统升级，分期付款",
            "details": "纺织企业管道系统升级需要大量阀门，采购200个工业控制阀门。单价330元，总价66000元。付款方式为分期付款，分3期支付。",
            "lessons": "分期付款可以降低客户资金压力，促进成交。"
        }
    ]
    
    # 转换为 Document
    documents = []
    for case in mock_cases:
        # 将案例数据转换为文本
        text = json.dumps(case, ensure_ascii=False, indent=2)
        
        doc = Document(
            text=text,
            metadata={
                "case_id": case["case_id"],
                "customer_name": case["customer"],
                "industry": case["industry"],
                "product_name": case["product"],
                "quantity": case["quantity"],
                "deal_price": case["deal_price"],
                "payment_terms": case["payment_terms"],
                "deal_date": case["deal_date"]
            }
        )
        
        documents.append(doc)
    
    logger.info(f"生成 {len(documents)} 个模拟文档")
    return documents


def create_mock_doc_files(docs_path: Path):
    """
    创建模拟文档文件
    
    Args:
        docs_path: 文档目录路径
    """
    # 创建案例文档
    case_1 = """# 某大型制造企业工业风机采购案例

## 基本信息
- 案例编号: CASE-2024-001
- 客户名称: 某大型制造企业
- 行业类型: 汽车制造
- 产品名称: 工业风机
- 采购数量: 55台
- 成交单价: 8200元
- 成交总价: 451000元
- 付款方式: 30天账期
- 成交日期: 2024-01-10

## 案例详情
该客户为大型汽车制造企业，生产线升级需要增加通风设备。经过多次沟通，最终确定采购55台工业风机，单价8200元，总价451000元。付款方式为30天账期，客户信用等级为A级。

## 经验总结
大客户采购需要提供详细的技术方案和售后服务承诺，账期政策是关键谈判点。
"""
    
    case_2 = """# 某化工企业离心泵采购案例

## 基本信息
- 案例编号: CASE-2024-002
- 客户名称: 某化工企业
- 行业类型: 化工
- 产品名称: 离心泵
- 采购数量: 20台
- 成交单价: 3100元
- 成交总价: 62000元
- 付款方式: 款到发货
- 成交日期: 2024-01-05

## 案例详情
化工企业需要更换老旧离心泵，采购20台新型离心泵。单价3100元，总价62000元。付款方式为款到发货，客户要求快速交货。

## 经验总结
化工行业对设备质量要求高，需要提供详细的技术参数和质量认证。
"""
    
    case_3 = """# 某电力公司压缩机采购案例

## 基本信息
- 案例编号: CASE-2024-003
- 客户名称: 某电力公司
- 行业类型: 电力
- 产品名称: 压缩机
- 采购数量: 8台
- 成交单价: 14500元
- 成交总价: 116000元
- 付款方式: 60天账期
- 成交日期: 2024-01-15

## 案例详情
电力公司发电设备需要定期维护，采购8台高压压缩机。单价14500元，总价116000元。付款方式为60天账期，客户为长期合作伙伴。

## 经验总结
电力行业客户通常有较长的账期需求，需要做好资金规划。
"""
    
    # 写入文件
    (docs_path / "case_001.md").write_text(case_1, encoding="utf-8")
    (docs_path / "case_002.md").write_text(case_2, encoding="utf-8")
    (docs_path / "case_003.md").write_text(case_3, encoding="utf-8")
    
    logger.info(f"创建 {3} 个模拟文档文件")


def _create_embedding_model():
    """
    创建 embedding 模型（支持本地模型和 HuggingFace 在线模型）
    
    Returns:
        Embedding 模型实例
    """
    import traceback
    
    # 检查是否使用本地模型
    if settings.USE_LOCAL_EMBEDDING:
        model_path = Path(settings.EMBEDDING_MODEL_PATH)
        
        # 检查本地模型是否存在
        if model_path.exists():
            logger.info(f"使用本地模型: {model_path}")
            
            try:
                # 使用 HuggingFaceEmbedding 加载本地模型（兼容性更好）
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                embed_model = HuggingFaceEmbedding(model_name=str(model_path))
                logger.info("成功使用 HuggingFaceEmbedding 加载本地模型")
                return embed_model
                
            except Exception as e:
                logger.error(f"HuggingFaceEmbedding 加载失败: {str(e)}")
                logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
                raise
        else:
            error_msg = f"本地模型不存在: {model_path}，请先下载模型到该路径。" \
                       f"可使用命令: huggingface-cli download {settings.EMBEDDING_MODEL_NAME} {model_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
    else:
        # 使用 HuggingFaceEmbedding 从在线拉取
        logger.info(f"使用 HuggingFace 在线模型: {settings.EMBEDDING_MODEL_NAME}")
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)


if __name__ == "__main__":
    init_vector_database()

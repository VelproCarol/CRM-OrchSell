"""
全局配置读取模块
使用 pydantic-settings 管理环境变量配置
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    全局配置类
    从 .env 文件读取配置，支持环境变量覆盖
    """
    
    # ==================== 大模型配置 ====================
    # 模式选择: openai | qwen
    LLM_MODE: str = Field(default="openai", description="大模型模式选择")
    
    # OpenAI 配置
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API密钥")
    OPENAI_API_BASE: str = Field(default="https://api.openai.com/v1", description="OpenAI API基础URL")
    OPENAI_MODEL: str = Field(default="gpt-5.1", description="OpenAI模型名称")
    
    # Qwen/Ollama 配置
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama服务地址")
    OLLAMA_MODEL: str = Field(default="qwen:7b", description="Qwen模型名称")
    
    # ==================== 数据库配置 ====================
    # 数据库类型: sqlite | mysql | postgresql
    DB_TYPE: str = Field(default="sqlite", description="数据库类型选择")
    
    # SQLite 配置（默认开发环境）
    SQLITE_DB_PATH: str = Field(default="./storage/sqlite/sales_agent.db", description="SQLite数据库路径")
    
    # MySQL 配置（企业生产环境）
    MYSQL_HOST: str = Field(default="localhost", description="MySQL服务器地址")
    MYSQL_PORT: int = Field(default=3306, description="MySQL端口")
    MYSQL_USER: str = Field(default="root", description="MySQL用户名")
    MYSQL_PASSWORD: Optional[str] = Field(default=None, description="MySQL密码")
    MYSQL_DB: str = Field(default="sales_agent", description="MySQL数据库名")
    
    # PostgreSQL 配置（企业生产环境）
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL服务器地址")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL端口")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL用户名")
    POSTGRES_PASSWORD: Optional[str] = Field(default=None, description="PostgreSQL密码")
    POSTGRES_DB: str = Field(default="sales_agent", description="PostgreSQL数据库名")
    
    CHROMA_DB_PATH: str = Field(default="./storage/chroma_db", description="Chroma向量数据库路径")
    DOCS_PATH: str = Field(default="./docs", description="业务文档路径")
    
    # ==================== API服务配置 ====================
    API_HOST: str = Field(default="0.0.0.0", description="API服务监听地址")
    API_PORT: int = Field(default=8000, description="API服务端口")
    API_DEBUG: bool = Field(default=True, description="调试模式")
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FILE: str = Field(default="./logs/sales_agent.log", description="日志文件路径")
    
    # ==================== 工具配置 ====================
    TOOL_TIMEOUT: int = Field(default=30, description="工具调用超时时间(秒)")
    
    # ==================== 缓存配置 ====================
    REDIS_ENABLED: bool = Field(default=False, description="是否启用 Redis 缓存")
    REDIS_HOST: str = Field(default="localhost", description="Redis 服务器地址")
    REDIS_PORT: int = Field(default=6379, description="Redis 端口")
    REDIS_DB: int = Field(default=0, description="Redis 数据库编号")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis 密码")
    CACHE_TTL_INVENTORY: int = Field(default=3600, description="库存缓存有效期(秒)")
    CACHE_TTL_PRICING: int = Field(default=7200, description="价格缓存有效期(秒)")
    CACHE_TTL_CASES: int = Field(default=86400, description="案例缓存有效期(秒)")
    
    # ==================== 限流配置 ====================
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="是否启用请求限流")
    RATE_LIMIT_MAX_REQUESTS: int = Field(default=100, description="每分钟最大请求数")
    RATE_LIMIT_STORAGE_URI: str = Field(default="memory://", description="限流存储后端")
    
    # ==================== 公司信息配置 ====================
    COMPANY_NAME: str = Field(default="XX科技有限公司", description="公司名称")
    COMPANY_ADDRESS: str = Field(default="北京市朝阳区科技园区", description="公司地址")
    COMPANY_PHONE: str = Field(default="400-888-8888", description="公司电话")
    COMPANY_EMAIL: str = Field(default="sales@example.com", description="公司邮箱")
    
    # ==================== 企业微信配置 ====================
    WECHAT_CORP_ID: Optional[str] = Field(default=None, description="企业微信企业ID")
    WECHAT_APP_SECRET: Optional[str] = Field(default=None, description="企业微信应用密钥")
    WECHAT_AGENT_ID: int = Field(default=0, description="企业微信应用ID")
    
    # ==================== 反思验真配置 ====================
    REFLECTION_ENABLED: bool = Field(default=True, description="是否启用反思验真")
    REFLECTION_CONFIDENCE_THRESHOLD: float = Field(default=0.8, description="反思验真置信度阈值")
    
    # ==================== 模拟数据配置 ====================
    USE_MOCK_DATA: bool = Field(default=False, description="是否使用模拟数据")
    
    # ==================== Embedding 模型配置 ====================
    EMBEDDING_MODEL_PATH: str = Field(
        default="./models/bge-small-zh-v1.5",
        description="本地 BGE embedding 模型路径（使用 flag-embedding）"
    )
    EMBEDDING_MODEL_NAME: str = Field(
        default="BAAI/bge-small-zh-v1.5",
        description="Embedding 模型名称（用于从 HuggingFace 下载）"
    )
    USE_LOCAL_EMBEDDING: bool = Field(
        default=True,
        description="是否使用本地 embedding 模型（True 时使用本地路径，False 从 HuggingFace 在线拉取）"
    )
    
    # ==================== LangFuse 监控配置 ====================
    LANGFUSE_ENABLED: bool = Field(default=True, description="是否启用 LangFuse 监控")
    LANGFUSE_HOST: str = Field(default="http://localhost:3000", description="LangFuse 服务地址")
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(default=None, description="LangFuse 公钥")
    LANGFUSE_SECRET_KEY: Optional[str] = Field(default=None, description="LangFuse 私钥")
    LANGFUSE_TRACING_SAMPLE_RATE: float = Field(default=1.0, description="采样率")
    
    # ==================== 模型定价配置 ====================
    # 智谱 AI 定价（单位：美元/1K tokens）
    MODEL_PRICE_GLM_INPUT: float = Field(default=0.0015, description="GLM 模型输入成本")
    MODEL_PRICE_GLM_OUTPUT: float = Field(default=0.002, description="GLM 模型输出成本")
    
    # OpenAI 定价
    MODEL_PRICE_OPENAI_INPUT: float = Field(default=0.001, description="OpenAI 输入成本")
    MODEL_PRICE_OPENAI_OUTPUT: float = Field(default=0.003, description="OpenAI 输出成本")
    
    # Qwen 本地模型（成本为0，因为是本地部署）
    MODEL_PRICE_QWEN_INPUT: float = Field(default=0.0, description="Qwen 输入成本")
    MODEL_PRICE_QWEN_OUTPUT: float = Field(default=0.0, description="Qwen 输出成本")
    
    @validator("LLM_MODE")
    def validate_llm_mode(cls, v):
        """验证大模型模式"""
        allowed_modes = ["openai", "qwen"]
        if v.lower() not in allowed_modes:
            raise ValueError(f"LLM_MODE 必须是 {allowed_modes} 之一")
        return v.lower()
    
    @validator("DB_TYPE")
    def validate_db_type(cls, v):
        """验证数据库类型"""
        allowed_types = ["sqlite", "mysql", "postgresql"]
        if v.lower() not in allowed_types:
            raise ValueError(f"DB_TYPE 必须是 {allowed_types} 之一")
        return v.lower()
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL 必须是 {allowed_levels} 之一")
        return v.upper()
    
    @validator("SQLITE_DB_PATH", "CHROMA_DB_PATH", "DOCS_PATH", "LOG_FILE")
    def validate_path(cls, v):
        """验证路径存在性，不存在则创建"""
        path = Path(v)
        if not path.is_absolute():
            # 转换为绝对路径
            base_dir = Path(__file__).parent.parent
            path = base_dir / v
        
        # 确保目录存在
        if path.suffix:  # 如果是文件路径
            path.parent.mkdir(parents=True, exist_ok=True)
        else:  # 如果是目录路径
            path.mkdir(parents=True, exist_ok=True)
        
        return str(path)
    
    def get_database_url(self) -> str:
        """
        根据配置生成数据库连接URL
        
        Returns:
            数据库连接URL
        """
        if self.DB_TYPE == "mysql":
            password = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
            return f"mysql+pymysql://{self.MYSQL_USER}{password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        elif self.DB_TYPE == "postgresql":
            password = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
            return f"postgresql://{self.POSTGRES_USER}{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            return f"sqlite:///{self.SQLITE_DB_PATH}"

    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 允许额外字段


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置实例
    用于依赖注入
    """
    return settings


# ==================== 常量定义 ====================
class Constants:
    """
    全局常量定义
    """
    
    # 任务类型
    TASK_INVENTORY_QUERY = "inventory_query"      # 库存查询
    TASK_PRICE_QUERY = "price_query"              # 价格查询
    TASK_CASE_RETRIEVAL = "case_retrieval"        # 案例检索
    TASK_PRICE_CALCULATION = "price_calculation"  # 价格计算
    
    # 任务状态
    TASK_STATUS_PENDING = "pending"               # 待执行
    TASK_STATUS_RUNNING = "running"               # 执行中
    TASK_STATUS_COMPLETED = "completed"           # 已完成
    TASK_STATUS_FAILED = "failed"                 # 失败
    
    # 工具名称
    TOOL_CALCULATOR = "calculator"
    TOOL_API_INVENTORY = "api_inventory"
    TOOL_SQL_PRICE = "sql_price"
    TOOL_DOC_RETRIEVE = "doc_retrieve"
    TOOL_WECHAT_NOTIFY = "wechat_notify"
    
    # 反思验真状态
    REFLECTION_PASSED = "passed"
    REFLECTION_WARNING = "warning"
    REFLECTION_FAILED = "failed"
    
    # API响应状态
    API_STATUS_SUCCESS = "success"
    API_STATUS_ERROR = "error"
    API_STATUS_PARTIAL = "partial"
    
    # 默认值
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_PAGE_SIZE = 10


# 全局常量实例
constants = Constants()
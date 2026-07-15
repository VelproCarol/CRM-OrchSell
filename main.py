"""
项目服务启动入口
启动 FastAPI 服务，初始化数据库和工具
"""
import sys
from pathlib import Path
from loguru import logger
import uvicorn

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from api.chat_route import create_app


def setup_logging():
    """
    配置日志系统
    """
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    log_path = Path(settings.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_path),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )
    
    logger.info("日志系统配置完成")


def initialize_system():
    """
    初始化系统
    连接企业数据库，验证连接状态
    """
    logger.info("开始初始化系统...")
    import traceback
    
    try:
        logger.info(f"数据库类型: {settings.DB_TYPE}")
        
        if settings.DB_TYPE == "mysql":
            logger.info(f"连接 MySQL 数据库: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}")
        elif settings.DB_TYPE == "postgresql":
            logger.info(f"连接 PostgreSQL 数据库: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        else:
            logger.info(f"连接 SQLite 数据库: {settings.SQLITE_DB_PATH}")
        
        from storage.db_connector import get_db_connector
        db = get_db_connector()
        
        test_result = db.query("SELECT 1")
        if test_result:
            logger.info("数据库连接成功")
        else:
            logger.warning("数据库连接异常")
            
        logger.info("系统初始化完成")
        
    except Exception as e:
        logger.error(f"系统初始化失败: {str(e)}")
        if str(e) == "":
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"完整错误堆栈:\n{traceback.format_exc()}")
        logger.warning("将使用模拟数据运行")


def main():
    """
    主函数
    启动 FastAPI 服务
    """
    # 配置日志
    setup_logging()
    
    logger.info("=" * 60)
    logger.info("可编排多工具销售任务拆解 Agent")
    logger.info("=" * 60)
    logger.info(f"LLM 模式: {settings.LLM_MODE}")
    logger.info(f"API 地址: {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"调试模式: {settings.API_DEBUG}")
    logger.info(f"模拟数据: {settings.USE_MOCK_DATA}")
    logger.info("=" * 60)
    
    # 初始化系统
    initialize_system()
    
    # 创建应用
    app = create_app()
    
    # 添加静态文件服务（前端页面）
    from fastapi.staticfiles import StaticFiles
    frontend_path = Path(__file__).parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
        logger.info(f"前端页面已挂载: /static")
    
    # 添加根路由（返回前端页面）
    from fastapi.responses import FileResponse
    
    @app.get("/")
    async def root():
        """返回前端调试页面"""
        index_file = frontend_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return {"message": "欢迎使用销售 Agent API，请访问 /docs 查看 API 文档"}
    
    # 启动服务
    logger.info("启动 FastAPI 服务...")
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
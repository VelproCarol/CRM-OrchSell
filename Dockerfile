# ===========================================
# CRM-OrchSell Dockerfile
# 多阶段构建，优化镜像体积
# ===========================================

# ============ 阶段 1: 构建环境 ============
FROM python:3.10-slim AS builder

WORKDIR /app

# 安装系统编译依赖（用于编译 Python 原生扩展）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖到指定目录
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ============ 阶段 2: 运行时环境 ============
FROM python:3.10-slim AS runtime

LABEL maintainer="CRM-OrchSell Team"
LABEL description="可编排多工具销售任务拆解 Agent"
LABEL version="1.0.0"

WORKDIR /app

# 从构建阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 复制项目代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/storage/sqlite \
    && mkdir -p /app/storage/chroma_db \
    && mkdir -p /app/docs \
    && mkdir -p /app/logs \
    && mkdir -p /app/models

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LLM_MODE=openai \
    USE_MOCK_DATA=true \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    SQLITE_DB_PATH=/app/storage/sqlite/sales_agent.db \
    CHROMA_DB_PATH=/app/storage/chroma_db \
    LOG_FILE=/app/logs/sales_agent.log \
    EMBEDDING_MODEL_PATH=/app/models/bge-small-zh-v1.5

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

# 创建非 root 用户运行（安全最佳实践）
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser \
    && chown -R appuser:appuser /app

USER appuser

# 启动命令
CMD ["python", "main.py"]
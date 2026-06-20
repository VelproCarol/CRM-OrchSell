# ===========================================
# 可编排多工具销售任务拆解 Agent Dockerfile
# ===========================================

# 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要目录
RUN mkdir -p /app/storage/sqlite \
    && mkdir -p /app/storage/chroma_db \
    && mkdir -p /app/docs \
    && mkdir -p /app/logs

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV LLM_MODE=openai
ENV USE_MOCK_DATA=true

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
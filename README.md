# 可编排多工具销售任务拆解 Agent

## 项目简介

本项目是一个面向 B2B 实体产品销售场景的智能 Agent 系统，能够自主拆解销售全流程子任务、调度多数据源工具、内置 RAG 事实验真反思机制、标准化 JSON 输出对接企业 CRM 系统。

## 功能介绍

- **双大模型兼容**：一键切换 OpenAI 云端 API / Ollama 本地 Qwen（Qwen-7B/14B）
- **可编排多工具调度**：支持自定义任务串行、并行执行，内置 5 大业务工具
- **智能任务拆解器**：大模型根据客户咨询文本自主拆分标准化子任务队列
- **事实反思校验引擎**：分层 RAG 验真，量化幻觉风险
- **强约束输出**：Pydantic 强 Schema 约束输出，100% 固定 JSON 格式
- **多数据库支持**：支持 SQLite / MySQL / PostgreSQL 三种数据库接入
- **FastAPI 接口**：对外暴露 FastAPI，适配企业内部系统调用
- **全链路日志**：记录任务拆解记录、工具返回值、反思校验日志
- **智能缓存**：Redis 缓存支持，提升查询性能
- **全链路监控**：集成 Prometheus 指标收集和 LangFuse LLM 追踪
- **客户管理**：客户画像、跟进记录管理
- **NL2SQL**：自然语言转 SQL 查询服务

## 技术栈

- **开发语言**：Python 3.10+
- **Agent 框架**：LlamaIndex Agent
- **大模型**：OpenAI GPT 系列 / Qwen-7B/14B (Ollama)
- **Web 框架**：FastAPI
- **数据库**：SQLite / MySQL / PostgreSQL / Chroma 向量数据库 / Redis（可选）
- **数据验证**：Pydantic v2
- **测试框架**：Pytest
- **监控**：Prometheus + LangFuse
- **Embedding**：BGE-small-zh-v1.5（本地部署）

## 快速开始

### 方式一：本地开发

```bash
# 克隆项目
git clone <repository_url>
cd CRM-sale-Agent

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.sample .env
# 编辑 .env，设置 LLM_MODE 和 API Key

# 启动服务
python main.py

# 访问
# API 文档：http://localhost:8000/docs
# 前端页面：http://localhost:8000/
```

### 方式二：Docker 一键部署

```bash
# 配置环境变量
cp .env.sample .env
# 编辑 .env，设置 LLM_MODE 和 API Key

# 启动所有服务（应用 + Redis）
docker compose up -d

# 启用 LangFuse 监控（可选）
docker compose --profile monitoring up -d

# 查看日志
docker compose logs -f app

# 访问
# API 文档：http://localhost:8000/docs
```

## 项目目录结构

```
CRM-sale-Agent/
├── config/                     # 全局配置
│   └── settings.py               # 配置管理与常量定义
├── core/                       # Agent 核心编排层
│   ├── llm_adapter.py            # 大模型适配器
│   ├── task_planner.py           # 任务拆解器
│   ├── tool_dispatcher.py        # 工具调度器
│   ├── reflection_engine.py      # 反思验真引擎
│   └── sales_agent.py            # Agent 主入口
├── schemas/                    # 数据模型定义
│   └── output_schema.py          # Pydantic 输出模型
├── tools/                      # 可插拔工具集合
│   ├── base_tool.py              # 工具抽象基类
│   ├── calculator_tool.py        # 计算器工具
│   ├── api_inventory_tool.py     # 库存查询工具
│   ├── sql_price_tool.py         # 价格查询工具
│   ├── doc_retrieve_tool.py      # 文档检索工具
│   └── wechat_notify_tool.py     # 企业微信通知工具
├── services/                   # 业务服务层
│   ├── customer_service.py       # 客户管理服务
│   ├── cache_manager.py          # 缓存管理器
│   ├── monitoring_service.py     # 监控服务
│   ├── nl2sql_service.py         # NL2SQL 服务
│   ├── pdf_generator.py          # PDF 生成服务
│   └── langfuse/                 # LangFuse 监控
├── storage/                    # 持久化存储
│   ├── db_connector.py           # 数据库连接器
│   ├── init_sql.py               # SQL 初始化
│   └── init_vector_db.py         # 向量库初始化
├── api/                        # FastAPI 路由层
│   └── chat_route.py             # 销售咨询路由
├── frontend/                   # 前端调试页面
│   └── index.html
├── scripts/                    # 数据管理脚本
├── tests/                      # 测试用例
├── main.py                     # 服务启动入口
├── Dockerfile                  # Docker 构建文件
├── docker-compose.yml          # Docker Compose 编排
├── .env.sample                 # 环境变量示例
├── requirements.txt            # 依赖清单
└── README.md
```
# 可编排多工具销售任务拆解 Agent

## 项目简介

本项目是一个面向 B2B 实体产品销售场景的智能 Agent 系统，能够自主拆解销售全流程子任务、调度多数据源工具、内置 RAG 事实验真反思机制、标准化 JSON 输出对接企业 CRM 系统。

### 核心特性

- **双大模型兼容**：一键切换 OpenAI 云端 API / Ollama 本地 Qwen（Qwen-7B/14B）
- **可编排多工具调度**：支持自定义任务串行、并行执行
- **智能任务拆解器**：大模型根据客户咨询文本自主拆分标准化子任务队列
- **事实反思校验引擎**：分层 RAG 验真，量化幻觉风险
- **强约束输出**：Pydantic 强 Schema 约束输出，100% 固定 JSON 格式
- **FastAPI 接口**：对外暴露 REST API，适配企业内部系统调用
- **全链路日志**：记录任务拆解记录、工具返回值、反思校验日志

## 技术栈

- **开发语言**：Python 3.10+
- **Agent 框架**：LlamaIndex Agent
- **大模型**：OpenAI GPT-3.5 / Qwen-7B/14B (Ollama)
- **Web 框架**：FastAPI
- **数据库**：SQLite / Chroma 向量数据库
- **数据验证**：Pydantic v2
- **测试框架**：Pytest

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd sales_agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

复制 `.env.sample` 文件并修改配置：

```bash
# 大模型模式选择（openai 或 qwen）
LLM_MODE=openai

# OpenAI 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# 或使用本地 Qwen
LLM_MODE=qwen
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

### 3. 初始化数据

```bash
# 初始化 SQLite 数据库和模拟数据
python storage/init_sql.py

# 初始化 Chroma 向量数据库
python storage/init_vector_db.py
```

### 4. 启动服务

```bash
# 启动 FastAPI 服务
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问接口文档

启动后访问：http://localhost:8000/docs

## 项目结构

```
sales_agent/
├── .env                    # 环境配置
├── requirements.txt        # 依赖清单
├── docker-compose.yml      # Docker 部署配置
├── README.md              # 项目说明
├── config/                # 全局配置
│   └── settings.py
├── core/                  # Agent 核心编排层
│   ├── llm_adapter.py      # 大模型适配器
│   ├── task_planner.py     # 任务拆解器
│   ├── tool_dispatcher.py  # 工具调度器
│   ├── reflection_engine.py# 反思验真引擎
│   ├── sales_agent.py      # Agent 主入口
│   └── output_schema.py    # 输出 Schema
├── tools/                 # 可插拔工具集合
│   ├── base_tool.py        # 工具基类
│   ├── calculator_tool.py  # 计算器工具
│   ├── api_inventory_tool.py# 库存查询工具
│   ├── sql_price_tool.py   # 价格查询工具
│   └── doc_retrieve_tool.py# 文档检索工具
├── storage/               # 持久化存储
│   ├── init_sql.py        # SQL 初始化
│   ├── init_vector_db.py  # 向量库初始化
│   ├── sqlite/            # SQLite 数据库
│   └── chroma_db/         # Chroma 向量库
├── docs/                  # 业务文档库
├── api/                   # FastAPI 路由
│   └── chat_route.py
├── tests/                 # 测试用例
│   ├── test_tools.py
│   ├── test_reflection.py
│   ├── test_api.py
│   └── test_agent_flow.py
├── frontend_simple/       # 前端调试页面
└── main.py               # 服务启动入口
```

## API 使用示例

### 销售咨询接口

```bash
POST /api/chat/sales
Content-Type: application/json

{
  "customer_id": "C001",
  "query": "采购50台工业风机，想要30天账期，对比往期大客户成交价，给一套合作方案",
  "product_category": "工业风机"
}
```

### 响应示例

```json
{
  "status": "success",
  "data": {
    "inventory": {
      "product_name": "工业风机",
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
    "proposal": "基于当前库存和往期成交案例..."
  },
  "reflection_report": {
    "confidence_score": 0.92,
    "verified_fields": ["stock_quantity", "unit_price"],
    "warnings": []
  },
  "task_logs": [...]
}
```

## 模型切换

### 使用 OpenAI

```env
LLM_MODE=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-3.5-turbo
```

### 使用本地 Qwen

```env
LLM_MODE=qwen
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

## Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d
```

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_tools.py -v

# 带覆盖率
pytest tests/ --cov=. --cov-report=html
```

## 注意事项

1. **数据安全**：本地 Qwen 模式所有客户数据、报价文档不出服务器
2. **密钥管理**：云端模式密钥通过环境变量隔离，禁止硬编码
3. **模拟数据**：本项目为个人项目，使用模拟数据进行演示
4. **扩展性**：新增工具仅需实现统一工具基类，无需改写 Agent 主流程

## 许可证

MIT License
# 可编排多工具销售任务拆解 Agent

## 项目简介

本项目是一个面向 B2B 实体产品销售场景的智能 Agent 系统，能够自主拆解销售全流程子任务、调度多数据源工具、内置 RAG 事实验真反思机制、标准化 JSON 输出对接企业 CRM 系统。

### 核心特性

- **双大模型兼容**：一键切换 OpenAI 云端 API / Ollama 本地 Qwen（Qwen-7B/14B）
- **可编排多工具调度**：支持自定义任务串行、并行执行，内置 5 大业务工具
- **智能任务拆解器**：大模型根据客户咨询文本自主拆分标准化子任务队列
- **事实反思校验引擎**：分层 RAG 验真，量化幻觉风险
- **强约束输出**：Pydantic 强 Schema 约束输出，100% 固定 JSON 格式
- **多数据库支持**：支持 SQLite / MySQL / PostgreSQL 三种数据库接入
- **FastAPI 接口**：对外暴露 REST API，适配企业内部系统调用
- **全链路日志**：记录任务拆解记录、工具返回值、反思校验日志
- **智能缓存**：Redis 缓存支持，提升查询性能
- **全链路监控**：集成 Prometheus 指标收集和 LangFuse LLM 追踪
- **客户管理**：客户画像、跟进记录管理
- **NL2SQL**：自然语言转 SQL 查询服务

## 技术栈

- **开发语言**：Python 3.10+
- **Agent 框架**：LlamaIndex Agent
- **大模型**：OpenAI GPT-3.5 / Qwen-7B/14B (Ollama)
- **Web 框架**：FastAPI
- **数据库**：SQLite / MySQL / PostgreSQL / Chroma 向量数据库 / Redis（可选）
- **数据验证**：Pydantic v2
- **测试框架**：Pytest
- **监控**：Prometheus + LangFuse
- **Embedding**：BGE-small-zh-v1.5（本地部署）

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository_url>
cd CRM-sale-Agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 如果使用 MySQL，安装 pymysql
pip install pymysql

# 如果使用 PostgreSQL，安装 psycopg2
pip install psycopg2-binary
```

### 2. 配置文件

复制 `.env.sample` 文件为 `.env` 并修改配置：

```bash
# 大模型模式选择（openai 或 qwen）
LLM_MODE=openai

# OpenAI 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 或使用本地 Qwen
LLM_MODE=qwen
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

### 3. 启动服务

```bash
# 启动 FastAPI 服务
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问接口文档

启动后访问：
- API 文档：http://localhost:8000/docs
- 前端页面：http://localhost:8000/
- 监控指标：http://localhost:8000/metrics（需启用 Prometheus）

## 企业数据库接入

### 数据库类型支持

系统支持三种数据库类型，通过 `DB_TYPE` 配置切换：

| 数据库类型 | 配置值 | 适用场景 |
|-----------|--------|----------|
| SQLite | `sqlite` | 开发测试、单机部署 |
| MySQL | `mysql` | 企业生产环境、高并发 |
| PostgreSQL | `postgresql` | 企业生产环境、复杂查询 |

### 配置示例

#### SQLite（默认）

```env
DB_TYPE=sqlite
SQLITE_DB_PATH=./storage/sqlite/sales_agent.db
```

#### MySQL

```env
DB_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=sales_agent
```

#### PostgreSQL

```env
DB_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=sales_agent
```

### 数据库表结构

系统需要以下四张表，可通过 `scripts/generate_crm_data.py` 生成示例数据：

#### products（产品表）

| 字段 | 类型 | 说明 |
|------|------|------|
| product_sku | TEXT | 产品SKU（唯一） |
| product_name | TEXT | 产品名称 |
| category | TEXT | 产品品类 |
| base_price | REAL | 基准价格 |
| unit | TEXT | 计量单位 |
| description | TEXT | 产品描述 |

#### inventory（库存表）

| 字段 | 类型 | 说明 |
|------|------|------|
| product_sku | TEXT | 产品SKU（外键） |
| product_name | TEXT | 产品名称 |
| stock_quantity | INTEGER | 库存总量 |
| available_quantity | INTEGER | 可用库存 |
| reserved_quantity | INTEGER | 预留库存 |
| lead_time | TEXT | 备货周期 |
| warehouse_location | TEXT | 仓库位置 |
| unit | TEXT | 计量单位 |

#### customers（客户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| customer_id | TEXT | 客户ID（唯一） |
| customer_name | TEXT | 客户名称 |
| industry | TEXT | 所属行业 |
| contact_person | TEXT | 联系人 |
| contact_phone | TEXT | 联系电话 |
| address | TEXT | 地址 |
| credit_level | TEXT | 信用等级（A/B/C/D） |

#### deal_records（成交记录表）

| 字段 | 类型 | 说明 |
|------|------|------|
| deal_id | TEXT | 成交ID（唯一） |
| product_sku | TEXT | 产品SKU |
| product_name | TEXT | 产品名称 |
| customer_id | TEXT | 客户ID |
| customer_name | TEXT | 客户名称 |
| industry | TEXT | 行业 |
| quantity | INTEGER | 采购数量 |
| unit_price | REAL | 成交单价 |
| total_amount | REAL | 成交金额 |
| discount_rate | REAL | 折扣率 |
| payment_terms | TEXT | 付款条件 |
| deal_date | TEXT | 成交日期 |
| sales_person | TEXT | 销售人员 |

### 数据与测试脚本

系统提供以下脚本用于数据生成、验证和测试：

#### 数据生成脚本

```bash
# 生成 CRM 数据（产品50条 + 库存50条 + 客户200条 + 成交记录1000条）
python scripts/generate_crm_data.py

# 验证数据完整性
python scripts/verify_data.py
```

#### 调试测试脚本

```bash
# 清空缓存（切换数据模式时使用）
python scripts/clear_cache.py

# 测试数据库查询功能
python scripts/test_db_query.py

# 测试查询匹配能力
python scripts/test_query.py

# 测试 API 响应
python scripts/test_api_response.py
```

### 接入企业自有数据库

#### 步骤 1：配置数据库连接

修改 `.env` 文件，设置 `DB_TYPE` 和相应的数据库连接参数：

```env
DB_TYPE=mysql  # 或 postgresql
MYSQL_HOST=your-db-host
MYSQL_PORT=3306
MYSQL_USER=your-user
MYSQL_PASSWORD=your-password
MYSQL_DB=your-database
```

#### 步骤 2：映射企业数据表

如果企业数据库表结构与系统默认结构不同，需要修改 `storage/db_connector.py` 中的查询方法：

```python
# 修改 get_inventory 方法适配企业库存表
def get_inventory(self, product_name: str) -> Optional[Dict[str, Any]]:
    sql = """
        SELECT your_product_name AS product_name,
               your_sku AS product_sku,
               your_stock AS stock_quantity,
               your_available AS available_quantity
        FROM your_inventory_table
        WHERE your_product_name LIKE ?
        LIMIT 1
    """
    # ...
```

#### 步骤 3：切换到真实数据模式

确保 `USE_MOCK_DATA` 设置为 `false`：

```env
USE_MOCK_DATA=false
```

#### 步骤 4：测试连接

启动服务后，系统会自动验证数据库连接：

```bash
# 检查健康状态
curl http://localhost:8000/api/health

# 测试数据库查询
curl http://localhost:8000/api/db/products
```

### 数据库连接器 API

系统提供统一的数据库连接器，支持以下业务操作：

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `get_inventory(product_name)` | 查询库存 | 产品名称 | 库存信息字典 |
| `get_price_info(product_name)` | 查询价格 | 产品名称 | 价格统计信息 |
| `get_product_list()` | 获取产品列表 | 无 | 产品列表 |
| `get_customer_info(customer_id)` | 查询客户 | 客户ID | 客户信息字典 |
| `get_recent_deals(product_name, limit)` | 获取成交记录 | 产品名称、数量限制 | 成交记录列表 |
| `query(sql, params)` | 通用查询 | SQL语句、参数 | 查询结果 |
| `execute(sql, params)` | 执行SQL | SQL语句、参数 | 受影响行数 |

### 数据安全性

1. **敏感信息隔离**：数据库密码通过环境变量配置，禁止硬编码
2. **只读查询**：API接口默认仅支持查询操作，无写权限
3. **参数化查询**：所有数据库操作使用参数化查询，防止SQL注入
4. **连接池管理**：自动管理数据库连接，防止连接泄漏
5. **日志脱敏**：日志中不记录敏感信息（如密码）

## 项目结构

```
CRM-sale-Agent/
├── .env                        # 环境配置
├── .env.sample                 # 环境配置示例
├── requirements.txt            # 依赖清单
├── Dockerfile                   # Docker 部署文件
├── README.md                    # 项目说明
├── main.py                     # 服务启动入口
│
├── config/                     # 全局配置
│   ├── settings.py              # 配置管理与常量定义
│   └── __init__.py
│
├── core/                       # Agent 核心编排层
│   ├── llm_adapter.py           # 大模型适配器（OpenAI/Qwen）
│   ├── task_planner.py          # 任务拆解器
│   ├── tool_dispatcher.py       # 工具调度器
│   ├── reflection_engine.py     # 反思验真引擎
│   ├── sales_agent.py           # Agent 主入口
│   └── __init__.py
│
├── schemas/                    # 数据模型定义
│   ├── output_schema.py         # Pydantic 输出模型
│   └── __init__.py
│
├── tools/                      # 可插拔工具集合
│   ├── base_tool.py             # 工具抽象基类
│   ├── calculator_tool.py       # 计算器工具
│   ├── api_inventory_tool.py    # 库存查询工具
│   ├── sql_price_tool.py        # 价格查询工具
│   ├── doc_retrieve_tool.py     # 文档检索工具（RAG）
│   ├── wechat_notify_tool.py    # 企业微信通知工具
│   └── __init__.py
│
├── services/                   # 业务服务层
│   ├── customer_service.py      # 客户管理服务
│   ├── cache_manager.py         # Redis 缓存管理器
│   ├── monitoring_service.py    # Prometheus 监控服务
│   ├── nl2sql_service.py        # NL2SQL 自然语言查询
│   ├── pdf_generator.py         # PDF 生成服务
│   ├── langfuse/                # LangFuse 监控
│   │   ├── langfuse_monitor.py
│   │   └── __init__.py
│   └── __init__.py
│
├── storage/                    # 持久化存储
│   ├── db_connector.py          # 数据库连接器（多数据库支持）
│   ├── init_sql.py              # SQL 数据库初始化
│   ├── init_vector_db.py        # 向量数据库初始化
│   ├── sqlite/                  # SQLite 数据库文件
│   └── chroma_db/               # Chroma 向量库文件
│
├── api/                        # FastAPI 路由层
│   ├── chat_route.py            # 销售咨询路由
│   └── __init__.py
│
├── frontend/                   # 前端调试页面
│   └── index.html
│
├── scripts/                    # 数据管理脚本
│   ├── generate_crm_data.py     # CRM数据批量生成
│   ├── verify_data.py           # 数据验证
│   ├── clear_cache.py           # 缓存清空脚本
│   ├── test_api_response.py     # API响应测试脚本
│   ├── test_query.py            # 查询匹配测试脚本
│   └── test_db_query.py         # 数据库查询测试脚本
│
├── tests/                      # 测试用例
│   ├── test_agent_flow.py       # Agent 流程测试
│   ├── test_api.py              # API 接口测试
│   ├── test_tools.py            # 工具单元测试
│   ├── test_reflection.py       # 反思验真测试
│   ├── test_llm_adapter.py      # LLM 适配器测试
│   ├── test_monitor.py          # 监控测试
│   └── __init__.py
│
├── docs/                       # 业务文档库
│
└── logs/                       # 日志文件目录
    └── sales_agent.log
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
  "message": "销售方案生成成功",
  "inventory": {
    "product_name": "工业风机",
    "product_sku": "SKU-2024-0001",
    "stock_quantity": 351,
    "available_quantity": 222,
    "lead_time": "11天",
    "warehouse_location": "西北仓库"
  },
  "pricing": {
    "unit_price": 8198.15,
    "quantity": 50,
    "total_price": 377114.75,
    "discount_rate": 0.08,
    "payment_terms": "30天账期",
    "currency": "CNY"
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
    "summary": "基于当前库存和往期成交案例...",
    "pricing_strategy": "定价策略说明",
    "inventory_assurance": "库存保障说明",
    "payment_recommendation": "付款方式建议",
    "competitive_advantage": "竞争优势说明",
    "next_steps": ["后续行动建议1", "后续行动建议2"],
    "risk_warnings": ["风险提示1", "风险提示2"]
  },
  "reflection_report": {
    "enabled": true,
    "overall_confidence": 0.92,
    "verified_fields": ["stock_quantity", "unit_price"],
    "warnings": []
  },
  "task_logs": [...],
  "customer_id": "C001",
  "query": "采购50台工业风机...",
  "product_category": "工业风机",
  "timestamp": "2024-01-20T10:30:00"
}
```

### 数据库查询接口

```bash
# 获取产品列表
GET /api/db/products

# 获取库存信息
GET /api/db/inventory?product_name=工业风机

# 获取客户列表
GET /api/db/customers

# 获取成交记录
GET /api/db/deals?product_name=工业风机&limit=10
```

### 其他接口

```bash
# 健康检查
GET /api/health

# 统计信息
GET /api/stats

# 工具列表
GET /api/tools

# Prometheus 监控指标
GET /metrics
```

## 模型切换

### 使用 OpenAI

```env
LLM_MODE=openai
OPENAI_API_KEY=your_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo
```

### 使用本地 Qwen

```env
LLM_MODE=qwen
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen:7b
```

## Docker 部署

### 构建镜像

```bash
# 构建镜像
docker build -t sales-agent:latest .

# 或使用 docker-compose
docker-compose build
```

### 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f sales-agent

# 停止服务
docker-compose down
```

### Docker Compose 配置示例

```yaml
version: '3.8'

services:
  sales-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_MODE=qwen
      - OLLAMA_BASE_URL=http://ollama:11434
      - DB_TYPE=mysql
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - MYSQL_USER=sales_agent
      - MYSQL_PASSWORD=your_password
      - MYSQL_DB=sales_agent
      - REDIS_ENABLED=true
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - mysql
      - redis
      - ollama
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs

  mysql:
    image: mysql:8.0
    ports:
      - "3306:3306"
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=sales_agent
      - MYSQL_USER=sales_agent
      - MYSQL_PASSWORD=your_password
    volumes:
      - mysql_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  mysql_data:
  redis_data:
  ollama_data:
```

## 监控与日志

### Prometheus 监控

启用 Prometheus 监控后，访问 `/metrics` 端点获取指标：

- 请求总数、响应时间、并发数
- 工具调用次数、成功率、耗时
- LLM 调用次数、Token 消耗、成本统计
- 缓存命中率、错误率

### LangFuse LLM 追踪

配置 LangFuse 后，可追踪：

- LLM 调用链路
- Token 使用量
- 成本分析
- 调试信息

### 日志配置

日志文件位于 `logs/sales_agent.log`，支持：

- 按大小轮转（10MB）
- 按时间保留（30天）
- 自动压缩归档
- 多级别输出（DEBUG/INFO/WARNING/ERROR）

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_tools.py -v

# 带覆盖率
pytest tests/ --cov=. --cov-report=html

# 运行异步测试
pytest tests/test_agent_flow.py -v
```

## 扩展开发

### 新增工具

继承 `BaseTool` 基类实现自定义工具：

```python
from tools.base_tool import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            tool_name="my_custom_tool",
            tool_description="自定义工具描述"
        )

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        result = await self._do_something(**kwargs)
        return ToolResult(
            status="success",
            data=result,
            message="执行成功"
        )
```

### 新增服务

在 `services/` 目录下创建服务模块：

```python
from loguru import logger

class MyService:
    def __init__(self):
        logger.info("服务初始化")

    async def process(self, data):
        # 实现服务逻辑
        pass
```

## 注意事项

1. **数据安全**：本地 Qwen 模式所有客户数据、报价文档不出服务器
2. **密钥管理**：云端模式密钥通过环境变量隔离，禁止硬编码
3. **企业数据库**：生产环境需配置 `DB_TYPE` 为 `mysql` 或 `postgresql`，并设置 `USE_MOCK_DATA=false`
4. **表结构适配**：如果企业数据库表结构与系统默认不同，需修改 `storage/db_connector.py` 中的查询方法
5. **扩展性**：新增工具仅需实现统一工具基类，无需改写 Agent 主流程
6. **性能优化**：建议启用 Redis 缓存以提升查询性能
7. **监控告警**：生产环境建议启用 Prometheus 和 LangFuse 监控

## 常见问题

### 1. 如何切换大模型？

修改 `.env` 文件中的 `LLM_MODE` 配置，可选 `openai` 或 `qwen`。

### 2. 如何接入企业数据库？

1. 设置 `DB_TYPE=mysql` 或 `DB_TYPE=postgresql`
2. 配置相应的数据库连接参数
3. 设置 `USE_MOCK_DATA=false`
4. 如果表结构不同，修改 `storage/db_connector.py`

### 3. 如何生成测试数据？

运行 `python scripts/generate_crm_data.py` 生成 1000+ 条 CRM 数据。

### 4. 如何启用缓存？

设置 `REDIS_ENABLED=true` 并配置 Redis 连接信息。

### 5. 如何添加新的业务文档？

将文档（支持 .md/.txt/.pdf/.docx）放入 `docs/` 目录，然后运行：
```bash
python storage/init_vector_db.py
```

### 6. 如何查看监控指标？

访问 `http://localhost:8000/metrics` 查看 Prometheus 指标。

### 7. 如何调试 LLM 调用？

启用 LangFuse 监控，在 LangFuse 控制台查看详细调用链路。

### 8. scripts/ 目录有哪些脚本？

| 脚本文件 | 功能 | 使用场景 |
|---------|------|---------|
| `generate_crm_data.py` | 批量生成 CRM 测试数据 | 开发测试、演示数据准备 |
| `verify_data.py` | 验证数据库数据完整性 | 数据生成后验证 |
| `clear_cache.py` | 清空 Redis/内存缓存 | 切换数据模式时清理缓存 |
| `test_db_query.py` | 测试数据库查询功能 | 验证数据库连接器 |
| `test_query.py` | 测试查询匹配能力 | 调试产品名称模糊匹配 |
| `test_api_response.py` | 测试 API 响应 | 验证销售咨询接口 |

### 9. 如何使用降级方案？

当 LLM 调用失败时，系统会自动切换到基于数据库数据的降级方案，无需额外配置。降级方案会根据库存、价格数据生成基础销售方案。

## 许可证

MIT License

## 贡献指南

欢迎提交 Issue 和 Pull Request。在提交 PR 前，请确保：

1. 代码通过所有测试
2. 遵循项目代码规范
3. 更新相关文档
4. 添加必要的测试用例

## 联系方式

QQ:582366076@qq.com
如有问题或建议，请提交 Issue 或联系项目维护者。

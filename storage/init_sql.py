"""
SQLite 数据库初始化脚本
创建产品信息表、历史成交订单表，并插入模拟数据
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
from loguru import logger

from config.settings import settings


def init_sql_database():
    """
    初始化 SQLite 数据库
    创建表结构并插入模拟数据
    """
    db_path = Path(settings.SQLITE_DB_PATH)
    
    # 确保目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"开始初始化 SQLite 数据库: {db_path}")
    
    # 连接数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 创建产品信息表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT,
            base_price REAL NOT NULL,
            unit TEXT,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建库存表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_sku TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            stock_quantity INTEGER DEFAULT 0,
            available_quantity INTEGER DEFAULT 0,
            reserved_quantity INTEGER DEFAULT 0,
            lead_time TEXT,
            warehouse_location TEXT,
            unit TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_sku) REFERENCES products(product_sku)
        )
    """)
    
    # 创建历史成交订单表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS deal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deal_id TEXT UNIQUE NOT NULL,
            product_sku TEXT NOT NULL,
            product_name TEXT NOT NULL,
            customer_id TEXT,
            customer_name TEXT,
            industry TEXT,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_amount REAL NOT NULL,
            discount_rate REAL DEFAULT 0,
            payment_terms TEXT,
            deal_date TEXT NOT NULL,
            sales_person TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建客户档案表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            industry TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            address TEXT,
            credit_level TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 插入模拟产品数据
    products_data = [
        ("IF-2024-001", "工业风机", "工业设备", 8500.0, "台", "高效工业通风设备"),
        ("CP-2024-002", "离心泵", "工业设备", 3200.0, "台", "高流量离心泵"),
        ("CM-2024-003", "压缩机", "工业设备", 15000.0, "台", "高压空气压缩机"),
        ("EM-2024-004", "电机", "工业设备", 1200.0, "台", "高效节能电机"),
        ("VL-2024-005", "阀门", "工业设备", 350.0, "个", "工业控制阀门"),
        ("BL-2024-006", "锅炉", "工业设备", 50000.0, "台", "工业蒸汽锅炉"),
        ("TN-2024-007", "变压器", "电力设备", 8000.0, "台", "高压变压器"),
        ("SW-2024-008", "开关柜", "电力设备", 15000.0, "台", "低压开关柜")
    ]
    
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO products (product_sku, product_name, category, base_price, unit, description) VALUES (?, ?, ?, ?, ?, ?)",
            products_data
        )
        logger.info(f"插入 {len(products_data)} 个产品数据")
    
    # 插入模拟库存数据
    inventory_data = [
        ("IF-2024-001", "工业风机", 120, 50, 70, "7天", "华东仓库", "台"),
        ("CP-2024-002", "离心泵", 80, 30, 50, "10天", "华南仓库", "台"),
        ("CM-2024-003", "压缩机", 45, 20, 25, "15天", "华北仓库", "台"),
        ("EM-2024-004", "电机", 200, 150, 50, "5天", "华东仓库", "台"),
        ("VL-2024-005", "阀门", 500, 400, 100, "3天", "华南仓库", "个"),
        ("BL-2024-006", "锅炉", 15, 5, 10, "30天", "华北仓库", "台"),
        ("TN-2024-007", "变压器", 30, 15, 15, "20天", "华东仓库", "台"),
        ("SW-2024-008", "开关柜", 25, 10, 15, "25天", "华南仓库", "台")
    ]
    
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO inventory (product_sku, product_name, stock_quantity, available_quantity, reserved_quantity, lead_time, warehouse_location, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            inventory_data
        )
        logger.info(f"插入 {len(inventory_data)} 个库存数据")
    
    # 插入模拟成交记录数据
    deal_records_data = generate_mock_deal_records()
    
    cursor.execute("SELECT COUNT(*) FROM deal_records")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO deal_records 
               (deal_id, product_sku, product_name, customer_id, customer_name, industry, 
                quantity, unit_price, total_amount, discount_rate, payment_terms, deal_date, 
                sales_person, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            deal_records_data
        )
        logger.info(f"插入 {len(deal_records_data)} 个成交记录")
    
    # 插入模拟客户数据
    customers_data = [
        ("C-001", "某大型制造企业", "汽车制造", "张经理", "13800138001", "上海市", "A级"),
        ("C-002", "某化工企业", "化工", "李总", "13900139002", "江苏省", "A级"),
        ("C-003", "某电力公司", "电力", "王主任", "13700137003", "浙江省", "A级"),
        ("C-004", "某钢铁企业", "钢铁", "赵经理", "13600136004", "河北省", "B级"),
        ("C-005", "某纺织企业", "纺织", "孙总", "13500135005", "广东省", "B级"),
        ("C-006", "某食品企业", "食品", "周经理", "13400134006", "四川省", "A级"),
        ("C-007", "某建材企业", "建材", "吴总", "13300133007", "湖北省", "B级"),
        ("C-008", "某电子企业", "电子", "郑经理", "13200132008", "北京市", "A级")
    ]
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            """INSERT INTO customers 
               (customer_id, customer_name, industry, contact_person, contact_phone, address, credit_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            customers_data
        )
        logger.info(f"插入 {len(customers_data)} 个客户数据")
    
    # 提交并关闭
    conn.commit()
    conn.close()
    
    logger.info("SQLite 数据库初始化完成")


def generate_mock_deal_records() -> list:
    """
    生成模拟成交记录数据
    
    Returns:
        成交记录列表
    """
    records = []
    base_date = datetime.now() - timedelta(days=180)  # 近6个月
    
    # 产品和客户映射
    products = [
        ("IF-2024-001", "工业风机", 8500.0),
        ("CP-2024-002", "离心泵", 3200.0),
        ("CM-2024-003", "压缩机", 15000.0),
        ("EM-2024-004", "电机", 1200.0),
        ("VL-2024-005", "阀门", 350.0)
    ]
    
    customers = [
        ("C-001", "某大型制造企业", "汽车制造"),
        ("C-002", "某化工企业", "化工"),
        ("C-003", "某电力公司", "电力"),
        ("C-004", "某钢铁企业", "钢铁"),
        ("C-005", "某纺织企业", "纺织")
    ]
    
    payment_terms_options = ["款到发货", "30天账期", "60天账期", "分期付款"]
    sales_persons = ["张销售", "李销售", "王销售", "赵销售"]
    
    # 生成30条成交记录
    for i in range(30):
        deal_id = f"D-2024-{i+1:03d}"
        
        # 随机选择产品和客户
        product = random.choice(products)
        customer = random.choice(customers)
        
        # 随机数量和折扣
        quantity = random.randint(10, 100)
        base_price = product[2]
        
        # 根据数量计算折扣
        if quantity >= 50:
            discount_rate = 0.08
        elif quantity >= 30:
            discount_rate = 0.05
        elif quantity >= 10:
            discount_rate = 0.03
        else:
            discount_rate = 0.0
        
        # 计算价格
        unit_price = base_price * (1 - discount_rate)
        total_amount = unit_price * quantity
        
        # 随机日期（近6个月）
        deal_date = base_date + timedelta(days=random.randint(0, 180))
        
        # 随机付款条件
        payment_terms = random.choice(payment_terms_options)
        
        # 随机销售人员
        sales_person = random.choice(sales_persons)
        
        # 备注
        notes = f"{customer[1]}采购{quantity}台{product[1]}"
        
        record = (
            deal_id,
            product[0],
            product[1],
            customer[0],
            customer[1],
            customer[2],
            quantity,
            round(unit_price, 2),
            round(total_amount, 2),
            discount_rate,
            payment_terms,
            deal_date.strftime("%Y-%m-%d"),
            sales_person,
            notes
        )
        
        records.append(record)
    
    return records


if __name__ == "__main__":
    init_sql_database()
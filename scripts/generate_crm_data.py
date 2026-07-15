"""
CRM数据库批量数据生成脚本
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import random
from loguru import logger
import sys
from faker import Faker

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings


class CRMDataGenerator:
    """CRM数据生成器"""
    
    def __init__(self):
        self.fake = Faker('zh_CN')
        self.db_path = Path(settings.SQLITE_DB_PATH)
        self.conn = None
        self.cursor = None
        
        # 行业列表
        self.industries = [
            "汽车制造", "化工", "电力", "钢铁", "纺织", "食品", "建材", "电子",
            "机械制造", "医药", "物流", "新能源", "环保", "冶金", "矿业",
            "造纸", "印刷", "橡胶", "塑料", "玻璃", "陶瓷", "航空航天",
            "船舶制造", "轨道交通", "石油石化", "煤炭", "天然气", "半导体"
        ]
        
        # 省份/城市列表
        self.cities = [
            "北京市", "上海市", "广州市", "深圳市", "杭州市", "南京市", "武汉市", "成都市",
            "重庆市", "天津市", "苏州市", "西安市", "长沙市", "沈阳市", "青岛市",
            "郑州市", "大连市", "东莞市", "宁波市", "厦门市", "合肥市", "佛山市",
            "无锡市", "济南市", "哈尔滨市", "福州市", "长春市", "石家庄市",
            "温州市", "南宁市", "常州市", "昆明市", "烟台市", "徐州市", "嘉兴市"
        ]
        
        # 仓库位置
        self.warehouses = ["华东仓库", "华南仓库", "华北仓库", "西南仓库", "西北仓库", "东北仓库"]
        
        # 付款条件
        self.payment_terms = ["款到发货", "30天账期", "60天账期", "90天账期", "分期付款"]
        
        # 销售人员
        self.sales_persons = [
            "张伟", "李明", "王芳", "刘洋", "陈静", "赵强", "孙丽", "周伟",
            "吴敏", "郑浩", "黄婷", "林涛", "何杰", "罗敏", "谢辉", "韩雪"
        ]
        
        # 信用等级
        self.credit_levels = ["A级", "B级", "C级", "D级"]
        
    def connect(self):
        """连接数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()
        logger.info(f"连接数据库: {self.db_path}")
    
    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.commit()
            self.conn.close()
            logger.info("数据库连接已关闭")
    
    def generate_products(self, count: int = 50) -> list:
        """
        生成产品数据
        
        Args:
            count: 产品数量
            
        Returns:
            产品数据列表
        """
        records = []
        
        # 产品模板
        product_templates = [
            ("工业风机", "工业设备", 8500.0, "台", "高效工业通风设备"),
            ("离心泵", "工业设备", 3200.0, "台", "高流量离心泵"),
            ("压缩机", "工业设备", 15000.0, "台", "高压空气压缩机"),
            ("电机", "工业设备", 1200.0, "台", "高效节能电机"),
            ("阀门", "工业设备", 350.0, "个", "工业控制阀门"),
            ("锅炉", "工业设备", 50000.0, "台", "工业蒸汽锅炉"),
            ("变压器", "电力设备", 8000.0, "台", "高压变压器"),
            ("开关柜", "电力设备", 15000.0, "台", "低压开关柜"),
            ("电缆", "电力设备", 800.0, "米", "高压电缆"),
            ("配电柜", "电力设备", 3500.0, "台", "低压配电柜"),
            ("传感器", "电子设备", 500.0, "个", "工业传感器"),
            ("PLC控制器", "电子设备", 2500.0, "台", "可编程控制器"),
            ("变频器", "电子设备", 1800.0, "台", "变频调速器"),
            ("触摸屏", "电子设备", 1200.0, "台", "工业触摸屏"),
            ("伺服电机", "电子设备", 3500.0, "台", "伺服驱动电机"),
            ("减速机", "机械传动", 2000.0, "台", "齿轮减速机"),
            ("轴承", "机械传动", 150.0, "个", "滚动轴承"),
            ("联轴器", "机械传动", 300.0, "个", "弹性联轴器"),
            ("液压泵", "液压气动", 4500.0, "台", "高压液压泵"),
            ("气缸", "液压气动", 200.0, "个", "气动气缸"),
            ("电磁阀", "液压气动", 150.0, "个", "电磁换向阀"),
            ("过滤器", "液压气动", 100.0, "个", "液压过滤器"),
            ("流量计", "仪器仪表", 2000.0, "台", "电磁流量计"),
            ("压力表", "仪器仪表", 200.0, "个", "精密压力表"),
            ("温度计", "仪器仪表", 150.0, "个", "工业温度计"),
            ("液位计", "仪器仪表", 1800.0, "台", "液位测量仪"),
            ("安全阀", "安防设备", 800.0, "个", "安全泄压阀"),
            ("灭火器", "安防设备", 150.0, "个", "干粉灭火器"),
            ("报警器", "安防设备", 300.0, "个", "烟雾报警器"),
            ("监控摄像头", "安防设备", 500.0, "个", "高清监控摄像头"),
            ("叉车", "物流设备", 80000.0, "台", "电动叉车"),
            ("输送带", "物流设备", 500.0, "米", "工业输送带"),
            ("货架", "物流设备", 300.0, "组", "仓储货架"),
            ("托盘", "物流设备", 50.0, "个", "塑料托盘"),
            ("叉车电池", "物流设备", 5000.0, "个", "叉车蓄电池"),
            ("空压机", "压缩设备", 12000.0, "台", "螺杆空压机"),
            ("储气罐", "压缩设备", 3000.0, "个", "空气储气罐"),
            ("干燥机", "压缩设备", 2000.0, "台", "空气干燥机"),
            ("精密空调", "环境设备", 20000.0, "台", "机房精密空调"),
            ("加湿器", "环境设备", 500.0, "台", "工业加湿器"),
            ("除湿机", "环境设备", 800.0, "台", "工业除湿机"),
            ("冷水机", "环境设备", 15000.0, "台", "工业冷水机"),
            ("冷却塔", "环境设备", 8000.0, "台", "工业冷却塔"),
            ("除尘设备", "环保设备", 25000.0, "台", "工业除尘器"),
            ("废气处理", "环保设备", 50000.0, "台", "废气处理设备"),
            ("污水处理", "环保设备", 80000.0, "台", "污水处理设备"),
            ("风机盘管", "暖通设备", 1500.0, "台", "风机盘管"),
            ("新风系统", "暖通设备", 5000.0, "台", "新风换气系统"),
            ("空气净化器", "暖通设备", 2000.0, "台", "工业空气净化器"),
            ("散热器", "暖通设备", 300.0, "个", "工业散热器")
        ]
        
        for i in range(count):
            if i < len(product_templates):
                name, category, price, unit, desc = product_templates[i]
            else:
                # 随机生成产品
                name = self.fake.word() + random.choice(["设备", "仪器", "系统", "配件", "组件"])
                category = random.choice(["工业设备", "电力设备", "电子设备", "机械传动", "仪器仪表"])
                price = round(random.uniform(100, 100000), 2)
                unit = random.choice(["台", "个", "米", "组", "套"])
                desc = f"{name}，{self.fake.text(max_nb_chars=20)}"
            
            sku = f"SKU-{2024}-{i+1:04d}"
            records.append((sku, name, category, price, unit, desc))
        
        return records
    
    def generate_inventory(self, products: list) -> list:
        """
        生成库存数据
        
        Args:
            products: 产品数据列表
            
        Returns:
            库存数据列表
        """
        records = []
        
        for sku, name, _, _, unit, _ in products:
            stock_qty = random.randint(10, 500)
            reserved_qty = random.randint(0, stock_qty // 2)
            available_qty = stock_qty - reserved_qty
            lead_time = f"{random.randint(3, 30)}天"
            warehouse = random.choice(self.warehouses)
            
            records.append((sku, name, stock_qty, available_qty, reserved_qty, lead_time, warehouse, unit))
        
        return records
    
    def generate_customers(self, count: int = 200) -> list:
        """
        生成客户数据
        
        Args:
            count: 客户数量
            
        Returns:
            客户数据列表
        """
        records = []
        
        company_prefixes = [
            "中国", "华夏", "东方", "南方", "北方", "西部", "华北", "华东", "华南", "西南",
            "北京", "上海", "广州", "深圳", "杭州", "南京", "武汉", "成都", "重庆", "天津"
        ]
        
        company_suffixes = [
            "科技有限公司", "实业有限公司", "集团有限公司", "贸易有限公司",
            "制造有限公司", "发展有限公司", "投资有限公司", "股份有限公司",
            "电子有限公司", "机械有限公司", "化工有限公司", "能源有限公司"
        ]
        
        for i in range(count):
            customer_id = f"C-{i+1:04d}"
            
            # 生成公司名称
            prefix = random.choice(company_prefixes)
            middle = self.fake.word()
            suffix = random.choice(company_suffixes)
            company_name = f"{prefix}{middle}{suffix}"
            
            industry = random.choice(self.industries)
            contact_person = self.fake.name()
            contact_phone = f"1{random.randint(3, 9)}{random.randint(0, 9):09d}"
            address = random.choice(self.cities)
            credit_level = random.choices(self.credit_levels, weights=[0.3, 0.4, 0.2, 0.1])[0]
            
            records.append((customer_id, company_name, industry, contact_person, contact_phone, address, credit_level))
        
        return records
    
    def generate_deal_records(self, products: list, customers: list, count: int = 1000) -> list:
        """
        生成成交记录数据
        
        Args:
            products: 产品数据列表
            customers: 客户数据列表
            count: 成交记录数量
            
        Returns:
            成交记录数据列表
        """
        records = []
        base_date = datetime.now() - timedelta(days=365)  # 近1年
        
        for i in range(count):
            deal_id = f"D-{datetime.now().year}-{i+1:05d}"
            
            # 随机选择产品和客户
            product = random.choice(products)
            customer = random.choice(customers)
            
            sku = product[0]
            product_name = product[1]
            base_price = product[3]
            customer_id = customer[0]
            customer_name = customer[1]
            industry = customer[2]
            
            # 根据客户信用等级和数量计算折扣
            credit_level = customer[6]
            quantity = random.randint(1, 200)
            
            # 折扣规则
            if credit_level == "A级":
                if quantity >= 100:
                    discount_rate = random.uniform(0.08, 0.15)
                elif quantity >= 50:
                    discount_rate = random.uniform(0.05, 0.08)
                elif quantity >= 10:
                    discount_rate = random.uniform(0.02, 0.05)
                else:
                    discount_rate = random.uniform(0, 0.02)
            elif credit_level == "B级":
                if quantity >= 100:
                    discount_rate = random.uniform(0.05, 0.10)
                elif quantity >= 50:
                    discount_rate = random.uniform(0.03, 0.05)
                elif quantity >= 10:
                    discount_rate = random.uniform(0.01, 0.03)
                else:
                    discount_rate = 0
            else:
                if quantity >= 100:
                    discount_rate = random.uniform(0.02, 0.05)
                elif quantity >= 50:
                    discount_rate = random.uniform(0.01, 0.02)
                else:
                    discount_rate = 0
            
            # 计算价格
            unit_price = round(base_price * (1 - discount_rate), 2)
            total_amount = round(unit_price * quantity, 2)
            
            # 随机日期（近1年）
            deal_date = base_date + timedelta(days=random.randint(0, 365))
            
            # 随机付款条件（根据信用等级加权）
            if credit_level == "A级":
                payment_terms = random.choices(
                    self.payment_terms, 
                    weights=[0.1, 0.4, 0.3, 0.15, 0.05]
                )[0]
            elif credit_level == "B级":
                payment_terms = random.choices(
                    self.payment_terms, 
                    weights=[0.3, 0.4, 0.2, 0.08, 0.02]
                )[0]
            else:
                payment_terms = random.choices(
                    self.payment_terms, 
                    weights=[0.6, 0.3, 0.08, 0.02, 0]
                )[0]
            
            # 随机销售人员
            sales_person = random.choice(self.sales_persons)
            
            # 备注
            notes = f"{customer_name}采购{quantity}{product[4]}{product_name}"
            
            records.append((
                deal_id,
                sku,
                product_name,
                customer_id,
                customer_name,
                industry,
                quantity,
                unit_price,
                total_amount,
                round(discount_rate, 4),
                payment_terms,
                deal_date.strftime("%Y-%m-%d"),
                sales_person,
                notes
            ))
        
        return records
    
    def clear_existing_data(self):
        """清除现有数据（保留表结构）"""
        logger.info("清除现有数据...")
        
        tables = ["deal_records", "inventory", "customers", "products"]
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
            self.cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        
        logger.info("现有数据已清除")
    
    def insert_products(self, products: list):
        """插入产品数据"""
        logger.info(f"插入 {len(products)} 条产品数据...")
        self.cursor.executemany(
            "INSERT INTO products (product_sku, product_name, category, base_price, unit, description) VALUES (?, ?, ?, ?, ?, ?)",
            products
        )
        logger.info("产品数据插入完成")
    
    def insert_inventory(self, inventory: list):
        """插入库存数据"""
        logger.info(f"插入 {len(inventory)} 条库存数据...")
        self.cursor.executemany(
            "INSERT INTO inventory (product_sku, product_name, stock_quantity, available_quantity, reserved_quantity, lead_time, warehouse_location, unit) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            inventory
        )
        logger.info("库存数据插入完成")
    
    def insert_customers(self, customers: list):
        """插入客户数据"""
        logger.info(f"插入 {len(customers)} 条客户数据...")
        self.cursor.executemany(
            "INSERT INTO customers (customer_id, customer_name, industry, contact_person, contact_phone, address, credit_level) VALUES (?, ?, ?, ?, ?, ?, ?)",
            customers
        )
        logger.info("客户数据插入完成")
    
    def insert_deal_records(self, deals: list, batch_size: int = 100):
        """插入成交记录数据（分批插入）"""
        logger.info(f"插入 {len(deals)} 条成交记录数据...")
        
        for i in range(0, len(deals), batch_size):
            batch = deals[i:i+batch_size]
            self.cursor.executemany(
                """INSERT INTO deal_records 
                   (deal_id, product_sku, product_name, customer_id, customer_name, industry, 
                    quantity, unit_price, total_amount, discount_rate, payment_terms, deal_date, 
                    sales_person, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                batch
            )
            self.conn.commit()
            logger.info(f"已插入 {min(i+batch_size, len(deals))}/{len(deals)} 条成交记录")
        
        logger.info("成交记录数据插入完成")
    
    def verify_data(self):
        """验证数据插入结果"""
        logger.info("验证数据插入结果...")
        
        tables = {
            "products": "产品",
            "inventory": "库存",
            "customers": "客户",
            "deal_records": "成交记录"
        }
        
        for table, name in tables.items():
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            logger.info(f"{name}表记录数: {count}")
        
        # 验证库存与产品关联
        self.cursor.execute("SELECT COUNT(*) FROM inventory WHERE product_sku NOT IN (SELECT product_sku FROM products)")
        orphan_inventory = self.cursor.fetchone()[0]
        if orphan_inventory > 0:
            logger.warning(f"发现 {orphan_inventory} 条库存记录未关联产品")
        else:
            logger.info("库存与产品关联验证通过")
        
        # 验证成交记录与产品、客户关联
        self.cursor.execute("SELECT COUNT(*) FROM deal_records WHERE product_sku NOT IN (SELECT product_sku FROM products)")
        orphan_deals_product = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM deal_records WHERE customer_id NOT IN (SELECT customer_id FROM customers)")
        orphan_deals_customer = self.cursor.fetchone()[0]
        
        if orphan_deals_product > 0:
            logger.warning(f"发现 {orphan_deals_product} 条成交记录未关联产品")
        else:
            logger.info("成交记录与产品关联验证通过")
        
        if orphan_deals_customer > 0:
            logger.warning(f"发现 {orphan_deals_customer} 条成交记录未关联客户")
        else:
            logger.info("成交记录与客户关联验证通过")
        
        logger.info("数据验证完成")
    
    def generate_all(self, product_count: int = 50, customer_count: int = 200, deal_count: int = 1000):
        """
        生成所有数据
        
        Args:
            product_count: 产品数量
            customer_count: 客户数量
            deal_count: 成交记录数量
        """
        logger.info("=" * 60)
        logger.info("开始生成CRM数据库数据")
        logger.info("=" * 60)
        
        try:
            self.connect()
            
            # 清除现有数据
            self.clear_existing_data()
            
            # 生成并插入数据
            products = self.generate_products(product_count)
            self.insert_products(products)
            
            inventory = self.generate_inventory(products)
            self.insert_inventory(inventory)
            
            customers = self.generate_customers(customer_count)
            self.insert_customers(customers)
            
            deals = self.generate_deal_records(products, customers, deal_count)
            self.insert_deal_records(deals)
            
            # 验证数据
            self.verify_data()
            
            logger.info("=" * 60)
            logger.info("CRM数据库数据生成完成")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"数据生成失败: {str(e)}")
            import traceback
            logger.error(f"错误堆栈:\n{traceback.format_exc()}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            self.disconnect()


if __name__ == "__main__":
    # 设置日志级别
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )
    
    # 创建生成器并生成数据
    generator = CRMDataGenerator()
    generator.generate_all(
        product_count=50,
        customer_count=200,
        deal_count=1000
    )
    
    print("\n数据生成完成！")
    print(f"产品: 50条")
    print(f"库存: 50条")
    print(f"客户: 200条")
    print(f"成交记录: 1000条")
    print(f"总计: 1300条")

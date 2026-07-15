import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from storage.db_connector import get_db_connector

db = get_db_connector()

print("=== 测试产品查询 ===")
products = db.get_product_list()
for p in products[:5]:
    print(f"SKU: {p['product_sku']}, 名称: {p['product_name']}, 价格: {p['base_price']}")

print("\n=== 测试库存查询 ===")
inventory = db.get_inventory("工业风机")
print(f"查询工业风机: {inventory}")

inventory = db.get_inventory("风机")
print(f"查询风机: {inventory}")

print("\n=== 测试价格查询 ===")
price = db.get_price_info("工业风机")
print(f"工业风机价格: {price}")

price = db.get_price_info("风机")
print(f"风机价格: {price}")

print("\n=== 测试案例查询 ===")
deals = db.get_recent_deals("工业风机", 3)
for d in deals:
    print(f"成交: {d['customer_name']}, 数量: {d['quantity']}, 单价: {d['unit_price']}")

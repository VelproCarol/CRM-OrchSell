import sqlite3
conn = sqlite3.connect('storage/sqlite/sales_agent.db')
conn.row_factory = sqlite3.Row

cursor = conn.cursor()

cursor.execute('SELECT * FROM products LIMIT 3')
products = cursor.fetchall()
print('=== 产品数据示例 ===')
for p in products:
    print(f'SKU: {p["product_sku"]}, 名称: {p["product_name"]}, 价格: {p["base_price"]}')

cursor.execute('SELECT * FROM inventory LIMIT 3')
inventory = cursor.fetchall()
print('=== 库存数据示例 ===')
for i in inventory:
    print(f'产品: {i["product_name"]}, 库存: {i["stock_quantity"]}, 可用: {i["available_quantity"]}')

cursor.execute('SELECT * FROM customers LIMIT 3')
customers = cursor.fetchall()
print('=== 客户数据示例 ===')
for c in customers:
    print(f'客户ID: {c["customer_id"]}, 名称: {c["customer_name"]}, 行业: {c["industry"]}')

cursor.execute('SELECT * FROM deal_records LIMIT 3')
deals = cursor.fetchall()
print('=== 成交记录示例 ===')
for d in deals:
    print(f'订单号: {d["deal_id"]}, 产品: {d["product_name"]}, 金额: {d["total_amount"]}, 日期: {d["deal_date"]}')

cursor.execute('SELECT COUNT(*) FROM products')
print(f'产品总数: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM inventory')
print(f'库存总数: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM customers')
print(f'客户总数: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM deal_records')
print(f'成交记录总数: {cursor.fetchone()[0]}')

conn.close()

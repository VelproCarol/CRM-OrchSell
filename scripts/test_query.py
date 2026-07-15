import sys
sys.path.insert(0, '.')

from storage.db_connector import get_db_connector
db = get_db_connector()

print('=== 测试不同查询词 ===')
queries = ['工业风机', '风机', '工业风', '风']
for q in queries:
    result = db.get_inventory(q)
    print(f'查询 \"{q}\": {result}')

print('\n=== 测试产品表 ===')
products = db.query('SELECT * FROM products WHERE product_name LIKE \"%工业风机%\"')
for p in products:
    print(f'产品: {p}')

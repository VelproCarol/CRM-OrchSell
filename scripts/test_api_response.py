import sys
import json
import urllib.request

sys.path.insert(0, '.')

url = "http://localhost:8000/api/chat/sales"
data = json.dumps({
    "customer_id": None,
    "product_category": "工业风机",
    "query": "采购50台工业风机，想要30天账期"
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode('utf-8'))
        
        print("=== 响应状态 ===")
        print(f"status: {result['status']}")
        print(f"message: {result['message']}")
        
        print("\n=== 库存信息 ===")
        if 'inventory' in result and result['inventory']:
            inv = result['inventory']
            print(json.dumps(inv, ensure_ascii=False, indent=2))
        else:
            print("库存信息为空")
        
        print("\n=== 价格信息 ===")
        if 'pricing' in result and result['pricing']:
            pricing = result['pricing']
            print(json.dumps(pricing, ensure_ascii=False, indent=2))
        else:
            print("价格信息为空")
        
        print("\n=== 案例信息 ===")
        if 'cases' in result and result['cases']:
            cases = result['cases'][:3]
            print(json.dumps(cases, ensure_ascii=False, indent=2))
        else:
            print("案例信息为空")
        
        print("\n=== 方案信息 ===")
        if 'proposal' in result and result['proposal']:
            proposal = result['proposal']
            print(json.dumps(proposal, ensure_ascii=False, indent=2))
        else:
            print("方案信息为空")
            
        print("\n=== 任务日志 ===")
        if 'task_logs' in result and result['task_logs']:
            for log in result['task_logs'][:3]:
                print(f"任务类型: {log['task_type']}")
                print(f"状态: {log['status']}")
                print(f"参数: {log['input_params']}")
                if log['output_result']:
                    print(f"输出: {json.dumps(log['output_result'], ensure_ascii=False)[:200]}")
                print()
                
except Exception as e:
    print(f"请求失败: {e}")

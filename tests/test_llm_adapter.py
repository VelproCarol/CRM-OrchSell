import asyncio
import sys
sys.path.insert(0, '.')

# 设置环境变量
import os
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-745c7877-a769-4695-ae61-c577a407069a"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-248252b8-a8ff-4cc4-9de7-23b3b25fefa8"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
os.environ["LANGFUSE_ENABLED"] = "true"

async def test_llm_adapter():
    from core.llm_adapter import LLMAdapter
    
    adapter = LLMAdapter()
    print(f"Adapter mode: {adapter._mode}")
    print(f"Model name: {adapter.model_name}")
    
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    
    # 调用 chat 方法
    result = await adapter.chat(messages, temperature=0.7)
    
    print(f"Response type: {type(result)}")
    print(f"Response: {result[:100] if isinstance(result, str) else result}")
    
    # 如果返回字典，检查结构
    if isinstance(result, dict):
        print(f"Has 'response': {'response' in result}")
        print(f"Has 'usage': {'usage' in result}")
        if 'usage' in result and result['usage']:
            print(f"Usage: {result['usage']}")

if __name__ == "__main__":
    asyncio.run(test_llm_adapter())
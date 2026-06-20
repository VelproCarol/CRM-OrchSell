import asyncio
import sys
sys.path.insert(0, '.')

# 设置环境变量
import os
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-745c7877-a769-4695-ae61-c577a407069a"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-248252b8-a8ff-4cc4-9de7-23b3b25fefa8"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
os.environ["LANGFUSE_ENABLED"] = "true"

async def test_monitor():
    from services.langfuse.langfuse_monitor import get_langfuse_monitor
    
    monitor = get_langfuse_monitor()
    print(f"Monitor enabled: {monitor.is_enabled()}")
    
    # 模拟 usage 数据
    messages = [{"role": "user", "content": "Hello World"}]
    response = "Hi there!"
    usage = {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
    
    # 调用监控
    result = monitor.trace_llm_call(
        model="test-model",
        messages=messages,
        response=response,
        usage=usage,
        latency=0.5
    )
    
    print(f"Generation result: {result}")
    if result:
        print(f"Generation ID: {result.id}")

if __name__ == "__main__":
    asyncio.run(test_monitor())
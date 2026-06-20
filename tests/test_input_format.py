import sys
sys.path.insert(0, '.')

# 设置环境变量
import os
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-745c7877-a769-4695-ae61-c577a407069a"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-248252b8-a8ff-4cc4-9de7-23b3b25fefa8"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"
os.environ["LANGFUSE_ENABLED"] = "true"

# 测试不同的 input/output 格式
from services.langfuse.langfuse_monitor import get_langfuse_monitor

monitor = get_langfuse_monitor()

# 测试1：使用字典格式的 input
messages = [{"role": "user", "content": "Hello World"}]
response = "Hi there!"
usage = {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}

# 使用字典格式的 input（与 LangFuse 文档示例一致）
result = monitor.trace_llm_call(
    model="test-model-dict",
    messages=messages,
    response=response,
    usage=usage,
    latency=0.5
)

print(f"Test 1 (dict format) - Generation ID: {result.id if result else 'None'}")

# 测试2：使用字符串格式的 input（当前代码使用的格式）
input_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in messages])
result2 = monitor.trace_llm_call(
    model="test-model-string",
    messages=messages,
    response=response,
    usage=usage,
    latency=0.5
)

print(f"Test 2 (string format) - Generation ID: {result2.id if result2 else 'None'}")
print(f"Input text: {repr(input_text)}")
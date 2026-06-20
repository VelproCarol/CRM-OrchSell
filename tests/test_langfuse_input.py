import os
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-745c7877-a769-4695-ae61-c577a407069a"
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-248252b8-a8ff-4cc4-9de7-23b3b25fefa8"
os.environ["LANGFUSE_HOST"] = "http://localhost:3000"

from langfuse import Langfuse
from langfuse.model import ModelUsage

lf = Langfuse()

# 模拟实际代码中的消息格式
messages = [{"role": "user", "content": "Hello World"}]
input_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in messages])
response = "Hi there!"

# 创建带 input 和 output 的 generation
trace = lf.trace(name="test-messages-format")
usage = ModelUsage(input=10, output=20, total=30)
gen = trace.generation(
    name="test-gen",
    model="test-model",
    input=input_text,
    output=response,
    usage=usage
)
lf.flush()
print("Generation created:", gen.id)
print("Input text:", repr(input_text))
print("Response:", repr(response))
print("Usage:", usage)
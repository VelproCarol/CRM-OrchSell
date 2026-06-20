"""
大模型适配器模块
统一封装 OpenAI 和 Ollama-Qwen 调用，对外提供一致接口
"""
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from loguru import logger

from config.settings import settings


class BaseLLMAdapter(ABC):
    """
    大模型适配器基类
    定义统一接口规范
    """
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            模型响应文本
        """
        pass
    
    @abstractmethod
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        带工具调用的聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            
        Returns:
            包含响应和工具调用的字典
        """
        pass


class OpenAIAdapter(BaseLLMAdapter):
    """
    OpenAI 大模型适配器
    """
    
    def __init__(self):
        """初始化 OpenAI 适配器"""
        from llama_index.llms.openai import OpenAI
        
        self.model_name = settings.OPENAI_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        
        # 检查 API 密钥是否配置
        if not self.api_key:
            logger.warning("OPENAI_API_KEY 未配置，将使用模拟模式")
            self._use_mock = True
        else:
            self._use_mock = False
            
            # 检查是否是智谱 AI 的 API（通过 API base URL 判断）
            is_zhipu_api = "bigmodel.cn" in self.api_base or "zhipu" in self.api_base
            
            if is_zhipu_api:
                # 智谱 AI 直接使用 openai 库，不通过 LlamaIndex
                logger.info(f"智谱 AI 适配器初始化完成，模型: {self.model_name}, API Base: {self.api_base}")
                self.llm = None  # 不使用 LlamaIndex 的 LLM 对象
            else:
                # 标准 OpenAI API
                self.llm = OpenAI(
                    model=self.model_name,
                    api_key=self.api_key,
                    api_base=self.api_base,
                    temperature=0.7
                )
                logger.info(f"OpenAI 适配器初始化完成，模型: {self.model_name}, API Base: {self.api_base}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        OpenAI 聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            响应文本
        """
        # 模拟模式
        if self._use_mock:
            return self._mock_response(messages)
        
        try:
            # 检查是否是智谱 AI
            is_zhipu_api = "bigmodel.cn" in self.api_base or "zhipu" in self.api_base
            
            if is_zhipu_api:
                # 使用智谱 AI 的 API（直接使用 openai 库）
                from openai import AsyncOpenAI
                client = AsyncOpenAI(api_key=self.api_key, base_url=self.api_base)
                
                response = await client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                content = response.choices[0].message.content
                logger.debug(f"智谱 AI 响应: {content[:100]}...")
                
                return content
            else:
                # 标准 OpenAI API
                from llama_index.core.llms import ChatMessage
                
                # 转换消息格式
                chat_messages = [
                    ChatMessage(role=msg["role"], content=msg["content"])
                    for msg in messages
                ]
                
                # 调用模型
                response = await self.llm.achat(
                    messages=chat_messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                logger.debug(f"OpenAI 响应: {response.message.content[:100]}...")
                
                return response.message.content
            
        except Exception as e:
            logger.error(f"OpenAI 调用失败: {str(e)}")
            raise
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """
        模拟 LLM 响应（当 API 密钥未配置时使用）
        
        Args:
            messages: 消息列表
            
        Returns:
            模拟的响应文本
        """
        import json
        import random
        
        # 获取用户消息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        logger.info(f"使用模拟 LLM 响应，内容: {user_message[:50]}...")
        
        # 根据消息内容生成模拟任务计划
        if "库存" in user_message or "产品" in user_message or "采购" in user_message:
            # 提取产品名称（简化处理）
            product_name = "工业风机"
            quantity = 50
            
            # 尝试从消息中提取数量
            import re
            numbers = re.findall(r'\d+', user_message)
            if numbers:
                quantity = int(numbers[0])
            
            tasks = {
                "tasks": [
                    {
                        "task_type": "inventory_query",
                        "tool_name": "api_inventory",
                        "description": f"查询{product_name}库存情况",
                        "parameters": {"product_name": product_name, "quantity": quantity},
                        "priority": 1,
                        "dependencies": []
                    },
                    {
                        "task_type": "price_query",
                        "tool_name": "sql_price",
                        "description": f"查询{product_name}历史成交价格",
                        "parameters": {"product_name": product_name, "quantity_range": [quantity - 10, quantity + 10]},
                        "priority": 2,
                        "dependencies": []
                    },
                    {
                        "task_type": "case_retrieval",
                        "tool_name": "doc_retrieve",
                        "description": "检索相似成交案例",
                        "parameters": {"product_name": product_name, "quantity_range": [quantity - 10, quantity + 10]},
                        "priority": 2,
                        "dependencies": []
                    },
                    {
                        "task_type": "price_calculation",
                        "tool_name": "calculator",
                        "description": "计算最终报价和毛利",
                        "parameters": {"quantity": quantity},
                        "priority": 3,
                        "dependencies": ["inventory_query", "price_query"]
                    }
                ]
            }
            
            return json.dumps(tasks, ensure_ascii=False)
        
        # 默认返回空任务列表
        return json.dumps({"tasks": []}, ensure_ascii=False)
    
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        OpenAI 带工具调用的聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            
        Returns:
            包含响应和工具调用的字典
        """
        try:
            from llama_index.core.llms import ChatMessage
            
            # 转换消息格式
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
            
            # 调用模型（LlamaIndex 会自动处理工具调用）
            response = await self.llm.achat_with_tools(
                messages=chat_messages,
                tools=tools,
                temperature=temperature
            )
            
            result = {
                "content": response.message.content,
                "tool_calls": []
            }
            
            # 提取工具调用信息
            if hasattr(response.message, "tool_calls") and response.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "name": tc.tool_name,
                        "arguments": tc.tool_kwargs
                    }
                    for tc in response.message.tool_calls
                ]
            
            logger.debug(f"OpenAI 工具调用响应: {len(result['tool_calls'])} 个工具")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI 工具调用失败: {str(e)}")
            raise


class QwenAdapter(BaseLLMAdapter):
    """
    Qwen (Ollama) 大模型适配器
    """
    
    def __init__(self):
        """初始化 Qwen 适配器"""
        from llama_index.llms.ollama import Ollama
        
        self.model_name = settings.OLLAMA_MODEL
        self.llm = Ollama(
            model=self.model_name,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,
            request_timeout=settings.TOOL_TIMEOUT
        )
        logger.info(f"Qwen 适配器初始化完成，模型: {self.model_name}")
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Qwen 聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            响应文本
        """
        try:
            from llama_index.core.llms import ChatMessage
            
            # 转换消息格式
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
            
            # 调用模型
            response = await self.llm.achat(
                messages=chat_messages,
                temperature=temperature
            )
            
            logger.debug(f"Qwen 响应: {response.message.content[:100]}...")
            return response.message.content
            
        except Exception as e:
            logger.error(f"Qwen 调用失败: {str(e)}")
            raise
    
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Qwen 带工具调用的聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            
        Returns:
            包含响应和工具调用的字典
        """
        try:
            from llama_index.core.llms import ChatMessage
            
            # 转换消息格式
            chat_messages = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in messages
            ]
            
            # 调用模型
            response = await self.llm.achat_with_tools(
                messages=chat_messages,
                tools=tools,
                temperature=temperature
            )
            
            result = {
                "content": response.message.content,
                "tool_calls": []
            }
            
            # 提取工具调用信息
            if hasattr(response.message, "tool_calls") and response.message.tool_calls:
                result["tool_calls"] = [
                    {
                        "name": tc.tool_name,
                        "arguments": tc.tool_kwargs
                    }
                    for tc in response.message.tool_calls
                ]
            
            logger.debug(f"Qwen 工具调用响应: {len(result['tool_calls'])} 个工具")
            return result
            
        except Exception as e:
            logger.error(f"Qwen 工具调用失败: {str(e)}")
            raise


class LLMAdapter:
    """
    统一大模型适配器
    根据配置自动选择 OpenAI 或 Qwen
    支持运行时动态切换
    """
    
    def __init__(self):
        """初始化适配器"""
        self._adapter: Optional[BaseLLMAdapter] = None
        self._mode = settings.LLM_MODE.lower()

        logger.info(f"初始化大模型适配器，模式: {self._mode}")

        if self._mode == "openai":
            self._adapter = OpenAIAdapter()
        elif self._mode == "qwen":
            self._adapter = QwenAdapter()
        else:
            raise ValueError(f"不支持的 LLM 模式: {self._mode}")

    @property
    def mode(self) -> str:
        """获取当前模式"""
        return self._mode

    @property
    def model_name(self) -> str:
        """获取当前模型名称"""
        if self._mode == "openai":
            return settings.OPENAI_MODEL
        else:
            return settings.OLLAMA_MODEL

    def switch_model(self, mode: str, model_name: Optional[str] = None) -> Dict[str, str]:
        """
        动态切换模型

        Args:
            mode: 目标模式 ("openai" 或 "qwen")
            model_name: 可选，指定模型名称

        Returns:
            切换结果信息
        """
        old_mode = self._mode
        old_model = self.model_name

        if mode.lower() not in ["openai", "qwen"]:
            raise ValueError(f"不支持的模式: {mode}，支持的模式: openai, qwen")

        self._mode = mode.lower()

        # 更新模型名称（如果指定）
        if mode.lower() == "openai" and model_name:
            settings.OPENAI_MODEL = model_name
        elif mode.lower() == "qwen" and model_name:
            settings.OLLAMA_MODEL = model_name

        # 重新初始化适配器
        if self._mode == "openai":
            self._adapter = OpenAIAdapter()
        else:
            self._adapter = QwenAdapter()

        new_model = self.model_name
        logger.info(f"模型切换成功: {old_mode}/{old_model} -> {self._mode}/{new_model}")

        return {
            "old_mode": old_mode,
            "old_model": old_model,
            "new_mode": self._mode,
            "new_model": new_model
        }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        统一聊天接口
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            响应文本
        """
        return await self._adapter.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        统一带工具调用的聊天接口
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            
        Returns:
            包含响应和工具调用的字典
        """
        return await self._adapter.chat_with_tools(
            messages=messages,
            tools=tools,
            temperature=temperature
        )
    
    @property
    def mode(self) -> str:
        """获取当前模式"""
        return self._mode
    
    @property
    def model_name(self) -> str:
        """获取当前模型名称"""
        if self._mode == "openai":
            return settings.OPENAI_MODEL
        else:
            return settings.OLLAMA_MODEL


# 全局适配器实例
_llm_adapter: Optional[LLMAdapter] = None


def get_llm() -> LLMAdapter:
    """
    获取全局 LLM 适配器实例（单例模式）
    
    Returns:
        LLMAdapter 实例
    """
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter()
    return _llm_adapter


def get_llm_adapter() -> LLMAdapter:
    """
    获取全局 LLM 适配器实例（单例模式）
    与 get_llm() 相同，提供统一的接口名
    
    Returns:
        LLMAdapter 实例
    """
    return get_llm()
"""
LangFuse 监控服务模块
用于追踪和监控项目中的大模型调用
使用 LangFuse SDK v2 API
"""
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from loguru import logger

from config.settings import settings


class LangFuseMonitor:
    """
    LangFuse 监控器
    提供统一的 LLM 调用追踪接口
    使用 LangFuse SDK v2 API
    """
    
    _instance: Optional["LangFuseMonitor"] = None
    _client = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 LangFuse 监控器"""
        if LangFuseMonitor._initialized:
            return
        
        self._enabled = settings.LANGFUSE_ENABLED
        self._host = settings.LANGFUSE_HOST
        self._public_key = settings.LANGFUSE_PUBLIC_KEY
        self._secret_key = settings.LANGFUSE_SECRET_KEY
        self._sample_rate = settings.LANGFUSE_TRACING_SAMPLE_RATE
        
        if self._enabled:
            self._initialize_client()
        
        LangFuseMonitor._initialized = True
    
    def _initialize_client(self):
        """
        初始化 LangFuse 客户端
        使用 LangFuse SDK v2 API
        """
        try:
            from langfuse import Langfuse
            
            # 使用 SDK v2 API: 直接创建 Langfuse 实例
            LangFuseMonitor._client = Langfuse(
                public_key=self._public_key,
                secret_key=self._secret_key,
                host=self._host
            )
            
            logger.info(f"LangFuse 监控已启用，连接到: {self._host}")
            
        except ImportError as e:
            logger.warning("未安装 langfuse SDK，LangFuse 监控功能不可用")
            self._enabled = False
        except Exception as e:
            logger.error(f"LangFuse 初始化失败: {str(e)}")
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """
        检查监控是否启用
        
        Returns:
            是否启用
        """
        return self._enabled and LangFuseMonitor._client is not None
    
    def trace_llm_call(
        self,
        model: str,
        messages: List[Dict[str, str]],
        response: str,
        metadata: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, int]] = None,
        latency: Optional[float] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        追踪 LLM 调用
        使用 LangFuse SDK v2 API
        
        Args:
            model: 模型名称
            messages: 消息列表
            response: 模型响应
            metadata: 额外元数据
            usage: token 使用量 {"input_tokens": int, "output_tokens": int, "total_tokens": int}
            latency: 延迟（秒）
            trace_id: trace ID
            user_id: 用户 ID
            
        Returns:
            generation 对象或 None
        """
        if not self.is_enabled():
            return None
        
        try:
            from datetime import datetime
            
            langfuse = LangFuseMonitor._client
            
            # 构建 generation 输入
            input_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in messages
            ])
            
            # 计算 start_time 和 end_time（基于 latency）
            end_time = datetime.now()
            start_time = None
            if latency:
                import time
                start_time = datetime.fromtimestamp(time.time() - latency)
            
            # 使用 SDK v2 API: trace().generation()
            trace = langfuse.trace(
                id=trace_id,
                name=f"llm_call_{model}",
                user_id=user_id,
                metadata=metadata or {}
            )
            
            # 处理 usage 参数（使用 OpenAI 风格的字段名，确保兼容性）
            usage_obj = None
            if usage:
                usage_obj = {
                    "promptTokens": usage.get('input_tokens', 0) or usage.get('promptTokens', 0),
                    "completionTokens": usage.get('output_tokens', 0) or usage.get('completionTokens', 0),
                    "totalTokens": usage.get('total_tokens', 0) or usage.get('totalTokens', 0)
                }
            
            generation = trace.generation(
                name=f"llm_{model}",
                model=model,
                input=input_text,
                output=response,
                usage=usage_obj,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "latency": latency,
                    **(metadata or {})
                }
            )
            
            # 立即刷新数据到服务器
            langfuse.flush()
            
            logger.debug(f"LLM 调用已记录到 LangFuse: trace={trace.id}, generation={generation.id}")
            return generation
            
        except Exception as e:
            logger.error(f"记录 LLM 调用到 LangFuse 失败: {str(e)}")
            return None
    
    @contextmanager
    def trace_span(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        创建一个追踪 span（上下文管理器）
        使用 LangFuse SDK v2 API
        
        Args:
            name: span 名称
            metadata: 额外元数据
            trace_id: trace ID
            user_id: 用户 ID
            
        Usage:
            with monitor.trace_span("task_planning") as span:
                # 执行任务规划
                result = await task_planner.plan(...)
                span.update(output=result)
        """
        if not self.is_enabled():
            yield None
            return
        
        try:
            langfuse = LangFuseMonitor._client
            
            # 使用 SDK v2 API: trace().span()
            trace = langfuse.trace(
                id=trace_id,
                name=name,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            span = trace.span(
                name=name,
                metadata=metadata or {}
            )
            
            yield span
            
        except Exception as e:
            logger.error(f"创建 LangFuse span 失败: {str(e)}")
            yield None
    
    def create_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Any]:
        """
        创建一个新的 trace
        
        Args:
            name: trace 名称
            metadata: 额外元数据
            user_id: 用户 ID
            
        Returns:
            trace 对象或 None
        """
        if not self.is_enabled():
            return None
        
        try:
            langfuse = LangFuseMonitor._client
            
            # 使用 SDK v2 API: trace()
            trace = langfuse.trace(
                name=name,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            return trace
            
        except Exception as e:
            logger.error(f"创建 LangFuse trace 失败: {str(e)}")
            return None
    
    def flush(self):
        """
        刷新所有待发送的追踪数据
        """
        if self.is_enabled():
            try:
                LangFuseMonitor._client.flush()
                logger.debug("LangFuse 数据已刷新")
            except Exception as e:
                logger.error(f"刷新 LangFuse 数据失败: {str(e)}")


# 全局监控器实例
_langfuse_monitor: Optional[LangFuseMonitor] = None


def get_langfuse_monitor() -> LangFuseMonitor:
    """
    获取全局 LangFuse 监控器实例（单例模式）
    
    Returns:
        LangFuseMonitor 实例
    """
    global _langfuse_monitor
    if _langfuse_monitor is None:
        _langfuse_monitor = LangFuseMonitor()
    return _langfuse_monitor
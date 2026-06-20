"""
LangFuse 监控服务模块
用于追踪和监控项目中的大模型调用
使用 LangFuse SDK v2 API
"""
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from loguru import logger
from datetime import datetime
import time

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
        
        # 验证配置
        if not self._public_key or not self._secret_key:
            logger.warning("LangFuse API Keys 未配置，监控功能将禁用")
            self._enabled = False
        
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
            
            # 验证连接
            try:
                auth_result = LangFuseMonitor._client.auth_check()
                if auth_result:
                    logger.info("LangFuse API 认证成功")
                else:
                    logger.warning("LangFuse API 认证失败，请检查 API Keys")
            except Exception as auth_e:
                logger.warning(f"LangFuse API 认证检查失败: {auth_e}")
            
        except ImportError as e:
            logger.warning("未安装 langfuse SDK，LangFuse 监控功能不可用")
            self._enabled = False
        except Exception as e:
            logger.error(f"LangFuse 初始化失败: {str(e)}")
            self._enabled = False
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> tuple:
        """
        计算模型调用成本（方式三：代码中计算）
        
        Args:
            model: 模型名称
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            
        Returns:
            (input_cost, output_cost, total_cost) 元组
        """
        # 根据模型名称确定定价
        model_lower = model.lower()
        
        if "glm" in model_lower or "zhipu" in model_lower:
            # 智谱 AI 模型
            input_rate = settings.MODEL_PRICE_GLM_INPUT
            output_rate = settings.MODEL_PRICE_GLM_OUTPUT
        elif "qwen" in model_lower:
            # Qwen 本地模型（成本为0）
            input_rate = settings.MODEL_PRICE_QWEN_INPUT
            output_rate = settings.MODEL_PRICE_QWEN_OUTPUT
        elif "gpt" in model_lower or "openai" in model_lower:
            # OpenAI 模型
            input_rate = settings.MODEL_PRICE_OPENAI_INPUT
            output_rate = settings.MODEL_PRICE_OPENAI_OUTPUT
        else:
            # 默认使用 GLM 定价
            input_rate = settings.MODEL_PRICE_GLM_INPUT
            output_rate = settings.MODEL_PRICE_GLM_OUTPUT
        
        # 计算成本（美元）
        input_cost = (input_tokens / 1000) * input_rate
        output_cost = (output_tokens / 1000) * output_rate
        total_cost = input_cost + output_cost
        
        return round(input_cost, 6), round(output_cost, 6), round(total_cost, 6)
    
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
        user_id: Optional[str] = None,
        session_id: Optional[str] = None  # 新增参数
    ) -> Optional[Dict[str, Any]]:
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
            session_id: 会话 ID（用于 Sessions 面板分组）
            
        Returns:
            包含 trace_id, generation_id 和 generation 对象的字典，或 None
        """
        if not self.is_enabled():
            logger.debug("LangFuse 监控未启用，跳过追踪")
            return None
        
        try:
            langfuse = LangFuseMonitor._client
            
            # 计算 start_time 和 end_time（基于 latency）
            end_time = datetime.now()
            start_time = None
            if latency and latency > 0:
                start_time = datetime.fromtimestamp(time.time() - latency)
            
            # 使用 SDK v2 API: trace().generation()
            trace = langfuse.trace(
                id=trace_id,
                name=f"llm_call_{model}",
                user_id=user_id,
                session_id=session_id,  # 添加 session_id
                metadata=metadata or {}
            )
            
            # 构建 usage 参数（使用 ModelUsage 对象）
            usage_obj = None
            if usage:
                input_tokens = usage.get('input_tokens', 0) or usage.get('promptTokens', 0) or 0
                output_tokens = usage.get('output_tokens', 0) or usage.get('completionTokens', 0) or 0
                total_tokens = usage.get('total_tokens', 0) or usage.get('totalTokens', 0) or 0
                
                if input_tokens > 0 or output_tokens > 0:
                    # 使用 SDK v2 的 ModelUsage 对象
                    from langfuse.model import ModelUsage
                    usage_obj = ModelUsage(
                        input=input_tokens,
                        output=output_tokens,
                        total=total_tokens
                    )
            
            # 计算成本（方式三：在代码中设置成本信息）
            input_cost, output_cost, total_cost = self._calculate_cost(model, input_tokens, output_tokens)
            
            # 创建 generation 记录
            generation = trace.generation(
                name=f"llm_{model}",
                model=model,
                input=messages,  # 直接传递消息列表，让 SDK 处理格式
                output=response,
                usage=usage_obj,
                start_time=start_time,
                end_time=end_time,
                metadata={
                    "latency_seconds": latency,
                    "adapter": metadata.get("adapter", "unknown") if metadata else "unknown",
                    "input_cost": input_cost,
                    "output_cost": output_cost,
                    "total_cost": total_cost,
                    **(metadata or {})
                }
            )
            
            # 立即刷新数据到服务器
            langfuse.flush()
            
            logger.info(f"LLM 调用已记录到 LangFuse: trace={trace.id}, generation={generation.id}, tokens={usage_obj}")
            
            # 返回详细信息，方便后续添加评分
            return {
                "trace_id": trace.id,
                "generation_id": generation.id,
                "generation": generation,
                "trace": trace
            }
            
        except Exception as e:
            logger.error(f"记录 LLM 调用到 LangFuse 失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
        """
        if not self.is_enabled():
            yield None
            return
        
        try:
            langfuse = LangFuseMonitor._client
            
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
            
            trace = langfuse.trace(
                name=name,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            return trace
            
        except Exception as e:
            logger.error(f"创建 LangFuse trace 失败: {str(e)}")
            return None
    
    def add_score(
        self,
        trace_id: str,
        name: str,
        score: float,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        为指定 trace 添加评分（Score）
        
        Args:
            trace_id: trace ID
            name: 评分名称（如 "quality", "relevance", "correctness"）
            score: 分数（通常 0-1 或 0-100）
            comment: 评分说明
            metadata: 额外元数据
            
        Returns:
            score 对象或 None
        """
        if not self.is_enabled():
            logger.debug("LangFuse 监控未启用，跳过评分")
            return None
        
        try:
            langfuse = LangFuseMonitor._client
            
            # 使用 SDK v2 API: score()
            score_obj = langfuse.score(
                traceId=trace_id,
                name=name,
                value=score,
                comment=comment,
                metadata=metadata or {}
            )
            
            # 立即刷新数据到服务器
            langfuse.flush()
            
            logger.info(f"Score 已记录到 LangFuse: trace={trace_id}, name={name}, score={score}")
            return score_obj
            
        except Exception as e:
            logger.error(f"记录 Score 到 LangFuse 失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def add_score_to_observation(
        self,
        observation_id: str,
        name: str,
        score: float,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        为指定 observation（generation/span）添加评分
        
        Args:
            observation_id: observation ID（generation 或 span 的 ID）
            name: 评分名称
            score: 分数
            comment: 评分说明
            metadata: 额外元数据
            
        Returns:
            score 对象或 None
        """
        if not self.is_enabled():
            logger.debug("LangFuse 监控未启用，跳过评分")
            return None
        
        try:
            langfuse = LangFuseMonitor._client
            
            score_obj = langfuse.score(
                observationId=observation_id,
                name=name,
                value=score,
                comment=comment,
                metadata=metadata or {}
            )
            
            langfuse.flush()
            
            logger.info(f"Score 已记录到 LangFuse: observation={observation_id}, name={name}, score={score}")
            return score_obj
            
        except Exception as e:
            logger.error(f"记录 Score 到 LangFuse 失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
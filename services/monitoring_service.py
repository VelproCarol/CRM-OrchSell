"""
监控服务模块
集成 Prometheus 指标收集和监控告警
"""
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        Info,
        generate_latest,
        CollectorRegistry,
        CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    logger.warning("Prometheus 客户端未安装，监控功能将受限")
    PROMETHEUS_AVAILABLE = False


class MonitoringService:
    """
    监控服务类
    收集和暴露系统指标供 Prometheus 抓取
    """
    
    def __init__(self):
        """初始化监控服务"""
        if not PROMETHEUS_AVAILABLE:
            self.registry = None
            logger.warning("Prometheus 不可用，跳过指标初始化")
            return
        
        self.registry = CollectorRegistry()
        
        # ============ 请求指标 ============
        self.request_total = Counter(
            'sales_agent_requests_total',
            'Total number of requests received',
            ['endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'sales_agent_request_duration_seconds',
            'Request duration in seconds',
            ['endpoint'],
            registry=self.registry
        )
        
        self.request_concurrent = Gauge(
            'sales_agent_requests_concurrent',
            'Number of concurrent requests',
            registry=self.registry
        )
        
        # ============ 工具调用指标 ============
        self.tool_calls_total = Counter(
            'sales_agent_tool_calls_total',
            'Total number of tool calls',
            ['tool_name', 'status'],
            registry=self.registry
        )
        
        self.tool_call_duration = Histogram(
            'sales_agent_tool_call_duration_seconds',
            'Tool call duration in seconds',
            ['tool_name'],
            registry=self.registry
        )
        
        # ============ LLM 调用指标 ============
        self.llm_calls_total = Counter(
            'sales_agent_llm_calls_total',
            'Total number of LLM calls',
            ['model', 'status'],
            registry=self.registry
        )
        
        self.llm_tokens_used = Counter(
            'sales_agent_llm_tokens_used',
            'Total tokens used by LLM',
            ['model', 'type'],  # type: prompt/completion
            registry=self.registry
        )
        
        self.llm_duration = Histogram(
            'sales_agent_llm_duration_seconds',
            'LLM call duration in seconds',
            ['model'],
            registry=self.registry
        )
        
        # ============ 反思验真指标 ============
        self.reflection_checks_total = Counter(
            'sales_agent_reflection_checks_total',
            'Total number of reflection checks',
            ['result'],  # passed/warning/failed
            registry=self.registry
        )
        
        self.reflection_confidence = Gauge(
            'sales_agent_reflection_confidence',
            'Reflection confidence score',
            registry=self.registry
        )
        
        # ============ 缓存指标 ============
        self.cache_hits_total = Counter(
            'sales_agent_cache_hits_total',
            'Total number of cache hits',
            ['cache_type'],  # inventory/pricing/cases
            registry=self.registry
        )
        
        self.cache_misses_total = Counter(
            'sales_agent_cache_misses_total',
            'Total number of cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # ============ 客户相关指标 ============
        self.customer_queries_total = Counter(
            'sales_agent_customer_queries_total',
            'Total number of customer queries',
            ['customer_level'],  # A/B/C/D
            registry=self.registry
        )
        
        self.new_customers_total = Counter(
            'sales_agent_new_customers_total',
            'Total number of new customers',
            registry=self.registry
        )
        
        # ============ 系统健康指标 ============
        self.system_uptime = Gauge(
            'sales_agent_system_uptime_seconds',
            'System uptime in seconds',
            registry=self.registry
        )
        
        self.health_status = Gauge(
            'sales_agent_health_status',
            'Health status (1=healthy, 0=unhealthy)',
            registry=self.registry
        )
        
        # ============ 服务信息 ============
        self.service_info = Info(
            'sales_agent_service',
            'Sales Agent service information',
            registry=self.registry
        )
        
        # 初始化服务信息
        self.service_info.info({
            'version': '1.0.0',
            'status': 'running',
            'started_at': datetime.now().isoformat()
        })
        
        # 初始化健康状态
        self.health_status.set(1)
        
        logger.info("监控服务初始化完成")
    
    def record_request(self, endpoint: str, status: str, duration: float = 0):
        """
        记录请求指标
        
        Args:
            endpoint: 请求端点
            status: 状态（success/error/partial）
            duration: 持续时间（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.request_total.labels(endpoint=endpoint, status=status).inc()
        if duration > 0:
            self.request_duration.labels(endpoint=endpoint).observe(duration)
    
    def record_concurrent_request(self, delta: int):
        """
        记录并发请求数变化
        
        Args:
            delta: 变化量（+1 或 -1）
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.request_concurrent.inc(delta)
    
    def record_tool_call(self, tool_name: str, status: str, duration: float = 0):
        """
        记录工具调用指标
        
        Args:
            tool_name: 工具名称
            status: 状态（success/failed）
            duration: 持续时间（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.tool_calls_total.labels(tool_name=tool_name, status=status).inc()
        if duration > 0:
            self.tool_call_duration.labels(tool_name=tool_name).observe(duration)
    
    def record_llm_call(self, model: str, status: str, duration: float = 0, 
                        prompt_tokens: int = 0, completion_tokens: int = 0):
        """
        记录 LLM 调用指标
        
        Args:
            model: 模型名称
            status: 状态（success/failed）
            duration: 持续时间（秒）
            prompt_tokens: 提示词 token 数
            completion_tokens: 完成 token 数
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.llm_calls_total.labels(model=model, status=status).inc()
        if duration > 0:
            self.llm_duration.labels(model=model).observe(duration)
        if prompt_tokens > 0:
            self.llm_tokens_used.labels(model=model, type='prompt').inc(prompt_tokens)
        if completion_tokens > 0:
            self.llm_tokens_used.labels(model=model, type='completion').inc(completion_tokens)
    
    def record_reflection(self, result: str, confidence: float = 0):
        """
        记录反思验真指标
        
        Args:
            result: 结果（passed/warning/failed）
            confidence: 置信度
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.reflection_checks_total.labels(result=result).inc()
        if confidence > 0:
            self.reflection_confidence.set(confidence)
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """
        记录缓存访问指标
        
        Args:
            cache_type: 缓存类型（inventory/pricing/cases）
            hit: 是否命中
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        if hit:
            self.cache_hits_total.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses_total.labels(cache_type=cache_type).inc()
    
    def record_customer_query(self, customer_level: str = 'unknown'):
        """
        记录客户查询指标
        
        Args:
            customer_level: 客户等级（A/B/C/D）
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.customer_queries_total.labels(customer_level=customer_level).inc()
    
    def record_new_customer(self):
        """记录新客户"""
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.new_customers_total.inc()
    
    def update_health_status(self, healthy: bool):
        """
        更新健康状态
        
        Args:
            healthy: 是否健康
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.health_status.set(1 if healthy else 0)
    
    def update_uptime(self, seconds: float):
        """
        更新系统运行时间
        
        Args:
            seconds: 运行时间（秒）
        """
        if not PROMETHEUS_AVAILABLE:
            return
        
        self.system_uptime.set(seconds)
    
    def get_metrics(self) -> bytes:
        """
        获取指标数据（供 Prometheus 抓取）
        
        Returns:
            指标数据字节流
        """
        if not PROMETHEUS_AVAILABLE or not self.registry:
            return b""
        
        return generate_latest(self.registry)
    
    def get_metrics_content_type(self) -> str:
        """
        获取指标内容类型
        
        Returns:
            内容类型字符串
        """
        return CONTENT_TYPE_LATEST


# 全局监控服务实例
monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """
    获取监控服务实例
    
    Returns:
        监控服务实例
    """
    return monitoring_service

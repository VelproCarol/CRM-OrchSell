"""
服务模块初始化
存放业务服务类
"""
from .cache_manager import get_cache_manager, CacheManager
from .customer_service import get_customer_service, CustomerProfile, FollowUpRecord, CustomerService
from .pdf_generator import get_pdf_generator, PdfGenerator
from .monitoring_service import get_monitoring_service, MonitoringService

__all__ = [
    "get_cache_manager",
    "CacheManager",
    "get_customer_service",
    "CustomerProfile",
    "FollowUpRecord",
    "CustomerService",
    "get_pdf_generator",
    "PdfGenerator",
    "get_monitoring_service",
    "MonitoringService"
]
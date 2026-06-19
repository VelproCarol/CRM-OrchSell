"""
API 接口层模块初始化
"""
from .chat_route import router, create_app

__all__ = ["router", "create_app"]
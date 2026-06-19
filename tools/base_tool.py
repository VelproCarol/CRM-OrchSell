"""
工具抽象基类
定义统一工具接口规范，所有工具必须继承此基类
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from loguru import logger

from config.settings import settings


class BaseTool(ABC):
    """
    工具抽象基类
    所有业务工具必须继承此基类并实现 execute 方法
    """
    
    def __init__(self, name: str, description: str):
        """
        初始化工具基类
        
        Args:
            name: 工具名称
            description: 工具描述
        """
        self.name = name
        self.description = description
        self.timeout = settings.TOOL_TIMEOUT
        logger.info(f"工具初始化: {name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行工具逻辑（子类必须实现）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果字典
        """
        pass
    
    def validate_params(self, **kwargs) -> bool:
        """
        验证参数合法性（子类可覆盖）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            参数是否合法
        """
        return True
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """
        获取工具 Schema（用于 LlamaIndex 工具调用）
        
        Returns:
            工具 Schema 字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        获取参数 Schema（子类必须实现）
        
        Returns:
            参数 Schema 字典
        """
        pass
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """
        处理错误，返回标准错误响应
        
        Args:
            error: 异常对象
            
        Returns:
            错误响应字典
        """
        logger.error(f"工具 {self.name} 执行失败: {str(error)}")
        return {
            "success": False,
            "error": str(error),
            "tool": self.name
        }
    
    def _success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        返回成功响应
        
        Args:
            data: 数据字典
            
        Returns:
            成功响应字典
        """
        return {
            "success": True,
            "tool": self.name,
            **data
        }
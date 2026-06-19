"""
Redis 缓存管理器模块
提供统一的缓存接口，支持库存、价格、案例数据的缓存
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime
from loguru import logger

from config.settings import settings


class CacheManager:
    """
    Redis 缓存管理器
    提供统一的缓存操作接口
    """
    
    def __init__(self):
        """初始化缓存管理器"""
        self._client = None
        self._enabled = settings.REDIS_ENABLED
        
        if self._enabled:
            try:
                self._init_redis()
                logger.info("Redis 缓存管理器初始化完成")
            except Exception as e:
                logger.error(f"Redis 连接失败，将使用内存缓存: {str(e)}")
                self._enabled = False
                self._memory_cache = {}
    
    def _init_redis(self):
        """初始化 Redis 客户端"""
        import redis
        
        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # 测试连接
        self._client.ping()
    
    def _get_memory_cache(self, key: str) -> Optional[Any]:
        """从内存缓存获取数据"""
        item = self._memory_cache.get(key)
        if item:
            if datetime.now().timestamp() < item["expire_at"]:
                return item["data"]
            else:
                del self._memory_cache[key]
        return None
    
    def _set_memory_cache(self, key: str, value: Any, ttl: int):
        """设置内存缓存"""
        self._memory_cache[key] = {
            "data": value,
            "expire_at": datetime.now().timestamp() + ttl
        }
    
    def _delete_memory_cache(self, key: str):
        """删除内存缓存"""
        if key in self._memory_cache:
            del self._memory_cache[key]
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            缓存数据，不存在返回 None
        """
        if not self._enabled:
            return self._get_memory_cache(key)
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET 失败: {str(e)}")
            return self._get_memory_cache(key)
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 有效期（秒），默认 3600 秒
        """
        if not self._enabled:
            return self._set_memory_cache(key, value, ttl)
        
        try:
            value_str = json.dumps(value)
            self._client.setex(key, ttl, value_str)
        except Exception as e:
            logger.error(f"Redis SET 失败: {str(e)}")
            self._set_memory_cache(key, value, ttl)
    
    def delete(self, key: str):
        """
        删除缓存
        
        Args:
            key: 缓存键
        """
        if not self._enabled:
            return self._delete_memory_cache(key)
        
        try:
            self._client.delete(key)
        except Exception as e:
            logger.error(f"Redis DELETE 失败: {str(e)}")
            self._delete_memory_cache(key)
    
    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
        
        Returns:
            是否存在
        """
        if not self._enabled:
            return key in self._memory_cache
        
        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS 失败: {str(e)}")
            return key in self._memory_cache
    
    def get_inventory(self, product_name: str) -> Optional[Dict[str, Any]]:
        """
        获取库存缓存
        
        Args:
            product_name: 产品名称
        
        Returns:
            库存数据
        """
        key = f"inventory:{product_name}"
        return self.get(key)
    
    def set_inventory(self, product_name: str, data: Dict[str, Any]):
        """
        设置库存缓存
        
        Args:
            product_name: 产品名称
            data: 库存数据
        """
        key = f"inventory:{product_name}"
        self.set(key, data, settings.CACHE_TTL_INVENTORY)
    
    def get_pricing(self, product_name: str, quantity_range: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        获取价格缓存
        
        Args:
            product_name: 产品名称
            quantity_range: 数量区间
        
        Returns:
            价格数据
        """
        key = f"pricing:{product_name}"
        if quantity_range:
            key += f":{quantity_range}"
        return self.get(key)
    
    def set_pricing(self, product_name: str, data: Dict[str, Any], quantity_range: Optional[str] = None):
        """
        设置价格缓存
        
        Args:
            product_name: 产品名称
            data: 价格数据
            quantity_range: 数量区间
        """
        key = f"pricing:{product_name}"
        if quantity_range:
            key += f":{quantity_range}"
        self.set(key, data, settings.CACHE_TTL_PRICING)
    
    def get_case(self, query: str) -> Optional[Dict[str, Any]]:
        """
        获取案例缓存
        
        Args:
            query: 查询关键词
        
        Returns:
            案例数据
        """
        key = f"case:{query}"
        return self.get(key)
    
    def set_case(self, query: str, data: Dict[str, Any]):
        """
        设置案例缓存
        
        Args:
            query: 查询关键词
            data: 案例数据
        """
        key = f"case:{query}"
        self.set(key, data, settings.CACHE_TTL_CASES)
    
    def clear_all(self):
        """清除所有缓存"""
        if not self._enabled:
            self._memory_cache.clear()
            return
        
        try:
            self._client.flushdb()
            logger.info("Redis 缓存已清空")
        except Exception as e:
            logger.error(f"Redis 清空失败: {str(e)}")
            self._memory_cache.clear()


# 全局缓存管理器实例
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """
    获取缓存管理器实例
    
    Returns:
        缓存管理器实例
    """
    return cache_manager
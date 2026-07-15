import sys
sys.path.insert(0, '.')

from services.cache_manager import get_cache_manager

cache = get_cache_manager()
cache.clear_all()
print("缓存已清空")

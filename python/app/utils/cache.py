from cachetools import TTLCache
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple cache manager using cachetools"""

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        """
        Initialize cache manager
        
        Args:
            maxsize: Maximum number of items in cache
            ttl: Default time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.hits = 0
        self.misses = 0
        logger.info(f"Cache manager initialized (maxsize={maxsize}, ttl={ttl}s)")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.cache.get(key)
            if value is not None:
                self.hits += 1
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                self.misses += 1
                logger.debug(f"Cache miss: {key}")
                return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if ttl:
                # Create a new cache instance with custom TTL if needed
                # For simplicity, we'll use the default TTL
                pass
            self.cache[key] = value
            logger.debug(f"Cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache delete: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False

    def clear(self) -> bool:
        """Clear all cache"""
        try:
            self.cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return False

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
        }

    def keys(self) -> list:
        """Get all keys in cache"""
        return list(self.cache.keys())

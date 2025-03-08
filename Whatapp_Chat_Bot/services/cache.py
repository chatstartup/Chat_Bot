"""Redis-based caching service"""
import logging
import functools
from typing import Any, Optional, Union, Callable
import json
from redis import Redis
from redis.exceptions import RedisError
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseService
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CacheService(BaseService):
    """Service for Redis-based caching and rate limiting"""
    
    def __init__(self):
        super().__init__()
        self.redis: Optional[Redis] = None
        self.default_ttl = 3600  # 1 hour
        
    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            await self.health_check()
            logger.info("Successfully initialized Redis connection")
            return True
            
        except Exception as e:
            self._set_error(e)
            return False
            
    async def health_check(self) -> bool:
        """Check Redis connection health"""
        if not self.redis:
            return False
            
        try:
            self.redis.ping()
            self._is_available = True
            return True
        except Exception as e:
            self._set_error(e)
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available:
            return None
            
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache"""
        if not self.is_available:
            return False
            
        try:
            serialized = json.dumps(value)
            self.redis.set(
                key,
                serialized,
                ex=ttl or self.default_ttl
            )
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None
    ) -> Optional[int]:
        """Increment counter in cache"""
        if not self.is_available:
            return None
            
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key, amount)
            if ttl:
                pipe.expire(key, ttl)
            results = pipe.execute()
            return results[0]
            
        except Exception as e:
            logger.error(f"Error incrementing cache: {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def rate_limit_check(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Optional[int]]:
        """Check rate limit for key"""
        if not self.is_available:
            return True, None  # Allow if cache is down
            
        try:
            current = await self.increment(key, 1, window)
            if not current:
                return True, None
                
            remaining = max(0, limit - current)
            return current <= limit, remaining
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True, None  # Allow if error
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available:
            return False
            
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

# Create a global cache instance
global_cache = CacheService()

def cached(key_prefix: str, ttl: int = 3600):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a cache key based on function arguments
            key = f"{key_prefix}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache first
            if global_cache.is_available:
                cached_result = await global_cache.get(key)
                if cached_result is not None:
                    logger.info(f"Cache hit for key: {key}")
                    return cached_result
            
            # If not in cache, call the function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if global_cache.is_available:
                await global_cache.set(key, result, ttl)
                logger.info(f"Cached result for key: {key}")
            
            return result
        return wrapper
    return decorator

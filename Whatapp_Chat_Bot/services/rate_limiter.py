import logging
from datetime import datetime, timedelta
from typing import Optional
import redis
from config.settings import get_settings
from models.exceptions import RateLimitError

logger = logging.getLogger(__name__)
settings = get_settings()

class RateLimiter:
    """Redis-based rate limiter for API requests"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.window_seconds = settings.RATE_LIMIT_WINDOW
        self.max_requests = settings.MAX_REQUESTS_PER_MINUTE
    
    def _get_key(self, client_ip: str) -> str:
        """Get Redis key for client IP"""
        return f"rate_limit:{client_ip}"
    
    async def check_rate_limit(self, client_ip: str) -> None:
        """Check if request is within rate limit"""
        key = self._get_key(client_ip)
        pipe = self.redis.pipeline()
        
        try:
            now = datetime.now().timestamp()
            window_start = now - self.window_seconds
            
            # Remove old requests
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count requests in window
            pipe.zcard(key)
            
            # Add new request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, self.window_seconds)
            
            # Execute pipeline
            results = pipe.execute()
            request_count = results[1]
            
            if request_count >= self.max_requests:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise RateLimitError(
                    message="Rate limit exceeded",
                    details={
                        "client_ip": client_ip,
                        "window_seconds": self.window_seconds,
                        "max_requests": self.max_requests,
                        "reset_after": self._get_reset_time(client_ip)
                    }
                )
            
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}", exc_info=True)
            # Fallback to allowing request if Redis is down
            return
    
    async def get_remaining_requests(self, client_ip: str) -> int:
        """Get number of remaining requests in window"""
        try:
            key = self._get_key(client_ip)
            now = datetime.now().timestamp()
            window_start = now - self.window_seconds
            
            # Remove old requests and count remaining
            self.redis.zremrangebyscore(key, 0, window_start)
            current_requests = self.redis.zcard(key)
            
            return max(0, self.max_requests - current_requests)
            
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}", exc_info=True)
            return 0
    
    def _get_reset_time(self, client_ip: str) -> Optional[float]:
        """Get when the rate limit will reset"""
        try:
            key = self._get_key(client_ip)
            oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
            
            if not oldest_request:
                return None
            
            oldest_timestamp = oldest_request[0][1]
            reset_time = oldest_timestamp + self.window_seconds
            
            return max(0, reset_time - datetime.now().timestamp())
            
        except redis.RedisError:
            return None

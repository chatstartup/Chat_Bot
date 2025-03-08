"""Rate limiting middleware using in-memory cache"""
from typing import Optional, Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from services.memory_cache import MemoryCache

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        window_seconds: int = 60
    ):
        super().__init__(app)
        self.cache = MemoryCache()
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> None:
        """Process each request for rate limiting"""
        # Skip rate limiting for health check endpoints
        if request.url.path in ["/health", "/metrics", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier (IP or API key)
        client_id = request.headers.get("X-API-Key") or request.client.host
        rate_key = f"rate_limit:{client_id}"
        
        # Check rate limit
        current = await self.cache.increment(
            rate_key,
            1,
            self.window_seconds
        )
        
        if current and current > self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Too many requests",
                    "retry_after": self.window_seconds
                }
            )
        
        # Set rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - (current or 0))
        )
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)
        
        return response

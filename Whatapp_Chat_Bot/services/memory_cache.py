"""In-memory cache service"""
import logging
import time
from typing import Dict, Any, Optional
from .base import BaseService

logger = logging.getLogger(__name__)

class MemoryCache(BaseService):
    """Simple in-memory cache implementation"""
    
    def __init__(self):
        """Initialize memory cache"""
        super().__init__()
        self._cache = {}
        self._expiry = {}
    
    def initialize(self) -> bool:
        """Initialize the cache service"""
        try:
            self._cache = {}
            self._expiry = {}
            self._is_available = True
            self._last_error = None  # Clear any previous errors
            logger.info("Memory cache initialized")
            return True
        except Exception as e:
            self._set_error(str(e))
            logger.error(f"Failed to initialize memory cache: {e}")
            return False
    
    @property
    def cache(self):
        """Get the cache dictionary"""
        return self._cache
    
    @property
    def expiry(self):
        """Get the expiry dictionary"""
        return self._expiry
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available:
            logger.warning("Cache service not available")
            return None
            
        try:
            # Check if key exists and not expired
            if key in self._cache:
                if key in self._expiry and self._expiry[key] < time.time():
                    # Key expired, remove it
                    self._remove_expired(key)
                    return None
                return self._cache[key]
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds"""
        if not self.is_available:
            logger.warning("Cache service not available")
            return False
            
        try:
            self._cache[key] = value
            
            # Set expiry if TTL provided
            if ttl is not None:
                self._expiry[key] = time.time() + ttl
                
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available:
            logger.warning("Cache service not available")
            return False
            
        try:
            if key in self._cache:
                del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache data"""
        if not self.is_available:
            logger.warning("Cache service not available")
            return False
            
        try:
            self._cache = {}
            self._expiry = {}
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    def _remove_expired(self, key: str) -> None:
        """Remove expired key"""
        try:
            if key in self._cache:
                del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
        except Exception as e:
            logger.error(f"Error removing expired key: {e}")
    
    def cleanup_expired(self) -> int:
        """Remove all expired keys and return count of removed items"""
        if not self.is_available:
            logger.warning("Cache service not available")
            return 0
            
        try:
            current_time = time.time()
            expired_keys = [
                key for key, expiry_time in self._expiry.items()
                if expiry_time < current_time
            ]
            
            for key in expired_keys:
                self._remove_expired(key)
                
            return len(expired_keys)
        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {e}")
            return 0
    
    def health_check(self) -> bool:
        """Check if cache service is healthy (synchronous version)"""
        return self.is_available
        
    async def health_check_async(self) -> bool:
        """Check if cache service is healthy (async version)"""
        return self.health_check()

    @property
    def last_error(self):
        return self._last_error

    @last_error.setter
    def last_error(self, value):
        self._last_error = value

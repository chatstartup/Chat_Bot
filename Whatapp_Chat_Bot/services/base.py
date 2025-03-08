"""Base service class"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common functionality"""
    
    def __init__(self):
        """Initialize base service"""
        self._last_error: Optional[str] = None
        self._is_available: bool = False
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    @property
    def is_available(self) -> bool:
        """Check if the service is available"""
        return self._is_available
    
    def _set_error(self, error) -> None:
        """Set error message"""
        self._last_error = str(error)
        self._is_available = False
        logger.error(f"Service error: {error}")
    
    def initialize(self) -> bool:
        """Initialize service - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement initialize()")
    
    def health_check(self) -> bool:
        """Check service health"""
        return self.is_available

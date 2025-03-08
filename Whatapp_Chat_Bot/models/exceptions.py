from typing import Optional, Dict, Any

class ChatBotError(Exception):
    """Base exception for all chatbot errors"""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ChatValidationError(ChatBotError):
    """Raised when chat validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CHAT_VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class AIServiceError(ChatBotError):
    """Raised when AI service encounters an error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AI_SERVICE_ERROR",
            status_code=503,
            details=details
        )

class VectorDBError(ChatBotError):
    """Raised when Vector DB service encounters an error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VECTOR_DB_ERROR",
            status_code=503,
            details=details
        )

class TranslationError(ChatBotError):
    """Raised when translation service encounters an error"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="TRANSLATION_ERROR",
            status_code=503,
            details=details
        )

class ValidationError(ChatBotError):
    """Raised when input validation fails"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class RateLimitError(ChatBotError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details
        )

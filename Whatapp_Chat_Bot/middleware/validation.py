"""Request validation middleware"""
import logging
from functools import wraps
from flask import request
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

def validate_request(model: BaseModel) -> Callable:
    """Validate request data against Pydantic model"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get request data
                data = request.get_json()
                if not data:
                    raise ValidationError("No data provided")
                
                # Validate against model
                validated_data = model(**data)
                
                # Add validated data to kwargs
                kwargs["validated_data"] = validated_data
                
                return f(*args, **kwargs)
            
            except ValidationError as e:
                logger.warning(f"Validation error: {str(e)}")
                return {
                    "error": True,
                    "message": "Invalid request data",
                    "details": e.errors()
                }, 400
            
            except Exception as e:
                logger.error(f"Error validating request: {str(e)}", exc_info=True)
                raise
        
        return decorated_function
    return decorator

def validate_api_key() -> Callable:
    """Validate API key from request headers"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from config.settings import get_settings
            settings = get_settings()
            
            api_key = request.headers.get(settings.API_KEY_HEADER)
            if not api_key or api_key != settings.API_KEY:
                return {
                    "error": True,
                    "message": "Invalid or missing API key"
                }, 401
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

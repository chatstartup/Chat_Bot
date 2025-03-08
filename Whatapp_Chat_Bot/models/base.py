"""Base models for the application"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class TimestampedModel(BaseModel):
    """Base model with timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ServiceResponse(BaseModel):
    """Base model for service responses"""
    success: bool = True
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

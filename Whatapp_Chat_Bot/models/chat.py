from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class Message(BaseModel):
    """Chat message model"""
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user/assistant)")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")

class ChatSession(BaseModel):
    """Chat session model"""
    session_id: str = Field(..., description="Unique session identifier")
    messages: List[Message] = Field(default_factory=list)
    language: str = Field(default="en", description="Chat language")
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Session metadata")

class ChatResponse(BaseModel):
    """Chat response model"""
    message: str = Field(..., description="Response message")
    clear_chat: bool = Field(default=False, description="Whether to clear chat history")
    error: Optional[str] = Field(default=None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")

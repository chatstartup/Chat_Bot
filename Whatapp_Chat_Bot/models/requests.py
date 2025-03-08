"""Request and response models for the chat API"""
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for chat continuity")

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str = Field(..., description="AI response")
    session_id: Optional[str] = Field(None, description="Session ID for chat continuity")

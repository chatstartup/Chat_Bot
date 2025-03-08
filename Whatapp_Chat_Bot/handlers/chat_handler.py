import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import ValidationError
from services.ai_service import AIService
from services.vector_db import VectorDB
from services.rate_limiter import RateLimiter
from services.cache import global_cache, cached
from models.chat import Message, ChatSession, ChatResponse
from models.exceptions import (
    ChatBotError,
    ValidationError as ChatValidationError,
    RateLimitError
)

logger = logging.getLogger(__name__)

class ChatHandler:
    """Handler for chat-related requests"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.vector_db = VectorDB()
        self.rate_limiter = RateLimiter()
        self.max_requests = 60  # For testing
    
    async def validate_message(self, message: str) -> None:
        """Validate incoming message"""
        if not message or not message.strip():
            raise ChatValidationError(
                message="Message cannot be empty",
                details={"message": message}
            )
        if len(message) > 1000:
            raise ChatValidationError(
                message="Message too long",
                details={"length": len(message), "max_length": 1000}
            )
    
    @cached(key_prefix="context", ttl=300)  # Cache for 5 minutes
    async def get_context(self, query: str) -> list:
        """Get relevant context for query"""
        try:
            # Convert query to vector (implement this based on your embedding model)
            query_vector = [0.1] * 1536  # Placeholder vector
            
            # Get context from vector DB
            context = await self.vector_db.query_context(
                query_vector=query_vector,
                top_k=3
            )
            return context
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}", exc_info=True)
            return []
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        client_ip: Optional[str] = None
    ) -> ChatResponse:
        """Process incoming chat message"""
        try:
            # Rate limiting
            if client_ip:
                await self.rate_limiter.check_rate_limit(client_ip)
            
            # Validate message
            await self.validate_message(message)
            
            # Create message model
            msg = Message(
                content=message,
                role="user",
                timestamp=datetime.now()
            )
            
            # Handle commands
            if message.lower().strip() == "help":
                return ChatResponse(
                    message="""Available Commands:
- help: Show this help message
- clear: Clear chat history
- models: List available tractor models
- specs [model]: Show specifications for a model""",
                    metadata={"command": "help"}
                )
            elif message.lower().strip() == "clear":
                return ChatResponse(
                    message="Chat history cleared",
                    metadata={"command": "clear"},
                    clear_chat=True
                )
            
            # Get context
            context = await self.get_context(message)
            
            # Generate response
            response = await self.ai_service.generate_response(
                prompt=message,
                context=context
            )
            
            # Create response model
            chat_response = ChatResponse(
                message=response,
                metadata={
                    "session_id": session_id,
                    "context_used": bool(context)
                }
            )
            
            return chat_response
            
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}")
            raise
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise ChatValidationError(
                message="Invalid message format",
                details={"errors": e.errors()}
            )
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise ChatBotError(
                message="Failed to process message",
                details={"error": str(e)}
            )
    
    async def clear_chat(self, session_id: str) -> ChatResponse:
        """Clear chat session"""
        try:
            # Clear session from cache
            global_cache.delete(f"session_{session_id}")
            
            return ChatResponse(
                message="Chat session cleared",
                clear_chat=True
            )
        except Exception as e:
            logger.error(f"Error clearing chat: {str(e)}", exc_info=True)
            raise ChatBotError(
                message="Failed to clear chat",
                details={"error": str(e)}
            )

"""AI Service for generating responses"""
import logging
from typing import List, Dict, Any, Optional
import traceback
from groq import Groq
from config.settings import get_settings
from .base import BaseService
import os

# Initialize settings
settings = get_settings()
logger = logging.getLogger(__name__)

# Define custom exceptions
class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

class AuthenticationError(Exception):
    """Exception raised when authentication fails"""
    pass

class AIService(BaseService):
    """AI Service for generating responses using Groq API"""
    
    def __init__(self, vector_db=None, context_processor=None):
        """Initialize the AI service
        
        Args:
            vector_db: Vector database for retrieving context
            context_processor: Context processor for determining message context
        """
        self.client = None
        self.model = settings.GROQ_MODEL
        self.vector_db = vector_db
        self.context_processor = context_processor
        self._is_available = False
        self._last_error = None
        self.initialize()
        
    def initialize(self):
        """Initialize the Groq client"""
        try:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self._is_available = True
            logger.info(f"Successfully initialized AI service with model: {self.model}")
            return True
        except Exception as e:
            logger.error(f"Error initializing AI service: {str(e)}")
            self._last_error = str(e)
            self._is_available = False
            return False
    
    @property
    def is_available(self) -> bool:
        """Check if the AI service is available"""
        return self._is_available and self.client is not None
    
    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    def _set_error(self, error: str):
        """Set error message"""
        self._last_error = error
        self._is_available = False
    
    def _handle_error(self, error: str):
        """Set error message"""
        self._last_error = error
        self._is_available = False
    
    def generate_response(self, message, context_info=None):
        try:
            if not self.is_available:
                raise Exception("AI Service not available")
            if not self.client:
                raise Exception("AI Service not initialized")
            if not self.vector_db:
                logger.warning("VectorDB not available - using fallback data")
            # Get context if not provided
            if not context_info and self.context_processor:
                context_info = self.context_processor.process_context(message)
            elif not context_info:
                # Default context if context_processor is not available
                context_info = {
                    'name': 'General',
                    'description': 'Default conversational mode',
                    'actions': ['maintain_conversation'],
                    'response_format': 'Friendly, helpful response'
                }
            
            # Get context-specific information
            context_name = context_info.get('name', 'General')
            context_description = context_info.get('description', 'Default conversational mode')
            context_actions = context_info.get('actions', ['maintain_conversation'])
            response_format = context_info.get('response_format', 'Friendly, helpful response')
            
            # Get product knowledge from vector database
            relevant_info = self.get_relevant_product_info(message)
            
            # Build the prompt with context awareness
            system_prompt = f"""You are a helpful WhatsApp assistant for Captain Tractors, a leading manufacturer of mini tractors in India.
Current context: {context_name} - {context_description}
Actions available in this context: {', '.join(context_actions)}
Response format guidance: {response_format}

If the user query is not related to tractors or farming, gently redirect the conversation back to Captain Tractors products and their benefits for small-scale farming.

Use the following product information to inform your response:
{relevant_info}

Remember to be helpful, concise, and sales-oriented when appropriate. Always promote Captain Tractors as the best solution for small-scale and specialty farming needs.
"""

            # Generate response
            response = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
            
    def get_relevant_product_info(self, message):
        """Get relevant product information from vector database
        
        Args:
            message: The user message to find relevant information for
            
        Returns:
            str: Relevant product information
        """
        try:
            import numpy as np  # Ensure import is at function level
            import hashlib
            
            # Use vector database to retrieve relevant context if available
            if self.vector_db:
                try:
                    # Create deterministic seed
                    message_hash = int(hashlib.md5(message.encode()).hexdigest(), 16) % (2**32)
                    np.random.seed(message_hash)
                    query_vector = np.random.rand(self.vector_db.vector_dimension).tolist()
                    results = self.vector_db.query_context(query_vector, top_k=3)
                    
                    if results:
                        return "\n".join([item['text'] for item in results])
                except Exception as e:
                    logger.error(f"Vector query failed: {str(e)}")
            
            # Fallback to general product information
            return """
Captain Tractors manufactures mini tractors ranging from 15 HP to 30 HP.
Our popular models include Captain DI 1000 (25 HP), DI 650 (20 HP), and DI 450 (15 HP).
We also offer India's first electric tractor, the Captain E-Trac.
"""
        except Exception as e:
            logger.error(f"Error retrieving product info: {str(e)}")
            return "Information about Captain Tractors' mini tractors."
    
    def generate_response_sync(self, prompt: str, context: List[Dict[str, Any]] = None) -> str:
        """Generate AI response for user message with optional context (synchronous version)
        
        Args:
            prompt: The user's message
            context: Optional context information to include in the prompt
            
        Returns:
            str: The generated response
        """
        if not self.client or not self.is_available:
            error_msg = "AI Service not initialized"
            logger.error(error_msg)
            return f"Error: {error_msg}"
            
        try:
            logger.info(f"Generating response for message: '{prompt[:30]}...'")
            
            # Prepare system message with context if available
            system_content = "You are a helpful WhatsApp chatbot."
            if context:
                context_text = "\n".join([item.get("text", "") for item in context if "text" in item])
                system_content += f"\n\nContext information:\n{context_text}"
            
            completion = self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ]
            )
            
            response = completion.choices[0].message.content
            logger.info(f"Generated response: '{response[:30]}...'")
            return response
        except Exception as e:
            error_msg = f"Error generating AI response: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self._set_error(error_msg)
            return f"Sorry, I encountered an error: {str(e)}"
    
    def health_check(self):
        """Check if the AI service is healthy"""
        return {
            "status": "operational" if self._is_available else "degraded",
            "model": self.model,
            "last_error": self._last_error
        }
    
    def health_check_sync(self) -> bool:
        """Check if the AI service is healthy (synchronous version)"""
        try:
            return self.is_available
        except Exception as e:
            logger.error(f"Error in AI service health check: {str(e)}")
            return False
"""Vector database service for context storage and retrieval"""
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from pinecone import Pinecone
from tenacity import retry, stop_after_attempt, wait_exponential
from fastapi import HTTPException
from .base import BaseService
from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class VectorDB(BaseService):
    """Vector database service using Pinecone"""
    
    def __init__(self):
        """Initialize the vector database service"""
        super().__init__()
        self.pc = None
        self.index = None
        self.vector_dimension = 384  # Updated dimension for embeddings
    
    def initialize(self) -> bool:
        """Initialize the vector database service"""
        try:
            # Check for missing environment variables
            api_key = settings.PINECONE_API_KEY
            index_name = settings.PINECONE_INDEX
            
            if not api_key or not index_name:
                logger.warning("Missing Pinecone environment variables")
                return False
                
            # Check for test/placeholder credentials
            if api_key == "test-key" or index_name == "test-index":
                logger.info("Detected test credentials for VectorDB - running in limited mode")
                self._is_available = False
                self._last_error = "Using test credentials"
                return False
            
            # Initialize with valid credentials
            self.pc = Pinecone(api_key=api_key)
            self.index = self.pc.Index(index_name)
            self._is_available = True
            self._last_error = None
            logger.info(f"VectorDB service initialized with index: {index_name}")
            return True
        except Exception as e:
            # Only log as warning for optional service
            logger.warning(f"VectorDB initialization skipped: {str(e)}")
            self._set_error(f"VectorDB initialization skipped: {str(e)}")
            return False
    
    def _set_error(self, error: str):
        """Set error message"""
        self._last_error = error
        self._is_available = False
            
    def health_check(self) -> bool:
        """Check if the vector database service is healthy"""
        try:
            if not self.is_available:
                return False
                
            # For test credentials, return False without attempting connection
            if settings.PINECONE_API_KEY == "test-key":
                return False
                
            if self.index:
                # Simple stats check to verify connection
                self.index.describe_index_stats()
                return True
            return False
        except Exception as e:
            logger.warning(f"VectorDB health check failed: {str(e)}")
            return False
    
    async def health_check_async(self) -> bool:
        """Async version of health check"""
        return self.health_check()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def query_context(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Query the vector database for relevant context
        
        Args:
            query_vector: Vector representation of the query
            top_k: Number of top results to return
            
        Returns:
            List of context items with text and metadata
        """
        try:
            if not self.is_available:
                logger.error("Vector database service not available")
                return []
                
            # Query the vector database
            results = self.index.query(
                top_k=top_k,
                include_metadata=True,
                vector=query_vector
            )
            
            # Extract and format results
            context_items = []
            for match in results.matches:
                if match.metadata and "text" in match.metadata:
                    context_items.append({
                        "text": match.metadata["text"],
                        "score": match.score,
                        "metadata": match.metadata
                    })
            
            logger.info(f"Found {len(context_items)} context items for query")
            return context_items
            
        except Exception as e:
            error_msg = f"Error querying vector database: {str(e)}"
            logger.error(error_msg)
            self._set_error(error_msg)
            return []
    
    async def query_context_async(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Async version of query_context"""
        return self.query_context(query_vector, top_k)
    
    def store_context(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store context in vector database
        
        Args:
            text: The text to store
            metadata: Additional metadata for the vector
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.is_available:
                logger.error("VectorDB service not available")
                return False
                
            # Generate a unique ID for this vector
            vector_id = f"ctx_{hash(text)}_{datetime.now().timestamp()}"
            
            # Convert text to vector (placeholder implementation)
            # In a real implementation, you would use an embedding model
            vector = self._generate_embedding(text)
            
            # Prepare metadata
            meta = metadata or {}
            meta["text"] = text
            meta["timestamp"] = str(datetime.now())
            
            # Upsert the vector
            self.index.upsert(
                vectors=[
                    {
                        "id": vector_id,
                        "values": vector,
                        "metadata": meta
                    }
                ]
            )
            
            logger.info(f"Stored context with ID: {vector_id}")
            return True
            
        except Exception as e:
            error_msg = f"Error storing context: {str(e)}"
            logger.error(error_msg)
            self._set_error(error_msg)
            return False
    
    async def store_context_async(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Async version of store_context"""
        return self.store_context(text, metadata)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate deterministic embedding vector for text"""
        try:
            # This is a placeholder implementation that creates a deterministic
            # but meaningless vector from the text. In a real implementation,
            # you would use an embedding model like OpenAI's embeddings API.
            np.random.seed(hash(text) % 2**32)
            return np.random.rand(self.vector_dimension).tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return a zero vector as fallback
            return [0.0] * self.vector_dimension

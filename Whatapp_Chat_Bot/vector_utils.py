import logging
from typing import List, Optional
import pinecone
from groq import AsyncGroq
from config.settings import get_settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)
settings = get_settings()

class VectorManager:
    def __init__(self):
        """Initialize the VectorManager with Pinecone and Groq clients."""
        self._is_available = False
        self.groq_client = None
        self.index = None
        
        logger.debug(f"Initializing VectorManager with keys - Pinecone: {bool(settings.PINECONE_API_KEY)}, Groq: {bool(settings.GROQ_API_KEY)}")
        
        if not settings.GROQ_API_KEY or not settings.PINECONE_API_KEY:
            logger.error("Required API keys missing. GROQ_API_KEY or PINECONE_API_KEY not set")
            raise HTTPException(
                status_code=500,
                detail="Required API keys missing. Check your configuration."
            )
            
        try:
            # Initialize Groq client
            self.groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
            
            # Initialize Pinecone
            pc = pinecone.Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Get or create index
            try:
                self.index = pc.Index(settings.PINECONE_INDEX)
                logger.info(f"Connected to existing Pinecone index: {settings.PINECONE_INDEX}")
            except Exception as e:
                logger.warning(f"Index {settings.PINECONE_INDEX} not found, creating new index")
                # Create new index if it doesn't exist
                pc.create_index(
                    name=settings.PINECONE_INDEX,
                    dimension=1536,  # OpenAI embedding dimension
                    metric='cosine',
                    spec=pinecone.ServerlessSpec(
                        cloud=settings.PINECONE_CLOUD or 'aws',
                        region=settings.PINECONE_REGION or 'us-west-2'
                    )
                )
                self.index = pc.Index(settings.PINECONE_INDEX)
                logger.info(f"Created new Pinecone index: {settings.PINECONE_INDEX}")
            
            self._is_available = True
            logger.info("Successfully initialized VectorManager")
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize vector services: {str(e)}"
            )
    
    @property
    def is_available(self) -> bool:
        """Check if the service is available."""
        return self._is_available and self.index is not None
    
    async def upsert_vectors(self, vectors: List[dict], namespace: Optional[str] = "") -> bool:
        """Upsert vectors to Pinecone index."""
        if not self.is_available:
            raise HTTPException(
                status_code=503,
                detail="Vector service is not available"
            )
        
        try:
            self.index.upsert(vectors=vectors, namespace=namespace)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upsert vectors: {str(e)}"
            )
    
    async def query_vectors(self, query_vector: List[float], top_k: int = 5, namespace: Optional[str] = ""):
        """Query vectors from Pinecone index."""
        if not self.is_available:
            raise HTTPException(
                status_code=503,
                detail="Vector service is not available"
            )
        
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query vectors: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to query vectors: {str(e)}"
            )
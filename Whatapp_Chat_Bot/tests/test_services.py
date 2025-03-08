"""Unit tests for services"""
import pytest
import unittest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from redis.exceptions import RedisError
from services.cache import CacheService
from services.ai_service import AIService
from services.vector_db import VectorDB
from services.memory_cache import MemoryCache

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch("services.cache.Redis") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def cache_service(mock_redis):
    """Cache service fixture"""
    return CacheService()

@pytest.fixture
def ai_service():
    """AI service fixture"""
    return AIService()

@pytest.fixture
def vector_db():
    """Vector DB fixture"""
    return VectorDB()

@pytest.fixture
def memory_cache():
    """Memory cache fixture"""
    return MemoryCache()

class TestCacheService:
    """Test cache service functionality"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, cache_service, mock_redis):
        """Test successful initialization"""
        mock_redis.ping.return_value = True
        assert await cache_service.initialize()
        assert cache_service.is_available
        
    @pytest.mark.asyncio
    async def test_initialize_failure(self, cache_service, mock_redis):
        """Test failed initialization"""
        mock_redis.ping.side_effect = RedisError()
        assert not await cache_service.initialize()
        assert not cache_service.is_available
        
    @pytest.mark.asyncio
    async def test_get_success(self, cache_service, mock_redis):
        """Test successful get operation"""
        mock_redis.get.return_value = '{"key": "value"}'
        cache_service._is_available = True
        result = await cache_service.get("test_key")
        assert result == {"key": "value"}
        
    @pytest.mark.asyncio
    async def test_set_success(self, cache_service, mock_redis):
        """Test successful set operation"""
        cache_service._is_available = True
        assert await cache_service.set("test_key", {"key": "value"})
        mock_redis.set.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_rate_limit(self, cache_service, mock_redis):
        """Test rate limiting"""
        cache_service._is_available = True
        mock_redis.pipeline.return_value.execute.return_value = [5]
        allowed, remaining = await cache_service.rate_limit_check(
            "test_key",
            limit=10,
            window=60
        )
        assert allowed
        assert remaining == 5

class TestAIService:
    """Test AI service functionality"""
    
    @pytest.mark.asyncio
    async def test_generate_response(self, ai_service):
        """Test response generation"""
        with patch.object(ai_service, "_call_llm") as mock_llm:
            mock_llm.return_value = "Test response"
            response = await ai_service.generate_response(
                "Test prompt",
                context=[{"text": "Test context"}]
            )
            assert response == "Test response"
            mock_llm.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_health_check(self, ai_service):
        """Test health check"""
        with patch.object(ai_service, "_call_llm") as mock_llm:
            mock_llm.return_value = "Test response"
            assert await ai_service.health_check()

class TestVectorDB:
    """Test vector database functionality"""
    
    @pytest.mark.asyncio
    async def test_query_context(self, vector_db):
        """Test context querying"""
        with patch.object(vector_db, "_query") as mock_query:
            mock_query.return_value = [
                {"text": "Test context", "score": 0.9}
            ]
            context = await vector_db.query_context("Test query")
            assert len(context) == 1
            assert context[0]["text"] == "Test context"
            mock_query.assert_called_once()

class TestCoreServices:
    @patch('services.ai_service.Groq')
    def test_response_generation(self, mock_groq):
        """Test AI response generation"""
        mock_client = mock_groq.return_value
        mock_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Test Response"))]
        )
        
        ai = AIService()
        ai.initialize()
        assert ai.generate_response("Test prompt") == "Test Response"

    def test_cache_operations(self):
        """Test cache set/get/delete operations"""
        cache = MemoryCache()
        cache.initialize()
        
        assert cache.set("key", "value") is True
        assert cache.get("key") == "value"
        assert cache.delete("key") is True
        assert cache.get("key") is None

    @patch('services.vector_db.Pinecone')
    def test_vector_operations(self, mock_pinecone):
        """Test vector database operations"""
        mock_index = mock_pinecone.Index.return_value
        mock_index.upsert.return_value = True
        
        db = VectorDB()
        db.initialize()
        assert db.upsert_vectors([("id", [0.1, 0.2])]) is True

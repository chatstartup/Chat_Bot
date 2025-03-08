"""Test configuration and fixtures"""
import os
import pytest
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from fastapi.testclient import TestClient
from services.ai_service import AIService
from services.vector_db import VectorDB
from services.memory_cache import MemoryCache
from main import app

# Set test environment
os.environ["ENV"] = "test"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["PINECONE_API_KEY"] = "test-key"
os.environ["JWT_SECRET_KEY"] = "test-key"
os.environ["PINECONE_ENVIRONMENT"] = "test"
os.environ["AZURE_TRANSLATOR_KEY"] = "test_key"
os.environ["AZURE_TRANSLATOR_ENDPOINT"] = "https://test.endpoint"

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    service = Mock(spec=AIService)
    service.generate_response = AsyncMock(return_value="Test response")
    return service

@pytest.fixture
def mock_vector_db():
    """Mock vector database for testing"""
    db = Mock(spec=VectorDB)
    db.query_context = AsyncMock(return_value=[
        {
            "text": "Test context",
            "score": 0.9,
            "source": "test"
        }
    ])
    db.is_available = True
    return db

@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings for tests"""
    with patch("config.settings.get_settings") as mock:
        mock.return_value = MagicMock(
            RATE_LIMIT_RPM=60,
            CHAT_CACHE_TTL=3600,
            CORS_ORIGINS=["*"],
            JWT_ALGORITHM="HS256",
            REDIS_HOST="localhost",
            REDIS_PORT=6379,
            REDIS_DB=0
        )
        yield mock

@pytest.fixture(autouse=True)
def mock_logger():
    """Mock logger for tests"""
    with patch("logging.getLogger") as mock:
        mock.return_value = MagicMock()
        yield mock

@pytest.fixture(autouse=True)
def mock_services(monkeypatch):
    """Mock external service dependencies"""
    # Mock AI Service
    mock_ai = Mock(spec=AIService)
    mock_ai.generate_response.return_value = "Mocked AI Response"
    mock_ai.health_check.return_value = True
    monkeypatch.setattr('services.ai_service.AIService', lambda: mock_ai)
    
    # Mock Memory Cache
    mock_cache = Mock(spec=MemoryCache)
    mock_cache.get.return_value = None
    mock_cache.health_check.return_value = True
    monkeypatch.setattr('services.memory_cache.MemoryCache', lambda: mock_cache)

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv('PINECONE_API_KEY', 'test-key')
    monkeypatch.setenv('PINECONE_INDEX', 'test-index')
    monkeypatch.setenv('GROQ_API_KEY', 'test-key')

@pytest.fixture(autouse=True)
def test_env():
    """Set test environment variables"""
    yield
    # Clean up
    os.environ.pop("GROQ_API_KEY", None)
    os.environ.pop("PINECONE_API_KEY", None)
    os.environ.pop("PINECONE_ENVIRONMENT", None)
    os.environ.pop("AZURE_TRANSLATOR_KEY", None)
    os.environ.pop("AZURE_TRANSLATOR_ENDPOINT", None)

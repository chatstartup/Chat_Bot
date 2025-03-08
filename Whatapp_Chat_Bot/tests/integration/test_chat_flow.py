import pytest
from unittest.mock import patch, AsyncMock
import json
from datetime import datetime
from handlers.chat_handler import ChatHandler
from models.chat import ChatResponse
from models.exceptions import ChatValidationError, RateLimitError
from services.ai_service import AIService
from services.vector_db import VectorDB

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    with patch.object(AIService, 'generate_response', new_callable=AsyncMock) as mock:
        mock.return_value = "This is a test response about tractors."
        yield mock

@pytest.fixture
def mock_vector_db():
    """Mock vector DB for testing"""
    with patch.object(VectorDB, 'query_context', new_callable=AsyncMock) as mock:
        mock.return_value = [{"text": "Test context about tractors"}]
        yield mock

@pytest.mark.asyncio
async def test_chat_flow(mock_ai_service, mock_vector_db):
    """Test complete chat flow"""
    # Create handler with mocked services
    with patch.object(ChatHandler, 'ai_service') as mock_handler_ai, \
         patch.object(ChatHandler, 'vector_db') as mock_handler_vector:
        
        # Set up the mocks on the handler
        mock_handler_ai.generate_response = mock_ai_service
        mock_handler_vector.query_context = mock_vector_db
        
        handler = ChatHandler()
        
        # Test basic message
        response = await handler.process_message(
            message="Tell me about your tractors",
            session_id="test_session",
            client_ip="127.0.0.1"
        )
        assert isinstance(response, ChatResponse)
        assert response.message
        assert not response.error
        
        # Test help command
        response = await handler.process_message(
            message="help",
            session_id="test_session",
            client_ip="127.0.0.1"
        )
        assert isinstance(response, ChatResponse)
        assert "Available Commands" in response.message
        assert response.metadata and response.metadata.get("command") == "help"

@pytest.mark.asyncio
async def test_error_handling(mock_ai_service):
    """Test error handling in chat flow"""
    handler = ChatHandler()
    
    # Test empty message
    with pytest.raises(ChatValidationError):
        await handler.process_message(
            message="",
            session_id="test_session",
            client_ip="127.0.0.1"
        )
    
    # Test message too long
    with pytest.raises(ChatValidationError):
        await handler.process_message(
            message="x" * 1001,  # Message longer than 1000 chars
            session_id="test_session",
            client_ip="127.0.0.1"
        )

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting in chat flow"""
    handler = ChatHandler()
    handler.max_requests = 1  # Set low limit for testing
    
    # First request should succeed
    response = await handler.process_message(
        message="Test message",
        session_id="test_session",
        client_ip="127.0.0.1"
    )
    assert isinstance(response, ChatResponse)
    
    # Second request should fail with rate limit error
    with patch.object(handler.rate_limiter, 'check_rate_limit', side_effect=RateLimitError("Rate limit exceeded")):
        with pytest.raises(RateLimitError):
            await handler.process_message(
                message="Another test",
                session_id="test_session",
                client_ip="127.0.0.1"
            )

@pytest.mark.asyncio
async def test_context_retrieval(mock_vector_db):
    """Test context retrieval in chat flow"""
    handler = ChatHandler()
    
    # Mock the vector_db on the handler
    with patch.object(handler, 'vector_db') as mock_handler_vector:
        mock_handler_vector.query_context = mock_vector_db
        
        # Call get_context
        context = await handler.get_context("What are the specs of the tractor?")
        
        # Verify context was retrieved
        assert context
        assert isinstance(context, list)
        assert context[0]["text"] == "Test context about tractors"
        
        # Verify vector_db was called
        mock_vector_db.assert_called_once()

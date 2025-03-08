"""Unit tests for AI Service"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from services.ai_service import AIService
from config.settings import get_settings

class TestAIService:
    """Test suite for AI Service"""
    
    @pytest.fixture
    def ai_service(self):
        """Create an AI service instance for testing"""
        return AIService()
    
    @pytest.fixture
    def mock_groq_client(self):
        """Mock Groq client for testing"""
        with patch('services.ai_service.Groq') as mock_groq:
            mock_client = MagicMock()
            mock_chat = MagicMock()
            mock_completions = MagicMock()
            
            # Set up the mock response
            mock_message = MagicMock()
            mock_message.content = "Test response"
            
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            
            # Set up the chain of calls
            mock_completions.create.return_value = mock_response
            mock_chat.completions = mock_completions
            mock_client.chat = mock_chat
            mock_groq.return_value = mock_client
            
            yield mock_groq
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing"""
        with patch('services.ai_service.get_settings') as mock:
            mock_settings = MagicMock()
            mock_settings.GROQ_API_KEY = "test-key"
            mock_settings.GROQ_MODEL = "test-model"
            mock.return_value = mock_settings
            yield mock_settings
    
    def test_initialize_success(self, ai_service, mock_groq_client, mock_settings):
        """Test successful initialization"""
        result = ai_service.initialize()
        
        assert result is True
        assert ai_service.last_error is None
        assert ai_service.client is not None
        mock_groq_client.assert_called_once_with(api_key=mock_settings.GROQ_API_KEY)
    
    def test_initialize_failure_no_api_key(self, ai_service, mock_settings):
        """Test initialization failure when API key is not set"""
        mock_settings.GROQ_API_KEY = None
        
        result = ai_service.initialize()
        
        assert result is False
        assert ai_service.last_error is not None
        assert "not set" in ai_service.last_error
    
    def test_initialize_failure_exception(self, ai_service, mock_groq_client):
        """Test initialization failure when an exception occurs"""
        mock_groq_client.side_effect = Exception("Test error")
        
        result = ai_service.initialize()
        
        assert result is False
        assert ai_service.last_error is not None
        assert "Test error" in ai_service.last_error
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, mock_groq_client):
        """Test successful response generation"""
        # Initialize the service
        ai_service = AIService()
        ai_service.initialize()
        
        # Test the response generation
        response = await ai_service.generate_response("Hello")
        
        assert response == "Test response"
        # Verify the client was called with the right parameters
        mock_client = mock_groq_client.return_value
        mock_client.chat.completions.create.assert_called_once()
    
    def test_generate_response_not_initialized(self, ai_service):
        """Test response generation when service is not initialized"""
        # Don't initialize the service
        response = ai_service.generate_response("Hello")
        
        assert "Error:" in response
        assert "not initialized" in response
    
    def test_generate_response_exception(self, ai_service, mock_groq_client):
        """Test response generation when an exception occurs"""
        # Initialize the service
        ai_service.initialize()
        
        # Make the client raise an exception
        client = mock_groq_client.return_value
        client.chat.completions.create.side_effect = Exception("Test error")
        
        # Test the response generation
        response = ai_service.generate_response("Hello")
        
        assert "Sorry, I encountered an error" in response
        assert "Test error" in response
    
    def test_health_check_success(self, ai_service):
        """Test health check when service is healthy"""
        # Initialize the service
        with patch.object(ai_service, 'initialize', return_value=True):
            ai_service.initialize()
            assert ai_service.health_check() is True
    
    def test_health_check_failure(self, ai_service):
        """Test health check when service has an error"""
        # Set an error
        ai_service._set_error("Test error")
        assert ai_service.health_check() is False

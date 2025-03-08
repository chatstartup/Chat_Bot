"""Comprehensive test suite for WhatsApp Chat Bot application"""
import unittest
import json
import logging
import sys
import os
import time
from unittest.mock import patch, MagicMock

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestConfiguration(unittest.TestCase):
    """Test configuration and environment setup"""
    
    def test_env_file_exists(self):
        """Test that .env file exists"""
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        self.assertTrue(os.path.exists(env_path), f".env file not found at {env_path}")
    
    def test_env_variables(self):
        """Test that required environment variables are set"""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check required variables
        required_vars = ['GROQ_API_KEY', 'GROQ_MODEL']
        for var in required_vars:
            value = os.getenv(var)
            self.assertIsNotNone(value, f"Environment variable {var} is not set")
            self.assertTrue(len(value) > 0, f"Environment variable {var} is empty")
    
    def test_settings_loading(self):
        """Test settings loading"""
        from config.settings import get_settings
        settings = get_settings()
        
        # Check settings attributes
        self.assertIsNotNone(settings.GROQ_API_KEY, "GROQ_API_KEY not set in settings")
        self.assertIsNotNone(settings.GROQ_MODEL, "GROQ_MODEL not set in settings")
        
        # Test caching works
        settings2 = get_settings()
        self.assertIs(settings, settings2, "Settings caching not working")


class TestBaseService(unittest.TestCase):
    """Test base service functionality"""
    
    def test_base_service_methods(self):
        """Test base service methods"""
        from services.base import BaseService
        
        # Create a concrete implementation for testing
        class TestService(BaseService):
            def initialize(self):
                return True
        
        service = TestService()
        
        # Test error handling
        service._set_error("Test error")
        self.assertEqual(service.last_error, "Test error")
        
        # Test health check
        service.last_error = None
        self.assertTrue(service.health_check())
        
        service.last_error = "Error"
        self.assertFalse(service.health_check())


class TestMemoryCache(unittest.TestCase):
    """Test memory cache service"""
    
    def setUp(self):
        """Set up test environment"""
        from services.memory_cache import MemoryCache
        self.cache = MemoryCache()
        self.cache.initialize()
    
    def tearDown(self):
        """Clean up after tests"""
        self.cache.clear()
    
    def test_set_get(self):
        """Test set and get operations"""
        # Test basic set/get
        self.cache.set("test_key", "test_value")
        self.assertEqual(self.cache.get("test_key"), "test_value")
        
        # Test with complex data
        complex_data = {"name": "Test", "data": [1, 2, 3], "nested": {"key": "value"}}
        self.cache.set("complex_key", complex_data)
        self.assertEqual(self.cache.get("complex_key"), complex_data)
        
        # Test non-existent key
        self.assertIsNone(self.cache.get("non_existent_key"))
    
    def test_ttl(self):
        """Test time-to-live functionality"""
        # Set with short TTL
        self.cache.set("ttl_key", "ttl_value", ttl=1)
        self.assertEqual(self.cache.get("ttl_key"), "ttl_value")
        
        # Wait for expiration
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("ttl_key"))
    
    def test_delete(self):
        """Test delete operation"""
        self.cache.set("delete_key", "delete_value")
        self.assertEqual(self.cache.get("delete_key"), "delete_value")
        
        # Delete and verify
        self.assertTrue(self.cache.delete("delete_key"))
        self.assertIsNone(self.cache.get("delete_key"))
        
        # Delete non-existent key
        self.assertTrue(self.cache.delete("non_existent_key"))
    
    def test_clear(self):
        """Test clear operation"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        # Clear and verify
        self.assertTrue(self.cache.clear())
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))


class TestAIService(unittest.TestCase):
    """Test AI service"""
    
    def setUp(self):
        """Set up test environment"""
        from services.ai_service import AIService
        self.ai_service = AIService()
        
        # Use patching to avoid actual API calls during tests
        patcher = patch('services.ai_service.Groq')
        self.mock_groq = patcher.start()
        
        # Configure the mock
        self.mock_client = MagicMock()
        self.mock_chat = MagicMock()
        self.mock_completions = MagicMock()
        
        # Set up the mock response
        mock_message = MagicMock()
        mock_message.content = "Test AI response"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Set up the chain of calls
        self.mock_completions.create.return_value = mock_response
        self.mock_chat.completions = self.mock_completions
        self.mock_client.chat = self.mock_chat
        self.mock_groq.return_value = self.mock_client
        
        # Initialize the service
        self.ai_service.initialize()
        
        # Store the patcher for cleanup
        self.patcher = patcher
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_initialization(self):
        """Test initialization"""
        self.assertIsNotNone(self.ai_service.client)
        self.assertIsNone(self.ai_service.last_error)
        self.mock_groq.assert_called_once()
    
    def test_initialization_error(self):
        """Test initialization error handling"""
        # Stop the current patcher and create a new one that raises an exception
        self.patcher.stop()
        
        with patch('services.ai_service.Groq', side_effect=Exception("Test error")):
            from services.ai_service import AIService
            ai_service = AIService()
            result = ai_service.initialize()
            
            self.assertFalse(result)
            self.assertIsNotNone(ai_service.last_error)
            self.assertIn("Test error", ai_service.last_error)
    
    def test_generate_response(self):
        """Test generate response"""
        response = self.ai_service.generate_response("Hello")
        
        # Verify the response
        self.assertEqual(response, "Test AI response")
        
        # Verify the client was called with the right parameters
        self.mock_completions.create.assert_called_once()
        call_kwargs = self.mock_completions.create.call_args[1]
        self.assertIn("messages", call_kwargs)
        self.assertEqual(len(call_kwargs["messages"]), 2)
        self.assertEqual(call_kwargs["messages"][1]["content"], "Hello")
    
    def test_generate_response_error(self):
        """Test generate response error handling"""
        # Make the client raise an exception
        self.mock_completions.create.side_effect = Exception("Test error")
        
        # Should return error message instead of raising
        response = self.ai_service.generate_response("Hello")
        self.assertIn("Sorry, I encountered an error", response)
        self.assertIn("Test error", response)
    
    def test_health_check(self):
        """Test health check"""
        # Service should be healthy by default
        self.assertTrue(self.ai_service.health_check())
        
        # Set an error and verify health check fails
        self.ai_service._set_error("Test error")
        self.assertFalse(self.ai_service.health_check())


class TestFlaskApp(unittest.TestCase):
    """Test Flask application"""
    
    def setUp(self):
        """Set up test environment"""
        # Patch services before importing app
        self.ai_service_patcher = patch('services.ai_service.AIService')
        self.mock_ai_service_class = self.ai_service_patcher.start()
        self.mock_ai_service = MagicMock()
        self.mock_ai_service.initialize.return_value = True
        self.mock_ai_service.generate_response.return_value = "Test AI response"
        self.mock_ai_service.health_check.return_value = True
        self.mock_ai_service_class.return_value = self.mock_ai_service
        
        self.cache_patcher = patch('services.memory_cache.MemoryCache')
        self.mock_cache_class = self.cache_patcher.start()
        self.mock_cache = MagicMock()
        self.mock_cache.initialize.return_value = True
        self.mock_cache.get.return_value = None
        self.mock_cache.set.return_value = True
        self.mock_cache.health_check.return_value = True
        self.mock_cache_class.return_value = self.mock_cache
        
        # Now import the app
        from app import app
        self.app = app.test_client()
    
    def tearDown(self):
        """Clean up after tests"""
        self.ai_service_patcher.stop()
        self.cache_patcher.stop()
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("services", data)
        self.assertTrue(data["services"]["ai_service"])
        self.assertTrue(data["services"]["cache"])
    
    def test_chat_endpoint(self):
        """Test chat endpoint"""
        # Test valid request
        response = self.app.post('/chat', 
                                json={"message": "Hello", "session_id": "test_session"})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertEqual(data["response"], "Test AI response")
        self.assertIn("session_id", data)
        self.assertEqual(data["session_id"], "test_session")
        
        # Verify service calls
        self.mock_ai_service.generate_response.assert_called_once_with("Hello")
        self.mock_cache.set.assert_called_once()
    
    def test_chat_endpoint_missing_message(self):
        """Test chat endpoint with missing message"""
        response = self.app.post('/chat', 
                                json={"session_id": "test_session"})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_chat_endpoint_empty_message(self):
        """Test chat endpoint with empty message"""
        response = self.app.post('/chat', 
                                json={"message": "", "session_id": "test_session"})
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn("error", data)
    
    def test_chat_endpoint_caching(self):
        """Test chat endpoint caching with session ID preservation"""
        # Set up cache to return a response
        cached_response = {
            "response": "Cached response",
            "session_id": "old_session"
        }
        self.mock_cache.get.return_value = cached_response
        
        # Request with different session ID
        response = self.app.post('/chat', 
                                json={"message": "Hello cache test", "session_id": "new_session"})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        # Response should be from cache
        self.assertEqual(data["response"], "Cached response")
        # But session ID should be updated
        self.assertEqual(data["session_id"], "new_session")
        
        # Verify AI service was not called
        self.mock_ai_service.generate_response.assert_not_called()
    
    def test_index_endpoint(self):
        """Test index endpoint"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"WhatsApp Chat Bot", response.data)


class TestEndToEnd(unittest.TestCase):
    """End-to-end tests"""
    
    def setUp(self):
        """Set up test environment"""
        # For E2E tests, we'll use the real services but mock the external API calls
        with patch('services.ai_service.Groq') as mock_groq:
            # Configure the mock
            mock_client = MagicMock()
            mock_chat = MagicMock()
            mock_completions = MagicMock()
            
            # Set up the mock response
            mock_message = MagicMock()
            mock_message.content = "I'm a helpful WhatsApp chatbot. How can I assist you today?"
            
            mock_choice = MagicMock()
            mock_choice.message = mock_message
            
            mock_response = MagicMock()
            mock_response.choices = [mock_choice]
            
            # Set up the chain of calls
            mock_completions.create.return_value = mock_response
            mock_chat.completions = mock_completions
            mock_client.chat = mock_chat
            mock_groq.return_value = mock_client
            
            # Import the app after patching
            from app import app
            self.app = app.test_client()
    
    def test_full_chat_flow(self):
        """Test full chat flow"""
        # First message
        response1 = self.app.post('/chat', 
                               json={"message": "Tell me about yourself", "session_id": "e2e_test"})
        self.assertEqual(response1.status_code, 200)
        
        data1 = json.loads(response1.data)
        self.assertIn("response", data1)
        self.assertTrue(len(data1["response"]) > 0)
        self.assertEqual(data1["session_id"], "e2e_test")
        
        # Second message with same session ID
        response2 = self.app.post('/chat', 
                               json={"message": "What can you help me with?", "session_id": "e2e_test"})
        self.assertEqual(response2.status_code, 200)
        
        data2 = json.loads(response2.data)
        self.assertIn("response", data2)
        self.assertTrue(len(data2["response"]) > 0)
        self.assertEqual(data2["session_id"], "e2e_test")


if __name__ == "__main__":
    unittest.main()

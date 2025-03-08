"""Test script for WhatsApp Chat Bot application"""
import unittest
import json
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)
logger = logging.getLogger(__name__)

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestChatBot(unittest.TestCase):
    """Test cases for WhatsApp Chat Bot"""
    
    def setUp(self):
        """Set up test environment"""
        logger.info("Setting up test environment")
        
        # Test environment variables
        self.check_environment_variables()
        
        # Import services after environment check
        from services.ai_service import AIService
        from services.memory_cache import MemoryCache
        
        # Initialize services
        self.ai_service = AIService()
        self.cache_service = MemoryCache()
        
        # Initialize services
        self.assertTrue(self.ai_service.initialize(), "AI Service initialization failed")
        self.assertTrue(self.cache_service.initialize(), "Memory Cache initialization failed")
        
        logger.info("Test environment setup complete")
    
    def check_environment_variables(self):
        """Check if required environment variables are set"""
        logger.info("Checking environment variables")
        
        # Check .env file
        from dotenv import load_dotenv, find_dotenv
        env_file = find_dotenv()
        if not env_file:
            logger.warning("No .env file found")
        else:
            logger.info(f"Found .env file at: {env_file}")
            load_dotenv(env_file)
        
        # Check GROQ API key
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.assertIsNotNone(groq_api_key, "GROQ_API_KEY is not set")
        self.assertTrue(len(groq_api_key) > 0, "GROQ_API_KEY is empty")
        logger.info("GROQ_API_KEY is set")
        
        # Check GROQ model
        groq_model = os.getenv("GROQ_MODEL")
        self.assertIsNotNone(groq_model, "GROQ_MODEL is not set")
        self.assertTrue(len(groq_model) > 0, "GROQ_MODEL is empty")
        logger.info(f"GROQ_MODEL is set to: {groq_model}")
    
    def test_settings(self):
        """Test settings loading"""
        logger.info("Testing settings loading")
        
        from config.settings import get_settings
        settings = get_settings()
        
        self.assertIsNotNone(settings, "Settings is None")
        self.assertIsNotNone(settings.GROQ_API_KEY, "GROQ_API_KEY is not set in settings")
        self.assertIsNotNone(settings.GROQ_MODEL, "GROQ_MODEL is not set in settings")
        
        logger.info("Settings test passed")
    
    def test_memory_cache(self):
        """Test memory cache functionality"""
        logger.info("Testing memory cache")
        
        # Test set and get
        key = "test_key"
        value = {"test": "value"}
        ttl = 60
        
        self.assertTrue(self.cache_service.set(key, value, ttl), "Failed to set cache")
        cached_value = self.cache_service.get(key)
        
        self.assertEqual(cached_value, value, "Cache get value does not match set value")
        
        # Test delete
        self.assertTrue(self.cache_service.delete(key), "Failed to delete cache")
        self.assertIsNone(self.cache_service.get(key), "Cache value still exists after delete")
        
        logger.info("Memory cache test passed")
    
    def test_ai_service(self):
        """Test AI service functionality"""
        logger.info("Testing AI service")
        
        # Test generate response
        message = "Hello, how are you?"
        response = self.ai_service.generate_response(message)
        
        self.assertIsNotNone(response, "AI response is None")
        self.assertTrue(len(response) > 0, "AI response is empty")
        
        logger.info("AI service test passed")
    
    def test_flask_app(self):
        """Test Flask app endpoints"""
        logger.info("Testing Flask app endpoints")
        
        # Import Flask app
        from app import app
        
        # Create test client
        self.client = app.test_client()
        
        # Test health endpoint
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200, "Health endpoint returned non-200 status code")
        data = json.loads(response.data)
        
        # Allow degraded status if optional services are missing
        self.assertIn(data["status"], ["healthy", "degraded"], "Unexpected health status")
        self.assertTrue(data["services"]["ai_service"], "AI service should be healthy")
        self.assertTrue(data["services"]["cache_service"], "Cache service should be healthy")
        # VectorDB may be unhealthy due to test configuration
        self.assertIsInstance(data["services"]["vector_db"], bool, "Invalid vector_db status type")
        
        # Test chat endpoint
        chat_data = {
            "message": "Test message",
            "session_id": "test-session"
        }
        response = self.client.post('/chat', json=chat_data)
        self.assertEqual(response.status_code, 200, "Chat endpoint returned non-200 status code")
        data = json.loads(response.data)
        self.assertIn("response", data, "Chat endpoint response does not contain 'response' field")
        self.assertIn("session_id", data, "Chat endpoint response does not contain 'session_id' field")
        
        logger.info("Flask app test passed")
    
    def test_error_handling(self):
        """Test error scenarios"""
        logger.info("Testing error handling")
        
        # Test empty message
        response = self.client.post('/chat', json={"message": ""})
        self.assertEqual(response.status_code, 400)
        
        # Test invalid JSON
        response = self.client.post('/chat', data="invalid")
        self.assertEqual(response.status_code, 400)
        
        # Test missing service scenario
        with unittest.mock.patch('services.ai_service.AIService.generate_response', side_effect=Exception("Service error")):
            response = self.client.post('/chat', json={"message": "test"})
            self.assertEqual(response.status_code, 500)
        
        logger.info("Error handling tests passed")

    # Add any needed test improvements here

if __name__ == "__main__":
    unittest.main()

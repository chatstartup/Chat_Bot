"""Unit tests for Flask application"""
import pytest
import json
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient

# Import the Flask app
from app import app, ai_service

@pytest.fixture
def client() -> FlaskClient:
    """Test client fixture for Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing"""
    with patch.object(ai_service, 'generate_response') as mock:
        mock.return_value = "Test AI response"
        yield mock

@pytest.fixture
def mock_context_processor():
    """Mock ContextProcessor for testing"""
    with patch('app.ContextProcessor') as mock:
        mock_instance = MagicMock()
        mock_instance.process_context.return_value = {
            'name': 'Test Context',
            'actions': ['action1', 'action2']
        }
        mock.return_value = mock_instance
        yield mock_instance

class TestHealthEndpoint:
    """Tests for the health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test successful health check"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
    
    def test_health_check_with_service_error(self, client):
        """Test health check when a service has an error"""
        with patch.object(ai_service, 'health_check', return_value=False):
            response = client.get('/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            # Even with service errors, the endpoint should return 200
            assert data['status'] == 'healthy'

class TestChatEndpoint:
    """Tests for the chat endpoint"""
    
    def test_chat_success(self, client, mock_ai_service, mock_context_processor):
        """Test successful chat request"""
        response = client.post(
            '/chat',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
        assert data['response'] == 'Test AI response'
        assert data['context'] == 'Test Context'
        assert 'suggested_actions' in data
        
        # Verify service calls
        mock_ai_service.assert_called_once()
        mock_context_processor.process_context.assert_called_once_with('Hello')
    
    def test_chat_missing_message(self, client):
        """Test chat with missing message"""
        response = client.post(
            '/chat',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_chat_empty_message(self, client):
        """Test chat with empty message"""
        response = client.post(
            '/chat',
            data=json.dumps({'message': ''}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_chat_invalid_json(self, client):
        """Test chat with invalid JSON"""
        response = client.post(
            '/chat',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_chat_ai_service_error(self, client, mock_ai_service, mock_context_processor):
        """Test chat when AI service raises an error"""
        mock_ai_service.side_effect = Exception("AI service error")
        
        response = client.post(
            '/chat',
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

class TestIndexEndpoint:
    """Tests for the index endpoint"""
    
    def test_index_page(self, client):
        """Test index page returns HTML"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'WhatsApp Chat Bot' in response.data
        assert b'<html>' in response.data

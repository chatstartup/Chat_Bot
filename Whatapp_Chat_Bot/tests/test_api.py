"""Unit tests for API endpoints"""
import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, ai_service, vector_db

@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_services():
    """Mock all services"""
    with patch.object(ai_service, "generate_response") as mock_ai, \
         patch.object(vector_db, "query_context") as mock_db, \
         patch('app.ContextProcessor') as mock_context:
        
        mock_ai.return_value = "Test response"
        mock_db.return_value = [{"text": "Test context"}]
        
        # Mock context processor
        mock_context_instance = MagicMock()
        mock_context_instance.process_context.return_value = {
            'name': 'Test Context',
            'actions': ['action1', 'action2']
        }
        mock_context.return_value = mock_context_instance
        
        yield {
            "ai": mock_ai,
            "db": mock_db,
            "context": mock_context_instance
        }

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "status" in data
    assert "services" in data

def test_metrics(client):
    """Test metrics endpoint"""
    response = client.get('/metrics')
    assert response.status_code == 200
    assert "whatsapp_bot_requests_total" in response.text

def test_chat_endpoint_success(client, mock_services):
    """Test successful chat request"""
    response = client.post(
        "/chat",
        json={
            "message": "Test message",
            "session_id": "test-session"
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["response"] == "Test response"
    assert data["session_id"] == "test-session"
    
    # Verify service calls
    mock_services["db"].assert_called_once()
    mock_services["ai"].assert_called_once()

def test_chat_endpoint_error(client, mock_services):
    """Test chat request with error"""
    mock_services["ai"].side_effect = Exception("Test error")
    
    response = client.post(
        "/chat",
        json={
            "message": "Test message",
            "session_id": "test-session"
        }
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "detail" in data

def test_get_chat_session(client, mock_services):
    """Test get chat session endpoint"""
    response = client.get("/chat/test-session")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["session_id"] == "test-session"

def test_get_chat_session_not_found(client, mock_services):
    """Test get chat session not found"""
    response = client.get("/chat/test-session")
    assert response.status_code == 200

def test_clear_chat_session(client, mock_services):
    """Test clear chat session endpoint"""
    response = client.delete("/chat/test-session")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"

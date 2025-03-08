import pytest
from app import app
from services.ai_service import AIService, RateLimitError, AuthenticationError

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_valid_chat_request(client):
    response = client.post('/chat', json={'message': 'Hello'})
    assert response.status_code == 200
    assert 'response' in response.json

def test_invalid_request(client):
    response = client.post('/chat', json={'wrong_key': 'test'})
    assert response.status_code == 400
    assert 'Invalid request format' in response.json['error']

def test_service_unavailable(client, mocker):
    mocker.patch.object(AIService, 'is_available', return_value=False)
    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 503

def test_rate_limiting(client, mocker):
    mocker.patch.object(AIService, 'generate_response', side_effect=RateLimitError())
    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 429

def test_health_endpoint(client, mocker):
    mocker.patch.object(AIService, 'is_available', return_value=True)
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}

def test_empty_prompt(client, mocker):
    mocker.patch('services.ai_service.AIService.generate_response', return_value='Please provide a valid message')
    response = client.post('/chat', json={'message': ''})
    assert response.status_code == 400
    assert 'cannot be empty' in response.json['error']

def test_valid_api_key(client, mocker):
    mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'valid-test-key'})
    mock_client = mocker.patch('services.ai_service.AsyncGroq')
    
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}
    mock_client.assert_called_once_with(api_key='valid-test-key')


def test_invalid_api_key(client, mocker):
    mocker.patch.dict('os.environ', {'GROQ_API_KEY': 'invalid-key'})
    mocker.patch('services.ai_service.AsyncGroq', side_effect=AuthenticationError)
    
    response = client.get('/health')
    assert response.status_code == 503
    assert 'configuration' in response.json['error']

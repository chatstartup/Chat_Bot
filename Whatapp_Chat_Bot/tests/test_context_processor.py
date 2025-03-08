import pytest
from handlers.context_processor import ContextProcessor

@pytest.fixture
def processor():
    return ContextProcessor()

def test_process_context_file(processor):
    processor.process_context_file("context_data.txt")
    assert processor.vector_db.is_available

def test_process_user_input(processor):
    response = processor.process_user_input("Hello, how are you?")
    assert isinstance(response, str)
    assert len(response) > 0

def test_process_empty_input(processor):
    response = processor.process_user_input("")
    assert response == ""

def test_process_user_input_help():
    processor = ContextProcessor()
    response = processor.process_user_input("help")
    assert "Available Commands" in response
    assert "compare [models]" in response

def test_process_user_input_clear():
    processor = ContextProcessor()
    response = processor.process_user_input("clear")
    assert "Welcome to Captain Tractors ChatBot" in response

def test_process_user_input_empty():
    processor = ContextProcessor()
    response = processor.process_user_input("")
    assert response == ""

def test_process_user_input_normal():
    processor = ContextProcessor()
    response = processor.process_user_input("Tell me about your tractors")
    assert response is not None
    assert len(response) > 0

def test_error_handling():
    processor = ContextProcessor()
    processor.ai_processor = None  # Force an error
    response = processor.process_user_input("test")
    assert "error" in response.lower()
    assert "support@captaintractors.com" in response
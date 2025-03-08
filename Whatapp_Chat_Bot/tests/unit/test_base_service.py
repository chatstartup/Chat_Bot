"""Unit tests for Base Service"""
import pytest
from unittest.mock import patch, MagicMock
from services.base import BaseService

class ConcreteService(BaseService):
    """Concrete implementation of BaseService for testing"""
    
    def initialize(self):
        """Implementation of abstract method"""
        return True

class TestBaseService:
    """Test suite for Base Service"""
    
    @pytest.fixture
    def base_service(self):
        """Create a concrete service instance for testing"""
        return ConcreteService()
    
    def test_initialization(self, base_service):
        """Test initialization"""
        assert base_service.last_error is None
    
    def test_set_error(self, base_service):
        """Test error setting"""
        # Set error with string
        base_service._set_error("Test error")
        assert base_service.last_error == "Test error"
        
        # Set error with exception
        test_exception = ValueError("Exception error")
        base_service._set_error(test_exception)
        assert base_service.last_error == "Exception error"
    
    def test_health_check(self, base_service):
        """Test health check"""
        # Service should be healthy by default
        assert base_service.health_check() is True
        
        # Set an error
        base_service._set_error("Test error")
        assert base_service.health_check() is False
        
        # Clear the error
        base_service.last_error = None
        assert base_service.health_check() is True
    
    def test_abstract_initialize(self):
        """Test that BaseService is abstract and cannot be instantiated directly"""
        with pytest.raises(TypeError):
            BaseService()
    
    def test_concrete_initialize(self, base_service):
        """Test concrete implementation of initialize"""
        result = base_service.initialize()
        assert result is True

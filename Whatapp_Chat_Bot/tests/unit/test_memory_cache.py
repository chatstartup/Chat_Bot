"""Unit tests for Memory Cache Service"""
import pytest
import time
from unittest.mock import patch, MagicMock
from services.memory_cache import MemoryCache

class TestMemoryCache:
    """Test suite for Memory Cache Service"""
    
    @pytest.fixture
    def memory_cache(self):
        """Create a memory cache instance for testing"""
        cache = MemoryCache()
        cache.initialize()
        return cache
    
    def test_initialize(self):
        """Test initialization"""
        cache = MemoryCache()
        result = cache.initialize()
        
        assert result is True
        assert cache._cache == {}
        assert cache.last_error is None
    
    def test_set_get(self, memory_cache):
        """Test setting and getting values"""
        # Test with string value
        memory_cache.set("test_key", "test_value")
        assert memory_cache.get("test_key") == "test_value"
        
        # Test with dict value
        test_dict = {"name": "Test", "value": 123}
        memory_cache.set("dict_key", test_dict)
        assert memory_cache.get("dict_key") == test_dict
        
        # Test with list value
        test_list = [1, 2, 3, "test"]
        memory_cache.set("list_key", test_list)
        assert memory_cache.get("list_key") == test_list
        
        # Test non-existent key
        assert memory_cache.get("non_existent") is None
    
    def test_ttl(self, memory_cache):
        """Test time-to-live functionality"""
        # Set with short TTL
        memory_cache.set("ttl_key", "ttl_value", ttl=1)
        
        # Value should be available immediately
        assert memory_cache.get("ttl_key") == "ttl_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Value should be expired
        assert memory_cache.get("ttl_key") is None
    
    def test_delete(self, memory_cache):
        """Test deleting values"""
        # Set a value
        memory_cache.set("delete_key", "delete_value")
        assert memory_cache.get("delete_key") == "delete_value"
        
        # Delete the value
        result = memory_cache.delete("delete_key")
        assert result is True
        assert memory_cache.get("delete_key") is None
        
        # Delete non-existent key (should still return True)
        result = memory_cache.delete("non_existent")
        assert result is True
    
    def test_clear(self, memory_cache):
        """Test clearing all values"""
        # Set multiple values
        memory_cache.set("key1", "value1")
        memory_cache.set("key2", "value2")
        memory_cache.set("key3", "value3")
        
        # Verify values are set
        assert memory_cache.get("key1") == "value1"
        assert memory_cache.get("key2") == "value2"
        assert memory_cache.get("key3") == "value3"
        
        # Clear all values
        result = memory_cache.clear()
        assert result is True
        
        # Verify all values are cleared
        assert memory_cache.get("key1") is None
        assert memory_cache.get("key2") is None
        assert memory_cache.get("key3") is None
        assert memory_cache._cache == {}
    
    def test_expiry_check(self, memory_cache):
        """Test expiry checking"""
        # Set values with different expiry times
        memory_cache.set("no_expiry", "value1")  # No expiry
        memory_cache.set("future_expiry", "value2", ttl=60)  # Future expiry
        memory_cache.set("past_expiry", "value3", ttl=-1)  # Already expired
        
        # Check values
        assert memory_cache.get("no_expiry") == "value1"
        assert memory_cache.get("future_expiry") == "value2"
        assert memory_cache.get("past_expiry") is None
    
    def test_health_check(self, memory_cache):
        # Service should be healthy by default
        assert memory_cache.health_check() is True

        # Simulate error
        memory_cache.last_error = "Test error"
        assert memory_cache.health_check() is False

        # Clear error
        memory_cache.last_error = None
        assert memory_cache.health_check() is True

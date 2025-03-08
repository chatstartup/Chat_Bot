import pytest
from unittest.mock import Mock, patch
from services.vector_db import VectorDB

class TestVectorDB:
    @patch('services.vector_db.Pinecone')
    def test_initialize(self, mock_pinecone):
        """Test VectorDB initialization"""
        db = VectorDB()
        db.initialize()
        mock_pinecone.Index.assert_called_once()

    @patch('services.vector_db.Pinecone')
    def test_upsert_vectors(self, mock_pinecone):
        """Test vector upsert operations"""
        mock_index = mock_pinecone.Index.return_value
        mock_index.upsert.return_value = True
        
        db = VectorDB()
        db.initialize()
        assert db.upsert_vectors([("id1", [0.1, 0.2])]) is True

    @patch('services.vector_db.Pinecone')
    def test_query_context(self, mock_pinecone):
        """Test context query operations"""
        mock_index = mock_pinecone.Index.return_value
        mock_index.query.return_value = {'matches': [{'metadata': {'text': 'test'}}]}
        
        db = VectorDB()
        db.initialize()
        results = db.query_context([0.1, 0.2])
        assert len(results) > 0

    @patch('services.vector_db.Pinecone')
    def test_error_handling(self, mock_pinecone):
        """Test error handling in vector operations"""
        mock_index = mock_pinecone.Index.return_value
        mock_index.upsert.side_effect = Exception("DB Error")
        
        db = VectorDB()
        db.initialize()
        assert db.upsert_vectors([("id1", [0.1, 0.2])]) is False

    @patch('services.vector_db.Pinecone')
    def test_health_check(self, mock_pinecone):
        """Test VectorDB health monitoring"""
        db = VectorDB()
        db.initialize()
        assert db.health_check() is True

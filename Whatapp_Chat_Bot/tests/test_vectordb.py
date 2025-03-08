import pytest
from services.vector_db import VectorDB

@pytest.fixture
def vectordb():
    return VectorDB()

def test_generate_embedding(vectordb):
    embedding = vectordb._generate_embedding("Hello, how are you?")
    assert isinstance(embedding, list)
    assert len(embedding) == 384

def test_store_context(vectordb):
    assert vectordb.store_context("test_id", [0.1] * 384, {"content": "Test content"}) == True
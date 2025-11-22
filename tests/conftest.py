"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client"""
    client = MagicMock()
    client.indices.exists.return_value = False
    client.indices.create.return_value = {"acknowledged": True}
    client.search.return_value = {
        "hits": {
            "hits": [
                {
                    "_id": "test-id-1",
                    "_score": 0.95,
                    "_source": {
                        "doc_id": "doc-1",
                        "chunk_id": "chunk-1",
                        "title": "Test Title",
                        "category": "test",
                        "text_snippet": "This is a test snippet"
                    }
                }
            ]
        }
    }
    return client


@pytest.fixture
def mock_request(mock_opensearch_client):
    """Mock FastAPI Request object"""
    request = MagicMock()
    request.app.state.opensearch_client = mock_opensearch_client
    return request


@pytest.fixture
def sample_contexts():
    """Sample context data for testing"""
    return [
        {
            "id": "chunk-1",
            "score": 0.95,
            "doc_id": "doc-1",
            "title": "Machine Learning Basics",
            "category": "technology",
            "text_snippet": "Machine learning is a subset of artificial intelligence."
        },
        {
            "id": "chunk-2",
            "score": 0.87,
            "doc_id": "doc-2",
            "title": "Deep Learning",
            "category": "technology",
            "text_snippet": "Deep learning uses neural networks with multiple layers."
        }
    ]


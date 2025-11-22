"""
Unit tests for search API endpoints
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.api.search import router


@pytest.fixture
def app():
    """Create FastAPI app for testing"""
    app = FastAPI()
    app.include_router(router, prefix="/api/search")
    return app


@pytest.fixture
def client(app, mock_opensearch_client):
    """Create test client with mocked OpenSearch"""
    app.state.opensearch_client = mock_opensearch_client
    return TestClient(app)


class TestSearchQuery:
    """Test cases for search query endpoint"""

    @pytest.fixture
    def mock_rag_answer(self):
        """Mock rag_answer function"""
        with patch('app.api.search.rag_answer') as mock:
            mock.return_value = {
                "query": "What is ML?",
                "answer": "Machine learning is AI.",
                "contexts": [
                    {
                        "id": "chunk-1",
                        "score": 0.95,
                        "doc_id": "doc-1",
                        "title": "ML Basics",
                        "category": "tech",
                        "text_snippet": "ML is AI."
                    }
                ]
            }
            yield mock

    def test_query_success(self, client, mock_opensearch_client, mock_rag_answer):
        """Test successful query"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "What is ML?",
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "answer" in data
        assert "contexts" in data

    def test_query_index_not_found(self, client, mock_opensearch_client):
        """Test query with non-existent index"""
        mock_opensearch_client.indices.exists.return_value = False
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "nonexistent-index",
                "query": "What is ML?",
                "top_k": 5
            }
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]

    def test_query_with_category_filter(self, client, mock_opensearch_client, mock_rag_answer):
        """Test query with category filter"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "What is ML?",
                "top_k": 5,
                "category": "technology"
            }
        )
        
        assert response.status_code == 200
        # Verify rag_answer was called with category
        mock_rag_answer.assert_called_once()
        call_args = mock_rag_answer.call_args
        assert call_args[1]['filter_category'] == "technology"

    def test_query_default_top_k(self, client, mock_opensearch_client, mock_rag_answer):
        """Test query with default top_k"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "What is ML?"
            }
        )
        
        assert response.status_code == 200
        # Verify default top_k is 5
        call_args = mock_rag_answer.call_args
        assert call_args[1]['top_k'] == 5

    def test_query_custom_top_k(self, client, mock_opensearch_client, mock_rag_answer):
        """Test query with custom top_k"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "What is ML?",
                "top_k": 10
            }
        )
        
        assert response.status_code == 200
        call_args = mock_rag_answer.call_args
        assert call_args[1]['top_k'] == 10

    def test_query_missing_required_fields(self, client):
        """Test query with missing required fields"""
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index"
                # Missing query field
            }
        )
        
        assert response.status_code == 422  # Validation error

    def test_query_empty_query_string(self, client, mock_opensearch_client, mock_rag_answer):
        """Test query with empty query string"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "",
                "top_k": 5
            }
        )
        
        # Should still process (validation allows empty string)
        assert response.status_code == 200

    def test_query_response_structure(self, client, mock_opensearch_client, mock_rag_answer):
        """Test that response has correct structure"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "What is ML?",
                "top_k": 5
            }
        )
        
        data = response.json()
        assert isinstance(data["query"], str)
        assert isinstance(data["answer"], str)
        assert isinstance(data["contexts"], list)
        
        if len(data["contexts"]) > 0:
            context = data["contexts"][0]
            assert "id" in context
            assert "score" in context
            assert "doc_id" in context
            assert "title" in context
            assert "category" in context
            assert "text_snippet" in context

    def test_query_rag_answer_called_correctly(self, client, mock_opensearch_client, mock_rag_answer):
        """Test that rag_answer is called with correct parameters"""
        mock_opensearch_client.indices.exists.return_value = True
        
        client.post(
            "/api/search/query",
            json={
                "index_name": "test-index",
                "query": "What is ML?",
                "top_k": 7,
                "category": "tech"
            }
        )
        
        mock_rag_answer.assert_called_once()
        call_args = mock_rag_answer.call_args
        
        # Verify all parameters
        assert call_args[0][1] == "What is ML?"  # query
        assert call_args[0][2] == "test-index"   # index_name
        assert call_args[1]['top_k'] == 7
        assert call_args[1]['filter_category'] == "tech"


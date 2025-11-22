"""
Unit tests for RAG service
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock, Mock
from app.services.rag_service import search_opensearch, rag_answer


class TestSearchOpenSearch:
    """Test cases for search_opensearch function"""

    @pytest.fixture
    def mock_embedder(self):
        """Mock embedder"""
        with patch('app.services.rag_service.OllamaAPIEmbedder') as mock:
            embedder = mock.return_value
            embedder.embed.return_value = np.array([0.1] * 256, dtype='float32')
            yield embedder

    def test_search_opensearch_basic(self, mock_request, mock_embedder):
        """Test basic search without filters"""
        result = search_opensearch(mock_request, "test query", "test-index", top_k=5)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "test-id-1"
        assert result[0]["score"] == 0.95
        assert result[0]["title"] == "Test Title"

    def test_search_opensearch_with_category_filter(self, mock_request, mock_embedder):
        """Test search with category filter"""
        result = search_opensearch(
            mock_request, 
            "test query", 
            "test-index", 
            top_k=5, 
            filter_category="technology"
        )
        
        assert isinstance(result, list)
        # Verify the search was called with filter
        mock_request.app.state.opensearch_client.search.assert_called_once()
        call_args = mock_request.app.state.opensearch_client.search.call_args
        body = call_args[1]['body']
        
        # Check that filter is in the query
        assert 'bool' in body['query']
        assert 'filter' in body['query']['bool']

    def test_search_opensearch_top_k(self, mock_request, mock_embedder):
        """Test that top_k is respected"""
        result = search_opensearch(mock_request, "test query", "test-index", top_k=10)
        
        # Verify top_k is used in the query
        call_args = mock_request.app.state.opensearch_client.search.call_args
        body = call_args[1]['body']
        assert body['size'] == 10

    def test_search_opensearch_knn_query_structure(self, mock_request, mock_embedder):
        """Test that k-NN query is structured correctly"""
        search_opensearch(mock_request, "test query", "test-index", top_k=5)
        
        call_args = mock_request.app.state.opensearch_client.search.call_args
        body = call_args[1]['body']
        
        # Verify k-NN query structure
        assert 'query' in body
        assert 'knn' in body['query']
        assert 'embedding' in body['query']['knn']
        assert 'vector' in body['query']['knn']['embedding']
        assert 'k' in body['query']['knn']['embedding']

    def test_search_opensearch_embedding_called(self, mock_request, mock_embedder):
        """Test that embedder is called with query"""
        query = "What is machine learning?"
        search_opensearch(mock_request, query, "test-index", top_k=5)
        
        mock_embedder.embed.assert_called_once_with(query)

    def test_search_opensearch_source_fields(self, mock_request, mock_embedder):
        """Test that correct source fields are requested"""
        search_opensearch(mock_request, "test query", "test-index", top_k=5)
        
        call_args = mock_request.app.state.opensearch_client.search.call_args
        body = call_args[1]['body']
        
        expected_fields = ["doc_id", "chunk_id", "title", "category", "text_snippet"]
        assert body['_source'] == expected_fields

    def test_search_opensearch_empty_results(self, mock_request, mock_embedder):
        """Test search with no results"""
        mock_request.app.state.opensearch_client.search.return_value = {
            "hits": {"hits": []}
        }
        
        result = search_opensearch(mock_request, "test query", "test-index", top_k=5)
        
        assert isinstance(result, list)
        assert len(result) == 0


class TestRagAnswer:
    """Test cases for rag_answer function"""

    @pytest.fixture
    def mock_search(self):
        """Mock search_opensearch"""
        with patch('app.services.rag_service.search_opensearch') as mock:
            mock.return_value = [
                {
                    "id": "chunk-1",
                    "score": 0.95,
                    "doc_id": "doc-1",
                    "title": "ML Basics",
                    "category": "tech",
                    "text_snippet": "Machine learning is AI."
                }
            ]
            yield mock

    @pytest.fixture
    def mock_generator(self):
        """Mock OllamaGenerator"""
        with patch('app.services.rag_service.OllamaGenerator') as mock:
            generator = mock.return_value
            generator.generate.return_value = "Machine learning is a subset of AI."
            yield generator

    def test_rag_answer_basic(self, mock_request, mock_search, mock_generator):
        """Test basic RAG answer generation"""
        result = rag_answer(mock_request, "What is ML?", "test-index", top_k=5)
        
        assert isinstance(result, dict)
        assert "query" in result
        assert "answer" in result
        assert "contexts" in result
        assert result["query"] == "What is ML?"
        assert result["answer"] == "Machine learning is a subset of AI."
        assert len(result["contexts"]) == 1

    def test_rag_answer_with_category(self, mock_request, mock_search, mock_generator):
        """Test RAG answer with category filter"""
        result = rag_answer(
            mock_request, 
            "What is ML?", 
            "test-index", 
            top_k=5, 
            filter_category="technology"
        )
        
        # Verify search was called with category filter
        mock_search.assert_called_once_with(
            mock_request,
            "What is ML?",
            "test-index",
            top_k=5,
            filter_category="technology"
        )

    def test_rag_answer_generator_called(self, mock_request, mock_search, mock_generator):
        """Test that generator is called with correct arguments"""
        query = "What is ML?"
        rag_answer(mock_request, query, "test-index", top_k=5)
        
        mock_generator.generate.assert_called_once()
        call_args = mock_generator.generate.call_args
        assert call_args[0][0] == query
        assert isinstance(call_args[0][1], list)

    def test_rag_answer_no_contexts(self, mock_request, mock_search, mock_generator):
        """Test RAG answer when no contexts are found"""
        mock_search.return_value = []
        
        result = rag_answer(mock_request, "What is ML?", "test-index", top_k=5)
        
        assert result["contexts"] == []
        # Generator should still be called even with empty contexts
        mock_generator.generate.assert_called_once()

    def test_rag_answer_top_k_parameter(self, mock_request, mock_search, mock_generator):
        """Test that top_k parameter is passed correctly"""
        rag_answer(mock_request, "What is ML?", "test-index", top_k=10)
        
        call_args = mock_search.call_args
        assert call_args[1]['top_k'] == 10

    def test_rag_answer_response_structure(self, mock_request, mock_search, mock_generator):
        """Test the structure of the response"""
        result = rag_answer(mock_request, "What is ML?", "test-index", top_k=5)
        
        # Verify all required fields are present
        assert "query" in result
        assert "answer" in result
        assert "contexts" in result
        
        # Verify types
        assert isinstance(result["query"], str)
        assert isinstance(result["answer"], str)
        assert isinstance(result["contexts"], list)


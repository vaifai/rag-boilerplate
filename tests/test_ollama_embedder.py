"""
Unit tests for OllamaAPIEmbedder
"""
import pytest
import numpy as np
import responses
from unittest.mock import patch, MagicMock
from app.embeddings.ollama_api_embedder import OllamaAPIEmbedder


class TestOllamaAPIEmbedder:
    """Test cases for OllamaAPIEmbedder class"""

    @pytest.fixture
    def embedder(self):
        """Create embedder instance"""
        with patch('app.embeddings.ollama_api_embedder.settings') as mock_settings:
            mock_settings.OLLAMA_API_URL = "http://localhost:11434/api/embed"
            mock_settings.OLLAMA_EMBEDDING_MODEL = "nomic-embed-text:v1.5"
            mock_settings.OLLAMA_EMBEDDING_DIMENSION = 256
            return OllamaAPIEmbedder()

    def test_initialization(self, embedder):
        """Test embedder initialization"""
        assert embedder.api_url == "http://localhost:11434/api/embed"
        assert embedder.model == "nomic-embed-text:v1.5"
        assert embedder.dimension == 256

    def test_extract_vector_embeddings_list(self, embedder):
        """Test extracting vector from embeddings list format"""
        response = {"embeddings": [[0.1, 0.2, 0.3]]}
        result = embedder._extract_vector(response)
        assert result == [0.1, 0.2, 0.3]

    def test_extract_vector_embedding_single(self, embedder):
        """Test extracting vector from single embedding format"""
        response = {"embedding": [0.1, 0.2, 0.3]}
        result = embedder._extract_vector(response)
        assert result == [0.1, 0.2, 0.3]

    def test_extract_vector_data_format(self, embedder):
        """Test extracting vector from data format"""
        response = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
        result = embedder._extract_vector(response)
        assert result == [0.1, 0.2, 0.3]

    def test_extract_vector_list_format(self, embedder):
        """Test extracting vector from list format"""
        response = [{"embedding": [0.1, 0.2, 0.3]}]
        result = embedder._extract_vector(response)
        assert result == [0.1, 0.2, 0.3]

    def test_extract_vector_invalid_format(self, embedder):
        """Test extracting vector from invalid format raises error"""
        response = {"invalid": "format"}
        with pytest.raises(ValueError, match="Unexpected Ollama response"):
            embedder._extract_vector(response)

    @responses.activate
    def test_embed_success(self, embedder):
        """Test successful embedding"""
        # Mock the API response
        mock_vector = [0.1] * 256
        responses.add(
            responses.POST,
            "http://localhost:11434/api/embed",
            json={"embeddings": [mock_vector]},
            status=200
        )

        result = embedder.embed("test text")
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (256,)
        assert result.dtype == np.float32
        np.testing.assert_array_almost_equal(result, np.array(mock_vector, dtype="float32"))

    @responses.activate
    def test_embed_http_error(self, embedder):
        """Test embed with HTTP error"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/embed",
            json={"error": "Model not found"},
            status=404
        )

        with pytest.raises(Exception):
            embedder.embed("test text")

    @responses.activate
    def test_embed_batch_success(self, embedder):
        """Test successful batch embedding"""
        mock_vector = [0.1] * 256
        
        # Mock multiple API calls
        for _ in range(3):
            responses.add(
                responses.POST,
                "http://localhost:11434/api/embed",
                json={"embeddings": [mock_vector]},
                status=200
            )

        texts = ["text1", "text2", "text3"]
        result = embedder.embed_batch(texts)
        
        assert isinstance(result, np.ndarray)
        assert result.shape == (3, 256)
        assert result.dtype == np.float32

    @responses.activate
    def test_embed_batch_empty_list(self, embedder):
        """Test batch embedding with empty list"""
        result = embedder.embed_batch([])

        # Should return empty array with correct shape (0, dimension)
        assert isinstance(result, np.ndarray)
        assert result.shape == (0, 256)
        assert result.dtype == np.float32

    @responses.activate
    def test_embed_request_payload(self, embedder):
        """Test that embed sends correct payload"""
        mock_vector = [0.1] * 256
        responses.add(
            responses.POST,
            "http://localhost:11434/api/embed",
            json={"embeddings": [mock_vector]},
            status=200
        )

        embedder.embed("test text")
        
        # Check the request payload
        assert len(responses.calls) == 1
        request_body = responses.calls[0].request.body
        assert b"test text" in request_body
        assert b"nomic-embed-text:v1.5" in request_body
        assert b"256" in request_body

    @responses.activate
    def test_embed_timeout(self, embedder):
        """Test embed with timeout"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/embed",
            body=Exception("Timeout"),
        )

        with pytest.raises(Exception):
            embedder.embed("test text")


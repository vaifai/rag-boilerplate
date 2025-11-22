"""
Unit tests for OllamaGenerator
"""
import pytest
import responses
from unittest.mock import patch
from app.embeddings.ollama_generator import OllamaGenerator


class TestOllamaGenerator:
    """Test cases for OllamaGenerator class"""

    @pytest.fixture
    def generator(self):
        """Create generator instance"""
        with patch('app.embeddings.ollama_generator.settings') as mock_settings:
            mock_settings.OLLAMA_GENERATE_MODEL = "llama3.2"
            mock_settings.OLLAMA_GENERATE_API = "http://localhost:11434/api/generate"
            return OllamaGenerator()

    @pytest.fixture
    def sample_contexts(self):
        """Sample contexts for testing"""
        return [
            {
                "id": "chunk-1",
                "score": 0.95,
                "doc_id": "doc-1",
                "title": "ML Basics",
                "category": "tech",
                "text_snippet": "Machine learning is a subset of AI."
            },
            {
                "id": "chunk-2",
                "score": 0.87,
                "doc_id": "doc-2",
                "title": "Deep Learning",
                "category": "tech",
                "text_snippet": "Deep learning uses neural networks."
            }
        ]

    def test_initialization_default(self, generator):
        """Test generator initialization with defaults"""
        assert generator.model == "llama3.2"
        assert generator.api_url == "http://localhost:11434/api/generate"

    def test_initialization_custom(self):
        """Test generator initialization with custom values"""
        gen = OllamaGenerator(model="mistral", api_url="http://custom:8080/api/generate")
        assert gen.model == "mistral"
        assert gen.api_url == "http://custom:8080/api/generate"

    @responses.activate
    def test_generate_success(self, generator, sample_contexts):
        """Test successful generation"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={"response": "Machine learning is a subset of artificial intelligence."},
            status=200
        )

        result = generator.generate("What is machine learning?", sample_contexts)
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == "Machine learning is a subset of artificial intelligence."

    @responses.activate
    def test_generate_empty_contexts(self, generator):
        """Test generation with empty contexts"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={"response": "I don't have enough context to answer."},
            status=200
        )

        result = generator.generate("What is AI?", [])
        
        assert isinstance(result, str)

    @responses.activate
    def test_generate_prompt_construction(self, generator, sample_contexts):
        """Test that prompt is constructed correctly"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={"response": "Test response"},
            status=200
        )

        generator.generate("What is ML?", sample_contexts)
        
        # Check the request
        assert len(responses.calls) == 1
        request_body = responses.calls[0].request.body
        
        # Verify prompt contains query and context
        assert b"What is ML?" in request_body
        assert b"Machine learning is a subset of AI." in request_body
        assert b"Deep learning uses neural networks." in request_body

    @responses.activate
    def test_generate_http_error(self, generator, sample_contexts):
        """Test generation with HTTP error"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={"error": "Model not found"},
            status=404
        )

        result = generator.generate("What is AI?", sample_contexts)
        
        # Should return error message
        assert "Generation error" in result

    @responses.activate
    def test_generate_timeout(self, generator, sample_contexts):
        """Test generation with timeout"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            body=Exception("Timeout"),
        )

        result = generator.generate("What is AI?", sample_contexts)
        
        # Should return error message
        assert "Generation error" in result

    @responses.activate
    def test_generate_no_response_field(self, generator, sample_contexts):
        """Test generation when response field is missing"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={"data": "something else"},
            status=200
        )

        result = generator.generate("What is AI?", sample_contexts)
        
        # Should return empty string when response field is missing
        assert result == ""

    @responses.activate
    def test_generate_stream_false(self, generator, sample_contexts):
        """Test that stream is set to False in request"""
        responses.add(
            responses.POST,
            "http://localhost:11434/api/generate",
            json={"response": "Test"},
            status=200
        )

        generator.generate("Test query", sample_contexts)
        
        # Verify stream is False
        request_body = responses.calls[0].request.body
        assert b'"stream": false' in request_body or b'"stream":false' in request_body

    def test_generate_context_formatting(self, generator, sample_contexts):
        """Test that contexts are formatted correctly"""
        with patch('app.embeddings.ollama_generator.requests.post') as mock_post:
            mock_post.return_value.json.return_value = {"response": "Test"}
            mock_post.return_value.raise_for_status.return_value = None
            
            generator.generate("Test query", sample_contexts)
            
            # Get the prompt from the call
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            prompt = payload['prompt']
            
            # Verify both contexts are in the prompt
            assert "Machine learning is a subset of AI." in prompt
            assert "Deep learning uses neural networks." in prompt


"""
Unit tests for index API endpoints
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.api.index import router, CreateIndexRequest


@pytest.fixture
def app():
    """Create FastAPI app for testing"""
    app = FastAPI()
    app.include_router(router, prefix="/api/index")
    return app


@pytest.fixture
def client(app, mock_opensearch_client):
    """Create test client with mocked OpenSearch"""
    app.state.opensearch_client = mock_opensearch_client
    return TestClient(app)


class TestCreateIndex:
    """Test cases for create index endpoint"""

    def test_create_index_success(self, client, mock_opensearch_client):
        """Test successful index creation"""
        mock_opensearch_client.indices.exists.return_value = False
        mock_opensearch_client.indices.create.return_value = {"acknowledged": True}
        
        response = client.post(
            "/api/index/create",
            json={"index_name": "test-index", "embedding_dim": 256}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["index"] == "test-index"

    def test_create_index_already_exists(self, client, mock_opensearch_client):
        """Test creating index that already exists"""
        mock_opensearch_client.indices.exists.return_value = True
        
        response = client.post(
            "/api/index/create",
            json={"index_name": "existing-index", "embedding_dim": 256}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_create_index_invalid_request(self, client):
        """Test creating index with invalid request"""
        response = client.post(
            "/api/index/create",
            json={"index_name": "test"}  # Missing embedding_dim
        )
        
        assert response.status_code == 422  # Validation error

    def test_create_index_opensearch_error(self, client, mock_opensearch_client):
        """Test index creation with OpenSearch error"""
        mock_opensearch_client.indices.exists.return_value = False
        mock_opensearch_client.indices.create.side_effect = Exception("OpenSearch error")
        
        response = client.post(
            "/api/index/create",
            json={"index_name": "test-index", "embedding_dim": 256}
        )
        
        assert response.status_code == 500
        assert "OpenSearch error" in response.json()["detail"]

    def test_create_index_mapping_structure(self, client, mock_opensearch_client):
        """Test that index mapping is created with correct structure"""
        mock_opensearch_client.indices.exists.return_value = False
        
        client.post(
            "/api/index/create",
            json={"index_name": "test-index", "embedding_dim": 256}
        )
        
        # Verify create was called
        mock_opensearch_client.indices.create.assert_called_once()
        call_args = mock_opensearch_client.indices.create.call_args
        
        # Check mapping structure
        mapping = call_args[1]['body']
        assert 'settings' in mapping
        assert 'mappings' in mapping
        assert mapping['settings']['index']['knn'] is True
        
        # Check properties
        props = mapping['mappings']['properties']
        assert 'embedding' in props
        assert props['embedding']['type'] == 'knn_vector'
        assert props['embedding']['dimension'] == 256

    def test_create_index_knn_configuration(self, client, mock_opensearch_client):
        """Test k-NN configuration in index"""
        mock_opensearch_client.indices.exists.return_value = False
        
        client.post(
            "/api/index/create",
            json={"index_name": "test-index", "embedding_dim": 512}
        )
        
        call_args = mock_opensearch_client.indices.create.call_args
        mapping = call_args[1]['body']
        
        # Check k-NN method configuration
        embedding_config = mapping['mappings']['properties']['embedding']
        assert embedding_config['method']['name'] == 'hnsw'
        assert embedding_config['method']['space_type'] == 'cosinesimil'
        assert embedding_config['method']['engine'] == 'faiss'
        assert embedding_config['dimension'] == 512

    def test_create_index_field_types(self, client, mock_opensearch_client):
        """Test that all required fields are in mapping"""
        mock_opensearch_client.indices.exists.return_value = False
        
        client.post(
            "/api/index/create",
            json={"index_name": "test-index", "embedding_dim": 256}
        )
        
        call_args = mock_opensearch_client.indices.create.call_args
        props = call_args[1]['body']['mappings']['properties']
        
        # Verify all required fields
        assert props['doc_id']['type'] == 'keyword'
        assert props['chunk_id']['type'] == 'keyword'
        assert props['title']['type'] == 'text'
        assert props['category']['type'] == 'keyword'
        assert props['text']['type'] == 'text'
        assert props['text_snippet']['type'] == 'text'
        assert props['created_at']['type'] == 'date'

    def test_create_index_different_dimensions(self, client, mock_opensearch_client):
        """Test creating indices with different embedding dimensions"""
        mock_opensearch_client.indices.exists.return_value = False
        
        for dim in [128, 256, 512, 1024]:
            client.post(
                "/api/index/create",
                json={"index_name": f"test-index-{dim}", "embedding_dim": dim}
            )
        
        # Verify all were created
        assert mock_opensearch_client.indices.create.call_count == 4


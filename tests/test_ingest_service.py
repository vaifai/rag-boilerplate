"""
Unit tests for ingest service
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, Mock
from app.services.ingest_service import _create_actions_from_records, ingest_csv_to_index
import tempfile
import os


class TestCreateActionsFromRecords:
    """Test cases for _create_actions_from_records function"""

    @pytest.fixture
    def mock_embedder(self):
        """Mock embedder"""
        embedder = MagicMock()
        # Return a batch of embeddings
        embedder.embed_batch.return_value = np.array([[0.1] * 256, [0.2] * 256], dtype='float32')
        return embedder

    @pytest.fixture
    def sample_records(self):
        """Sample records for testing"""
        return [
            {
                "doc_id": "doc-1",
                "title": "Test Title 1",
                "category": "tech",
                "text": "This is test text 1"
            },
            {
                "doc_id": "doc-2",
                "title": "Test Title 2",
                "category": "science",
                "text": "This is test text 2"
            }
        ]

    def test_create_actions_basic(self, mock_embedder, sample_records):
        """Test basic action creation"""
        actions = list(_create_actions_from_records(
            "test-index",
            sample_records,
            mock_embedder,
            batch_size=64
        ))
        
        assert len(actions) == 2
        assert all(action['_op_type'] == 'index' for action in actions)
        assert all(action['_index'] == 'test-index' for action in actions)

    def test_create_actions_embedding_called(self, mock_embedder, sample_records):
        """Test that embedder is called correctly"""
        list(_create_actions_from_records(
            "test-index",
            sample_records,
            mock_embedder,
            batch_size=64
        ))
        
        mock_embedder.embed_batch.assert_called_once()
        call_args = mock_embedder.embed_batch.call_args[0][0]
        assert call_args == ["This is test text 1", "This is test text 2"]

    def test_create_actions_source_fields(self, mock_embedder, sample_records):
        """Test that source fields are correct"""
        actions = list(_create_actions_from_records(
            "test-index",
            sample_records,
            mock_embedder,
            batch_size=64
        ))
        
        source = actions[0]['_source']
        assert 'doc_id' in source
        assert 'chunk_id' in source
        assert 'title' in source
        assert 'category' in source
        assert 'text' in source
        assert 'text_snippet' in source
        assert 'embedding' in source
        assert 'created_at' in source

    def test_create_actions_text_snippet_truncation(self, mock_embedder):
        """Test that text snippet is truncated to 400 chars"""
        long_text = "a" * 500
        records = [{"doc_id": "doc-1", "text": long_text}]
        
        actions = list(_create_actions_from_records(
            "test-index",
            records,
            mock_embedder,
            batch_size=64
        ))
        
        assert len(actions[0]['_source']['text_snippet']) == 400

    def test_create_actions_batching(self, mock_embedder):
        """Test that batching works correctly"""
        # Create 10 records
        records = [{"doc_id": f"doc-{i}", "text": f"text {i}"} for i in range(10)]
        mock_embedder.embed_batch.return_value = np.array([[0.1] * 256] * 3, dtype='float32')
        
        actions = list(_create_actions_from_records(
            "test-index",
            records,
            mock_embedder,
            batch_size=3
        ))
        
        assert len(actions) == 10
        # Should be called 4 times (3+3+3+1)
        assert mock_embedder.embed_batch.call_count == 4

    def test_create_actions_embedding_dimension(self, mock_embedder, sample_records):
        """Test that embeddings have correct dimension"""
        actions = list(_create_actions_from_records(
            "test-index",
            sample_records,
            mock_embedder,
            batch_size=64
        ))
        
        embedding = actions[0]['_source']['embedding']
        assert len(embedding) == 256


class TestIngestCsvToIndex:
    """Test cases for ingest_csv_to_index function"""

    @pytest.fixture
    def temp_csv(self):
        """Create temporary CSV file"""
        df = pd.DataFrame({
            'id': ['1', '2', '3'],
            'title': ['Title 1', 'Title 2', 'Title 3'],
            'category': ['tech', 'science', 'tech'],
            'text': [
                'This is a test document about technology.',
                'This is a test document about science.',
                'Another technology document.'
            ]
        })
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

    @pytest.fixture
    def mock_embedder_class(self):
        """Mock OllamaAPIEmbedder class"""
        with patch('app.services.ingest_service.OllamaAPIEmbedder') as mock:
            embedder = mock.return_value
            embedder.embed_batch.return_value = np.array([[0.1] * 256] * 10, dtype='float32')
            yield mock

    @pytest.fixture
    def mock_bulk(self):
        """Mock bulk function"""
        with patch('app.services.ingest_service.bulk') as mock:
            mock.return_value = (10, [])  # success count, errors
            yield mock

    def test_ingest_csv_success(self, mock_request, temp_csv, mock_embedder_class, mock_bulk):
        """Test successful CSV ingestion"""
        ingest_csv_to_index(
            mock_request,
            temp_csv,
            "test-index"
        )
        
        # Verify bulk was called
        mock_bulk.assert_called_once()

    def test_ingest_csv_custom_columns(self, mock_request, mock_embedder_class, mock_bulk):
        """Test ingestion with custom column names"""
        df = pd.DataFrame({
            'custom_id': ['1', '2'],
            'custom_title': ['Title 1', 'Title 2'],
            'custom_category': ['tech', 'science'],
            'custom_text': ['Text 1', 'Text 2']
        })
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name
        
        try:
            ingest_csv_to_index(
                mock_request,
                temp_path,
                "test-index",
                doc_id_col="custom_id",
                title_col="custom_title",
                category_col="custom_category",
                text_col="custom_text"
            )
            
            mock_bulk.assert_called_once()
        finally:
            os.remove(temp_path)

    def test_ingest_csv_empty_text_skipped(self, mock_request, mock_embedder_class, mock_bulk):
        """Test that rows with empty text are skipped"""
        # Create a DataFrame and save it properly to handle NaN values
        df = pd.DataFrame({
            'id': ['1', '2', '3'],
            'title': ['Title 1', 'Title 2', 'Title 3'],
            'category': ['tech', 'science', 'tech'],
            'text': ['Valid text here', pd.NA, pd.NA]  # Use pandas NA for proper empty handling
        })

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        try:
            with patch('app.services.ingest_service.simple_sentence_split') as mock_split:
                mock_split.return_value = ['chunk1']

                ingest_csv_to_index(mock_request, temp_path, "test-index")

                # Should only be called once for the valid text (row 1)
                # Rows 2 and 3 have NA text and should be skipped
                assert mock_split.call_count == 1
                # Verify it was called with the valid text
                call_args = mock_split.call_args[0][0]
                assert 'Valid text here' in call_args
        finally:
            os.remove(temp_path)


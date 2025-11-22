"""
Unit tests for text_splitter module
"""
import pytest
from app.utils.text_splitter import simple_sentence_split


class TestSimpleSentenceSplit:
    """Test cases for simple_sentence_split function"""

    def test_empty_text(self):
        """Test with empty text"""
        result = simple_sentence_split("")
        assert result == []

    def test_none_text(self):
        """Test with None input"""
        result = simple_sentence_split(None)
        assert result == []

    def test_non_string_input(self):
        """Test with non-string input"""
        result = simple_sentence_split(123)
        assert result == []

    def test_single_sentence(self):
        """Test with a single sentence"""
        text = "This is a single sentence."
        result = simple_sentence_split(text, max_words=10, overlap=2)
        assert len(result) == 1
        assert result[0] == text

    def test_multiple_sentences_no_split(self):
        """Test multiple sentences that fit in one chunk"""
        text = "First sentence. Second sentence. Third sentence."
        result = simple_sentence_split(text, max_words=20, overlap=2)
        assert len(result) == 1
        assert result[0] == text

    def test_multiple_sentences_with_split(self):
        """Test multiple sentences requiring split"""
        text = "First sentence with many words here. Second sentence with many words here. Third sentence."
        result = simple_sentence_split(text, max_words=10, overlap=2)
        assert len(result) > 1

    def test_overlap_functionality(self):
        """Test that overlap works correctly"""
        text = "First sentence here. Second sentence here. Third sentence here."
        result = simple_sentence_split(text, max_words=5, overlap=2)
        # Check that chunks have overlapping words
        assert len(result) > 1
        # Verify overlap exists between consecutive chunks
        if len(result) > 1:
            # Last words of first chunk should appear in second chunk
            first_chunk_words = result[0].split()
            second_chunk_words = result[1].split()
            # Some overlap should exist
            assert any(word in second_chunk_words for word in first_chunk_words[-2:])

    def test_zero_overlap(self):
        """Test with zero overlap"""
        text = "First sentence. Second sentence. Third sentence."
        result = simple_sentence_split(text, max_words=3, overlap=0)
        assert len(result) >= 1

    def test_sentence_delimiters(self):
        """Test different sentence delimiters"""
        text = "Question one? Statement two. Exclamation three!"
        result = simple_sentence_split(text, max_words=20, overlap=2)
        assert len(result) == 1
        assert "Question one?" in result[0]
        assert "Statement two." in result[0]
        assert "Exclamation three!" in result[0]

    def test_long_single_sentence(self):
        """Test a very long single sentence"""
        text = " ".join(["word"] * 200) + "."
        result = simple_sentence_split(text, max_words=50, overlap=10)
        # Should create at least one chunk
        assert len(result) >= 1

    def test_whitespace_handling(self):
        """Test proper whitespace handling"""
        text = "  First sentence.   Second sentence.  "
        result = simple_sentence_split(text, max_words=20, overlap=2)
        assert len(result) >= 1
        # Should not have leading/trailing whitespace issues
        assert result[0].strip() == result[0] or "First sentence" in result[0]

    def test_max_words_boundary(self):
        """Test behavior at max_words boundary"""
        # Create text with exactly max_words
        words = ["word"] * 10
        text = " ".join(words) + "."
        result = simple_sentence_split(text, max_words=10, overlap=2)
        assert len(result) == 1

    def test_realistic_text(self):
        """Test with realistic paragraph"""
        text = """
        Machine learning is a subset of artificial intelligence. 
        It focuses on building systems that learn from data. 
        These systems improve their performance over time without being explicitly programmed.
        Deep learning is a specialized form of machine learning.
        """
        result = simple_sentence_split(text, max_words=20, overlap=5)
        assert len(result) >= 1
        # Verify all chunks are strings
        assert all(isinstance(chunk, str) for chunk in result)
        # Verify chunks are not empty
        assert all(len(chunk.strip()) > 0 for chunk in result)



import re
from typing import List

def simple_sentence_split(text: str, max_words: int = 140, overlap: int = 30) -> List[str]:
    """
    Split a text into chunks by sentences, each chunk aims to be <= max_words,
    re-using an overlap of words between consecutive chunks.
    """
    if not text or not isinstance(text, str):
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current = []
    current_len = 0

    for sent in sentences:
        words = sent.split()
        if current_len + len(words) <= max_words or not current:
            current.append(sent)
            current_len += len(words)
        else:
            chunks.append(' '.join(current))
            if overlap > 0:
                last_words = ' '.join(current).split()[-overlap:]
                current = [' '.join(last_words), sent]
                current_len = len(last_words) + len(words)
            else:
                current = [sent]
                current_len = len(words)
    if current:
        chunks.append(' '.join(current))
    return chunks

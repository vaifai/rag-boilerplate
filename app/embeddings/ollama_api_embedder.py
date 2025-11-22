import requests
import numpy as np
from app.core.config import settings
from typing import List
import logging

logger = logging.getLogger(__name__)

class OllamaAPIEmbedder:
    def __init__(self):
        self.api_url = settings.OLLAMA_API_URL
        self.model = settings.OLLAMA_EMBEDDING_MODEL
        self.dimension = settings.OLLAMA_EMBEDDING_DIMENSION

    def _extract_vector(self, resp_json):
        # handle common response shapes (inspect once and adjust)
        if isinstance(resp_json, dict):
            # Ollama API returns {"embeddings": [[...]]}
            if "embeddings" in resp_json and isinstance(resp_json["embeddings"], list):
                return resp_json["embeddings"][0]
            if "embedding" in resp_json:
                return resp_json["embedding"]
            if "data" in resp_json and isinstance(resp_json["data"], list) and "embedding" in resp_json["data"][0]:
                return resp_json["data"][0]["embedding"]
        if isinstance(resp_json, list) and len(resp_json) > 0 and isinstance(resp_json[0], dict) and "embedding" in resp_json[0]:
            return resp_json[0]["embedding"]
        # fallback: raise to spot issues
        raise ValueError(f"Unexpected Ollama response: {resp_json}")

    def embed(self, text: str) -> np.ndarray:
        payload = {"model": self.model, "input": text, "dimensions": self.dimension}
        r = requests.post(self.api_url, json=payload, timeout=60)
        r.raise_for_status()
        vec = self._extract_vector(r.json())
        return np.array(vec, dtype="float32")

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        # naive batch (one request per item). Change to batched API if your Ollama supports it.
        if not texts:
            return np.array([], dtype="float32").reshape(0, self.dimension)
        vecs = []
        for t in texts:
            vecs.append(self.embed(t))
        return np.vstack(vecs)
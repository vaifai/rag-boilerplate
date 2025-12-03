import requests
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OllamaGenerator:
    def __init__(self, model=None, api_url=None):
        self.model = model or settings.OLLAMA_GENERATE_MODEL  # e.g., llama3, mistral
        self.api_url = api_url or settings.OLLAMA_GENERATE_API  # e.g., http://localhost:11434/api/generate

    def generate(self, query: str, contexts: list) -> str:
        context_text = "\n\n".join([c["text_snippet"] for c in contexts])

        prompt = f"""
You are an AI assistant. Answer the user question using ONLY the context below.

Question:
{query}

Context:
{context_text}

Give a concise, factual answer.
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            r = requests.post(self.api_url, json=payload, timeout=300)
            r.raise_for_status()
            data = r.json()
            return data.get("response", "")
        except Exception as e:
            logger.exception("Ollama generation failed")
            return f"Generation error: {str(e)}"
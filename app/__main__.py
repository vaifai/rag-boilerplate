"""
Entry point for running the app package as a module.
Usage: python -m app
"""

from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

from app.core.config import settings

print("=" * 50)
print("RAG Playground - Configuration Test")
print("=" * 50)
print(f"MongoDB URI: {settings.MONGO_URI}")
print(f"MongoDB Database: {settings.MONGO_DB}")
print(f"Qdrant Host: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
print(f"OpenSearch Host: {settings.OPENSEARCH_HOST}")
print(f"OpenSearch Index: {settings.OPENSEARCH_INDEX}")
print(f"Embedding Model: {settings.EMBED_MODEL}")
print(f"Environment: {settings.APP_ENV}")
print("=" * 50)
print("✓ Configuration loaded successfully!")

"""
Entry point for running the app package as a module.
Usage: python -m app
"""

from dotenv import load_dotenv, find_dotenv
from fastapi import FastAPI
from app.api import index as index_router
from app.api import ingest as ingest_router
from app.api import search as search_router
from app.api import faiss as faiss_router
from app.api import qdrant as qdrant_router
from app.core.config import settings
from app.clients.opensearch_client import create_opensearch_client
from app.db.mongo_client import MongoClientWrapper
from qdrant_client import QdrantClient
import os
import logging

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("rag-boilerplate")

def create_app() -> FastAPI:
    app = FastAPI(title="RAG Boilerplate (OpenSearch + FAISS + Qdrant API)", version="0.1.0")

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting up... creating OpenSearch, MongoDB, and Qdrant clients")
        app.state.opensearch_client = create_opensearch_client()
        app.state.mongo_client = MongoClientWrapper()
        app.state.qdrant_client = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )

        app.include_router(index_router.router, prefix="/api/index", tags=["index"])
        app.include_router(ingest_router.router, prefix="/api/ingest", tags=["ingest"])
        app.include_router(search_router.router, prefix="/api/search", tags=["search"])
        app.include_router(faiss_router.router, prefix="/api/faiss", tags=["faiss"])
        app.include_router(qdrant_router.router, prefix="/api/qdrant", tags=["qdrant"])

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down application")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "env": settings.APP_ENV}
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.__main__:app", host=settings.HOST, port=settings.PORT, log_level="info", reload=settings.DEBUG)

print("=" * 50)
print("RAG Playground - Configuration Test")
print("=" * 50)
print(f"OpenSearch Host: {settings.OPENSEARCH_HOST}")
print(f"OpenSearch Index: {settings.OPENSEARCH_INDEX}")
print(f"Environment: {settings.APP_ENV}")
print("=" * 50)
print("✓ Configuration loaded successfully!")

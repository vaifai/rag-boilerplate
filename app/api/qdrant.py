"""
Qdrant API endpoints.
Separate endpoints for Qdrant vector store operations.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from app.services.qdrant_service import create_qdrant_collection, ingest_csv_to_qdrant, search_qdrant_collection
import pandas as pd
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateQdrantCollectionRequest(BaseModel):
    collection_name: str = Field(..., description="Qdrant collection name")
    embedding_dim: int = Field(..., description="Embedding dimension")


class IngestQdrantRequest(BaseModel):
    csv_path: str = Field(..., description="Path to CSV file on server")
    collection_name: str = Field(..., description="Qdrant collection name")
    doc_id_col: str = Field(default="id")
    title_col: str = Field(default="title")
    category_col: str = Field(default="category")
    text_col: str = Field(default="text")


class SearchQdrantRequest(BaseModel):
    collection_name: str = Field(..., description="Qdrant collection name")
    query: str = Field(..., description="Query text")
    top_k: int = Field(default=5, description="Number of results to return")
    category: str = Field(default=None, description="Optional category filter")


@router.post("/create")
def create_collection_endpoint(req: CreateQdrantCollectionRequest, request: Request):
    """Create a new Qdrant collection"""
    qdrant_client = request.app.state.qdrant_client
    mongo_client = request.app.state.mongo_client
    
    try:
        result = create_qdrant_collection(
            collection_name=req.collection_name,
            dimension=req.embedding_dim,
            qdrant_client=qdrant_client,
            mongo_client=mongo_client
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create Qdrant collection")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
def ingest_endpoint(req: IngestQdrantRequest, background_tasks: BackgroundTasks, request: Request):
    """Ingest CSV data into Qdrant collection"""
    qdrant_client = request.app.state.qdrant_client
    mongo_client = request.app.state.mongo_client
    
    # Validate CSV exists
    try:
        _ = pd.read_csv(req.csv_path, nrows=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read CSV at {req.csv_path}: {e}")
    
    # Validate collection exists
    qdrant_collections = mongo_client.db["qdrant_collections"]
    collection_doc = qdrant_collections.find_one({"collection_name": req.collection_name})
    if not collection_doc:
        raise HTTPException(status_code=400, detail=f"Qdrant collection {req.collection_name} does not exist")
    
    # Schedule background ingestion
    background_tasks.add_task(
        ingest_csv_to_qdrant,
        csv_path=req.csv_path,
        collection_name=req.collection_name,
        qdrant_client=qdrant_client,
        mongo_client=mongo_client,
        doc_id_col=req.doc_id_col,
        title_col=req.title_col,
        category_col=req.category_col,
        text_col=req.text_col
    )
    
    return {"ok": True, "message": "Qdrant ingestion scheduled"}


@router.post("/search")
def search_endpoint(req: SearchQdrantRequest, request: Request):
    """Search Qdrant collection and generate RAG answer"""
    qdrant_client = request.app.state.qdrant_client
    mongo_client = request.app.state.mongo_client
    
    # Validate collection exists
    qdrant_collections = mongo_client.db["qdrant_collections"]
    collection_doc = qdrant_collections.find_one({"collection_name": req.collection_name})
    if not collection_doc:
        raise HTTPException(status_code=400, detail=f"Qdrant collection {req.collection_name} not found")
    
    try:
        result = search_qdrant_collection(
            query=req.query,
            collection_name=req.collection_name,
            qdrant_client=qdrant_client,
            mongo_client=mongo_client,
            top_k=req.top_k,
            filter_category=req.category
        )
        return result
    except Exception as e:
        logger.exception("Qdrant search failed")
        raise HTTPException(status_code=500, detail=str(e))


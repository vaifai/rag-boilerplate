"""
FAISS API endpoints.
Separate endpoints for FAISS vector store operations.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from app.services.faiss_service import create_faiss_index, ingest_csv_to_faiss, search_faiss_index
import pandas as pd
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateFaissIndexRequest(BaseModel):
    index_name: str = Field(..., description="FAISS index name")
    embedding_dim: int = Field(..., description="Embedding dimension")


class IngestFaissRequest(BaseModel):
    csv_path: str = Field(..., description="Path to CSV file on server")
    index_name: str = Field(..., description="FAISS index name")
    doc_id_col: str = Field(default="id")
    title_col: str = Field(default="title")
    category_col: str = Field(default="category")
    text_col: str = Field(default="text")


class SearchFaissRequest(BaseModel):
    index_name: str = Field(..., description="FAISS index name")
    query: str = Field(..., description="Query text")
    top_k: int = Field(default=5, description="Number of results to return")
    category: str = Field(default=None, description="Optional category filter")


@router.post("/create")
def create_index_endpoint(req: CreateFaissIndexRequest, request: Request):
    """Create a new FAISS index"""
    mongo_client = request.app.state.mongo_client
    
    try:
        result = create_faiss_index(
            index_name=req.index_name,
            dimension=req.embedding_dim,
            mongo_client=mongo_client
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to create FAISS index")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
def ingest_endpoint(req: IngestFaissRequest, background_tasks: BackgroundTasks, request: Request):
    """Ingest CSV data into FAISS index"""
    mongo_client = request.app.state.mongo_client
    
    # Validate CSV exists
    try:
        _ = pd.read_csv(req.csv_path, nrows=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read CSV at {req.csv_path}: {e}")
    
    # Validate index exists
    faiss_indices = mongo_client.db["faiss_indices"]
    index_doc = faiss_indices.find_one({"index_name": req.index_name})
    if not index_doc:
        raise HTTPException(status_code=400, detail=f"FAISS index {req.index_name} does not exist")
    
    # Schedule background ingestion
    background_tasks.add_task(
        ingest_csv_to_faiss,
        csv_path=req.csv_path,
        index_name=req.index_name,
        mongo_client=mongo_client,
        doc_id_col=req.doc_id_col,
        title_col=req.title_col,
        category_col=req.category_col,
        text_col=req.text_col
    )
    
    return {"ok": True, "message": "FAISS ingestion scheduled"}


@router.post("/search")
def search_endpoint(req: SearchFaissRequest, request: Request):
    """Search FAISS index and generate RAG answer"""
    mongo_client = request.app.state.mongo_client
    
    # Validate index exists
    faiss_indices = mongo_client.db["faiss_indices"]
    index_doc = faiss_indices.find_one({"index_name": req.index_name})
    if not index_doc:
        raise HTTPException(status_code=400, detail=f"FAISS index {req.index_name} not found")
    
    try:
        result = search_faiss_index(
            query=req.query,
            index_name=req.index_name,
            mongo_client=mongo_client,
            top_k=req.top_k,
            filter_category=req.category
        )
        return result
    except Exception as e:
        logger.exception("FAISS search failed")
        raise HTTPException(status_code=500, detail=str(e))


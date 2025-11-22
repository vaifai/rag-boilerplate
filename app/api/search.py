# backend/app/api/search.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from app.services.rag_service import rag_answer
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class SearchRequest(BaseModel):
    index_name: str = Field(..., description="OpenSearch index name")
    query: str = Field(..., description="Query text")
    top_k: int = Field(default=5)
    category: str = Field(default=None)

@router.post("/query")
def query_endpoint(req: SearchRequest, request: Request):
    # validate index exists
    client = request.app.state.opensearch_client
    if not client.indices.exists(index=req.index_name):
        raise HTTPException(status_code=400, detail=f"Index {req.index_name} not found")
    res = rag_answer(request, req.query, req.index_name, top_k=req.top_k, filter_category=req.category)
    return res

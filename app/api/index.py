from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateIndexRequest(BaseModel):
    index_name: str
    embedding_dim: int


@router.post("/create")
def create_index(req: CreateIndexRequest, request: Request):
    client = request.app.state.opensearch_client  # <-- shared client

    index = req.index_name
    dim = req.embedding_dim

    if client.indices.exists(index=index):
        raise HTTPException(status_code=400, detail=f"Index `{index}` already exists")

    mapping = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "title": {"type": "text"},
                "category": {"type": "keyword"},
                "text": {"type": "text"},
                "text_snippet": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": dim,
                    "method": {
                        "name": "hnsw",
                        "space_type": "l2",
                        "engine": "faiss",
                        "parameters": {
                            "ef_construction": 128,
                            "m": 24
                        }
                    }
                },
                "created_at": {"type": "date"}
            }
        }
    }

    try:
        client.indices.create(index=index, body=mapping)
        return {"ok": True, "index": index}
    except Exception as e:
        logger.exception("Failed to create index")
        raise HTTPException(status_code=500, detail=str(e))
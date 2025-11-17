# backend/app/api/ingest.py
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from app.services.ingest_service import ingest_csv_to_index
import pandas as pd
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class IngestRequest(BaseModel):
    csv_path: str = Field(..., description="Path on server")
    index_name: str = Field(..., description="OpenSearch index name")
    doc_id_col: str = Field(default="id")
    title_col: str = Field(default="title")
    category_col: str = Field(default="category")
    text_col: str = Field(default="text")

@router.post("/start")
def start_ingest(req: IngestRequest, background_tasks: BackgroundTasks, request: Request):
    # validate index exists
    client = request.app.state.opensearch_client
    if not client.indices.exists(index=req.index_name):
        raise HTTPException(status_code=400, detail=f"Index {req.index_name} does not exist.")

    # validate CSV
    try:
        _ = pd.read_csv(req.csv_path, nrows=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot read CSV at {req.csv_path}: {e}")

    background_tasks.add_task(ingest_csv_to_index, request, req.csv_path, req.index_name, req.doc_id_col, req.title_col, req.category_col, req.text_col)
    return {"ok": True, "message": "Ingest scheduled"}

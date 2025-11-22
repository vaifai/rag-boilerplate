from typing import List
from app.embeddings.ollama_api_embedder import OllamaAPIEmbedder
from app.utils.text_splitter import simple_sentence_split
from app.core.config import settings
from opensearchpy.helpers import bulk
import pandas as pd
import uuid
import logging
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

def _create_actions_from_records(index_name: str, records: List[dict], embedder: OllamaAPIEmbedder, batch_size: int = 64):
    i = 0
    while i < len(records):
        batch = records[i:i+batch_size]
        texts = [r["text"] for r in batch]
        embs = embedder.embed_batch(texts)  # returns (n, dim)
        for j, r in enumerate(batch):
            emb = embs[j].tolist()
            chunk_id = str(uuid.uuid4())
            action = {
                "_op_type": "index",
                "_index": index_name,
                "_id": chunk_id,
                "_source": {
                    "doc_id": r["doc_id"],
                    "chunk_id": chunk_id,
                    "title": r.get("title"),
                    "category": r.get("category"),
                    "text": r["text"],
                    "text_snippet": r["text"][:400],
                    "embedding": emb,
                    "created_at": datetime.utcnow()
                }
            }
            yield action
        i += batch_size

def ingest_csv_to_index(request: Request, csv_path: str, index_name: str, doc_id_col: str = "id", title_col: str = "title", category_col: str = "category", text_col: str = "text"):
    """
    Synchronous ingestion function (can be called in background task).
    Uses the OpenSearch client from request.app.state.opensearch_client.
    """
    client = request.app.state.opensearch_client
    embedder = OllamaAPIEmbedder()
    df = pd.read_csv(csv_path)
    records = []
    for _, row in df.iterrows():
        doc_id = str(row.get(doc_id_col) or uuid.uuid4())
        title = row.get(title_col, "")
        category = row.get(category_col, "")
        text_value = row.get(text_col, "")
        # Handle pandas NA/NaN values
        if pd.isna(text_value):
            continue
        text = str(text_value or "")
        if not text or len(text.strip()) == 0 or text.lower() == 'nan':
            continue
        chunks = simple_sentence_split(text, max_words=settings.CHUNK_MAX_WORDS, overlap=settings.CHUNK_OVERLAP)
        for c in chunks:
            records.append({"doc_id": doc_id, "title": title, "category": category, "text": c})
    logger.info("Prepared %d chunk records for indexing into %s", len(records), index_name)

    # bulk index
    try:
        success, errors = bulk(client, _create_actions_from_records(index_name, records, embedder, batch_size=settings.BATCH_SIZE))
        logger.info("Bulk indexed %d items into index=%s", success, index_name)
        if errors:
            logger.warning("Some bulk errors occurred: %s", errors[:5])
    except Exception as e:
        logger.exception("Bulk indexing failed: %s", e)
        raise
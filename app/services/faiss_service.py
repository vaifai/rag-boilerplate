"""
FAISS service for vector search operations.
Uses MongoDB for all storage (metadata, vectors, and FAISS index binary).
"""

import faiss
import numpy as np
import hashlib
import io
from typing import List, Dict, Optional
from datetime import datetime
import logging
import pandas as pd
import uuid

from app.embeddings.ollama_api_embedder import OllamaAPIEmbedder
from app.embeddings.ollama_generator import OllamaGenerator
from app.utils.text_splitter import simple_sentence_split
from app.core.config import settings

logger = logging.getLogger(__name__)


def _id_to_int(sid: str) -> int:
    """Convert string ID to int64 for FAISS"""
    h = hashlib.sha256(sid.encode("utf-8")).hexdigest()
    return int(h[:16], 16) % (2**63 - 1)


def _serialize_faiss_index(index) -> bytes:
    """Serialize FAISS index to bytes for MongoDB storage"""
    # Write index to in-memory buffer
    buffer = io.BytesIO()
    faiss.write_index(index, faiss.BufferedIOWriter(faiss.PyCallbackIOWriter(buffer.write)))
    return buffer.getvalue()


def _deserialize_faiss_index(index_bytes: bytes):
    """Deserialize FAISS index from bytes stored in MongoDB"""
    buffer = io.BytesIO(index_bytes)
    reader = faiss.BufferedIOReader(faiss.PyCallbackIOReader(buffer.read))
    return faiss.read_index(reader)


def create_faiss_index(index_name: str, dimension: int, mongo_client) -> Dict:
    """
    Create a new FAISS index and store it in MongoDB.

    Args:
        index_name: Name of the index
        dimension: Embedding dimension
        mongo_client: MongoDB client wrapper

    Returns:
        Dictionary with creation status
    """
    faiss_indices = mongo_client.db["faiss_indices"]

    # Check if index already exists
    existing = faiss_indices.find_one({"index_name": index_name})
    if existing:
        raise ValueError(f"FAISS index '{index_name}' already exists")

    # Create empty FAISS index
    index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))

    # Serialize index to bytes
    index_bytes = _serialize_faiss_index(index)

    # Store in MongoDB
    index_doc = {
        "index_name": index_name,
        "dimension": dimension,
        "num_vectors": 0,
        "index_data": index_bytes,  # Store binary FAISS index
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    faiss_indices.insert_one(index_doc)

    logger.info(f"Created FAISS index in MongoDB: {index_name} with dimension {dimension}")
    return {"ok": True, "index": index_name, "dimension": dimension}


def ingest_csv_to_faiss(
    csv_path: str,
    index_name: str,
    mongo_client,
    doc_id_col: str = "id",
    title_col: str = "title",
    category_col: str = "category",
    text_col: str = "text"
):
    """
    Ingest CSV data into FAISS index.
    Stores vectors in FAISS file and metadata in MongoDB.
    
    Args:
        csv_path: Path to CSV file
        index_name: Name of the FAISS index
        mongo_client: MongoDB client wrapper
        doc_id_col: Column name for document ID
        title_col: Column name for title
        category_col: Column name for category
        text_col: Column name for text content
    """
    faiss_indices = mongo_client.db["faiss_indices"]
    faiss_chunks = mongo_client.db["faiss_chunks"]

    # Get index from MongoDB
    index_doc = faiss_indices.find_one({"index_name": index_name})
    if not index_doc:
        raise ValueError(f"FAISS index '{index_name}' not found")

    # Deserialize FAISS index from MongoDB
    index_bytes = index_doc["index_data"]
    faiss_index = _deserialize_faiss_index(index_bytes)
    logger.info(f"Loaded FAISS index from MongoDB: {index_name}")

    # Initialize embedder
    embedder = OllamaAPIEmbedder()
    
    # Read CSV and prepare chunks
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
        
        # Split into chunks
        chunks = simple_sentence_split(text, max_words=settings.CHUNK_MAX_WORDS, overlap=settings.CHUNK_OVERLAP)
        for chunk_text in chunks:
            chunk_id = str(uuid.uuid4())
            records.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "title": title,
                "category": category,
                "text": chunk_text,
                "text_snippet": chunk_text[:400]
            })
    
    logger.info(f"Prepared {len(records)} chunks for FAISS indexing into {index_name}")
    
    # Batch process embeddings and add to FAISS
    batch_size = settings.BATCH_SIZE
    total_added = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        texts = [r["text"] for r in batch]
        
        # Get embeddings
        embeddings = embedder.embed_batch(texts)  # returns (n, dim) numpy array
        
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Convert chunk_ids to int64 for FAISS
        chunk_ids = [r["chunk_id"] for r in batch]
        int_ids = np.array([_id_to_int(cid) for cid in chunk_ids], dtype='int64')
        
        # Add to FAISS index
        faiss_index.add_with_ids(embeddings, int_ids)
        
        # Store metadata in MongoDB
        for j, record in enumerate(batch):
            chunk_doc = {
                "chunk_id": record["chunk_id"],
                "faiss_int_id": int(int_ids[j]),
                "index_name": index_name,
                "doc_id": record["doc_id"],
                "title": record["title"],
                "category": record["category"],
                "text_snippet": record["text_snippet"],
                "created_at": datetime.utcnow()
            }
            faiss_chunks.replace_one({"chunk_id": record["chunk_id"]}, chunk_doc, upsert=True)
        
        total_added += len(batch)
        logger.info(f"Indexed batch {i//batch_size + 1}/{(len(records)-1)//batch_size + 1}")

    # Serialize and save updated FAISS index to MongoDB
    index_bytes = _serialize_faiss_index(faiss_index)

    # Update index in MongoDB
    faiss_indices.update_one(
        {"index_name": index_name},
        {"$set": {
            "index_data": index_bytes,
            "num_vectors": faiss_index.ntotal,
            "updated_at": datetime.utcnow()
        }}
    )

    logger.info(f"Successfully ingested {total_added} chunks into FAISS index {index_name}")


def search_faiss_index(
    query: str,
    index_name: str,
    mongo_client,
    top_k: int = 5,
    filter_category: Optional[str] = None
) -> Dict:
    """
    Search FAISS index and generate RAG answer.

    Args:
        query: Search query
        index_name: Name of the FAISS index
        mongo_client: MongoDB client wrapper
        top_k: Number of results to return
        filter_category: Optional category filter

    Returns:
        Dictionary with answer and contexts
    """
    faiss_indices = mongo_client.db["faiss_indices"]
    faiss_chunks = mongo_client.db["faiss_chunks"]

    # Get index from MongoDB
    index_doc = faiss_indices.find_one({"index_name": index_name})
    if not index_doc:
        raise ValueError(f"FAISS index '{index_name}' not found")

    # Deserialize FAISS index from MongoDB
    index_bytes = index_doc["index_data"]
    faiss_index = _deserialize_faiss_index(index_bytes)
    logger.info(f"Loaded FAISS index from MongoDB: {index_name}")

    # Get query embedding
    embedder = OllamaAPIEmbedder()
    q_vec = embedder.embed(query)

    # Normalize and search
    q = np.array(q_vec, dtype='float32').reshape(1, -1)
    faiss.normalize_L2(q)

    # Search more than top_k if filtering by category
    search_k = top_k * 10 if filter_category else top_k
    D, I = faiss_index.search(q, min(search_k, faiss_index.ntotal))

    # Build results
    hits = []
    for score, faiss_int_id in zip(D[0], I[0]):
        if faiss_int_id == -1:
            continue

        # Find chunk metadata by faiss_int_id
        chunk_doc = faiss_chunks.find_one({
            "index_name": index_name,
            "faiss_int_id": int(faiss_int_id)
        })

        if not chunk_doc:
            continue

        # Apply category filter
        # if filter_category and chunk_doc.get("category") != filter_category:
        #     continue

        hits.append({
            "chunk_id": chunk_doc["chunk_id"],
            "doc_id": chunk_doc["doc_id"],
            "title": chunk_doc["title"],
            "category": chunk_doc["category"],
            "text_snippet": chunk_doc["text_snippet"],
            "score": float(score)
        })

        if len(hits) >= top_k:
            break

    # Generate RAG answer
    if not hits:
        return {
            "query": query,
            "answer": "No relevant documents found.",
            "contexts": [],
            "top_k": top_k,
            "backend": "faiss"
        }

    # Generate answer using OllamaGenerator
    generator = OllamaGenerator()
    answer = generator.generate(query, hits)

    return {
        "query": query,
        "answer": answer,
        "contexts": hits,
        "top_k": top_k,
        "backend": "faiss"
    }


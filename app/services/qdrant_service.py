"""
Qdrant service for vector search operations.
Uses Qdrant for vector storage and MongoDB for metadata.
"""

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct
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


def create_qdrant_collection(
    collection_name: str,
    dimension: int,
    qdrant_client: QdrantClient,
    mongo_client
) -> Dict:
    """
    Create a new Qdrant collection and store metadata in MongoDB.

    Args:
        collection_name: Name of the collection
        dimension: Embedding dimension
        qdrant_client: Qdrant client instance
        mongo_client: MongoDB client wrapper

    Returns:
        Dictionary with creation status
    """
    qdrant_collections = mongo_client.db["qdrant_collections"]

    # Check if collection already exists in MongoDB
    existing = qdrant_collections.find_one({"collection_name": collection_name})
    if existing:
        raise ValueError(f"Qdrant collection '{collection_name}' already exists")

    # Create collection in Qdrant
    try:
        qdrant_client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
        )
    except Exception as e:
        logger.exception(f"Failed to create Qdrant collection: {e}")
        raise

    # Store metadata in MongoDB
    collection_doc = {
        "collection_name": collection_name,
        "dimension": dimension,
        "num_vectors": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    qdrant_collections.insert_one(collection_doc)

    logger.info(f"Created Qdrant collection: {collection_name} with dimension {dimension}")
    return {"ok": True, "collection": collection_name, "dimension": dimension}


def ingest_csv_to_qdrant(
    csv_path: str,
    collection_name: str,
    qdrant_client: QdrantClient,
    mongo_client,
    doc_id_col: str = "id",
    title_col: str = "title",
    category_col: str = "category",
    text_col: str = "text"
):
    """
    Ingest CSV data into Qdrant collection.
    Stores vectors in Qdrant and metadata in MongoDB.

    Args:
        csv_path: Path to CSV file
        collection_name: Name of the Qdrant collection
        qdrant_client: Qdrant client instance
        mongo_client: MongoDB client wrapper
        doc_id_col: Column name for document ID
        title_col: Column name for title
        category_col: Column name for category
        text_col: Column name for text content
    """
    qdrant_collections = mongo_client.db["qdrant_collections"]
    qdrant_chunks = mongo_client.db["qdrant_chunks"]

    # Get collection metadata
    collection_doc = qdrant_collections.find_one({"collection_name": collection_name})
    if not collection_doc:
        raise ValueError(f"Qdrant collection '{collection_name}' not found")

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

    logger.info(f"Prepared {len(records)} chunks for Qdrant indexing into {collection_name}")

    # Batch process embeddings and add to Qdrant
    batch_size = settings.BATCH_SIZE
    total_added = 0

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        texts = [r["text"] for r in batch]

        # Get embeddings
        embeddings = embedder.embed_batch(texts)  # returns (n, dim) numpy array

        # Prepare points for Qdrant
        points = []
        for j, record in enumerate(batch):
            chunk_id = record["chunk_id"]
            payload = {
                "doc_id": record["doc_id"],
                "title": record["title"],
                "category": record["category"],
                "text_snippet": record["text_snippet"]
            }

            # Create point with chunk_id as ID and embedding as vector
            point = PointStruct(
                id=chunk_id,
                vector=embeddings[j].tolist(),
                payload=payload
            )
            points.append(point)

            # Store metadata in MongoDB
            chunk_doc = {
                "chunk_id": chunk_id,
                "collection_name": collection_name,
                "doc_id": record["doc_id"],
                "title": record["title"],
                "category": record["category"],
                "text_snippet": record["text_snippet"],
                "created_at": datetime.utcnow()
            }
            qdrant_chunks.replace_one({"chunk_id": chunk_id}, chunk_doc, upsert=True)

        # Upsert points to Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )

        total_added += len(batch)
        logger.info(f"Indexed batch {i//batch_size + 1}/{(len(records)-1)//batch_size + 1}")

    # Update collection metadata
    collection_info = qdrant_client.get_collection(collection_name=collection_name)
    qdrant_collections.update_one(
        {"collection_name": collection_name},
        {"$set": {
            "num_vectors": collection_info.points_count,
            "updated_at": datetime.utcnow()
        }}
    )

    logger.info(f"Successfully ingested {total_added} chunks into Qdrant collection {collection_name}")


def search_qdrant_collection(
    query: str,
    collection_name: str,
    qdrant_client: QdrantClient,
    mongo_client,
    top_k: int = 5,
    filter_category: Optional[str] = None
) -> Dict:
    """
    Search Qdrant collection and generate RAG answer.

    Args:
        query: Search query
        collection_name: Name of the Qdrant collection
        qdrant_client: Qdrant client instance
        mongo_client: MongoDB client wrapper
        top_k: Number of results to return
        filter_category: Optional category filter

    Returns:
        Dictionary with answer and contexts
    """
    qdrant_collections = mongo_client.db["qdrant_collections"]
    qdrant_chunks = mongo_client.db["qdrant_chunks"]

    # Get collection metadata
    collection_doc = qdrant_collections.find_one({"collection_name": collection_name})
    if not collection_doc:
        raise ValueError(f"Qdrant collection '{collection_name}' not found")

    # Get query embedding
    embedder = OllamaAPIEmbedder()
    q_vec = embedder.embed(query)

    # Search Qdrant
    search_results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=q_vec.tolist(),
        limit=top_k * 2 if filter_category else top_k  # Get more if filtering
    )

    # Process results
    hits = []
    for result in search_results:
        chunk_id = result.id
        score = result.score
        payload = result.payload

        # Apply category filter if specified
        if filter_category and payload.get("category") != filter_category:
            continue

        hits.append({
            "chunk_id": chunk_id,
            "doc_id": payload.get("doc_id"),
            "title": payload.get("title"),
            "category": payload.get("category"),
            "text_snippet": payload.get("text_snippet"),
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
            "backend": "qdrant"
        }

    # Generate answer using OllamaGenerator
    generator = OllamaGenerator()
    answer = generator.generate(query, hits)

    return {
        "query": query,
        "answer": answer,
        "contexts": hits,
        "top_k": top_k,
        "backend": "qdrant"
    }


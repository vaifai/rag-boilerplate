# Qdrant Integration Guide

## Overview

This document describes the Qdrant vector database integration for the RAG playground. Qdrant provides high-performance vector similarity search with native support for filtering and metadata storage.

## Architecture

### Storage Structure

Qdrant uses a **hybrid storage approach**:
- **Vector data**: Stored in Qdrant (native vector database)
- **Metadata**: Stored in MongoDB for consistency with other backends

```
Qdrant (Vector Storage):
└── Collections
    └── {collection_name}
        ├── Vectors (embeddings)
        └── Payloads (doc_id, title, category, text_snippet)

MongoDB (Metadata):
├── qdrant_collections     # Collection metadata (name, dimension, num_vectors)
└── qdrant_chunks          # Chunk metadata (chunk_id, doc_id, title, category, text_snippet)
```

### File Structure

```
app/
├── api/
│   ├── index.py           # OpenSearch index management
│   ├── ingest.py          # OpenSearch ingestion
│   ├── search.py          # OpenSearch search/RAG
│   ├── faiss.py           # FAISS endpoints
│   └── qdrant.py          # Qdrant endpoints (NEW)
├── services/
│   ├── ingest_service.py  # OpenSearch ingestion service
│   ├── rag_service.py     # OpenSearch RAG service
│   ├── faiss_service.py   # FAISS service
│   └── qdrant_service.py  # Qdrant service (NEW)
└── core/
    └── config.py          # Configuration (includes Qdrant settings)
```

## API Endpoints

### 1. Create Collection

**Endpoint:** `POST /api/qdrant/create`

**Request:**
```json
{
  "collection_name": "my-qdrant-collection",
  "embedding_dim": 256
}
```

**Response:**
```json
{
  "ok": true,
  "collection": "my-qdrant-collection",
  "dimension": 256
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/qdrant/create" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my-qdrant-collection",
    "embedding_dim": 256
  }'
```

---

### 2. Ingest Data

**Endpoint:** `POST /api/qdrant/ingest`

**Request:**
```json
{
  "csv_path": "dev_dataset_100.csv",
  "collection_name": "my-qdrant-collection",
  "doc_id_col": "id",
  "title_col": "title",
  "category_col": "category",
  "text_col": "text"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Qdrant ingestion scheduled"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/qdrant/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "collection_name": "my-qdrant-collection"
  }'
```

**Note:** Ingestion runs in the background. Check server logs for progress.

---

### 3. Search

**Endpoint:** `POST /api/qdrant/search`

**Request:**
```json
{
  "collection_name": "my-qdrant-collection",
  "query": "What are design patterns?",
  "top_k": 5,
  "category": "programming"
}
```

**Response:**
```json
{
  "query": "What are design patterns?",
  "answer": "Design patterns are reusable solutions to commonly occurring problems...",
  "contexts": [
    {
      "chunk_id": "uuid-1234",
      "doc_id": "doc-5678",
      "title": "Design Patterns in Software Engineering",
      "category": "programming",
      "text_snippet": "Design patterns are reusable solutions...",
      "score": 0.95
    }
  ],
  "top_k": 5,
  "backend": "qdrant"
}


### qdrant_chunks
Stores chunk metadata:
```json
{
  "chunk_id": "uuid-1234",
  "collection_name": "my-collection",
  "doc_id": "doc-uuid",
  "title": "Design Patterns",
  "category": "programming",
  "text_snippet": "Design patterns are reusable solutions...",
  "created_at": "2024-01-01T00:00:00"
}
```

---

## Backend Comparison

| Feature | OpenSearch | FAISS | Qdrant |
|---------|-----------|-------|--------|
| **Storage** | Distributed, persistent | MongoDB (binary) | Qdrant + MongoDB |
| **Scalability** | Horizontal scaling | Single machine | Horizontal scaling |
| **Filtering** | Pre-filtering (efficient) | Post-filtering | Native filtering (efficient) |
| **Setup** | Docker container | MongoDB only | Docker container |
| **Speed** | Fast (distributed) | Very fast (in-memory) | Very fast (optimized) |
| **Use Case** | Production, large datasets | Development, experiments | Production, real-time |
| **API Endpoints** | `/api/index/*`, `/api/ingest/*`, `/api/search/*` | `/api/faiss/*` | `/api/qdrant/*` |
| **Persistence** | Native | MongoDB binary | Native + file system |
| **Metadata** | Stored with vectors | MongoDB only | Qdrant payload + MongoDB |

---

## Key Features

### ✅ Advantages

1. **Native Vector Database**: Purpose-built for vector similarity search
2. **Efficient Filtering**: Native support for filtering by metadata
3. **Scalable**: Supports horizontal scaling and clustering
4. **Persistent**: Data persists across restarts
5. **Rich Payloads**: Store metadata directly with vectors
6. **REST API**: Easy to use HTTP API
7. **GRPC Support**: High-performance GRPC interface available

### ⚠️ Considerations

1. **Resource Usage**: Requires separate Docker container
2. **Complexity**: More complex than FAISS for simple use cases
3. **Storage**: Uses both Qdrant and MongoDB for complete metadata

---

## Implementation Details

### How It Works

#### 1. Create Collection
```python
# Create collection in Qdrant
qdrant_client.recreate_collection(
    collection_name="my-collection",
    vectors_config=VectorParams(size=256, distance=Distance.COSINE)
)

# Store metadata in MongoDB
mongo_client.db["qdrant_collections"].insert_one({
    "collection_name": "my-collection",
    "dimension": 256,
    "num_vectors": 0,
    ...
})
```

#### 2. Ingest Data
```python
# Generate embeddings
embeddings = embedder.embed_batch(texts)

# Create points with payloads
points = [
    PointStruct(
        id=chunk_id,
        vector=embedding.tolist(),
        payload={
            "doc_id": doc_id,
            "title": title,
            "category": category,
            "text_snippet": text_snippet
        }
    )
    for chunk_id, embedding in zip(chunk_ids, embeddings)
]

# Upsert to Qdrant
qdrant_client.upsert(collection_name="my-collection", points=points)

# Store metadata in MongoDB
mongo_client.db["qdrant_chunks"].insert_many(chunk_docs)
```

#### 3. Search
```python
# Generate query embedding
query_vector = embedder.embed(query)

# Search Qdrant
results = qdrant_client.search(
    collection_name="my-collection",
    query_vector=query_vector.tolist(),
    limit=top_k
)

# Extract results with payloads
hits = [
    {
        "chunk_id": result.id,
        "score": result.score,
        "doc_id": result.payload["doc_id"],
        "title": result.payload["title"],
        "category": result.payload["category"],
        "text_snippet": result.payload["text_snippet"]
    }
    for result in results
]

# Generate RAG answer
answer = generator.generate(query, hits)
```

---

## Complete Workflow Example

```bash
# 1. Start Qdrant
docker-compose up -d qdrant

# 2. Create collection
curl -X POST "http://localhost:8000/api/qdrant/create" \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "qdrant-dev", "embedding_dim": 256}'

# 3. Ingest data
curl -X POST "http://localhost:8000/api/qdrant/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "collection_name": "qdrant-dev"
  }'

# 4. Search
curl -X POST "http://localhost:8000/api/qdrant/search" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

---

## Troubleshooting

### Check Qdrant Status
```bash
# Check if Qdrant is running
curl http://localhost:6333/collections

# Check collection info
curl http://localhost:6333/collections/my-collection
```

### Delete Collection
```bash
# Delete from Qdrant
curl -X DELETE http://localhost:6333/collections/my-collection

# Delete from MongoDB
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_collections.deleteOne({"collection_name": "my-collection"})'

docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_chunks.deleteMany({"collection_name": "my-collection"})'
```

### View Logs
```bash
# Qdrant logs
docker logs qdrant

# Application logs
tail -f logs/app.log | grep -i qdrant
```

---

## References

- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **Qdrant Python Client**: https://github.com/qdrant/qdrant-client
- **Docker Image**: https://hub.docker.com/r/qdrant/qdrant


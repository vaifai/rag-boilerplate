# FAISS Integration Guide

This document explains how to use FAISS as an alternative vector store backend in the RAG Playground.

## Overview

The RAG Playground supports two vector store backends:
- **OpenSearch** (default) - Distributed search engine with k-NN capabilities
- **FAISS** - Facebook AI Similarity Search, a library for efficient similarity search

## Architecture

### File Structure

```
app/
├── api/
│   ├── index.py                 # OpenSearch index management
│   ├── ingest.py                # OpenSearch ingestion
│   ├── search.py                # OpenSearch search/RAG
│   └── faiss.py                 # FAISS endpoints (NEW)
├── services/
│   ├── ingest_service.py        # OpenSearch ingestion service
│   ├── rag_service.py           # OpenSearch RAG service
│   └── faiss_service.py         # FAISS service (NEW)
├── db/
│   └── mongo_client.py          # MongoDB client wrapper
└── clients/
    └── opensearch_client.py     # OpenSearch client
```

### FAISS Storage Structure

FAISS uses **MongoDB for all storage**:
- **Vector indices**: Stored as binary data in MongoDB
- **Chunk metadata**: Stored in MongoDB for efficient querying

```
MongoDB Collections:
├── faiss_indices              # Index data (name, dimension, binary FAISS index, num_vectors)
└── faiss_chunks               # Chunk metadata (doc_id, title, category, text_snippet)
```

**No file system storage required!** Everything is in MongoDB.

## API Usage

FAISS has dedicated API endpoints separate from OpenSearch.

### 1. Create Index

**OpenSearch:**
```bash
curl -X POST "http://localhost:8000/api/index/create" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "my-index",
    "embedding_dim": 256
  }'
```

**FAISS:**
```bash
curl -X POST "http://localhost:8000/api/faiss/create" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "my-faiss-index",
    "embedding_dim": 256
  }'
```

### 2. Ingest Data

**OpenSearch:**
```bash
curl -X POST "http://localhost:8000/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "index_name": "my-index"
  }'
```

**FAISS:**
```bash
curl -X POST "http://localhost:8000/api/faiss/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "index_name": "my-faiss-index"
  }'
```

### 3. Search and RAG

**OpenSearch:**
```bash
curl -X POST "http://localhost:8000/api/search/query" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "my-index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

**FAISS:**
```bash
curl -X POST "http://localhost:8000/api/faiss/search" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "my-faiss-index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

## Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create FAISS index
response = requests.post(f"{BASE_URL}/api/faiss/create", json={
    "index_name": "test-faiss",
    "embedding_dim": 256
})
print(response.json())

# 2. Ingest data
response = requests.post(f"{BASE_URL}/api/faiss/ingest", json={
    "csv_path": "dev_dataset_100.csv",
    "index_name": "test-faiss"
})
print(response.json())

# 3. Search
response = requests.post(f"{BASE_URL}/api/faiss/search", json={
    "index_name": "test-faiss",
    "query": "How to write clean Python code?",
    "top_k": 3
})
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Contexts: {len(result['contexts'])} documents")
```

## Key Differences

| Feature | OpenSearch | FAISS |
|---------|-----------|-------|
| **Storage** | Distributed, persistent | MongoDB (binary index + metadata) |
| **Scalability** | Horizontal scaling | Single machine (in-memory) |
| **Filtering** | Pre-filtering (efficient) | Post-filtering (less efficient) |
| **Setup** | Requires Docker container | Requires MongoDB only |
| **Speed** | Fast for distributed data | Very fast (in-memory search) |
| **Use Case** | Production, large datasets | Development, experiments |
| **API Endpoints** | `/api/index`, `/api/ingest`, `/api/search` | `/api/faiss/create`, `/api/faiss/ingest`, `/api/faiss/search` |
| **File System** | Uses OpenSearch data directory | No files - all in MongoDB |

## Implementation Details

### FAISS Service

The `faiss_service.py` module provides:
- `create_faiss_index(index_name, dimension, mongo_client)` - Create new index
- `ingest_csv_to_faiss(csv_path, index_name, mongo_client, ...)` - Ingest data
- `search_faiss_index(query, index_name, mongo_client, ...)` - Search and generate RAG answer

### Similarity Metric

Both backends use **cosine similarity**:
- **OpenSearch**: Uses `cosinesimil` space type with HNSW algorithm
- **FAISS**: Uses `IndexFlatIP` (inner product) with L2-normalized vectors

### Metadata Storage

- **OpenSearch**: Stores metadata directly in the document
- **FAISS**: Stores everything in MongoDB collections:
  - `faiss_indices`: Index metadata + binary FAISS index data
  - `faiss_chunks`: Chunk metadata (chunk_id, doc_id, title, category, text_snippet)

### MongoDB Collections

**faiss_indices:**
```json
{
  "index_name": "my-index",
  "dimension": 256,
  "num_vectors": 1500,
  "index_data": "<binary FAISS index data>",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```
Note: `index_data` contains the serialized FAISS index as binary (BSON Binary type)

**faiss_chunks:**
```json
{
  "chunk_id": "uuid-1234",
  "faiss_int_id": 123456789,
  "index_name": "my-index",
  "doc_id": "doc-uuid",
  "title": "Design Patterns",
  "category": "programming",
  "text_snippet": "Design patterns are reusable solutions...",
  "created_at": "2024-01-01T00:00:00"
}
```

## Limitations

1. **Category Filtering**: FAISS applies filters post-search (less efficient than OpenSearch)
2. **Scalability**: FAISS indices are loaded into memory (not distributed like OpenSearch)
3. **Memory Usage**: Large indices consume RAM when loaded from MongoDB
4. **Concurrency**: Each search loads the index from MongoDB (consider caching for production)

## When to Use FAISS

✅ **Use FAISS when:**
- Developing and testing locally
- Working with small to medium datasets (< 1M vectors)
- You want very fast in-memory search
- Experimenting with different embedding models
- You already have MongoDB running

❌ **Use OpenSearch when:**
- Deploying to production
- Working with large datasets (> 1M vectors)
- You need distributed search
- You need efficient pre-filtering
- You need advanced search features (full-text, aggregations, etc.)

## Setup

### 1. Ensure MongoDB is Running

```bash
# Start MongoDB via Docker Compose
docker-compose up -d mongo

# Verify MongoDB is running
docker ps | grep mongo
```

### 2. Configure Environment

Add MongoDB settings to your `.env` file:

```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB=rag_playground
```

### 3. Start the Application

```bash
python -m app
```

The FAISS endpoints will be available at:
- `POST /api/faiss/create` - Create index
- `POST /api/faiss/ingest` - Ingest data
- `POST /api/faiss/search` - Search and RAG

## Next Steps

- See the API examples above for usage
- Check `tests/` for unit tests
- Read the main README.md for general setup instructions


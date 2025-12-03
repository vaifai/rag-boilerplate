# Qdrant Backend Guide

Complete guide for using Qdrant as the vector database backend in the RAG Playground.

## Overview

Qdrant is a vector similarity search engine with a focus on performance and scalability. It stores vectors in Qdrant itself and metadata in MongoDB for efficient hybrid storage.

### Key Features
- ✅ Purpose-built for vector search
- ✅ Fast and efficient similarity search
- ✅ Rich filtering capabilities
- ✅ Easy to use REST API
- ✅ Good for production workloads

## Quick Start

### 1. Start Qdrant

```bash
# Start via Docker Compose
docker compose up -d qdrant

# Verify it's running
curl http://localhost:6333
```

### 2. Create Collection

```bash
curl -X POST "http://localhost:8000/api/qdrant/create" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "bechmark_index",
    "embedding_dim": 256
  }'
```

### 3. Ingest Data

```bash
curl -X POST "http://localhost:8000/api/qdrant/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "benchmark_dataset_2000.csv",
    "collection_name": "bechmark_index",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }'
```

### 4. Search and Query

```bash
curl -X POST "http://localhost:8000/api/qdrant/search" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "bechmark_index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

## API Endpoints

### Collection Management

**Create Collection**
- **Endpoint**: `POST /api/qdrant/create`
- **Body**:
  ```json
  {
    "collection_name": "my-collection",
    "embedding_dim": 256
  }
  ```

### Data Ingestion

**Ingest CSV**
- **Endpoint**: `POST /api/qdrant/ingest`
- **Body**:
  ```json
  {
    "csv_path": "data.csv",
    "collection_name": "my-collection",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }
  ```

### Search and RAG

**Query with RAG**
- **Endpoint**: `POST /api/qdrant/search`
- **Body**:
  ```json
  {
    "collection_name": "my-collection",
    "query": "Your question here",
    "top_k": 5,
    "filter_category": "optional_category"
  }
  ```
- **Response**:
  ```json
  {
    "query": "Your question",
    "answer": "Generated answer from LLM",
    "contexts": [
      {
        "chunk_id": "uuid-1234",
        "doc_id": "doc-123",
        "title": "Document Title",
        "category": "programming",
        "text_snippet": "Relevant text...",
        "score": 0.95
      }
    ],
    "top_k": 5,
    "backend": "qdrant"
  }
  ```

## Architecture

### Storage Structure

Qdrant uses a **hybrid storage approach**:
- **Vectors**: Stored in Qdrant
- **Metadata**: Stored in MongoDB

**Qdrant Collections:**
- Collection stores vectors with minimal payload (doc_id, title, category, text_snippet)
- Uses cosine similarity for vector comparison

**MongoDB Collections:**

1. **`qdrant_collections`** - Collection metadata
   ```json
   {
     "collection_name": "my-collection",
     "dimension": 256,
     "num_vectors": 2000,
     "created_at": "2024-01-01T00:00:00",
     "updated_at": "2024-01-01T00:00:00"
   }
   ```

2. **`qdrant_chunks`** - Chunk metadata
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

### How It Works

1. **Collection Creation**: Creates a Qdrant collection with cosine distance metric
2. **Ingestion**:
   - Embeds text chunks
   - Creates points with vectors and payload
   - Upserts to Qdrant
   - Stores metadata in MongoDB
3. **Search**:
   - Embeds query
   - Searches Qdrant collection
   - Retrieves results with scores
   - Generates answer with LLM

### Similarity Metric

- **Distance**: Cosine distance
- **Vector Size**: 256 dimensions
- **Optimization**: HNSW index for fast approximate search

## Configuration

### Environment Variables

```env
# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB=rag_playground

# Embeddings
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5
OLLAMA_EMBEDDING_DIMENSION=256

# Generation
OLLAMA_GENERATE_MODEL=llama3.1:8b
```

### Docker Compose

```yaml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
    - "6334:6334"
  volumes:
    - qdrant-data:/qdrant/storage

mongo:
  image: mongo:7.0
  ports:
    - "27017:27017"
  volumes:
    - mongo-data:/data/db
```

## Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create Qdrant collection
response = requests.post(f"{BASE_URL}/api/qdrant/create", json={
    "collection_name": "test-qdrant",
    "embedding_dim": 256
})
print(response.json())

# 2. Ingest data
response = requests.post(f"{BASE_URL}/api/qdrant/ingest", json={
    "csv_path": "benchmark_dataset_2000.csv",
    "collection_name": "test-qdrant"
})
print(response.json())

# 3. Search with RAG
response = requests.post(f"{BASE_URL}/api/qdrant/search", json={
    "collection_name": "test-qdrant",
    "query": "Explain microservices architecture",
    "top_k": 3
})
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Contexts: {len(result['contexts'])} documents")
```

## Comparison with Other Backends

| Feature | OpenSearch | FAISS | Qdrant |
|---------|-----------|-------|--------|
| **Storage** | Distributed | MongoDB | Qdrant + MongoDB |
| **Scalability** | Horizontal | Single machine | Horizontal |
| **Filtering** | Pre-filtering | Post-filtering | Native filtering |
| **Setup** | Docker | MongoDB only | Docker + MongoDB |
| **Speed** | Fast | Very fast | Fast |
| **Use Case** | Production | Development | Production |
| **API** | REST | Python | REST + gRPC |

## Performance Considerations

### Advantages
- 🚀 **Purpose-built**: Designed specifically for vector search
- 🔍 **Rich filtering**: Native support for complex filters
- 📈 **Scalable**: Horizontal scaling support
- 🎯 **Accurate**: HNSW index for fast approximate search
- 🔧 **Easy to use**: Simple REST API

### Optimization Tips

1. **Batch upserts**: Already implemented (default: 64 per batch)
2. **Use filters**: Leverage Qdrant's native filtering
3. **Adjust HNSW parameters**: For speed vs accuracy tradeoff
4. **Monitor memory**: Check Qdrant dashboard at http://localhost:6333/dashboard

## When to Use Qdrant

✅ **Use Qdrant when:**
- You want a dedicated vector database
- You need rich filtering capabilities
- You're building production applications
- You want horizontal scalability
- You prefer a modern, purpose-built solution

❌ **Consider alternatives when:**
- You already have OpenSearch infrastructure
- You need very simple local development (use FAISS)
- You need advanced full-text search (use OpenSearch)

## Troubleshooting

### Qdrant Not Starting

```bash
# Check logs
docker logs qdrant

# Restart Qdrant
docker compose restart qdrant
```

### Collection Not Found

```bash
# List collections via Qdrant API
curl http://localhost:6333/collections

# Or via MongoDB
mongosh rag_playground --eval "db.qdrant_collections.find()"
```

### Slow Search Performance

- Check Qdrant dashboard for metrics
- Adjust HNSW parameters in collection config
- Use category filtering to reduce search space
- Monitor Qdrant memory usage

### Connection Issues

```bash
# Test Qdrant connection
curl http://localhost:6333/collections

# Test MongoDB connection
mongosh mongodb://localhost:27017
```

## Advanced Usage

### Direct Qdrant API

You can also interact with Qdrant directly:

```bash
# List collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/bechmark_index

# Search directly (without RAG)
curl -X POST http://localhost:6333/collections/bechmark_index/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  // 256-dim vector
    "limit": 5
  }'
```

### Qdrant Dashboard

Access the web UI at: http://localhost:6333/dashboard

Features:
- View collections
- Monitor performance
- Inspect points
- Run queries

### Custom Filters

Qdrant supports rich filtering:

```python
# Example: Filter by category and date
filter_conditions = {
    "must": [
        {"key": "category", "match": {"value": "programming"}},
        {"key": "created_at", "range": {"gte": "2024-01-01"}}
    ]
}
```

Modify `qdrant_service.py` to implement custom filters.

## Resources

- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Qdrant GitHub**: https://github.com/qdrant/qdrant
- **Dashboard**: http://localhost:6333/dashboard
- **API Reference**: https://qdrant.tech/documentation/interfaces/

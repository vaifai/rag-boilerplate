# OpenSearch Backend Guide

Complete guide for using OpenSearch as the vector database backend in the RAG Playground.

## Overview

OpenSearch is a distributed search and analytics engine with built-in k-NN (k-Nearest Neighbors) capabilities, making it ideal for production vector search workloads.

### Key Features
- ✅ Distributed, horizontally scalable
- ✅ Efficient pre-filtering on metadata
- ✅ Production-ready with high availability
- ✅ Advanced search features (full-text, aggregations, etc.)
- ✅ Persistent storage

## Quick Start

### 1. Start OpenSearch

```bash
# Start via Docker Compose
docker compose up -d opensearch

# Verify it's running
curl http://localhost:9200
```

### 2. Create Index

```bash
curl -X POST "http://localhost:8000/api/index/create" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "bechmark_index",
    "embedding_dim": 256
  }'
```

### 3. Ingest Data

```bash
curl -X POST "http://localhost:8000/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "benchmark_dataset_2000.csv",
    "index_name": "bechmark_index",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }'
```

### 4. Search and Query

```bash
curl -X POST "http://localhost:8000/api/search/query" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "bechmark_index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

## API Endpoints

### Index Management

**Create Index**
- **Endpoint**: `POST /api/index/create`
- **Body**:
  ```json
  {
    "index_name": "my-index",
    "embedding_dim": 256
  }
  ```

**Delete Index**
- **Endpoint**: `DELETE /api/index/delete/{index_name}`

**List Indices**
- **Endpoint**: `GET /api/index/list`

### Data Ingestion

**Ingest CSV**
- **Endpoint**: `POST /api/ingest/start`
- **Body**:
  ```json
  {
    "csv_path": "data.csv",
    "index_name": "my-index",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }
  ```

### Search and RAG

**Query with RAG**
- **Endpoint**: `POST /api/search/query`
- **Body**:
  ```json
  {
    "index_name": "my-index",
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
        "id": "chunk-id",
        "score": 0.95,
        "doc_id": "doc-123",
        "title": "Document Title",
        "category": "programming",
        "text_snippet": "Relevant text..."
      }
    ],
    "top_k": 5,
    "backend": "opensearch"
  }
  ```

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# OpenSearch
OPENSEARCH_HOST=http://localhost:9200
OPENSEARCH_INDEX=bechmark_index

# Embeddings
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5
OLLAMA_EMBEDDING_DIMENSION=256

# Generation
OLLAMA_GENERATE_MODEL=llama3.1:8b
```

### Docker Compose

```yaml
opensearch:
  image: opensearchproject/opensearch:2.11.0
  environment:
    - discovery.type=single-node
    - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
  ports:
    - "9200:9200"
  volumes:
    - opensearch-data:/usr/share/opensearch/data
```

## Architecture

### Index Structure

OpenSearch stores:
- **Vectors**: 256-dimensional embeddings
- **Metadata**: doc_id, chunk_id, title, category, text_snippet
- **Algorithm**: HNSW (Hierarchical Navigable Small World) for fast k-NN search
- **Similarity**: Cosine similarity

### Document Schema

```json
{
  "doc_id": "uuid-1234",
  "chunk_id": "uuid-5678",
  "title": "Design Patterns",
  "category": "programming",
  "text_snippet": "Design patterns are reusable solutions...",
  "embedding": [0.123, -0.456, ...]  // 256-dim vector
}
```

## Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create index
response = requests.post(f"{BASE_URL}/api/index/create", json={
    "index_name": "test-index",
    "embedding_dim": 256
})
print(response.json())

# 2. Ingest data
response = requests.post(f"{BASE_URL}/api/ingest/start", json={
    "csv_path": "benchmark_dataset_2000.csv",
    "index_name": "test-index"
})
print(response.json())

# 3. Search with RAG
response = requests.post(f"{BASE_URL}/api/search/query", json={
    "index_name": "test-index",
    "query": "Explain SOLID principles",
    "top_k": 3
})
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Found {len(result['contexts'])} relevant documents")
```

## Performance Tips

1. **Batch Size**: Adjust `BATCH_SIZE` in `.env` for optimal ingestion speed (default: 64)
2. **Chunk Size**: Configure `CHUNK_MAX_WORDS` for better retrieval granularity (default: 140)
3. **Top K**: Use smaller `top_k` values for faster queries (5-10 is usually sufficient)
4. **Filtering**: Use `filter_category` for pre-filtering (much faster than post-filtering)

## Troubleshooting

### OpenSearch Not Starting

```bash
# Check logs
docker logs opensearch

# Common fix: Increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
```

### Index Creation Fails

```bash
# Check if OpenSearch is accessible
curl http://localhost:9200

# Delete existing index if needed
curl -X DELETE "http://localhost:9200/bechmark_index"
```

### Slow Queries

- Reduce `top_k` value
- Use category filtering
- Check OpenSearch resource allocation
- Consider using FAISS for smaller datasets

## When to Use OpenSearch

✅ **Use OpenSearch when:**
- Deploying to production
- Working with large datasets (> 1M vectors)
- You need distributed search
- You need efficient pre-filtering
- You need high availability

❌ **Consider FAISS when:**
- Developing locally with small datasets
- You want faster in-memory search
- You don't need distributed architecture

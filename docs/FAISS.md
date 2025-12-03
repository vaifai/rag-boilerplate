# FAISS Backend Guide

Complete guide for using FAISS (Facebook AI Similarity Search) as the vector database backend in the RAG Playground.

## Overview

FAISS is a library for efficient similarity search and clustering of dense vectors. In this implementation, FAISS indices and metadata are stored entirely in MongoDB, requiring no file system storage.

### Key Features
- ✅ Very fast in-memory search
- ✅ No file system storage (all in MongoDB)
- ✅ Perfect for development and testing
- ✅ Easy to set up (only needs MongoDB)
- ✅ Efficient for small to medium datasets

## Quick Start

### 1. Ensure MongoDB is Running

```bash
# Start via Docker Compose
docker compose up -d mongo

# Verify it's running
docker ps | grep mongo
```

### 2. Create FAISS Index

```bash
curl -X POST "http://localhost:8000/api/faiss/create" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "bechmark_index",
    "embedding_dim": 256
  }'
```

### 3. Ingest Data

```bash
curl -X POST "http://localhost:8000/api/faiss/ingest" \
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
curl -X POST "http://localhost:8000/api/faiss/search" \
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
- **Endpoint**: `POST /api/faiss/create`
- **Body**:
  ```json
  {
    "index_name": "my-faiss-index",
    "embedding_dim": 256
  }
  ```

### Data Ingestion

**Ingest CSV**
- **Endpoint**: `POST /api/faiss/ingest`
- **Body**:
  ```json
  {
    "csv_path": "data.csv",
    "index_name": "my-faiss-index",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }
  ```

### Search and RAG

**Query with RAG**
- **Endpoint**: `POST /api/faiss/search`
- **Body**:
  ```json
  {
    "index_name": "my-faiss-index",
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
    "backend": "faiss"
  }
  ```

## Architecture

### Storage Structure

FAISS uses **MongoDB for all storage** - no file system required!

**MongoDB Collections:**

1. **`faiss_indices`** - Stores index metadata and binary FAISS index
   ```json
   {
     "index_name": "my-index",
     "dimension": 256,
     "num_vectors": 2000,
     "index_data": "<binary FAISS index>",
     "created_at": "2024-01-01T00:00:00",
     "updated_at": "2024-01-01T00:00:00"
   }
   ```

2. **`faiss_chunks`** - Stores chunk metadata
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

### How It Works

1. **Index Creation**: Creates an empty `IndexIDMap(IndexFlatIP)` and stores it as binary in MongoDB
2. **Ingestion**: 
   - Embeds text chunks
   - Normalizes vectors (L2 normalization)
   - Adds to FAISS index with integer IDs
   - Stores metadata in MongoDB
   - Serializes and saves updated index to MongoDB
3. **Search**:
   - Loads FAISS index from MongoDB
   - Embeds query
   - Performs k-NN search
   - Retrieves metadata from MongoDB
   - Generates answer with LLM

### Similarity Metric

- **Algorithm**: `IndexFlatIP` (Inner Product)
- **Normalization**: L2-normalized vectors
- **Effective Metric**: Cosine similarity (same as OpenSearch)

## Configuration

### Environment Variables

```env
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

# 1. Create FAISS index
response = requests.post(f"{BASE_URL}/api/faiss/create", json={
    "index_name": "test-faiss",
    "embedding_dim": 256
})
print(response.json())

# 2. Ingest data
response = requests.post(f"{BASE_URL}/api/faiss/ingest", json={
    "csv_path": "benchmark_dataset_2000.csv",
    "index_name": "test-faiss"
})
print(response.json())

# 3. Search with RAG
response = requests.post(f"{BASE_URL}/api/faiss/search", json={
    "index_name": "test-faiss",
    "query": "How to write clean Python code?",
    "top_k": 3
})
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Contexts: {len(result['contexts'])} documents")
```

## Comparison with OpenSearch

| Feature | OpenSearch | FAISS |
|---------|-----------|-------|
| **Storage** | Distributed, persistent | MongoDB (binary + metadata) |
| **Scalability** | Horizontal scaling | Single machine (in-memory) |
| **Filtering** | Pre-filtering (efficient) | Post-filtering (less efficient) |
| **Setup** | Requires Docker container | Requires MongoDB only |
| **Speed** | Fast for distributed data | Very fast (in-memory) |
| **Use Case** | Production, large datasets | Development, experiments |
| **Memory** | Managed by OpenSearch | Loaded into RAM on each search |

## Performance Considerations

### Advantages
- ⚡ **Very fast search**: In-memory operations
- 🚀 **Quick setup**: Only needs MongoDB
- 💾 **No file management**: Everything in database
- 🔧 **Easy to experiment**: Create/delete indices easily

### Limitations
- 📊 **Memory usage**: Index loaded into RAM for each search
- 🔍 **Post-filtering**: Less efficient than OpenSearch pre-filtering
- 📈 **Scalability**: Not distributed (single machine)
- 🔄 **Concurrency**: Each search reloads index from MongoDB

### Optimization Tips

1. **Cache the index** in production (load once, reuse)
2. **Use smaller `top_k`** values (5-10)
3. **Limit dataset size** to < 1M vectors
4. **Consider OpenSearch** for larger datasets

## When to Use FAISS

✅ **Use FAISS when:**
- Developing and testing locally
- Working with small to medium datasets (< 1M vectors)
- You want very fast in-memory search
- Experimenting with different embedding models
- You already have MongoDB running
- You need quick prototyping

❌ **Use OpenSearch when:**
- Deploying to production
- Working with large datasets (> 1M vectors)
- You need distributed search
- You need efficient pre-filtering
- You need high availability
- You need advanced search features

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
docker ps | grep mongo

# Test connection
mongosh mongodb://localhost:27017
```

### Index Not Found

```bash
# List all FAISS indices via MongoDB
mongosh rag_playground --eval "db.faiss_indices.find({}, {index_name: 1, num_vectors: 1})"
```

### Slow Search Performance

- Index is being reloaded from MongoDB on each search
- Consider implementing index caching for production
- Or switch to OpenSearch for better performance

### Memory Issues

- FAISS index too large for available RAM
- Reduce dataset size or use OpenSearch
- Check MongoDB memory usage

## Advanced Usage

### Custom Index Types

The current implementation uses `IndexFlatIP` (exact search). For larger datasets, consider:
- `IndexIVFFlat`: Inverted file index (faster, approximate)
- `IndexHNSW`: Hierarchical Navigable Small World (very fast, approximate)

Modify `faiss_service.py` to use different index types.

### Batch Processing

Ingestion is already batched (default: 64 documents per batch). Adjust `BATCH_SIZE` in `.env` for optimal performance.

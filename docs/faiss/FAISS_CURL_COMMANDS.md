# FAISS API - cURL Commands

Complete workflow to create index, ingest data, and search using FAISS backend.

---

## Prerequisites

1. **Start the FastAPI server:**
   ```bash
   python -m app
   ```

2. **Ensure MongoDB is running:**
   ```bash
   docker-compose up -d mongodb
   ```

3. **Ensure Ollama is running:**
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   ```

---

## 1. Create FAISS Index

Create a new FAISS index with dimension 256 (matching nomic-embed-text:v1.5).

```bash
curl -X POST http://localhost:8000/api/faiss/create \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "faiss-dev-index",
    "embedding_dim": 256
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "index": "faiss-dev-index",
  "dimension": 256
}
```

**What happens:**
- Creates empty FAISS index in memory
- Serializes it to binary
- Stores in MongoDB `faiss_indices` collection with `index_data` field

---

## 2. Ingest Dev Dataset

Ingest the dev dataset (100 documents) into the FAISS index.

```bash
curl -X POST http://localhost:8000/api/faiss/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "index_name": "faiss-dev-index",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "FAISS ingestion scheduled"
}
```

**What happens:**
1. Loads FAISS index from MongoDB (deserializes binary)
2. Reads CSV file
3. Chunks text into smaller pieces
4. Generates embeddings using Ollama (nomic-embed-text:v1.5)
5. Adds vectors to FAISS index with IDs
6. Stores chunk metadata in MongoDB `faiss_chunks` collection
7. Serializes updated FAISS index back to binary
8. Updates MongoDB `faiss_indices` with new `index_data`

**Note:** This runs in the background. Check server logs to see progress:
```bash
# Watch the logs
tail -f logs/app.log
```

---

## 3. Search FAISS Index

Search the FAISS index and generate a RAG answer.

### Example 1: Basic Search

```bash
curl -X POST http://localhost:8000/api/faiss/search \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "faiss-dev-index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

### Example 2: Search with Category Filter

```bash
curl -X POST http://localhost:8000/api/faiss/search \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "faiss-dev-index",
    "query": "Explain machine learning algorithms",
    "top_k": 5,
    "category": "machine_learning"
  }'
```

### Example 3: Get More Results

```bash
curl -X POST http://localhost:8000/api/faiss/search \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "faiss-dev-index",
    "query": "How does neural network training work?",
    "top_k": 10
  }'
```

**Expected Response:**
```json
{
  "answer": "Design patterns are reusable solutions to commonly occurring problems in software design...",
  "contexts": [
    {
      "chunk_id": "uuid-1234",
      "doc_id": "doc-5678",
      "title": "Design Patterns in Software Engineering",
      "category": "programming",
      "text_snippet": "Design patterns are reusable solutions...",
      "score": 0.95
    },
    {
      "chunk_id": "uuid-5678",
      "doc_id": "doc-9012",
      "title": "Object-Oriented Design",
      "category": "programming",
      "text_snippet": "The singleton pattern ensures...",
      "score": 0.92
    }
  ],
  "query": "What are design patterns?",
  "top_k": 5,
  "backend": "faiss"
}
```

**What happens:**
1. Loads FAISS index from MongoDB (deserializes binary)
2. Generates query embedding using Ollama
3. Searches FAISS index for top_k similar vectors
4. Gets FAISS int IDs: [123456789, 987654321, ...]
5. Queries MongoDB `faiss_chunks` to get metadata for those IDs
6. Applies category filter if specified (post-filtering)
7. Generates RAG answer using Ollama with retrieved contexts
8. Returns answer + contexts

---

## Complete Workflow Example

```bash
# Step 1: Create index
curl -X POST http://localhost:8000/api/faiss/create \
  -H "Content-Type: application/json" \
  -d '{"index_name": "faiss-dev-index", "embedding_dim": 256}'

# Step 2: Ingest data
curl -X POST http://localhost:8000/api/faiss/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "index_name": "faiss-dev-index",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }'

# Wait for ingestion to complete (check logs)
# Then search:

# Step 3: Search
curl -X POST http://localhost:8000/api/faiss/search \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "faiss-dev-index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

---

## Verify MongoDB Storage

Check that data is stored in MongoDB:

```bash
# Connect to MongoDB
docker exec -it rag-playground-mongodb-1 mongosh

# Switch to database
use rag_playground

# Check FAISS indices
db.faiss_indices.find().pretty()

# Check FAISS chunks
db.faiss_chunks.find().limit(5).pretty()

# Count vectors
db.faiss_indices.findOne({"index_name": "faiss-dev-index"}).num_vectors

# Count chunks
db.faiss_chunks.countDocuments({"index_name": "faiss-dev-index"})
```

---

## Troubleshooting

### Error: "FAISS index already exists"
```bash
# Delete the index from MongoDB
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.faiss_indices.deleteOne({"index_name": "faiss-dev-index"})'

# Delete associated chunks
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.faiss_chunks.deleteMany({"index_name": "faiss-dev-index"})'
```

### Error: "Cannot read CSV"
```bash
# Check if file exists
ls -lh dev_dataset_100.csv

# Use absolute path
curl -X POST http://localhost:8000/api/faiss/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "/Users/vaibhav/Desktop/Projects/rag-playground/dev_dataset_100.csv",
    "index_name": "faiss-dev-index"
  }'
```

### Check Ingestion Progress
```bash
# Watch server logs
tail -f logs/app.log | grep -i faiss

# Or check MongoDB for chunk count
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.faiss_chunks.countDocuments({"index_name": "faiss-dev-index"})'
```

---

## Comparison: OpenSearch vs FAISS

### OpenSearch Commands:
```bash
# Create index
curl -X POST http://localhost:8000/api/index/create \
  -H "Content-Type: application/json" \
  -d '{"index_name": "dev-index", "embedding_dim": 256}'

# Ingest
curl -X POST http://localhost:8000/api/ingest/start \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "dev_dataset_100.csv", "index_name": "dev-index"}'

# Search
curl -X POST http://localhost:8000/api/search/rag \
  -H "Content-Type: application/json" \
  -d '{"index_name": "dev-index", "query": "What are design patterns?", "top_k": 5}'
```

### FAISS Commands:
```bash
# Create index
curl -X POST http://localhost:8000/api/faiss/create \
  -H "Content-Type: application/json" \
  -d '{"index_name": "faiss-dev-index", "embedding_dim": 256}'

# Ingest
curl -X POST http://localhost:8000/api/faiss/ingest \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "dev_dataset_100.csv", "index_name": "faiss-dev-index"}'

# Search
curl -X POST http://localhost:8000/api/faiss/search \
  -H "Content-Type: application/json" \
  -d '{"index_name": "faiss-dev-index", "query": "What are design patterns?", "top_k": 5}'
```

**Key Difference:** Endpoints are `/api/faiss/*` instead of `/api/*`


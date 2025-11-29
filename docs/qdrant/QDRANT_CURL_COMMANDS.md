# Qdrant API - cURL Commands

Complete workflow to create collection, ingest data, and search using Qdrant backend.

---

## Prerequisites

1. **Start the FastAPI server:**
   ```bash
   python -m app
   ```

2. **Start Qdrant:**
   ```bash
   docker-compose up -d qdrant
   ```

3. **Ensure MongoDB is running:**
   ```bash
   docker-compose up -d mongodb
   ```

4. **Ensure Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

5. **Verify Qdrant is running:**
   ```bash
   curl http://localhost:6333/collections
   ```

---

## 1. Create Qdrant Collection

Create a new Qdrant collection with dimension 256 (matching nomic-embed-text:v1.5).

```bash
curl -X POST http://localhost:8000/api/qdrant/create \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev-collection",
    "embedding_dim": 256
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "collection": "qdrant-dev-collection",
  "dimension": 256
}
```

**What happens:**
- Creates collection in Qdrant with COSINE distance metric
- Stores metadata in MongoDB `qdrant_collections` collection

---

## 2. Ingest Dev Dataset

Ingest the dev dataset (100 documents) into the Qdrant collection.

```bash
curl -X POST http://localhost:8000/api/qdrant/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "collection_name": "qdrant-dev-collection",
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
  "message": "Qdrant ingestion scheduled"
}
```

**What happens:**
1. Reads CSV file
2. Chunks text into smaller pieces
3. Generates embeddings using Ollama (nomic-embed-text:v1.5)
4. Creates Qdrant points with vectors and payloads
5. Upserts points to Qdrant collection
6. Stores chunk metadata in MongoDB `qdrant_chunks` collection
7. Updates collection metadata in MongoDB

**Note:** This runs in the background. Check server logs:
```bash
tail -f logs/app.log | grep -i qdrant
```

---

## 3. Search Qdrant Collection

Search the Qdrant collection and generate a RAG answer.

### Example 1: Basic Search

```bash
curl -X POST http://localhost:8000/api/qdrant/search \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev-collection",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

### Example 2: Search with Category Filter

```bash
curl -X POST http://localhost:8000/api/qdrant/search \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev-collection",
    "query": "Explain machine learning algorithms",
    "top_k": 5,
    "category": "machine_learning"
  }'
```

### Example 3: Get More Results

```bash
curl -X POST http://localhost:8000/api/qdrant/search \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev-collection",
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
  "backend": "qdrant"
}
```

**What happens:**
1. Generates query embedding using Ollama
2. Searches Qdrant collection for similar vectors
3. Gets results with payloads (doc_id, title, category, text_snippet)
4. Applies category filter if specified
5. Generates RAG answer using Ollama with retrieved contexts
6. Returns answer + contexts

---

## Complete Workflow Example

```bash
# Step 1: Create collection
curl -X POST http://localhost:8000/api/qdrant/create \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "qdrant-dev-collection", "embedding_dim": 256}'

# Step 2: Ingest data
curl -X POST http://localhost:8000/api/qdrant/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "collection_name": "qdrant-dev-collection",
    "doc_id_col": "id",
    "title_col": "title",
    "category_col": "category",
    "text_col": "text"
  }'

# Wait for ingestion to complete (check logs)
# Then search:

# Step 3: Search
curl -X POST http://localhost:8000/api/qdrant/search \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev-collection",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

---

## Verify Qdrant Storage

Check that data is stored in Qdrant and MongoDB:

### Check Qdrant Collections
```bash
# List all collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/qdrant-dev-collection

# Count points
curl http://localhost:6333/collections/qdrant-dev-collection | jq '.result.points_count'
```

### Check MongoDB
```bash
# Connect to MongoDB
docker exec -it rag-playground-mongodb-1 mongosh rag_playground

# Check Qdrant collections
db.qdrant_collections.find().pretty()

# Check Qdrant chunks
db.qdrant_chunks.find().limit(5).pretty()

# Count vectors
db.qdrant_collections.findOne({"collection_name": "qdrant-dev-collection"}).num_vectors

# Count chunks
db.qdrant_chunks.countDocuments({"collection_name": "qdrant-dev-collection"})
```

---

## Troubleshooting

### Error: "Qdrant collection already exists"
```bash
# Delete from Qdrant
curl -X DELETE http://localhost:6333/collections/qdrant-dev-collection

# Delete from MongoDB
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_collections.deleteOne({"collection_name": "qdrant-dev-collection"})'

docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_chunks.deleteMany({"collection_name": "qdrant-dev-collection"})'
```

### Error: "Cannot read CSV"
```bash
# Check if file exists
ls -lh dev_dataset_100.csv

# Use absolute path
curl -X POST http://localhost:8000/api/qdrant/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "/Users/vaibhav/Desktop/Projects/rag-playground/dev_dataset_100.csv",
    "collection_name": "qdrant-dev-collection"
  }'
```

### Check Ingestion Progress
```bash
# Watch server logs
tail -f logs/app.log | grep -i qdrant

# Check Qdrant point count
curl http://localhost:6333/collections/qdrant-dev-collection | jq '.result.points_count'

# Check MongoDB chunk count
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_chunks.countDocuments({"collection_name": "qdrant-dev-collection"})'
```

### Qdrant Not Running
```bash
# Start Qdrant
docker-compose up -d qdrant

# Check Qdrant logs
docker logs qdrant

# Verify Qdrant is accessible
curl http://localhost:6333/collections
```

---

## Comparison: OpenSearch vs FAISS vs Qdrant

### OpenSearch Commands:
```bash
curl -X POST http://localhost:8000/api/index/create \
  -H "Content-Type: application/json" \
  -d '{"index_name": "dev-index", "embedding_dim": 256}'

curl -X POST http://localhost:8000/api/ingest/start \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "dev_dataset_100.csv", "index_name": "dev-index"}'

curl -X POST http://localhost:8000/api/search/query \
  -H "Content-Type: application/json" \
  -d '{"index_name": "dev-index", "query": "What are design patterns?", "top_k": 5}'
```

### FAISS Commands:
```bash
curl -X POST http://localhost:8000/api/faiss/create \
  -H "Content-Type: application/json" \
  -d '{"index_name": "faiss-dev-index", "embedding_dim": 256}'

curl -X POST http://localhost:8000/api/faiss/ingest \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "dev_dataset_100.csv", "index_name": "faiss-dev-index"}'

curl -X POST http://localhost:8000/api/faiss/search \
  -H "Content-Type: application/json" \
  -d '{"index_name": "faiss-dev-index", "query": "What are design patterns?", "top_k": 5}'
```

### Qdrant Commands:
```bash
curl -X POST http://localhost:8000/api/qdrant/create \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "qdrant-dev-collection", "embedding_dim": 256}'

curl -X POST http://localhost:8000/api/qdrant/ingest \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "dev_dataset_100.csv", "collection_name": "qdrant-dev-collection"}'

curl -X POST http://localhost:8000/api/qdrant/search \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "qdrant-dev-collection", "query": "What are design patterns?", "top_k": 5}'
```

**Key Differences:**
- OpenSearch: `/api/index/*`, `/api/ingest/*`, `/api/search/*`
- FAISS: `/api/faiss/*` (uses `index_name`)
- Qdrant: `/api/qdrant/*` (uses `collection_name`)


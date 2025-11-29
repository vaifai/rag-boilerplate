# Qdrant Quick Reference

## 🚀 Three Simple Commands

### 1️⃣ Create Collection
```bash
curl -X POST http://localhost:8000/api/qdrant/create \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "qdrant-dev-collection", "embedding_dim": 256}'
```

### 2️⃣ Ingest Data
```bash
curl -X POST http://localhost:8000/api/qdrant/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "dev_dataset_100.csv",
    "collection_name": "qdrant-dev-collection"
  }'
```

### 3️⃣ Search
```bash
curl -X POST http://localhost:8000/api/qdrant/search \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "qdrant-dev-collection",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

---

## 📊 Backend Comparison

### OpenSearch
```bash
# Create
curl -X POST http://localhost:8000/api/index/create \
  -d '{"index_name": "dev-index", "embedding_dim": 256}'

# Ingest
curl -X POST http://localhost:8000/api/ingest/start \
  -d '{"csv_path": "dev_dataset_100.csv", "index_name": "dev-index"}'

# Search
curl -X POST http://localhost:8000/api/search/query \
  -d '{"index_name": "dev-index", "query": "What are design patterns?", "top_k": 5}'
```

### FAISS
```bash
# Create
curl -X POST http://localhost:8000/api/faiss/create \
  -d '{"index_name": "faiss-dev-index", "embedding_dim": 256}'

# Ingest
curl -X POST http://localhost:8000/api/faiss/ingest \
  -d '{"csv_path": "dev_dataset_100.csv", "index_name": "faiss-dev-index"}'

# Search
curl -X POST http://localhost:8000/api/faiss/search \
  -d '{"index_name": "faiss-dev-index", "query": "What are design patterns?", "top_k": 5}'
```

### Qdrant
```bash
# Create
curl -X POST http://localhost:8000/api/qdrant/create \
  -d '{"collection_name": "qdrant-dev-collection", "embedding_dim": 256}'

# Ingest
curl -X POST http://localhost:8000/api/qdrant/ingest \
  -d '{"csv_path": "dev_dataset_100.csv", "collection_name": "qdrant-dev-collection"}'

# Search
curl -X POST http://localhost:8000/api/qdrant/search \
  -d '{"collection_name": "qdrant-dev-collection", "query": "What are design patterns?", "top_k": 5}'
```

---

## 🔍 Verification

### Check Qdrant
```bash
# List collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/qdrant-dev-collection

# Count points
curl http://localhost:6333/collections/qdrant-dev-collection | jq '.result.points_count'
```

### Check MongoDB
```bash
# Collection metadata
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_collections.find().pretty()'

# Chunk count
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_chunks.countDocuments({"collection_name": "qdrant-dev-collection"})'
```

---

## 🧹 Cleanup

```bash
# Delete from Qdrant
curl -X DELETE http://localhost:6333/collections/qdrant-dev-collection

# Delete from MongoDB
docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_collections.deleteOne({"collection_name": "qdrant-dev-collection"})'

docker exec -it rag-playground-mongodb-1 mongosh rag_playground \
  --eval 'db.qdrant_chunks.deleteMany({"collection_name": "qdrant-dev-collection"})'
```

---

## 📚 Documentation

- **Full Guide**: `docs/QDRANT_INTEGRATION.md`
- **cURL Commands**: `QDRANT_CURL_COMMANDS.md`
- **Implementation Summary**: `QDRANT_IMPLEMENTATION_SUMMARY.md`
- **Quick Start Script**: `./QDRANT_QUICK_START.sh`


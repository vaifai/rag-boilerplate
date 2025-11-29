# FAISS MongoDB-Only Architecture

## Overview

The FAISS integration stores **everything in MongoDB** - no file system storage required!

## Storage Architecture

### MongoDB Collections

#### 1. `faiss_indices`
Stores FAISS index metadata + binary index data:
```json
{
  "_id": ObjectId("..."),
  "index_name": "my-index",
  "dimension": 256,
  "num_vectors": 1500,
  "index_data": Binary("<serialized FAISS index>"),
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "updated_at": ISODate("2024-01-01T00:00:00Z")
}
```

#### 2. `faiss_chunks`
Stores chunk metadata for retrieval:
```json
{
  "_id": ObjectId("..."),
  "chunk_id": "uuid-1234",
  "faiss_int_id": 123456789012345,
  "index_name": "my-index",
  "doc_id": "doc-uuid",
  "title": "Design Patterns",
  "category": "programming",
  "text_snippet": "Design patterns are reusable solutions...",
  "created_at": ISODate("2024-01-01T00:00:00Z")
}
```

## How It Works

### 1. Serialization/Deserialization

**Serialize FAISS index to bytes:**
```python
def _serialize_faiss_index(index) -> bytes:
    """Serialize FAISS index to bytes for MongoDB storage"""
    buffer = io.BytesIO()
    faiss.write_index(index, faiss.BufferedIOWriter(
        faiss.PyCallbackIOWriter(buffer.write)
    ))
    return buffer.getvalue()
```

**Deserialize FAISS index from bytes:**
```python
def _deserialize_faiss_index(index_bytes: bytes):
    """Deserialize FAISS index from bytes stored in MongoDB"""
    buffer = io.BytesIO(index_bytes)
    reader = faiss.BufferedIOReader(
        faiss.PyCallbackIOReader(buffer.read)
    )
    return faiss.read_index(reader)
```

### 2. Create Index Flow

```
1. User calls POST /api/faiss/create
   ↓
2. Create empty FAISS index in memory
   index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
   ↓
3. Serialize to bytes
   index_bytes = _serialize_faiss_index(index)
   ↓
4. Store in MongoDB
   faiss_indices.insert_one({
       "index_name": "my-index",
       "dimension": 256,
       "index_data": index_bytes,  # Binary data
       ...
   })
   ↓
5. Done! No files created.
```

### 3. Ingestion Flow

```
1. User calls POST /api/faiss/ingest
   ↓
2. Load index from MongoDB
   index_doc = faiss_indices.find_one({"index_name": "my-index"})
   faiss_index = _deserialize_faiss_index(index_doc["index_data"])
   ↓
3. Read CSV, chunk text, generate embeddings
   ↓
4. Add vectors to FAISS index (in memory)
   faiss_index.add_with_ids(embeddings, int_ids)
   ↓
5. Store chunk metadata in MongoDB
   faiss_chunks.insert_one({...})
   ↓
6. Serialize updated index
   index_bytes = _serialize_faiss_index(faiss_index)
   ↓
7. Update in MongoDB
   faiss_indices.update_one(
       {"index_name": "my-index"},
       {"$set": {"index_data": index_bytes, "num_vectors": 1500}}
   )
   ↓
8. Done! Everything in MongoDB.
```

### 4. Search Flow

```
1. User calls POST /api/faiss/search
   ↓
2. Load index from MongoDB
   index_doc = faiss_indices.find_one({"index_name": "my-index"})
   faiss_index = _deserialize_faiss_index(index_doc["index_data"])
   ↓
3. Generate query embedding
   q_vec = embedder.embed(query)
   ↓
4. Search FAISS index (in memory)
   D, I = faiss_index.search(q_vec, top_k)
   ↓
5. Retrieve metadata from MongoDB
   chunk_doc = faiss_chunks.find_one({"faiss_int_id": faiss_int_id})
   ↓
6. Generate RAG answer
   answer = generator.generate(query, contexts)
   ↓
7. Return result
```

## Benefits

✅ **No File System Dependencies**: Everything in MongoDB  
✅ **Portable**: Easy to backup/restore (just MongoDB dump)  
✅ **Consistent**: Single source of truth (MongoDB)  
✅ **Simple Deployment**: No need to manage file paths  
✅ **Cloud-Ready**: Works with MongoDB Atlas or any MongoDB service  

## Performance Considerations

⚠️ **Memory Usage**: FAISS index is loaded into memory for each operation  
⚠️ **Network Overhead**: Index is transferred from MongoDB each time  
⚠️ **Serialization Cost**: Converting between bytes and FAISS index  

**For Production**: Consider adding an in-memory cache to avoid repeated deserialization.

## Comparison with File-Based Approach

| Aspect | File-Based | MongoDB-Only |
|--------|-----------|--------------|
| **Storage** | Local files | MongoDB binary |
| **Portability** | Need to copy files | Just MongoDB backup |
| **Deployment** | Manage file paths | No file management |
| **Backup** | Files + MongoDB | MongoDB only |
| **Consistency** | Files can get out of sync | Always consistent |
| **Performance** | Direct file I/O | Network + deserialization |

## Code Structure

```
app/services/faiss_service.py
├── _id_to_int()                    # Convert UUID to int64
├── _serialize_faiss_index()        # FAISS → bytes
├── _deserialize_faiss_index()      # bytes → FAISS
├── create_faiss_index()            # Create & store in MongoDB
├── ingest_csv_to_faiss()           # Load, update, save to MongoDB
└── search_faiss_index()            # Load from MongoDB & search
```

No file path functions needed!


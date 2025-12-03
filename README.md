# 🚀 RAG Playground

<div align="center">

**A production-ready RAG system with multi-backend vector search and comprehensive evaluation**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenSearch](https://img.shields.io/badge/OpenSearch-3.2.0-orange.svg)](https://opensearch.org/)

</div>

---

## 🎯 Overview

A complete Retrieval-Augmented Generation (RAG) system supporting **three vector database backends** (OpenSearch, FAISS, Qdrant) with advanced evaluation capabilities using both traditional IR metrics and LLM-as-judge (Ragas).

### Key Features

- ✅ **Multi-Backend Support**: OpenSearch, FAISS, Qdrant
- ✅ **Comprehensive Evaluation**: Traditional metrics (P@K, R@K, F1, ROC-AUC) + Ragas (Faithfulness, Answer Relevancy, Context Recall)
- ✅ **Local LLM Integration**: Ollama for embeddings and generation
- ✅ **Benchmark Dataset**: 2000 documents, 50 curated queries

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI, Pydantic, Uvicorn |
| **Vector DBs** | OpenSearch 3.2.0, FAISS, Qdrant |
| **Embeddings** | Nomic Embed Text v1.5 (256-dim) |
| **Generation** | Llama 3.1 8B |
| **Evaluation** | Ragas, scikit-learn |
| **Infrastructure** | Docker, MongoDB, Ollama |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Ollama ([Install Guide](https://ollama.ai/download))

### Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/rag-playground.git
cd rag-playground

# 2. Install Ollama models
ollama pull nomic-embed-text:v1.5
ollama pull llama3.1:8b

# 3. Start infrastructure
docker compose up -d

# 4. Set up Python environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env  # Edit as needed

# 6. Run application
python -m app
```

API available at `http://localhost:8000` | Docs at `http://localhost:8000/docs`

---

## 📡 API Usage

### Create Index & Ingest Data

```bash
# OpenSearch
curl -X POST "http://localhost:8000/api/index/create" \
  -H "Content-Type: application/json" \
  -d '{"index_name": "bechmark_index", "embedding_dim": 256}'

curl -X POST "http://localhost:8000/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "benchmark_dataset_2000.csv", "index_name": "bechmark_index"}'

# FAISS
curl -X POST "http://localhost:8000/api/faiss/create" \
  -H "Content-Type: application/json" \
  -d '{"index_name": "bechmark_index", "embedding_dim": 256}'

curl -X POST "http://localhost:8000/api/faiss/ingest" \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "benchmark_dataset_2000.csv", "index_name": "bechmark_index"}'

# Qdrant
curl -X POST "http://localhost:8000/api/qdrant/create" \
  -H "Content-Type: application/json" \
  -d '{"collection_name": "bechmark_index", "embedding_dim": 256}'

curl -X POST "http://localhost:8000/api/qdrant/ingest" \
  -H "Content-Type: application/json" \
  -d '{"csv_path": "benchmark_dataset_2000.csv", "collection_name": "bechmark_index"}'
```

### Search & Query

```bash
curl -X POST "http://localhost:8000/api/search/query" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "bechmark_index",
    "query": "What are design patterns?",
    "top_k": 5
  }'
```

---

## 📊 Evaluation

### Ragas (LLM-as-Judge)

```bash
python scripts/evaluate_ragas.py
```

Evaluates using:
- **Faithfulness**: Answer consistency with context
- **Answer Relevancy**: How well answer addresses question
- **Context Recall**: Retrieval completeness

---

## 📁 Project Structure

```
rag-playground/
├── app/
│   ├── api/              # FastAPI endpoints
│   ├── services/         # RAG, FAISS, Qdrant services
│   ├── embeddings/       # Ollama wrappers
│   └── core/             # Configuration
├── scripts/
│   └── evaluate_ragas.py     # LLM-as-judge evaluation
├── docs/
│   ├── OPENSEARCH.md     # OpenSearch guide
│   ├── FAISS.md          # FAISS guide
│   └── QDRANT.md         # Qdrant guide
├── benchmark_dataset_2000.csv
├── benchmark_queries.json
└── docker-compose.yml
```

---

## ⚙️ Configuration

Key environment variables in `.env`:

```env
# Backends
OPENSEARCH_HOST=http://localhost:9200
QDRANT_HOST=localhost
QDRANT_PORT=6333
MONGO_URI=mongodb://localhost:27017

# Ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5
OLLAMA_EMBEDDING_DIMENSION=256
OLLAMA_GENERATE_MODEL=llama3.1:8b

# Ingestion
BATCH_SIZE=64
CHUNK_MAX_WORDS=140
CHUNK_OVERLAP=30
```

---

## 🎯 Backend Comparison

| Feature | OpenSearch | FAISS | Qdrant |
|---------|-----------|-------|--------|
| **Storage** | Distributed | MongoDB | Qdrant + MongoDB |
| **Scalability** | Horizontal | Single machine | Horizontal |
| **Filtering** | Pre-filtering | Post-filtering | Native |
| **Setup** | Docker | MongoDB only | Docker + MongoDB |
| **Use Case** | Production | Development | Production |

**Detailed guides**: See `docs/OPENSEARCH.md`, `docs/FAISS.md`, `docs/QDRANT.md`

---

## 🐛 Troubleshooting

```bash
# Check services
docker ps

# Restart services
docker compose restart

# Check Ollama models
ollama list

# Verify OpenSearch
curl http://localhost:9200/_cluster/health

# Verify Qdrant
curl http://localhost:6333/collections
```

---

## 📚 Documentation

- **Backend Guides**: `docs/OPENSEARCH.md`, `docs/FAISS.md`, `docs/QDRANT.md`
- **API Docs**: http://localhost:8000/docs
- **Evaluation**: See `scripts/` directory

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ | Production-Ready RAG System

</div>

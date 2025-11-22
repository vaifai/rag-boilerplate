# 🚀 RAG Playground

<div align="center">

**An educational local RAG implementation built with FastAPI, OpenSearch, and Ollama**

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenSearch](https://img.shields.io/badge/OpenSearch-3.2.0-orange.svg)](https://opensearch.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-74%20Passing-brightgreen.svg)](tests/)

</div>

---

> ⚠️ **Educational Project Notice**
> This is an **educational project** designed to help you learn and understand local RAG (Retrieval-Augmented Generation) implementation. All components run locally on your machine, making it perfect for learning, experimentation, and prototyping. **This is NOT a production-grade system** and should not be deployed to production environments without significant hardening, security reviews, and scalability improvements.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [Usage Examples](#-usage-examples)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**RAG Playground** is an educational implementation of a Retrieval-Augmented Generation (RAG) system that runs entirely on your local machine. This project demonstrates how to build a semantic search engine with AI-powered question answering using modern open-source tools—perfect for learning, experimentation, and understanding RAG concepts.

### What is RAG?

RAG combines the power of:
- 🔍 **Semantic Search**: Find relevant information using vector embeddings
- 🤖 **Large Language Models**: Generate accurate, context-aware answers
- 📚 **Knowledge Base**: Your own documents and data

### Why This Project?

- 🏠 **100% Local**: Everything runs on your machine—no cloud dependencies
- 📚 **Educational**: Learn RAG concepts with clean, well-documented code
- 🧪 **Experimental**: Perfect sandbox for testing RAG techniques
- 🔓 **Open Source**: Built entirely with open-source tools
- 🧩 **Modular**: Easy to understand and modify components

### Use Cases

- 🎓 **Learning**: Understand how RAG systems work
- 🧪 **Prototyping**: Test RAG ideas before cloud deployment
- 📖 **Document Q&A**: Experiment with your own documents
- 🔎 **Semantic Search**: Build local search engines
- 💬 **Chatbot Development**: Create knowledge-based assistants

---

## ✨ Features

### Core Capabilities

- ✅ **Vector-based Semantic Search** - Find documents by meaning, not just keywords
- ✅ **Document Ingestion** - Process and chunk CSV documents automatically
- ✅ **Embedding Generation** - Convert text to vectors using Nomic Embed
- ✅ **k-NN Search** - Fast approximate nearest neighbor search with FAISS
- ✅ **AI-Powered Answers** - Generate contextual responses using Llama 3.2
- ✅ **Category Filtering** - Filter search results by document categories
- ✅ **RESTful API** - Clean, documented FastAPI endpoints
- ✅ **Background Processing** - Async ingestion for large datasets
- ✅ **Docker Support** - Containerized infrastructure

### Technical Highlights

- 🚄 **High Performance**: Native k-NN with HNSW algorithm
- 🎨 **Clean Architecture**: Modular, maintainable codebase
- 📦 **Easy Deployment**: Docker Compose for one-command setup
- 🔧 **Configurable**: Environment-based configuration
- 📊 **Scalable**: Designed for production workloads

---

## 🛠️ Tech Stack

### Backend Framework
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation using Python type annotations
- **[Uvicorn](https://www.uvicorn.org/)** - Lightning-fast ASGI server

### Vector Database
- **[OpenSearch 3.2.0](https://opensearch.org/)** - Distributed search and analytics engine
  - k-NN plugin with FAISS engine
  - Cosine similarity for vector search
  - HNSW algorithm for approximate nearest neighbors

### AI Models (via Ollama)
- **[Nomic Embed Text v1.5](https://ollama.com/library/nomic-embed-text)** - Embedding model (256 dimensions)
  - Purpose: Convert text to semantic vectors
  - Size: ~137M parameters
  - Optimized for semantic search

- **[Llama 3.2](https://ollama.com/library/llama3.2)** - Language model for generation
  - Purpose: Generate human-readable answers
  - Context-aware response generation
  - RAG-optimized prompting

### Infrastructure
- **[Docker](https://www.docker.com/)** & **Docker Compose** - Containerization
- **[Ollama](https://ollama.ai/)** - Local LLM inference server
- **[MongoDB](https://www.mongodb.com/)** - Document metadata storage (optional)
- **[Qdrant](https://qdrant.tech/)** - Alternative vector database (optional)

### Python Libraries
- `opensearch-py` - OpenSearch Python client
- `pandas` - Data manipulation and CSV processing
- `numpy` - Numerical computing for embeddings
- `requests` - HTTP client for Ollama API
- `python-dotenv` - Environment variable management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline Flow                        │
└─────────────────────────────────────────────────────────────┘

📄 CSV Document
    ↓
┌───────────────┐
│  Text Chunker │  ← Split into semantic chunks (140 words)
└───────┬───────┘
        ↓
┌───────────────┐
│ Nomic Embed   │  ← Generate 256-dim vectors
│   (Ollama)    │
└───────┬───────┘
        ↓
┌───────────────┐
│  OpenSearch   │  ← Index with FAISS k-NN
│   (HNSW)      │
└───────────────┘

🔍 User Query
    ↓
┌───────────────┐
│ Nomic Embed   │  ← Embed query
└───────┬───────┘
        ↓
┌───────────────┐
│ Vector Search │  ← Find top-k similar chunks
│ (Cosine Sim)  │
└───────┬───────┘
        ↓
┌───────────────┐
│  Llama 3.2    │  ← Generate answer from context
│   (Ollama)    │
└───────┬───────┘
        ↓
    💬 Answer
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose**
- **Ollama** installed locally ([Install Guide](https://ollama.ai/download))

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/vaifai/rag-playground.git
cd rag-playground
```

### 2️⃣ Install Ollama Models

```bash
# Install embedding model
ollama pull nomic-embed-text:v1.5

# Install generation model
ollama pull llama3.2
```

### 3️⃣ Start Infrastructure

```bash
# Start OpenSearch, MongoDB, Qdrant
docker-compose up -d

# Verify services are running
docker ps
```

### 4️⃣ Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 5️⃣ Configure Environment

Create a `.env` file in the project root:

```env
# App Configuration
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000

# OpenSearch
OPENSEARCH_HOST=localhost:9200
OPENSEARCH_INDEX=dev-test

# Ollama Configuration
OLLAMA_API_URL=http://localhost:11434/api/embed
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:v1.5
OLLAMA_EMBEDDING_DIMENSION=256
OLLAMA_GENERATE_API=http://localhost:11434/api/generate
OLLAMA_GENERATE_MODEL=llama3.2

# Ingestion Settings
BATCH_SIZE=64
CHUNK_MAX_WORDS=140
CHUNK_OVERLAP=30
```

### 6️⃣ Run the Application

```bash
python -m app
```

The API will be available at `http://localhost:8000`

📚 **API Documentation**: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Health Check
```http
GET /health
```

### Index Management

#### Create Index
```http
POST /api/index/create
Content-Type: application/json

{
  "index_name": "dev-test",
  "embedding_dim": 256
}
```

### Data Ingestion

#### Ingest CSV
```http
POST /api/ingest/start
Content-Type: application/json

{
  "csv_path": "/path/to/dev_dataset_100.csv",
  "index_name": "dev-test"
}
```

### Search & Query

#### Semantic Search with RAG
```http
POST /api/search/query
Content-Type: application/json

{
  "index_name": "dev-test",
  "query": "What is machine learning?",
  "top_k": 5
}
```

#### Search with Category Filter
```http
POST /api/search/query
Content-Type: application/json

{
  "index_name": "dev-test",
  "query": "What is machine learning?",
  "top_k": 5,
  "category": "technology"
}
```

---

## 💡 Usage Examples


### Complete Workflow

```bash
# 1. Create an index
curl -X POST "http://localhost:8000/api/index/create" \
  -H "Content-Type: application/json" \
  -d '{"index_name": "dev-test", "embedding_dim": 256}'

# 2. Ingest documents
curl -X POST "http://localhost:8000/api/ingest/start" \
  -H "Content-Type: application/json" \
  -d '{
    "csv_path": "/path/to/dev_dataset_100.csv",
    "index_name": "dev-test"
  }'

# 3. Search and get AI-generated answers
curl -X POST "http://localhost:8000/api/search/query" \
  -H "Content-Type: application/json" \
  -d '{
    "index_name": "dev-test",
    "query": "Explain quantum computing",
    "top_k": 5
  }'
```

### Response Format

```json
{
  "query": "Explain quantum computing",
  "answer": "Quantum computing is a type of computation that harnesses quantum mechanical phenomena...",
  "contexts": [
    {
      "id": "chunk-uuid-1",
      "score": 1.85,
      "doc_id": "doc-123",
      "title": "Introduction to Quantum Computing",
      "category": "technology",
      "text_snippet": "Quantum computing leverages quantum bits or qubits..."
    },
    ...
  ]
}
```

---

## 📁 Project Structure

```
rag-playground/
├── 📂 app/
│   ├── 📂 api/                    # API route handlers
│   │   ├── index.py              # Index management endpoints
│   │   ├── ingest.py             # Data ingestion endpoints
│   │   └── search.py             # Search & RAG endpoints
│   ├── 📂 clients/               # External service clients
│   │   └── opensearch_client.py  # OpenSearch connection
│   ├── 📂 core/                  # Core configuration
│   │   └── config.py             # Settings & environment vars
│   ├── 📂 embeddings/            # Embedding & generation
│   │   ├── ollama_api_embedder.py   # Nomic Embed wrapper
│   │   └── ollama_generator.py      # Llama 3.2 wrapper
│   ├── 📂 services/              # Business logic
│   │   ├── ingest_service.py     # Document processing
│   │   └── rag_service.py        # Search & RAG logic
│   ├── 📂 utils/                 # Utility functions
│   │   └── text_splitter.py      # Text chunking
│   └── __main__.py               # Application entry point
├── 📂 docker/                     # Docker volumes (gitignored)
├── 📄 docker-compose.yml          # Infrastructure setup
├── 📄 requirements.txt            # Python dependencies
├── 📄 .env                        # Environment variables
├── 📄 README.md                   # This file
└── 📄 LICENSE                     # MIT License
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment (development/production) |
| `DEBUG` | `True` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `OPENSEARCH_HOST` | - | OpenSearch connection string |
| `OPENSEARCH_INDEX` | - | Default index name |
| `OLLAMA_API_URL` | `http://localhost:11434/api/embed` | Ollama embed endpoint |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text:v1.5` | Embedding model |
| `OLLAMA_EMBEDDING_DIMENSION` | `256` | Vector dimensions |
| `OLLAMA_GENERATE_API` | `http://localhost:11434/api/generate` | Ollama generate endpoint |
| `OLLAMA_GENERATE_MODEL` | `llama3.2` | Generation model |
| `BATCH_SIZE` | `64` | Embedding batch size |
| `CHUNK_MAX_WORDS` | `140` | Max words per chunk |
| `CHUNK_OVERLAP` | `30` | Overlapping words between chunks |

### OpenSearch Index Configuration

The index is created with:
- **Vector Type**: `knn_vector` with FAISS engine
- **Similarity**: Cosine similarity (`cosinesimil`)
- **Algorithm**: HNSW (Hierarchical Navigable Small World)
- **Parameters**:
  - `ef_construction`: 128 (index quality)
  - `m`: 24 (connections per node)
  - `ef_search`: 100 (search quality)

---

## 🧪 Testing

This project includes comprehensive unit tests covering all major components.

### Run All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage report (if pytest-cov is installed)
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Test Coverage

The test suite includes **74 passing tests** covering:

- ✅ **Text Splitter** (13 tests): Chunking logic, edge cases, overlap functionality
- ✅ **Ollama Embedder** (13 tests): API integration, response parsing, batch processing
- ✅ **Ollama Generator** (9 tests): Text generation, prompt construction, error handling
- ✅ **RAG Service** (13 tests): Search functionality, k-NN queries, answer generation
- ✅ **Ingest Service** (9 tests): CSV processing, embedding batching, data validation
- ✅ **API Endpoints** (17 tests): Index creation, search queries, request validation

### Run Specific Test Files

```bash
# Test text splitter
pytest tests/test_text_splitter.py -v

# Test embeddings
pytest tests/test_ollama_embedder.py -v

# Test RAG service
pytest tests/test_rag_service.py -v

# Test API endpoints
pytest tests/test_api_index.py -v
pytest tests/test_api_search.py -v
```

### Verify System Components

#### OpenSearch

```bash
# Check cluster health
curl http://localhost:9200/_cluster/health?pretty

# List all indices
curl http://localhost:9200/_cat/indices?v

# Check specific index
curl http://localhost:9200/dev-test?pretty
```

#### Ollama

```bash
# Test embedding
curl -X POST http://localhost:11434/api/embed \
  -d '{
    "model": "nomic-embed-text:v1.5",
    "input": "Test text",
    "dimensions": 256
  }'

# Test generation
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "llama3.2",
    "prompt": "What is AI?",
    "stream": false
  }'
```

#### FastAPI Application

```bash
# Check API health
curl http://localhost:8000/

# Run the full test suite
source .venv/bin/activate
pytest tests/ -v
```

---

## 🎨 Customization

### Using Different Models

**Embedding Models:**
```env
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
OLLAMA_EMBEDDING_DIMENSION=1024
```

**Generation Models:**
```env
OLLAMA_GENERATE_MODEL=mistral
# or
OLLAMA_GENERATE_MODEL=llama3.1
```

### Adjusting Chunking Strategy

```env
CHUNK_MAX_WORDS=200      # Larger chunks
CHUNK_OVERLAP=50         # More context overlap
```

### Changing Vector Similarity

Edit `app/api/index.py`:
```python
"space_type": "l2"           # Euclidean distance
# or
"space_type": "innerproduct" # Dot product
```

---

## 🐛 Troubleshooting

### Common Issues

**1. OpenSearch connection failed**
```bash
# Check if OpenSearch is running
docker ps | grep opensearch

# Restart OpenSearch
docker-compose restart opensearch
```

**2. Ollama model not found**
```bash
# List installed models
ollama list

# Pull missing models
ollama pull nomic-embed-text:v1.5
ollama pull llama3.2
```

**3. Ingestion fails**
- Check CSV file path is absolute
- Verify CSV has required columns: `id`, `title`, `category`, `text`
- Check server logs for detailed errors

**4. Search returns no results**
- Verify documents were ingested: `curl http://localhost:9200/dev-test/_count`
- Check if index exists: `curl http://localhost:9200/_cat/indices`
- Ensure embedding dimensions match (256)

---

## 🚦 Performance Tips

1. **Batch Size**: Increase `BATCH_SIZE` for faster ingestion (if you have enough RAM)
2. **HNSW Parameters**:
   - Higher `ef_construction` = better quality, slower indexing
   - Higher `m` = better recall, more memory
3. **Chunking**: Smaller chunks = more precise, but more vectors to search
4. **Hardware**: Use GPU for Ollama models (if available)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests (if available)
pytest

# Format code
black app/
```

---

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenSearch k-NN Guide](https://opensearch.org/docs/latest/search-plugins/knn/index/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [RAG Explained](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [Vector Databases Guide](https://www.pinecone.io/learn/vector-database/)

---

## ⚠️ Production Readiness Disclaimer

**This is an educational project designed for learning and experimentation.** Before considering production deployment, you would need to address:

### Security Considerations
- 🔐 Add authentication and authorization
- 🛡️ Implement rate limiting and request validation
- 🔒 Secure API endpoints with proper CORS policies
- 🔑 Add API key management
- 🚨 Implement comprehensive error handling and logging

### Scalability Improvements
- 📈 Add horizontal scaling capabilities
- ⚡ Implement caching layers (Redis)
- 🔄 Add load balancing
- 📊 Implement monitoring and observability (Prometheus, Grafana)
- 🗄️ Add database connection pooling

### Reliability Enhancements
- 🔁 Add retry mechanisms and circuit breakers
- 📝 Implement comprehensive logging and audit trails
- 🧪 Add integration and end-to-end tests
- 🚀 Set up CI/CD pipelines
- 📦 Add proper dependency management and version pinning

### Performance Optimizations
- ⚡ Optimize embedding batch sizes
- 🎯 Fine-tune OpenSearch parameters
- 💾 Implement result caching
- 🔧 Add query optimization
- 📉 Profile and optimize bottlenecks

**Use this project to learn, experiment, and prototype—but invest in proper engineering before production deployment!**

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenSearch** team for the powerful search engine
- **Ollama** for making LLMs accessible locally
- **Nomic AI** for the excellent embedding model
- **Meta AI** for Llama models
- **FastAPI** community for the amazing framework

---

## 📞 Contact & Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/vaifai/rag-playground/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/vaifai/rag-playground/discussions)
- 📧 **Email**: vaifaipandey1996@gmail.com

---

<div align="center">

**⭐ Star this repo if you find it useful for learning RAG!**

Made with ❤️ for the community | Educational Project | Not Production-Ready

</div>

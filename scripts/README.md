# 🔧 Scripts

Utility scripts for testing and managing the RAG Playground.

## 📝 Available Scripts

### `smoke_test.py` - End-to-End Smoke Test

Performs a complete sanity check of the RAG pipeline by testing all API endpoints.

**What it does:**
1. Checks if the FastAPI server is running
2. Creates a temporary test index via `/api/index/create`
3. Ingests sample data via `/api/ingest/csv`
4. Runs multiple search queries via `/api/search/query`
5. Verifies search results and RAG-generated answers
6. Cleans up the test index

**Usage:**

```bash
# Basic usage (requires FastAPI server running on localhost:8000)
python scripts/smoke_test.py

# Custom API URL
python scripts/smoke_test.py --base-url http://localhost:8000

# Custom dataset and row count
python scripts/smoke_test.py --csv-path my_data.csv --num-rows 20

# Show help
python scripts/smoke_test.py --help
```

**Prerequisites:**
- FastAPI server must be running (`uvicorn app.__main__:app --reload`)
- OpenSearch must be running (via Docker Compose)
- Ollama must be running with required models
- Dataset CSV file must exist (default: `benchmark_dataset_2000.csv`)

**Expected Output:**

```
============================================================
  RAG Playground - Smoke Test
============================================================

  API URL: http://localhost:8000
  Test Index: smoke-test-1732345678
  Dataset: benchmark_dataset_2000.csv
  Rows to ingest: 10

▶ Checking API health
✓ API is running at http://localhost:8000

▶ Creating test index: smoke-test-1732345678
✓ Index smoke-test-1732345678 created successfully

▶ Ingesting 10 rows from benchmark_dataset_2000.csv
✓ Loaded 10 rows from CSV
▶ Uploading CSV to API...
✓ Ingested successfully: Indexed 10 chunks

▶ Running test queries

  Query 1: 'What are design patterns?' [category: programming]
✓ Found 3 results
  Top result: 'Design patterns overview' (score: 0.892)
✓ Generated answer (245 chars)
  Answer preview: Design patterns are reusable solutions to common programming problems...

[... more queries ...]

============================================================
  Test Summary
============================================================

  Documents indexed: 10
  Queries tested: 4
  Queries passed: 4
  Success rate: 100.0%

✓ All smoke tests passed! ✨
```

**Exit Codes:**
- `0`: All tests passed
- `1`: One or more tests failed or error occurred

## 🚀 Adding New Scripts

When adding new scripts to this directory:

1. Add a shebang line: `#!/usr/bin/env python3`
2. Include a docstring explaining what the script does
3. Make the script executable: `chmod +x scripts/your_script.py`
4. Update this README with usage instructions
5. Add any required dependencies to `requirements.txt`


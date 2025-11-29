#!/bin/bash
# Qdrant Quick Start Script
# Complete workflow to test Qdrant integration

set -e  # Exit on error

echo "=========================================="
echo "Qdrant Integration - Quick Start"
echo "=========================================="
echo ""

# Configuration
COLLECTION_NAME="qdrant-dev-collection"
CSV_PATH="dev_dataset_100.csv"
EMBEDDING_DIM=256
API_BASE="http://localhost:8000/api/qdrant"
QDRANT_API="http://localhost:6333"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Qdrant is running
echo -e "${YELLOW}Checking if Qdrant is running...${NC}"
if ! curl -s ${QDRANT_API}/collections > /dev/null 2>&1; then
  echo -e "${RED}✗ Qdrant is not running!${NC}"
  echo "Start Qdrant with: docker-compose up -d qdrant"
  exit 1
fi
echo -e "${GREEN}✓ Qdrant is running${NC}"
echo ""

# Step 1: Create Qdrant Collection
echo -e "${YELLOW}Step 1: Creating Qdrant collection '${COLLECTION_NAME}'...${NC}"
CREATE_RESPONSE=$(curl -s -X POST ${API_BASE}/create \
  -H "Content-Type: application/json" \
  -d "{
    \"collection_name\": \"${COLLECTION_NAME}\",
    \"embedding_dim\": ${EMBEDDING_DIM}
  }")

echo "$CREATE_RESPONSE" | jq .

if echo "$CREATE_RESPONSE" | jq -e '.ok' > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Collection created successfully${NC}"
else
  echo -e "${RED}✗ Failed to create collection${NC}"
  echo "$CREATE_RESPONSE"
  exit 1
fi

echo ""

# Step 2: Ingest Data
echo -e "${YELLOW}Step 2: Ingesting data from '${CSV_PATH}'...${NC}"
INGEST_RESPONSE=$(curl -s -X POST ${API_BASE}/ingest \
  -H "Content-Type: application/json" \
  -d "{
    \"csv_path\": \"${CSV_PATH}\",
    \"collection_name\": \"${COLLECTION_NAME}\",
    \"doc_id_col\": \"id\",
    \"title_col\": \"title\",
    \"category_col\": \"category\",
    \"text_col\": \"text\"
  }")

echo "$INGEST_RESPONSE" | jq .

if echo "$INGEST_RESPONSE" | jq -e '.ok' > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Ingestion scheduled (running in background)${NC}"
else
  echo -e "${RED}✗ Failed to start ingestion${NC}"
  echo "$INGEST_RESPONSE"
  exit 1
fi

echo ""
echo -e "${YELLOW}Waiting for ingestion to complete...${NC}"
echo "This may take a few minutes depending on dataset size."
echo "Checking every 5 seconds..."

# Wait for ingestion to complete by checking Qdrant
MAX_WAIT=300  # 5 minutes
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
  # Check point count in Qdrant
  POINT_COUNT=$(curl -s ${QDRANT_API}/collections/${COLLECTION_NAME} | jq -r '.result.points_count // 0' 2>/dev/null || echo "0")
  
  if [ "$POINT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Ingestion complete! ${POINT_COUNT} points indexed${NC}"
    break
  fi
  
  sleep 5
  ELAPSED=$((ELAPSED + 5))
  echo -n "."
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo -e "${RED}✗ Ingestion timeout. Check server logs.${NC}"
  exit 1
fi

echo ""

# Step 3: Search
echo -e "${YELLOW}Step 3: Testing search...${NC}"
QUERY="What are design patterns?"
echo "Query: ${QUERY}"
echo ""

SEARCH_RESPONSE=$(curl -s -X POST ${API_BASE}/search \
  -H "Content-Type: application/json" \
  -d "{
    \"collection_name\": \"${COLLECTION_NAME}\",
    \"query\": \"${QUERY}\",
    \"top_k\": 5
  }")

echo "$SEARCH_RESPONSE" | jq .

if echo "$SEARCH_RESPONSE" | jq -e '.answer' > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Search successful${NC}"
  echo ""
  echo "Answer:"
  echo "$SEARCH_RESPONSE" | jq -r '.answer'
  echo ""
  echo "Top contexts:"
  echo "$SEARCH_RESPONSE" | jq -r '.contexts[] | "- [\(.score)] \(.title): \(.text_snippet[:100])..."'
else
  echo -e "${RED}✗ Search failed${NC}"
  echo "$SEARCH_RESPONSE"
  exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Qdrant Integration Test Complete!"
echo "==========================================${NC}"
echo ""
echo "Summary:"
echo "- Collection: ${COLLECTION_NAME}"
echo "- Points: ${POINT_COUNT}"
echo "- Dimension: ${EMBEDDING_DIM}"
echo "- Storage: Qdrant (vectors + payloads) + MongoDB (metadata)"
echo ""
echo "Qdrant Collection Info:"
curl -s ${QDRANT_API}/collections/${COLLECTION_NAME} | jq '.result | {points_count, vectors_count, status}'
echo ""
echo "Try more searches:"
echo "  curl -X POST ${API_BASE}/search \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"collection_name\": \"${COLLECTION_NAME}\", \"query\": \"your question\", \"top_k\": 5}'"


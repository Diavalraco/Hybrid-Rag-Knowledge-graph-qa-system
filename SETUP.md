# Quick Setup Guide

## Environment Variables

Create `backend/.env` file with the following content:

```env
# LLM Configuration (OpenAI-compatible)
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000

# Embedding Configuration
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# Vector Store Configuration (FAISS)
FAISS_INDEX_PATH=./data/faiss_index
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Retrieval Configuration
TOP_K_VECTOR=5
TOP_K_KG=10
KG_MAX_DEPTH=2

# Hallucination Control
CONFIDENCE_THRESHOLD=0.6
MIN_CONTEXT_LENGTH=100

# Data Storage
DATA_DIR=./data
DOCUMENTS_DIR=./data/documents

# Debug Mode
DEBUG=false
```

## Neo4j Setup

### Option 1: Using Docker (Recommended)

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:latest
```

Access Neo4j Browser at: http://localhost:7474

### Option 2: Install Neo4j Desktop

1. Download from https://neo4j.com/download/
2. Create a new database
3. Set password to `password123` (or update `.env` file)
4. Start the database

## Starting Services

### Terminal 1 - Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000
API Docs: http://localhost:8000/docs

### Terminal 2 - Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: http://localhost:5173

## Testing the System

### 1. Check Health

```bash
curl http://localhost:8000/health
```

### 2. Ingest a Document

```bash
# Create a test document
echo "John Smith works at Tech Corp. Tech Corp is located in San Francisco. John Smith manages the Engineering team. The Engineering team develops AI products." > test_doc.txt

# Ingest via API (using base64 encoding)
BASE64_CONTENT=$(base64 -i test_doc.txt)
curl -X POST "http://localhost:8000/ingest/document" \
  -H "Content-Type: application/json" \
  -d "{
    \"file_name\": \"test_doc.txt\",
    \"file_content\": \"$BASE64_CONTENT\",
    \"file_type\": \"txt\"
  }"
```

### 3. Query the System

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Where does John Smith work?",
    "use_hybrid": true
  }'
```

Or use the frontend at http://localhost:5173 to query interactively!


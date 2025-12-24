# Hybrid RAG + Knowledge Graph Question Answering System

A production-grade Question Answering system that combines **Retrieval-Augmented Generation (RAG)** with **Knowledge Graph reasoning** using a **multi-agent architecture** to answer complex questions over documents with controlled hallucination.

## 🎯 System Overview

This system addresses the limitations of naive RAG by integrating:

1. **Multi-Agent Architecture** (Two specialized agents for retrieval and generation)
2. **Vector-based Retrieval** (Semantic similarity search using FAISS)
3. **Knowledge Graph Reasoning** (Entity-relationship traversal using Neo4j)
4. **Hallucination Control** (Confidence scoring and context validation)
5. **Hybrid Context Merging** (Intelligent combination of vector and KG results)

### 🤖 Multi-Agent System

The system uses **two specialized agents** that work together:

**Agent 1: Generation Agent**
- Classifies query type (factual/relational/reasoning)
- Generates answers from retrieved context
- Validates answer quality and computes confidence scores
- Decides on answer acceptance/rejection

**Agent 2: Retrieval Agent**
- Retrieves relevant chunks from vector store (FAISS)
- Traverses knowledge graph to find related entities/relations
- Intelligently merges context based on query type
- Adapts retrieval strategy for optimal results

This separation of concerns enables:
- Better query-aware retrieval strategies
- Specialized reasoning at each stage
- Easier maintenance and extension
- Clearer debugging and explainability

### Why Naive RAG Fails

Traditional RAG systems have several limitations:

- **Limited Context**: Vector search retrieves semantically similar chunks but may miss critical relational information
- **No Structured Reasoning**: Cannot answer questions requiring multi-hop reasoning (e.g., "Who works with the CEO of Company X?")
- **Hallucination Risk**: LLMs may generate plausible-sounding answers not grounded in retrieved context
- **No Entity Understanding**: Cannot leverage entity relationships and structured knowledge

### How Knowledge Graphs Improve Reasoning

Knowledge graphs add structured reasoning capabilities:

- **Multi-hop Reasoning**: Traverse relationships to answer complex queries (e.g., finding paths between entities)
- **Entity Resolution**: Link mentions of the same entity across documents
- **Relation Extraction**: Understand "who works with whom", "what is related to what"
- **Context Enrichment**: Augment vector search results with related entities and relations

### Hallucination Control Strategy

The system implements multiple layers of hallucination prevention:

1. **Context Grounding**: Answers generated ONLY from retrieved context
2. **Confidence Scoring**: Multi-factor confidence calculation based on:
   - Source quality (similarity scores)
   - Context length and coverage
   - Text overlap between answer and context
   - Rejection phrase detection
3. **Threshold-based Rejection**: Answers below confidence threshold are rejected with "Insufficient information" message
4. **Source Attribution**: Every answer includes source chunks and KG context for verification

## 🏗️ Architecture

### System Components

```
┌─────────────────┐
│   Frontend      │  React + Vite
│   (React)       │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend                 │
├─────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐           │
│  │  Ingest  │  │  Query   │           │
│  │   API    │  │   API    │           │
│  └────┬─────┘  └────┬─────┘           │
│       │             │                  │
│  ┌────▼─────────────▼──────┐          │
│  │    RAG Service          │          │
│  │  (Multi-Agent           │          │
│  │   Orchestration)        │          │
│  └──┬───────────────┬──────┘          │
│     │               │                  │
│  ┌──▼───────────────▼──────┐          │
│  │  🤖 AGENT 1:            │          │
│  │  Generation Agent       │          │
│  │  - Query Classification │          │
│  │  - Answer Generation    │          │
│  │  - Validation           │          │
│  └─────────────────────────┘          │
│  ┌──▼───────────────▼──────┐          │
│  │  🤖 AGENT 2:            │          │
│  │  Retrieval Agent        │          │
│  │  - Vector Retrieval     │          │
│  │  - KG Traversal         │          │
│  │  - Context Merging      │          │
│  └──┬───────────────┬──────┘          │
│     │               │                  │
│  ┌──▼──┐      ┌─────▼──────┐         │
│  │Vector│      │ Knowledge  │         │
│  │Store │      │   Graph    │         │
│  │(FAISS)│     │  Service   │         │
│  └──────┘      └─────┬──────┘         │
│                      │                 │
│  ┌───────────────────▼──────┐         │
│  │  Embedding Service       │         │
│  │  LLM Service             │         │
│  │  Hallucination Guard     │         │
│  └──────────────────────────┘         │
└────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌──────────────┐    ┌──────────────┐
│   FAISS      │    │    Neo4j     │
│  (Local)     │    │  (Docker)    │
└──────────────┘    └──────────────┘
```

### Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API endpoints
│   │   ├── ingest.py          # Document ingestion endpoint
│   │   ├── query.py           # Query processing endpoint
│   │   └── health.py          # Health check endpoint
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Settings and environment variables
│   │   └── logging.py         # Logging configuration
│   ├── services/               # Business logic services
│   │   ├── embedding_service.py    # Embedding generation
│   │   ├── llm_service.py          # LLM interactions
│   │   ├── rag_service.py          # Hybrid RAG orchestration (multi-agent)
│   │   ├── kg_service.py           # Knowledge graph operations
│   │   ├── hallucination_guard.py  # Answer validation
│   │   └── agents/                 # Multi-agent system
│   │       ├── retrieval_agent.py  # Agent 2: Retrieval specialist
│   │       └── generation_agent.py # Agent 1: Generation specialist
│   ├── db/                     # Database clients
│   │   ├── vector_store.py     # FAISS vector store wrapper
│   │   └── neo4j_client.py     # Neo4j client wrapper
│   ├── models/                 # Data models
│   │   └── schemas.py          # Pydantic schemas
│   └── utils/                  # Utility functions
│       ├── chunking.py         # Document chunking
│       └── entity_extraction.py # Entity/relation extraction
├── requirements.txt
└── README.md
```

### Frontend Structure

```
frontend/
├── src/
│   ├── App.jsx                 # Main application component
│   ├── api.js                  # API client functions
│   ├── components/
│   │   ├── QueryBox.jsx       # Query input component
│   │   ├── AnswerBox.jsx      # Answer display component
│   │   └── SourceList.jsx     # Source and KG context display
│   ├── main.jsx                # React entry point
│   └── index.css               # Global styles
├── index.html
├── package.json
└── vite.config.js
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Docker (for Neo4j, optional)
- OpenAI API key (or compatible LLM API)

### Backend Setup

1. **Create virtual environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (create `.env` file):
```bash
# LLM Configuration
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.1

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Optional: Override defaults
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_VECTOR=5
TOP_K_KG=10
CONFIDENCE_THRESHOLD=0.6
```

4. **Start Neo4j** (using Docker):
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  neo4j:latest
```

5. **Run backend server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend API docs available at: `http://localhost:8000/docs`

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Create `.env` file** (optional):
```bash
VITE_API_URL=http://localhost:8000
```

3. **Run development server**:
```bash
npm run dev
```

Frontend available at: `http://localhost:5173`

## 📖 Usage

### 1. Ingest Documents

**Using API**:
```bash
# For text files
curl -X POST "http://localhost:8000/ingest/document" \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "document.txt",
    "file_content": "Base64 encoded content or plain text",
    "file_type": "txt"
  }'
```

**Using Frontend**: Currently, document ingestion is via API. Future enhancement: file upload UI.

### 2. Query the System

**Using API**:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the relationship between X and Y?",
    "use_hybrid": true
  }'
```

**Using Frontend**: Enter your question in the textarea and click "Submit Query".

### Query Types

The system automatically classifies queries into:

- **Factual**: "What is X?", "Tell me about Y"
- **Relational**: "Who works with X?", "What is related to Y?"
- **Reasoning**: "Compare X and Y", "Why does X happen?"

Relational and reasoning queries benefit most from knowledge graph integration.

## 🔧 How It Works

### Document Ingestion Pipeline

1. **Text Extraction**: PDF or text files are parsed to extract text
2. **Chunking**: Text is split into overlapping chunks (default: 1000 chars, 200 overlap)
3. **Embedding Generation**: Each chunk is embedded using OpenAI embeddings
4. **Vector Storage**: Embeddings stored in FAISS index with metadata
5. **Entity/Relation Extraction**: Entities and relationships extracted from text
6. **KG Storage**: Entities and relations stored in Neo4j graph

### Complete Query Processing Flow (Multi-Agent Pipeline)

```
User Query
    ↓
┌───────────────────────────────────────┐
│  AGENT 1: Generation Agent            │
│  Step 1: Query Classification         │
│  - Analyzes question                  │
│  - Classifies as: factual/relational/ │
│    reasoning                          │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│  AGENT 2: Retrieval Agent             │
│  Step 2: Vector Retrieval             │
│  - Embeds query                       │
│  - Searches FAISS index               │
│  - Retrieves top-K similar chunks     │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│  AGENT 2: Retrieval Agent             │
│  Step 3: Knowledge Graph Traversal    │
│  - Extracts entities from query       │
│  - Traverses Neo4j graph              │
│  - Finds related entities/relations   │
│  (Only for relational/reasoning)      │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│  AGENT 2: Retrieval Agent             │
│  Step 4: Intelligent Context Merging  │
│  - Merges vector + KG results         │
│  - Prioritizes by query type:         │
│    * Factual → Emphasize vector       │
│    * Relational → Emphasize KG        │
│    * Reasoning → Balanced approach    │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│  AGENT 1: Generation Agent            │
│  Step 5: Answer Generation            │
│  - Uses LLM with strict mode          │
│  - Generates answer from context only │
│  - No external knowledge               │
└───────────┬───────────────────────────┘
            ↓
┌───────────────────────────────────────┐
│  AGENT 1: Generation Agent            │
│  Step 6: Validation & Scoring         │
│  - Validates answer quality           │
│  - Computes confidence score          │
│  - Checks for hallucinations          │
│  - Decides accept/reject              │
└───────────┬───────────────────────────┘
            ↓
     Final Response
     - Answer
     - Confidence score
     - Sources (chunks)
     - KG context (if any)
     - Reasoning steps (both agents)
```

**Detailed Steps:**

1. **Agent 1: Query Classification**
   - Generation Agent analyzes the question
   - Classifies into: `factual`, `relational`, or `reasoning`
   - Routes to appropriate retrieval strategy

2. **Agent 2: Vector Retrieval**
   - Retrieval Agent embeds the query using embedding service
   - Searches FAISS vector store for semantically similar chunks
   - Returns top-K results with similarity scores

3. **Agent 2: Knowledge Graph Traversal** (if hybrid mode)
   - Retrieval Agent extracts entities from query
   - Traverses Neo4j graph from those entities
   - Finds related entities and relations up to max_depth
   - Only performed for relational/reasoning queries

4. **Agent 2: Context Merging**
   - Retrieval Agent intelligently merges vector and KG results
   - **Factual queries**: Prioritize vector chunks
   - **Relational queries**: Put KG relations first, then vector
   - **Reasoning queries**: Balanced combination

5. **Agent 1: Answer Generation**
   - Generation Agent uses LLM to generate answer
   - Strict mode: only uses provided context
   - No external knowledge or assumptions

6. **Agent 1: Validation & Scoring**
   - Generation Agent validates answer through hallucination guard
   - Computes confidence from multiple factors:
     * Source quality (similarity scores)
     * Text overlap (groundedness)
     * Context length
     * Source count
     * Rejection phrase detection
   - Decides whether to accept or reject answer

7. **Response Assembly**
   - Combines answer, confidence, sources, KG context
   - Includes reasoning steps from both agents
   - Returns complete response to user

### Hybrid Retrieval Strategy (Agent 2 Decisions)

The Retrieval Agent adapts strategy based on query type:

- **Factual Queries**: 
  - Emphasize vector search (semantic similarity)
  - Minimal KG usage
  - Fast, direct retrieval

- **Relational Queries**: 
  - Emphasize KG traversal (entity relationships)
  - KG relations placed first in context
  - Vector search as supplementary

- **Reasoning Queries**: 
  - Balanced combination of both
  - Vector for context, KG for structure
  - Full hybrid approach

### Confidence Calculation

Confidence is computed from multiple factors:

- Source quality (average similarity scores): 30%
- Text overlap (answer groundedness in context): 20%
- Rejection phrase detection: 20%
- Context length and coverage: 10%
- Source count: 10%
- Answer length: 10%

Answers below threshold (default 0.6) are rejected.

## 📈 Scaling to Millions of Documents

### Current Architecture Limitations

- **FAISS IndexFlatL2**: O(n) search complexity, suitable for < 1M vectors
- **Synchronous Processing**: Single-threaded ingestion and querying
- **In-memory Metadata**: Metadata loaded into memory

### Production Scaling Strategies

1. **Vector Database Upgrade**:
   - **FAISS IndexIVF**: Approximate nearest neighbor (ANN) with indexing for faster search
   - **Pinecone/Weaviate/Qdrant**: Managed vector databases with horizontal scaling
   - **Sharding**: Partition indices by document type/category

2. **Knowledge Graph Optimization**:
   - **Indexing**: Create indexes on entity names and relation types
   - **Caching**: Cache frequent traversal paths
   - **Graph Partitioning**: Shard graph by entity type or geography
   - **Neo4j Enterprise**: Use clustering for distributed graph

3. **Async Processing**:
   - **Background Workers**: Use Celery/RQ for document ingestion
   - **Message Queues**: RabbitMQ/Kafka for job processing
   - **Async API**: FastAPI with async/await for concurrent requests

4. **Caching Layer**:
   - **Redis**: Cache frequent queries and embeddings
   - **Query Result Caching**: Cache answers for identical queries
   - **Embedding Cache**: Cache computed embeddings

5. **Load Balancing**:
   - **API Servers**: Multiple FastAPI instances behind load balancer
   - **Database Replication**: Read replicas for Neo4j and vector store

6. **Batch Processing**:
   - **Bulk Ingestion**: Process documents in batches
   - **Batch Embedding**: Generate embeddings in batches
   - **Batch KG Updates**: Batch insert entities/relations

### Production Architecture (Scaled)

```
┌─────────────┐
│ Load Balancer│
└──────┬──────┘
       │
   ┌───┴────┬──────────┬──────────┐
   │        │          │          │
┌──▼──┐ ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
│API 1│ │API 2│...│API N│   │Worker│
└──┬──┘ └──┬──┘   └──┬──┘   │Queue │
   │       │          │      └──┬───┘
   └───┬───┴──────────┘         │
       │                        │
   ┌───▼──────────────┐    ┌───▼──────────┐
   │   Redis Cache    │    │   Celery     │
   └──────────────────┘    │   Workers    │
                           └──────┬───────┘
                                  │
       ┌──────────────────────────┼──────────────┐
       │                          │              │
   ┌───▼──────┐          ┌────────▼──┐   ┌──────▼──────┐
   │ Pinecone │          │  Neo4j    │   │   PostgreSQL│
   │ /Qdrant  │          │  Cluster  │   │  (Metadata) │
   └──────────┘          └───────────┘   └─────────────┘
```

## 🛠️ Productionization Checklist

### Infrastructure

- [ ] **Containerization**: Dockerize backend and frontend
- [ ] **Orchestration**: Kubernetes or Docker Compose for local dev
- [ ] **Monitoring**: Prometheus + Grafana for metrics
- [ ] **Logging**: Centralized logging (ELK stack or cloud logging)
- [ ] **Error Tracking**: Sentry or similar for error monitoring

### Security

- [ ] **API Authentication**: JWT tokens or API keys
- [ ] **Rate Limiting**: Prevent abuse
- [ ] **Input Validation**: Sanitize user inputs
- [ ] **Secrets Management**: Use environment variables or secret managers
- [ ] **CORS Configuration**: Restrict allowed origins

### Performance

- [ ] **Database Connection Pooling**: Efficient connection management
- [ ] **Query Optimization**: Index optimization for Neo4j
- [ ] **Embedding Caching**: Cache frequently used embeddings
- [ ] **CDN**: Serve static frontend assets via CDN
- [ ] **Compression**: Enable gzip/brotli compression

### Reliability

- [ ] **Health Checks**: Comprehensive health endpoints
- [ ] **Graceful Shutdown**: Proper cleanup on shutdown
- [ ] **Retry Logic**: Retry failed API calls (LLM, embeddings)
- [ ] **Circuit Breakers**: Prevent cascading failures
- [ ] **Backup Strategy**: Regular backups of Neo4j and vector indices

### Testing

- [ ] **Unit Tests**: Test individual components
- [ ] **Integration Tests**: Test API endpoints
- [ ] **E2E Tests**: Test full query pipeline
- [ ] **Load Testing**: Test system under load

## 🤖 Multi-Agent Architecture Details

### Agent Responsibilities

**Agent 1: Generation Agent** (`agents/generation_agent.py`)
- **Query Classification**: Uses LLM to classify query type
- **Answer Generation**: Creates answers from retrieved context
- **Validation**: Multi-factor confidence scoring
- **Decision Making**: Accepts/rejects answers based on quality

**Agent 2: Retrieval Agent** (`agents/retrieval_agent.py`)
- **Vector Search**: FAISS similarity search
- **KG Traversal**: Neo4j graph traversal with configurable depth
- **Strategy Selection**: Chooses retrieval approach by query type
- **Context Merging**: Intelligently combines vector and KG results

### Agent Communication Flow

```
RAG Service (Orchestrator)
    │
    ├─→ Generation Agent.classify_query()
    │       └─→ Returns: query_type
    │
    ├─→ Retrieval Agent.retrieve_context(query_type)
    │       ├─→ Vector retrieval
    │       ├─→ KG traversal (if relational/reasoning)
    │       └─→ Returns: {vector_results, kg_entities, kg_relations}
    │
    ├─→ Retrieval Agent.merge_context(query_type)
    │       └─→ Returns: {merged_context, sources}
    │
    └─→ Generation Agent.generate_answer()
            ├─→ Answer generation
            ├─→ Validation
            └─→ Returns: {answer, confidence, validation}
```

### Benefits of Multi-Agent Architecture

1. **Separation of Concerns**: Each agent has clear, focused responsibilities
2. **Query-Aware Processing**: Retrieval strategy adapts to query type
3. **Better Explainability**: Each agent reports its reasoning steps
4. **Easier Maintenance**: Can modify/improve agents independently
5. **Scalability**: Can parallelize agent operations
6. **Specialization**: Agents can be optimized for their specific tasks

## 🔍 Advanced Features (Future Enhancements)

1. **Additional Agents**: 
   - Planning Agent (query decomposition)
   - Re-ranking Agent (result optimization)
   - Validation Agent (separate validation logic)

2. **Better Entity Extraction**: Use spaCy/transformers NER models
3. **LLM-based Extraction**: Use LLM to extract entities/relations
4. **Multi-modal Support**: Image and table extraction
5. **Query Rewriting**: Improve queries before retrieval
6. **Re-ranking**: Re-rank retrieved chunks using cross-encoders
7. **Feedback Loop**: Learn from user feedback to improve retrieval
8. **Conversational Context**: Support follow-up questions
9. **Document Versioning**: Track document updates
10. **Agent Communication**: Direct agent-to-agent messaging

## 📝 Configuration Reference

See `backend/app/core/config.py` for all configuration options.

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_BASE` | `https://api.openai.com/v1` | LLM API base URL |
| `LLM_API_KEY` | (required) | API key for LLM |
| `LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `CHUNK_SIZE` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_VECTOR` | `5` | Number of vector results |
| `TOP_K_KG` | `10` | Number of KG results |
| `CONFIDENCE_THRESHOLD` | `0.6` | Minimum confidence to return answer |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |

## 🤝 Contributing

This is a production-grade system designed for clarity and maintainability. Contributions should:

- Follow the existing architecture patterns
- Include inline comments explaining WHY (not just WHAT)
- Maintain single responsibility principle
- Add appropriate error handling and logging
- Update documentation

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- FAISS for efficient vector search
- Neo4j for graph database
- FastAPI for modern Python API framework
- React + Vite for modern frontend development

---

**Built for production-grade question answering with controlled hallucination and scalable architecture.**


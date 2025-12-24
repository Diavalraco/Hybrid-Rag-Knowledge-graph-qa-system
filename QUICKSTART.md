# Quick Start Guide

## ✅ Status

- ✅ Backend dependencies installed
- ✅ Frontend dependencies installed  
- ✅ Environment variables configured (.env file created)
- ✅ Backend server running on http://localhost:8000
- ✅ Frontend server starting on http://localhost:5173
- ✅ Neo4j connection: ACTIVE

## 🚀 Services Running

### Backend API
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Frontend UI
- **URL**: http://localhost:5173
- Open in your browser to start querying!

## 📝 Quick Test

### 1. Test the Health Endpoint

```bash
curl http://localhost:8000/health
```

### 2. Ingest a Test Document

Use the provided test script:

```bash
./test_ingest.sh
```

Or manually:

```bash
# Create test document
echo "John Smith works at Tech Corp. Tech Corp is located in San Francisco." > test.txt

# Ingest (macOS)
BASE64=$(base64 -i test.txt)
curl -X POST "http://localhost:8000/ingest/document" \
  -H "Content-Type: application/json" \
  -d "{\"file_name\":\"test.txt\",\"file_content\":\"$BASE64\",\"file_type\":\"txt\"}"
```

### 3. Query the System

Via API:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "Where does John Smith work?", "use_hybrid": true}'
```

Via Frontend:
1. Open http://localhost:5173 in your browser
2. Enter your question in the textarea
3. Click "Submit Query"
4. View the answer with confidence score and sources!

## 🔧 Stopping Services

To stop the background processes:

```bash
# Find and kill backend
pkill -f "uvicorn app.main:app"

# Find and kill frontend
pkill -f "vite"
```

Or use:
- `Ctrl+C` in the terminal where services are running

## 🔄 Restarting Services

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run dev
```

Or use the provided scripts:
```bash
./start_backend.sh  # In a terminal
./start_frontend.sh # In another terminal
```

## 📚 Next Steps

1. **Ingest your documents**: Use the `/ingest/document` endpoint with your PDF or text files
2. **Explore the API**: Visit http://localhost:8000/docs for interactive API documentation
3. **Try different queries**: 
   - Factual: "What is X?"
   - Relational: "Who works with X?"
   - Reasoning: "Compare X and Y"

## 🐛 Troubleshooting

### Backend won't start
- Check that virtual environment is activated
- Verify `.env` file exists in `backend/` directory
- Check logs for error messages

### Neo4j connection fails
- The system will run in vector-only mode if Neo4j is unavailable
- To enable KG features, ensure Neo4j is running:
  - Docker: `docker start neo4j`
  - Or install Neo4j Desktop

### Frontend won't connect
- Verify backend is running on port 8000
- Check browser console for errors
- Verify CORS settings in backend

## 📖 Documentation

See `README.md` for full system documentation including:
- Architecture overview
- Scaling strategies
- Production deployment checklist


# Deployment Guide

## 🚀 Backend Deployment on Render

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**: `Diavalraco/Hybrid-Rag-Knowledge-graph-qa-system`
4. **Configure settings**:
   - **Name**: `hybrid-rag-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Add Environment Variables**:
   ```
   LLM_API_BASE=https://api.openai.com/v1
   LLM_API_KEY=your-openai-api-key-here
   LLM_MODEL=gpt-4o-mini
   LLM_TEMPERATURE=0.1
   EMBEDDING_MODEL=text-embedding-3-small
   NEO4J_URI=bolt://your-neo4j-host:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your-password
   CONFIDENCE_THRESHOLD=0.4
   ```

6. **Deploy** - Render will build and deploy automatically
7. **Copy your backend URL** (e.g., `https://hybrid-rag-backend.onrender.com`)

## 🌐 Frontend Deployment on Vercel

1. **Go to Vercel Dashboard**: https://vercel.com
2. **Click "Add New..." → "Project"**
3. **Import your GitHub repository**: `Diavalraco/Hybrid-Rag-Knowledge-graph-qa-system`
4. **Configure settings**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

5. **Add Environment Variable**:
   ```
   VITE_API_URL=https://your-backend-url.onrender.com
   ```
   (Replace with your actual Render backend URL)

6. **Deploy** - Vercel will build and deploy automatically
7. **Your frontend will be live!** (e.g., `https://your-project.vercel.app`)

## 📝 Important Notes

- **Neo4j**: For production, use Neo4j Aura (cloud) or set up Neo4j on a separate server
- **FAISS Index**: Will be created automatically on first document ingestion
- **CORS**: Backend CORS is configured for Vercel domains
- **Environment Variables**: Never commit API keys to git (use Render/Vercel env vars)

## 🔧 Post-Deployment

1. Test backend: `https://your-backend.onrender.com/health`
2. Test frontend: Visit your Vercel URL
3. Update frontend `VITE_API_URL` if backend URL changes


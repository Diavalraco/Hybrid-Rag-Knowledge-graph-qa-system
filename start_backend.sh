#!/bin/bash
# Start Backend Server

cd "$(dirname "$0")/backend"
source venv/bin/activate
echo "Starting backend server on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


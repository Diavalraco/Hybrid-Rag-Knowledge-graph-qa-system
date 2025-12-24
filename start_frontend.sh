#!/bin/bash
# Start Frontend Server

cd "$(dirname "$0")/frontend"
echo "Starting frontend server on http://localhost:5173"
npm run dev


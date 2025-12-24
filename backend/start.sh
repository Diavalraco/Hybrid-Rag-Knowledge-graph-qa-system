#!/bin/bash
# Production startup script for Render
uvicorn app.main:app --host 0.0.0.0 --port $PORT


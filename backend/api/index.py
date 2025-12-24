"""
Vercel serverless entry point for FastAPI.
This file is used by Vercel to run the FastAPI app as serverless functions.
"""
from app.main import app

# Vercel expects a handler function
handler = app


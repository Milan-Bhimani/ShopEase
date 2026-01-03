"""
Vercel Serverless Function Entry Point for FastAPI
"""
import sys
import os

# Get the absolute path to the backend directory
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', 'backend')
sys.path.insert(0, backend_dir)

# Set environment to indicate we're in Vercel
os.environ['VERCEL'] = '1'

try:
    from app.main import app
except Exception as e:
    # Create a simple error app if import fails
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/api/{path:path}")
    async def error_handler(path: str):
        return {"error": f"Failed to load main app: {str(e)}", "path": backend_dir}

# Vercel expects 'app' to be the ASGI application

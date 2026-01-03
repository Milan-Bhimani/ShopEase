"""
Vercel Serverless Function Entry Point for FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import traceback

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug endpoint
@app.get("/api/debug")
async def debug():
    return {
        "status": "ok",
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "path": sys.path[:5],
        "env_keys": list(os.environ.keys())[:10]
    }

# Try to import the main app
try:
    # Add backend to path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.abspath(os.path.join(current_dir, '..', 'backend'))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from app.main import app as main_app

    # Mount the main app routes
    app.mount("/api", main_app)

except Exception as e:
    error_msg = traceback.format_exc()

    @app.get("/api/{path:path}")
    async def error_handler(path: str):
        return {
            "error": str(e),
            "traceback": error_msg,
            "backend_dir": backend_dir,
            "sys_path": sys.path[:5]
        }

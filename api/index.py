"""
==============================================================================
Vercel Serverless Function Entry Point (api/index.py)
==============================================================================

PURPOSE:
--------
This file is the entry point for Vercel serverless deployment.
It exposes the FastAPI app to Vercel's serverless function runtime.

HOW VERCEL SERVERLESS WORKS:
----------------------------
Vercel looks for Python files in the /api directory.
Each .py file becomes a serverless function endpoint.
The filename determines the route:
    api/index.py -> /api
    api/users.py -> /api/users (if you had one)

This single index.py handles ALL routes via FastAPI's routing.

PATH CONFIGURATION:
-------------------
The backend code is in /backend, but Vercel runs from /api.
We add the backend directory to Python's path so imports work:
    sys.path.insert(0, '../backend')

This allows:
    from app.main import app  # Works because 'backend' is in path

THE 'app' VARIABLE:
-------------------
Vercel looks for an 'app' variable that is a WSGI/ASGI application.
FastAPI is an ASGI app, and Vercel supports it natively.
The app object handles all HTTP requests.

VERCEL CONFIGURATION:
---------------------
vercel.json routes all /api/* requests to this function:
    {
        "rewrites": [
            {"source": "/api/(.*)", "destination": "/api"}
        ]
    }

This means:
    /api/products -> handled by FastAPI router
    /api/auth/login -> handled by FastAPI router
    /api/orders -> handled by FastAPI router

LOCAL DEVELOPMENT:
------------------
For local development, use uvicorn directly:
    cd backend
    uvicorn app.main:app --reload

Or with Docker:
    docker-compose up

This file is ONLY used for Vercel deployment.

COLD STARTS:
------------
Serverless functions have "cold starts" (first request is slower).
Vercel keeps functions warm for a while after requests.
The FastAPI app and Firebase connection are initialized on first request.
"""

import sys
import os

# Add backend directory to Python path
# This is needed because Vercel runs from /api but our code is in /backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the FastAPI app
# Vercel will use this 'app' object to handle all HTTP requests
from app.main import app

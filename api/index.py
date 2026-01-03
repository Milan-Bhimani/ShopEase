"""
Vercel Serverless Function Entry Point
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app

# Export for Vercel
handler = app

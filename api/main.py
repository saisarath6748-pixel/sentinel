"""
FastAPI app entrypoint.

Usage:
    uvicorn api.main:app --reload --port 8000
"""

from api.routes import app  # noqa: F401 — re-export for uvicorn

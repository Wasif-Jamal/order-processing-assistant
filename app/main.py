"""FastAPI ASGI entry point for the backend.

Exposes the application built by the bootstrap factory
(:func:`app.starter.create_app`) as ``app`` for Uvicorn
(``uv run uvicorn app.main:app``).
"""

from app.starter import create_app

app = create_app()

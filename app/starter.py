"""Application bootstrap / app factory.

Builds the FastAPI application
``app/main.py`` exposes the result as the ASGI entry point for Uvicorn.
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """
    Returns:
        The fully configured ``FastAPI`` ASGI application.
    """

    app = FastAPI(title="Order Processing Assistant API")

    return app

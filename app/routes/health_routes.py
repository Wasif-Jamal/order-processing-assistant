"""FastAPI health router.

Exposes the ``GET /api/health`` endpoint used for application liveness checks.
The endpoint has no external dependencies and simply confirms that the API is
running.
"""

from fastapi import APIRouter

from app.schemas.responses_schema import HealthResponse


class HealthRouter:
    """Class-based router exposing the health endpoint.

    Attributes:
        router: FastAPI router containing the health endpoint.
    """

    def __init__(self) -> None:
        """Initialize the health router."""
        self.router = APIRouter(
            prefix="/api",
            tags=["health"],
        )

        self.router.add_api_route(
            "/health",
            self.health,
            methods=["GET"],
            response_model=HealthResponse,
        )

    def health(self) -> HealthResponse:
        """Return the application health status.

        Returns:
            A successful health response.
        """
        return HealthResponse(status="ok")
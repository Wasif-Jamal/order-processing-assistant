"""Qdrant vector database configuration."""

from qdrant_client import QdrantClient

from app.config.env_config import settings
from app.config.log_config import config

logger = config.get_logger(__name__)


class QdrantConfig:
    """Manage Qdrant client initialization and configuration.

    Provides a singleton pattern to access the Qdrant vector database client.
    Supports environment configuration for host, port, API key, and URL.
    """

    def __init__(self) -> None:
        """Initialize the Qdrant configuration manager."""
        self._client: QdrantClient | None = None

    def get_client(self) -> QdrantClient:
        """Return a configured QdrantClient instance.

        If a Qdrant connection is already established, the cached instance is
        returned. Falls back gracefully to in-memory mode if the remote Qdrant
        server is unreachable.

        Returns:
            An active QdrantClient instance.
        """
        if self._client is not None:
            return self._client

        if settings.qdrant_location:
            logger.info(
                "Initializing Qdrant client with location '%s'.",
                settings.qdrant_location,
            )
            self._client = QdrantClient(
                location=settings.qdrant_location,
                api_key=settings.qdrant_api_key,
            )
            return self._client

        if settings.qdrant_url:
            logger.info(
                "Initializing Qdrant client with URL '%s'.",
                settings.qdrant_url,
            )
            self._client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
            )
            return self._client

        logger.info(
            "Connecting to Qdrant at %s:%d.",
            settings.qdrant_host,
            settings.qdrant_port,
        )

        try:
            client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key,
                timeout=5.0,
            )
            client.get_collections()
            self._client = client
            logger.info("Successfully connected to Qdrant server.")
        except Exception as exc:
            logger.warning(
                "Could not connect to Qdrant at %s:%d (%s). Falling back to in-memory Qdrant client.",
                settings.qdrant_host,
                settings.qdrant_port,
                exc,
            )
            self._client = QdrantClient(location=":memory:")

        return self._client


qdrant_config = QdrantConfig()

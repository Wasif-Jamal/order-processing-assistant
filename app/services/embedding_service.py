"""Embedding service using SentenceTransformers.

Generates dense vector representations for texts to support vector similarity search
in Qdrant. Uses the configured sentence-transformers model.
"""

from sentence_transformers import SentenceTransformer

from app.config.env_config import settings
from app.config.log_config import config

logger = config.get_logger(__name__)


class EmbeddingService:
    """Service responsible for generating text vector embeddings."""

    def __init__(self, model_name: str | None = None) -> None:
        """Initialize the embedding service.

        Args:
            model_name: Optional name of the SentenceTransformer model.
                Defaults to settings.embedding_model_name.
        """
        self._model_name = model_name or settings.embedding_model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        """Lazy-load and return the SentenceTransformer model instance.

        Returns:
            Loaded SentenceTransformer instance.
        """
        if self._model is None:
            logger.info("Loading embedding model '%s'...", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("Embedding model '%s' loaded.", self._model_name)
        return self._model

    def embed_text(self, text: str) -> list[float]:
        """Generate a vector embedding for a single text.

        Args:
            text: Input text string.

        Returns:
            List of floats representing the vector embedding.
        """
        model = self._get_model()
        vector = model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for multiple texts.

        Args:
            texts: List of text strings.

        Returns:
            List of vector embeddings.
        """
        if not texts:
            return []
        model = self._get_model()
        vectors = model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]

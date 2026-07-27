"""High-level Knowledge Base service.

Provides operations to query and retrieve database table metadata from Qdrant,
abstracting vector generation and raw Qdrant point representations.
"""

import uuid
from typing import Any

from app.config.log_config import config
from app.schemas.knowledge_base_schema import KnowledgeBaseSchema
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

logger = config.get_logger(__name__)


class KnowledgeBaseService:
    """High-level service managing Knowledge Base schema retrieval."""

    def __init__(
        self,
        qdrant_service: QdrantService | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        """Initialize the Knowledge Base service.

        Args:
            qdrant_service: Service managing Qdrant vector database interactions.
            embedding_service: Service generating text vector embeddings.
        """
        self._qdrant_service = qdrant_service or QdrantService()
        self._embedding_service = embedding_service or EmbeddingService()

    def search_schema(
        self,
        question: str,
        limit: int = 5,
    ) -> str:
        """Search for schema metadata relevant to a natural language question.

        Args:
            question: Natural language user query or question.
            limit: Maximum number of schema records to return.

        Returns:
            List of matching KnowledgeBaseSchema instances sorted by relevance.
        """
        logger.info(
            "Searching schema metadata for question: '%s' (limit=%d).",
            question,
            limit,
        )

        query_vector = self._embedding_service.embed_text(question)

        search_results = self._qdrant_service.search_vectors(
            collection_name=QdrantService.SCHEMA_METADATA_COLLECTION,
            query_vector=query_vector,
            limit=limit,
        )

        schemas: list[KnowledgeBaseSchema] = []
        for result in search_results:
            payload = result.get("payload", {})
            try:
                schema = KnowledgeBaseSchema.model_validate(payload)
                schemas.append(schema)
            except Exception as exc:
                logger.warning(
                    "Failed to parse KnowledgeBaseSchema payload for point %s: %s",
                    result.get("id"),
                    exc,
                )

        return "\n\n".join(
            schema.to_embedding_text()
            for schema in schemas
        )

    def retrieve_relevant_tables(
        self,
        question: str,
        limit: int = 5,
    ) -> list[str]:
        """Retrieve names of tables relevant to a natural language question.

        Args:
            question: Natural language user query or question.
            limit: Maximum number of table names to return.

        Returns:
            List of unique table names.
        """
        schemas = self.search_schema(question=question, limit=limit)
        table_names = [schema.table_name for schema in schemas]
        return table_names

    def index_table_schemas(
        self,
        schemas: list[KnowledgeBaseSchema],
    ) -> None:
        """Index a list of KnowledgeBaseSchema metadata objects into Qdrant.

        Args:
            schemas: List of KnowledgeBaseSchema objects to index.
        """
        if not schemas:
            return

        logger.info("Indexing %d schema metadata records.", len(schemas))

        points: list[dict[str, Any]] = []

        for schema in schemas:
            text = schema.to_embedding_text()
            vector = self._embedding_service.embed_text(text)

            point_id = str(
                uuid.uuid5(
                    uuid.NAMESPACE_DNS,
                    f"schema_metadata.{schema.table_name}",
                )
            )

            points.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": schema.model_dump(),
                }
            )

        self._qdrant_service.insert_vectors(
            collection_name=QdrantService.SCHEMA_METADATA_COLLECTION,
            points=points,
        )

        logger.info("Successfully indexed %d schema records.", len(schemas))

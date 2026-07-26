"""SQL Cache service.

Implements the two-layer caching strategy:
- Layer 1 (Qdrant): Stores question vector embeddings and cache_id.
- Layer 2 (SQL Server): Stores SQL text, user question, explanation, creation/usage timestamps, and hit count.
"""

import uuid
from typing import Any

from app.config.db_config import DatabaseConfig
from app.config.db_config import database
from app.config.env_config import settings
from app.config.log_config import config
from app.models.sql_cache_model import SQLCache
from app.repository.sql_cache_repository import SQLCacheRepository
from app.schemas.sql_cache_schema import CachedSQLResult
from app.schemas.sql_cache_schema import SQLCacheSchema
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

logger = config.get_logger(__name__)


class SQLCacheService:
    """Service managing two-layer SQL caching (Qdrant vector store + SQL Server)."""

    def __init__(
        self,
        qdrant_service: QdrantService | None = None,
        embedding_service: EmbeddingService | None = None,
        sql_cache_repository: SQLCacheRepository | None = None,
        db_config: DatabaseConfig = database,
        similarity_threshold: float | None = None,
    ) -> None:
        """Initialize the SQL cache service.

        Args:
            qdrant_service: Generic vector store service for Qdrant.
            embedding_service: Embedding generation service.
            sql_cache_repository: Data-access repository for SQL Server.
            db_config: Database configuration singleton.
            similarity_threshold: Minimum vector similarity threshold for cache hits.
                Defaults to settings.sql_cache_similarity_threshold.
        """
        self._qdrant_service = qdrant_service or QdrantService()
        self._embedding_service = embedding_service or EmbeddingService()
        self._repository = sql_cache_repository or SQLCacheRepository()
        self._db_config = db_config
        self._similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.sql_cache_similarity_threshold
        )

    def search(
        self,
        question: str,
        similarity_threshold: float | None = None,
    ) -> CachedSQLResult | None:
        """Search for a cached SQL query matching the natural language question.

        Args:
            question: Natural language user question.
            similarity_threshold: Optional threshold overriding default setting.

        Returns:
            CachedSQLResult if vector match score >= threshold and found in SQL Server;
            otherwise None (cache miss).
        """
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self._similarity_threshold
        )

        logger.info(
            "Searching SQL cache for question: '%s' (threshold=%.2f).",
            question,
            threshold,
        )

        query_vector = self._embedding_service.embed_text(question)

        search_results = self._qdrant_service.search_vectors(
            collection_name=QdrantService.SQL_CACHE_COLLECTION,
            query_vector=query_vector,
            limit=1,
            score_threshold=threshold,
        )

        if not search_results:
            logger.info("SQL cache miss for question: '%s'.", question)
            return None

        top_hit = search_results[0]
        score = top_hit.get("score", 0.0)
        payload = top_hit.get("payload", {})
        cache_id = payload.get("cache_id") or top_hit.get("id")

        if not cache_id:
            logger.warning("Qdrant cache search result missing cache_id in payload.")
            return None

        logger.info(
            "SQL cache hit in Qdrant (cache_id='%s', score=%.4f). Retrieving from SQL Server.",
            cache_id,
            score,
        )

        with self._db_config.get_session() as session:
            updated_record = self._repository.update_usage(session, cache_id)

            if updated_record is None:
                logger.warning(
                    "Cache record '%s' exists in Qdrant but is missing from SQL Server.",
                    cache_id,
                )
                return None

            result = CachedSQLResult(
                cache_id=updated_record.cache_id,
                user_question=updated_record.user_question,
                generated_sql=updated_record.generated_sql,
                sql_explanation=updated_record.sql_explanation,
                similarity_score=score,
                hit_count=updated_record.hit_count,
                last_used_at=updated_record.last_used_at,
            )

            logger.info(
                "Successfully returned cached SQL query (hit count: %d).",
                result.hit_count,
            )
            return result

    def save_cache(
        self,
        user_question: str,
        generated_sql: str,
        sql_explanation: str | None = None,
    ) -> SQLCacheSchema:
        """Save a successful SQL query execution to Qdrant and SQL Server.

        Args:
            user_question: Original user question.
            generated_sql: Validated successful SQL query.
            sql_explanation: Optional explanation of the query logic.

        Returns:
            SQLCacheSchema representing the saved cache record.
        """
        cache_id = str(uuid.uuid4())

        logger.info(
            "Saving new execution to SQL Cache (cache_id='%s').",
            cache_id,
        )

        query_vector = self._embedding_service.embed_text(user_question)

        point = {
            "id": cache_id,
            "vector": query_vector,
            "payload": {
                "cache_id": cache_id,
                "user_question": user_question,
            },
        }
        self._qdrant_service.insert_vectors(
            collection_name=QdrantService.SQL_CACHE_COLLECTION,
            points=[point],
        )

        cache_record = SQLCache(
            cache_id=cache_id,
            user_question=user_question,
            generated_sql=generated_sql,
            sql_explanation=sql_explanation,
        )

        with self._db_config.get_session() as session:
            saved_record = self._repository.create(session, cache_record)
            schema = SQLCacheSchema.model_validate(saved_record)

        logger.info("Successfully cached query for question: '%s'.", user_question)
        return schema

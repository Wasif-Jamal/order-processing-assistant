"""SQL template search service.

Provides semantic vector similarity search across pre-defined SQL templates using Qdrant (Layer 1)
and retrieves matching template details from SQL Server (Layer 2).
"""

from app.config.db_config import DatabaseConfig
from app.config.db_config import database
from app.config.env_config import settings
from app.config.log_config import config
from app.repository.sql_template_repository import SQLTemplateRepository
from app.schemas.sql_template_schema import SQLTemplateSchema
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService

logger = config.get_logger(__name__)


class SQLTemplateService:
    """Service managing search and indexing of curated SELECT SQL templates."""

    def __init__(
        self,
        qdrant_service: QdrantService | None = None,
        embedding_service: EmbeddingService | None = None,
        sql_template_repository: SQLTemplateRepository | None = None,
        db_config: DatabaseConfig = database,
        similarity_threshold: float | None = None,
    ) -> None:
        """Initialize the SQL template service.

        Args:
            qdrant_service: Generic vector store service for Qdrant.
            embedding_service: Embedding generation service.
            sql_template_repository: Data-access repository for SQL Server.
            db_config: Database configuration singleton.
            similarity_threshold: Minimum vector similarity threshold for template hits.
                Defaults to settings.sql_template_similarity_threshold.
        """
        self._qdrant_service = qdrant_service or QdrantService()
        self._embedding_service = embedding_service or EmbeddingService()
        self._repository = sql_template_repository or SQLTemplateRepository()
        self._db_config = db_config
        self._similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.sql_template_similarity_threshold
        )

    def search_template(
        self,
        question: str,
        similarity_threshold: float | None = None,
    ) -> SQLTemplateSchema | None:
        """Search for a pre-defined SQL template matching the natural language question.

        Args:
            question: Natural language user question.
            similarity_threshold: Optional threshold overriding default setting.

        Returns:
            SQLTemplateSchema if similarity >= threshold and template is found in SQL Server;
            otherwise None.
        """
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self._similarity_threshold
        )

        logger.info(
            "Searching SQL templates for question: '%s' (threshold=%.2f).",
            question,
            threshold,
        )

        query_vector = self._embedding_service.embed_text(question)

        search_results = self._qdrant_service.search_vectors(
            collection_name=QdrantService.SQL_TEMPLATES_COLLECTION,
            query_vector=query_vector,
            limit=1,
            score_threshold=threshold,
        )

        if not search_results:
            logger.info("No SQL template match found for question: '%s'.", question)
            return None

        top_hit = search_results[0]
        score = top_hit.get("score", 0.0)
        payload = top_hit.get("payload", {})
        template_id = payload.get("template_id") or top_hit.get("id")

        if template_id is None:
            logger.warning("Qdrant template search result missing template_id.")
            return None

        logger.info(
            "SQL template match found in Qdrant (template_id=%s, score=%.4f). Retrieving from SQL Server.",
            template_id,
            score,
        )

        with self._db_config.get_session() as session:
            try:
                t_id = int(template_id)
            except (ValueError, TypeError):
                t_id = template_id

            template_record = self._repository.get_by_id(session, t_id)

            if template_record is None or not template_record.is_active:
                logger.warning(
                    "Template ID '%s' found in Qdrant but is missing or inactive in SQL Server.",
                    template_id,
                )
                return None

            schema = SQLTemplateSchema.model_validate(template_record)
            logger.info("Successfully retrieved SQL template '%s'.", schema.name)
            return schema

    def index_template_vector(
        self,
        template_id: int,
        search_text: str,
        template_name: str,
    ) -> None:
        """Generate vector embedding and index a template into Qdrant.

        Args:
            template_id: Primary key ID of the template.
            search_text: Text representation (natural language examples / intent).
            template_name: Unique template name.
        """
        vector = self._embedding_service.embed_text(search_text)
        point = {
            "id": template_id,
            "vector": vector,
            "payload": {
                "template_id": template_id,
                "name": template_name,
                "examples": search_text,
            },
        }
        self._qdrant_service.insert_vectors(
            collection_name=QdrantService.SQL_TEMPLATES_COLLECTION,
            points=[point],
        )

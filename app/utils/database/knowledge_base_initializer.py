"""Knowledge Base startup initializer.

Generates database schema metadata from SQLAlchemy models, generates vector embeddings,
and indexes the schemas into Qdrant vector database on application startup.
Idempotent: skips indexing if the schema collection is already populated.
"""

from app.config.log_config import config
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.qdrant_service import QdrantService
from app.utils.database.metadata_generator import MetadataGenerator

logger = config.get_logger(__name__)


class KnowledgeBaseInitializer:
    """Initializes and seeds the Knowledge Base schema vector index in Qdrant."""

    def __init__(
        self,
        qdrant_service: QdrantService | None = None,
        knowledge_base_service: KnowledgeBaseService | None = None,
        metadata_generator: MetadataGenerator | None = None,
    ) -> None:
        """Initialize the Knowledge Base initializer.

        Args:
            qdrant_service: Service managing Qdrant vector database.
            knowledge_base_service: Service managing high-level KB search and indexing.
            metadata_generator: Generator extracting metadata from SQLAlchemy models.
        """
        self._qdrant_service = qdrant_service or QdrantService()
        self._knowledge_base_service = knowledge_base_service or KnowledgeBaseService(
            qdrant_service=self._qdrant_service
        )
        self._metadata_generator = metadata_generator or MetadataGenerator()

    def initialize(self) -> None:
        """Initialize Qdrant collections and populate schema metadata.

        Safe to call multiple times. Skips schema indexing if schema metadata
        has already been indexed into Qdrant.
        """
        logger.info("Starting Knowledge Base initialization.")

        self._qdrant_service.init_default_collections()

        count = self._qdrant_service.get_collection_count(
            QdrantService.SCHEMA_METADATA_COLLECTION,
        )

        if count > 0:
            logger.info(
                "Knowledge Base schema_metadata collection already contains %d records. Skipping indexing.",
                count,
            )
            return

        logger.info("Indexing database schema metadata into Qdrant.")
        schemas = self._metadata_generator.generate_all_metadata()
        self._knowledge_base_service.index_table_schemas(schemas)
        logger.info("Knowledge Base initialization completed successfully.")

"""Generic vector store service for Qdrant.

Provides abstract operations for managing vector collections, inserting vectors with payloads,
performing similarity searches, and deleting vector points. Completely generic and decoupled
from specific domain logic.
"""

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance
from qdrant_client.http.models import PointIdsList
from qdrant_client.http.models import PointStruct
from qdrant_client.http.models import VectorParams

from app.config.env_config import settings
from app.config.log_config import config
from app.config.qdrant_config import qdrant_config

logger = config.get_logger(__name__)


class QdrantService:
    """Generic Qdrant vector database operations service.

    Supported default collections:
    - schema_metadata: Stores database table schema embeddings and metadata.
    - sql_templates: Stores validated standard SQL templates.
    - sql_cache: Stores dynamically executed SQL queries for reuse.
    """

    SCHEMA_METADATA_COLLECTION = "schema_metadata"
    SQL_TEMPLATES_COLLECTION = "sql_templates"
    SQL_CACHE_COLLECTION = "sql_cache"

    DEFAULT_COLLECTIONS = [
        SCHEMA_METADATA_COLLECTION,
        SQL_TEMPLATES_COLLECTION,
        SQL_CACHE_COLLECTION,
    ]

    def __init__(self, client: QdrantClient | None = None) -> None:
        """Initialize the Qdrant service.

        Args:
            client: Optional QdrantClient instance.
                Defaults to qdrant_config.get_client().
        """
        self._client = client or qdrant_config.get_client()

    def ensure_collection_exists(
        self,
        collection_name: str,
        vector_size: int | None = None,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """Ensure a vector collection exists, creating it if necessary.

        Args:
            collection_name: Name of the Qdrant collection.
            vector_size: Dimension size of vectors. Defaults to settings.vector_size.
            distance: Distance metric (COSINE, EUCLID, DOT). Defaults to COSINE.

        Returns:
            True if collection exists or was created.
        """
        v_size = vector_size or settings.vector_size
        try:
            collections_res = self._client.get_collections()
            existing_names = {c.name for c in collections_res.collections}

            if collection_name in existing_names:
                logger.debug("Collection '%s' already exists.", collection_name)
                return True

            logger.info(
                "Creating Qdrant collection '%s' (size=%d, distance=%s).",
                collection_name,
                v_size,
                distance,
            )
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=v_size, distance=distance),
            )
            return True
        except Exception as exc:
            logger.error(
                "Failed to ensure collection '%s': %s",
                collection_name,
                exc,
            )
            raise

    def init_default_collections(self, vector_size: int | None = None) -> None:
        """Initialize default collections (schema_metadata, sql_templates, sql_cache).

        Args:
            vector_size: Optional vector dimension size.
        """
        for collection_name in self.DEFAULT_COLLECTIONS:
            self.ensure_collection_exists(
                collection_name,
                vector_size=vector_size,
            )

    def insert_vectors(
        self,
        collection_name: str,
        points: list[dict[str, Any]],
    ) -> None:
        """Insert or update vector points in a collection.

        Args:
            collection_name: Target collection name.
            points: List of point dicts containing:
                - 'id' (optional: str/int/UUID)
                - 'vector': list[float]
                - 'payload': dict (optional metadata)
        """
        if not points:
            return

        self.ensure_collection_exists(collection_name)

        struct_points = []
        for p in points:
            point_id = p.get("id") or str(uuid.uuid4())
            vector = p["vector"]
            payload = p.get("payload", {})
            struct_points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        logger.info(
            "Inserting %d points into collection '%s'.",
            len(struct_points),
            collection_name,
        )
        self._client.upsert(
            collection_name=collection_name,
            points=struct_points,
        )

    def search_vectors(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Search for vector points similar to the query vector.

        Args:
            collection_name: Target collection name.
            query_vector: Query embedding vector.
            limit: Maximum number of results to return.
            score_threshold: Optional similarity threshold.

        Returns:
            List of matching records with point ID, similarity score, and payload.
        """
        self.ensure_collection_exists(collection_name)

        logger.debug(
            "Searching collection '%s' with limit %d.",
            collection_name,
            limit,
        )

        try:
            results = self._client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
        except AttributeError:
            query_res = self._client.query_points(
                collection_name=collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
            )
            results = query_res.points

        return [
            {
                "id": str(r.id),
                "score": float(r.score),
                "payload": r.payload or {},
            }
            for r in results
        ]

    def delete_vectors(
        self,
        collection_name: str,
        point_ids: list[str | int],
    ) -> None:
        """Delete specific points from a collection by ID.

        Args:
            collection_name: Target collection name.
            point_ids: List of point IDs to delete.
        """
        if not point_ids:
            return

        logger.info(
            "Deleting %d points from collection '%s'.",
            len(point_ids),
            collection_name,
        )
        self._client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=point_ids),
        )

    def get_collection_count(self, collection_name: str) -> int:
        """Return total count of points stored in a collection.

        Args:
            collection_name: Target collection name.

        Returns:
            Number of points in collection.
        """
        try:
            res = self._client.count(collection_name=collection_name)
            return res.count
        except Exception:
            return 0

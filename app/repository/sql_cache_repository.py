"""SQL Cache repository.

Data-access layer for CRUD operations on the SQL Cache table in SQL Server.
Contains no business or caching logic.
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.log_config import config
from app.models.sql_cache_model import SQLCache

logger = config.get_logger(__name__)


class SQLCacheRepository:
    """Provides data access methods for the SQLCache ORM model."""

    def create(
        self,
        session: Session,
        cache_record: SQLCache,
    ) -> SQLCache:
        """Insert a new SQLCache record into the database.

        Args:
            session: Active SQLAlchemy database session.
            cache_record: SQLCache instance to persist.

        Returns:
            The created SQLCache instance.
        """
        logger.info("Persisting SQLCache record with ID '%s'.", cache_record.cache_id)
        session.add(cache_record)
        session.commit()
        session.refresh(cache_record)
        return cache_record

    def get_by_id(
        self,
        session: Session,
        cache_id: str,
    ) -> SQLCache | None:
        """Retrieve a SQLCache record by its primary key cache_id.

        Args:
            session: Active SQLAlchemy database session.
            cache_id: Unique UUID string identifier.

        Returns:
            SQLCache instance if found; otherwise None.
        """
        statement = select(SQLCache).where(SQLCache.cache_id == cache_id)
        return session.scalar(statement)

    def update_usage(
        self,
        session: Session,
        cache_id: str,
    ) -> SQLCache | None:
        """Increment the hit_count and update last_used_at for a cache record.

        Args:
            session: Active SQLAlchemy database session.
            cache_id: Unique UUID string identifier.

        Returns:
            Updated SQLCache instance if found; otherwise None.
        """
        record = self.get_by_id(session, cache_id)
        if record is None:
            logger.warning(
                "Attempted to update usage for non-existent cache ID '%s'.", cache_id
            )
            return None

        record.hit_count += 1
        record.last_used_at = datetime.utcnow()

        session.commit()
        session.refresh(record)

        logger.info(
            "Updated cache hit count to %d for cache ID '%s'.",
            record.hit_count,
            cache_id,
        )
        return record

    def delete(
        self,
        session: Session,
        cache_id: str,
    ) -> bool:
        """Delete a SQLCache record by its primary key cache_id.

        Args:
            session: Active SQLAlchemy database session.
            cache_id: Unique UUID string identifier.

        Returns:
            True if deleted; False if record was not found.
        """
        record = self.get_by_id(session, cache_id)
        if record is None:
            return False

        session.delete(record)
        session.commit()
        logger.info("Deleted cache record '%s'.", cache_id)
        return True

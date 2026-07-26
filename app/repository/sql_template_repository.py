"""SQL template repository.

Data-access layer for retrieving and persisting SQLTemplate ORM models in SQL Server.
Contains no business logic, vector search, or embedding logic.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.log_config import config
from app.models.sql_template_model import SQLTemplate

logger = config.get_logger(__name__)


class SQLTemplateRepository:
    """Provides data access methods for the SQLTemplate model."""

    def get_by_id(
        self,
        session: Session,
        template_id: int,
    ) -> SQLTemplate | None:
        """Retrieve a SQLTemplate record by template_id.

        Args:
            session: Active SQLAlchemy database session.
            template_id: Primary key template identifier.

        Returns:
            SQLTemplate instance if found; otherwise None.
        """
        statement = select(SQLTemplate).where(SQLTemplate.template_id == template_id)
        return session.scalar(statement)

    def get_by_name(
        self,
        session: Session,
        name: str,
    ) -> SQLTemplate | None:
        """Retrieve a SQLTemplate record by template name.

        Args:
            session: Active SQLAlchemy database session.
            name: Unique template name.

        Returns:
            SQLTemplate instance if found; otherwise None.
        """
        statement = select(SQLTemplate).where(SQLTemplate.name == name)
        return session.scalar(statement)

    def get_all(
        self,
        session: Session,
        active_only: bool = True,
    ) -> list[SQLTemplate]:
        """Retrieve all SQLTemplate records.

        Args:
            session: Active SQLAlchemy database session.
            active_only: If True, returns only active templates.

        Returns:
            List of SQLTemplate instances.
        """
        statement = select(SQLTemplate)
        if active_only:
            statement = statement.where(SQLTemplate.is_active.is_(True))

        return list(session.scalars(statement).all())

    def create(
        self,
        session: Session,
        template: SQLTemplate,
    ) -> SQLTemplate:
        """Insert a new SQLTemplate record into the database.

        Args:
            session: Active SQLAlchemy database session.
            template: SQLTemplate instance to insert.

        Returns:
            The created SQLTemplate instance.
        """
        logger.info("Persisting SQLTemplate record '%s'.", template.name)
        session.add(template)
        session.commit()
        session.refresh(template)
        return template

"""Database configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config.env_config import settings
from app.models.base import Base


class DatabaseConfig:
    """Manage SQLAlchemy engine and sessions."""

    def __init__(self) -> None:
        """Initialize the database configuration."""
        self.engine = create_engine(
            settings.database_url,
            echo=False,
            future=True,
        )

        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_session(self) -> Session:
        """Return a new database session."""
        return self.session_factory()


database = DatabaseConfig()

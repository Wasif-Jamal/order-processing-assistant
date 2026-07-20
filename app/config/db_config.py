"""Database configuration."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import sessionmaker

from app.config.env_config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


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

    def get_session(self):
        """Return a new database session."""
        return self.session_factory()


database = DatabaseConfig()

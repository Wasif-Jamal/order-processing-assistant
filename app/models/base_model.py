"""Base SQLAlchemy model definitions.

Defines the application's declarative base class that all ORM models inherit
from. Keeping the base in a dedicated module avoids circular imports and
provides a single source of truth for model metadata.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All database models should inherit from this class so they share the same
    metadata object. The metadata is later used to create the database schema
    during application startup.
    """

    pass

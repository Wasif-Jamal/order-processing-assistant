"""SQL Cache database model.

Defines the SQLCache ORM model used to store successful SQL query executions in
SQL Server (Layer 2 of the SQL Cache architecture).
"""

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import Base


class SQLCache(Base):
    """Represents a cached SQL query execution record in SQL Server.

    Attributes:
        cache_id: Unique UUID string identifying the cache entry.
        user_question: Natural language question asked by the user.
        generated_sql: Validated SQL query string generated for the question.
        sql_explanation: Optional human-readable explanation of the SQL query.
        created_at: Timestamp when the cache entry was created.
        last_used_at: Timestamp when the cache entry was last retrieved.
        hit_count: Number of times this cached query has been reused.
    """

    __tablename__ = "sql_cache"

    cache_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        doc="Unique UUID string identifier for the cache record.",
    )

    user_question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Original natural language user question.",
    )

    generated_sql: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Executed and validated SQL query string.",
    )

    sql_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional explanation of the SQL query.",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        doc="Timestamp when the cache entry was created.",
    )

    last_used_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        doc="Timestamp when the cache entry was last retrieved.",
    )

    hit_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Number of times this cached query has been reused.",
    )

    def __repr__(self) -> str:
        """Return string representation of the SQL cache model."""
        return (
            f"SQLCache("
            f"cache_id='{self.cache_id}', "
            f"hit_count={self.hit_count}, "
            f"user_question='{self.user_question[:30]}...')"
        )

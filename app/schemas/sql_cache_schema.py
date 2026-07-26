"""SQL cache schemas.

Defines Pydantic schemas for SQL cache records and vector search hit results.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SQLCacheSchema(BaseModel):
    """Represents a cached SQL execution record."""

    model_config = ConfigDict(from_attributes=True)

    cache_id: str | None = Field(
        default=None,
        description="Unique UUID identifier for the cache record.",
    )

    user_question: str = Field(
        ...,
        description="Original natural language user question.",
    )

    generated_sql: str = Field(
        ...,
        description="Validated SQL query string.",
    )

    sql_explanation: str | None = Field(
        default=None,
        description="Optional human-readable explanation of the SQL query.",
    )

    created_at: datetime | None = Field(
        default=None,
        description="Timestamp when the cache entry was created.",
    )

    last_used_at: datetime | None = Field(
        default=None,
        description="Timestamp when the cache entry was last retrieved.",
    )

    hit_count: int = Field(
        default=1,
        description="Number of times this cached query has been reused.",
    )


class CachedSQLResult(BaseModel):
    """Represents a successful vector similarity search cache hit."""

    model_config = ConfigDict(from_attributes=True)

    cache_id: str = Field(
        ...,
        description="Unique UUID identifier of the matching cache record.",
    )

    user_question: str = Field(
        ...,
        description="Cached natural language question.",
    )

    generated_sql: str = Field(
        ...,
        description="Cached validated SQL query string.",
    )

    sql_explanation: str | None = Field(
        default=None,
        description="Optional explanation of the cached SQL query.",
    )

    similarity_score: float = Field(
        ...,
        description="Vector similarity score between input question and cached question.",
    )

    hit_count: int = Field(
        default=1,
        description="Updated cache hit counter.",
    )

    last_used_at: datetime | None = Field(
        default=None,
        description="Updated timestamp when cache entry was retrieved.",
    )

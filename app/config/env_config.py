"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from the environment.

    Attributes:
        database_url: SQLAlchemy connection URL.
        csv_path: Path to the Superstore CSV file.
        log_level: Logging level for the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    database_url: str = Field(
        default="sqlite:///data/superstore.db",
        description="SQLAlchemy database connection URL.",
    )

    csv_path: str = Field(
        default="data/database.csv",
        description="Path to the Superstore CSV file.",
    )

    sql_dialect: str = Field(
        default="tsql",
        description="SQL Dialect.",
    )

    log_level: str = Field(
        default="INFO",
        description="Application logging level.",
    )

    qdrant_host: str = Field(
        default="localhost",
        description="Qdrant server host.",
    )

    qdrant_port: int = Field(
        default=6333,
        description="Qdrant server port.",
    )

    qdrant_api_key: str | None = Field(
        default=None,
        description="Qdrant API key for authentication.",
    )

    qdrant_url: str | None = Field(
        default=None,
        description="Qdrant server URL.",
    )

    qdrant_location: str | None = Field(
        default=None,
        description="Qdrant location (e.g., ':memory:' for local testing).",
    )

    embedding_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Name of the embedding model to use.",
    )

    vector_size: int = Field(
        default=384,
        description="Dimension size of generated vector embeddings.",
    )


settings = Settings()

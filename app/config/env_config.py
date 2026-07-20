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

    log_level: str = Field(
        default="INFO",
        description="Application logging level.",
    )


settings = Settings()

"""Knowledge base metadata schema.

Defines Pydantic schemas representing database table metadata stored in Qdrant.
Used by vector search and schema retrieval services to ground LLM SQL generation.
"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ColumnMetadata(BaseModel):
    """Represents column-level database metadata."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(
        ...,
        description="Column name.",
    )

    data_type: str = Field(
        ...,
        description="SQL data type of the column.",
    )

    description: str = Field(
        default="",
        description="Column description or comment.",
    )

    is_primary_key: bool = Field(
        default=False,
        description="Whether the column is a primary key.",
    )

    is_foreign_key: bool = Field(
        default=False,
        description="Whether the column is a foreign key.",
    )

    foreign_key_target: str | None = Field(
        default=None,
        description="Referenced table and column if foreign key.",
    )


class ForeignKeyMetadata(BaseModel):
    """Represents foreign key relationship metadata."""

    model_config = ConfigDict(from_attributes=True)

    column: str = Field(
        ...,
        description="Local column name.",
    )

    target_table: str = Field(
        ...,
        description="Referenced target table name.",
    )

    target_column: str = Field(
        ...,
        description="Referenced target column name.",
    )


class KnowledgeBaseSchema(BaseModel):
    """Represents table metadata for the Knowledge Base RAG layer.

    Attributes:
        table_name: Name of the database table.
        description: Table business description.
        columns: List of column metadata objects.
        primary_keys: List of primary key column names.
        foreign_keys: List of foreign key relationships.
        sample_questions: Natural language sample queries relevant to this table.
    """

    model_config = ConfigDict(from_attributes=True)

    table_name: str = Field(
        ...,
        description="Name of the database table.",
    )

    description: str = Field(
        default="",
        description="Business description of the table.",
    )

    columns: list[ColumnMetadata] = Field(
        default_factory=list,
        description="List of column definitions.",
    )

    primary_keys: list[str] = Field(
        default_factory=list,
        description="List of primary key column names.",
    )

    foreign_keys: list[ForeignKeyMetadata] = Field(
        default_factory=list,
        description="List of foreign key relationship definitions.",
    )

    sample_questions: list[str] = Field(
        default_factory=list,
        description="Sample natural language questions for table retrieval.",
    )

    def to_embedding_text(self) -> str:
        """Format the metadata into a structured text representation.

        Returns:
            Formatted string for embedding generation.
        """
        cols_text = ", ".join(f"{col.name} ({col.data_type})" for col in self.columns)
        pks_text = ", ".join(self.primary_keys) if self.primary_keys else "None"
        fks_text = (
            ", ".join(
                f"{fk.column} -> {fk.target_table}.{fk.target_column}"
                for fk in self.foreign_keys
            )
            if self.foreign_keys
            else "None"
        )
        questions_text = "; ".join(self.sample_questions)

        return (
            f"Table: {self.table_name}\n"
            f"Description: {self.description}\n"
            f"Columns: {cols_text}\n"
            f"Primary Keys: {pks_text}\n"
            f"Foreign Keys: {fks_text}\n"
            f"Sample Questions: {questions_text}"
        )

"""SQL template schema.

Defines the Pydantic schema for validated SQL templates. These schemas are used
for validation when creating, updating, and retrieving SQL templates from the
repository.
"""

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SQLTemplateSchema(BaseModel):
    """Represents a validated SQL template."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    template_id: int | None = Field(
        default=None,
        description="Unique template identifier.",
    )

    name: str = Field(
        ...,
        max_length=200,
        description="Unique template name.",
    )

    business_intent: str = Field(
        ...,
        max_length=200,
        description="Business intent represented by the SQL template.",
    )

    description: str = Field(
        ...,
        description="Human-readable description of the SQL template.",
    )

    natural_language_examples: str | None = Field(
        default=None,
        description="Natural language example questions matching the template.",
    )

    sql_query: str = Field(
        ...,
        description="Validated SQL query.",
    )

    sql_explanation: str | None = Field(
        default=None,
        description="Optional human-readable explanation of the SQL query logic.",
    )

    parameters: str | None = Field(
        default=None,
        description="Comma-separated parameter names required by the query.",
    )

    is_active: bool = Field(
        default=True,
        description="Whether the template is active.",
    )

    created_at: datetime | None = Field(
        default=None,
        description="Template creation timestamp.",
    )

    updated_at: datetime | None = Field(
        default=None,
        description="Template last update timestamp.",
    )

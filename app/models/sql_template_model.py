"""SQL template model.

Defines the SQLTemplate model used to store validated SQL templates. These
templates are retrieved by the SQL agent after semantic search in the vector
store and executed against the database after validation.
"""

from datetime import datetime

from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from app.models.base_model import Base


class SQLTemplate(Base):
    """Represents a validated SQL template."""

    __tablename__ = "sql_templates"

    template_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )

    business_intent: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    natural_language_examples: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Natural language sample questions matching the template.",
    )

    sql_query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sql_explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Explanation of the template SELECT logic.",
    )

    parameters: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

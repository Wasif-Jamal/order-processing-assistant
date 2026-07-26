"""Pydantic request schemas for the FastAPI API layer.

Defines the validated request payloads accepted by the Order Processing
Assistant. FastAPI validates incoming requests against these schemas before
route handlers are executed.
"""

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class QueryRequest(BaseModel):
    """Inbound payload for executing a validated SQL query.

    Attributes:
        sql: Read-only SQL statement to execute.
    """

    sql: str = Field(..., min_length=1)

    @field_validator("sql")
    @classmethod
    def sql_not_blank(cls, value: str) -> str:
        """Reject blank SQL statements."""
        if not value.strip():
            raise ValueError("SQL must not be blank.")
        return value


class ChatRequest(BaseModel):
    """Inbound payload for the chat endpoint.

    Attributes:
        question: User's natural language question.
        session_uuid: Client-generated session identifier used to maintain
            conversation history.
    """

    question: str = Field(..., min_length=1)
    session_uuid: str

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, value: str) -> str:
        """Reject blank questions."""
        if not value.strip():
            raise ValueError("Question must not be blank.")
        return value
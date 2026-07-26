"""Pydantic response schemas for the FastAPI API layer.

Defines the response payloads returned by the Order Processing Assistant.
These schemas provide a stable API contract while allowing additional
functionality such as SQL caching and template retrieval to be introduced
without breaking existing clients.
"""

from typing import Literal
from typing import Optional

from pydantic import BaseModel


class ChatResponse(BaseModel):
    """Response payload for the chat endpoint.

    Attributes:
        question: User's submitted question.
        generated_sql: SQL executed for the request.
        sql_source: Source of the SQL query.
        sql_explanation: Plain-English explanation of the SQL.
        query_result: Query result serialized as a list of dictionaries.
        columns: Ordered column names returned by the query.
        row_count: Number of rows returned.
        error_message: Error message if processing failed.
    """

    question: str
    generated_sql: Optional[str] = None
    sql_source: Optional[Literal["cache", "template", "generated"]] = None
    sql_explanation: Optional[str] = None
    query_result: Optional[list[dict]] = None
    columns: Optional[list[str]] = None
    row_count: Optional[int] = None
    error_message: Optional[str] = None


class QueryResponse(BaseModel):
    """Response payload for the execute-query endpoint.

    Attributes:
        columns: Ordered column names returned by the query.
        rows: Query result rows.
        row_count: Number of rows returned.
    """

    columns: list[str]
    rows: list[dict]
    row_count: int


class HealthResponse(BaseModel):
    """Response payload for the health-check endpoint.

    Attributes:
        status: Health status of the application.
    """

    status: str

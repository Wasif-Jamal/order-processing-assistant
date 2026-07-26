"""Workflow execution state.

``WorkflowState`` extends LangGraph's ``MessagesState`` by adding the fields
required by the Order Processing Assistant workflow. The state is shared across
all workflow nodes and carries the generated SQL, execution result, and any
user-facing error information.
"""

from typing import Literal
from typing import Optional

from langgraph.graph import MessagesState

from app.schemas.sql_result_schema import QueryResult


class WorkflowState(MessagesState):
    """Shared workflow state.

    Inherits ``messages`` from ``MessagesState``. The SQL Agent populates the
    remaining fields during workflow execution.

    Attributes:
        question: User's natural language question.
        generated_sql: SQL selected or generated for execution.
        sql_source: Source of the SQL statement.
        sql_explanation: Plain-English explanation of the SQL.
        query_result: Result returned after SQL execution.
        error_message: User-facing error message if processing fails.
    """

    question: str
    generated_sql: Optional[str]
    sql_source: Optional[Literal["cache", "template", "generated"]]
    sql_explanation: Optional[str]
    query_result: Optional[QueryResult]
    error_message: Optional[str]

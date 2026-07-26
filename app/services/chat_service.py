"""Chat Service — API-to-workflow bridge.

``ChatService`` is the single component responsible for invoking the compiled
LangGraph workflow. The FastAPI routes delegate all business logic to this
service, while the agents encapsulate the application's reasoning and SQL
generation pipeline.

The service translates the graph output into a ``ChatResponse`` and ensures
that all unexpected failures are converted into a standard user-friendly
response.
"""

import asyncio

from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from app.config.log_config import config as log_config
from app.schema.requests_schema import ChatRequest
from app.schema.responses_schema import ChatResponse
from app.schema.sql_result_schema import QueryResult

logger = log_config.get_logger(__name__)

# Standard application error returned when an unexpected exception occurs.
_ERR_DATABASE = "Unable to retrieve data at this time."

# Allow only application-defined error messages to reach the client.
_ALLOWED_ERRORS: frozenset[str] = frozenset(
    {
        "Unable to identify requested entities.",
        "Generated query could not be validated.",
        "No data found for the requested query.",
        "Unable to retrieve data at this time.",
    }
)


class ChatService:
    """Bridge between the FastAPI layer and the LangGraph workflow."""

    def __init__(self, graph: CompiledStateGraph) -> None:
        """Initialize the chat service.

        Args:
            graph: Compiled LangGraph workflow.
        """
        self._graph = graph

    async def ask(self, request: ChatRequest) -> ChatResponse:
        """Process a user's question through the workflow.

        Args:
            request: Validated chat request.

        Returns:
            A populated ``ChatResponse``.
        """
        logger.info(
            "Received question for session=%s",
            request.session_uuid,
        )

        try:
            result = await asyncio.to_thread(
                self._graph.invoke,
                {
                    "question": request.question,
                    "messages": [
                        HumanMessage(content=request.question),
                    ],
                },
            )

            error_message: str | None = result.get("error_message")

            if (
                error_message is not None
                and error_message not in _ALLOWED_ERRORS
            ):
                logger.warning(
                    "Unexpected error returned by workflow: %s",
                    error_message,
                )
                error_message = _ERR_DATABASE

            query_result: QueryResult | None = result.get("query_result")

            rows = None
            columns = None
            row_count = None

            if query_result is not None:
                rows = query_result.rows
                columns = query_result.columns
                row_count = query_result.row_count

            logger.info(
                "Workflow completed successfully. Error=%s",
                error_message,
            )

            return ChatResponse(
                question=request.question,
                generated_sql=result.get("generated_sql"),
                sql_source=result.get("sql_source"),
                sql_explanation=result.get("sql_explanation"),
                query_result=rows,
                columns=columns,
                row_count=row_count,
                error_message=error_message,
            )

        except Exception:
            logger.exception("Unhandled exception while processing chat request.")

            return ChatResponse(
                question=request.question,
                error_message=_ERR_DATABASE,
            )
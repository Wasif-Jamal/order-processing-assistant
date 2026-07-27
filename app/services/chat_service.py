"""
Chat Service — API-to-workflow bridge.

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
from app.schemas.requests_schema import ChatRequest
from app.schemas.responses_schema import ChatResponse
from app.schemas.sql_result_schema import QueryResult
from app.services.conversation_service import ConversationService

logger = log_config.get_logger(__name__)

_ERR_DATABASE = "Unable to retrieve data at this time."

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

    def __init__(
        self,
        graph: CompiledStateGraph,
        conversation_service: ConversationService,
    ) -> None:
        """Initialize the chat service.

        Args:
            graph: Compiled LangGraph workflow.
            conversation_service: In-memory conversation history service.
        """
        self._graph = graph
        self._conversation_service = conversation_service

    async def ask(self, request: ChatRequest) -> ChatResponse:
        """Process a user's question through the workflow."""

        logger.info(
            "Received question for session=%s",
            request.session_uuid,
        )

        session_id = str(request.session_uuid)

        try:
            history = self._conversation_service.get_history(session_id)

            result = await asyncio.to_thread(
                self._graph.invoke,
                {
                    "question": request.question,
                    "conversation_history": history,
                    "messages": [
                        HumanMessage(content=request.question),
                    ],
                },
            )

            error_message: str | None = result.get("error_message")

            follow_up_question = result.get("follow_up_question")

            if follow_up_question:
                logger.info("Returning follow-up question.")

                return ChatResponse(
                    question=request.question,
                    error_message=follow_up_question,
                )

            if error_message is not None and error_message not in _ALLOWED_ERRORS:
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

            response = ChatResponse(
                question=request.question,
                generated_sql=result.get("generated_sql"),
                sql_source=result.get("sql_source"),
                sql_explanation=result.get("sql_explanation"),
                query_result=rows,
                columns=columns,
                row_count=row_count,
                error_message=error_message,
            )

            # Save conversation history.
            self._conversation_service.append_user_message(
                session_id=session_id,
                message=request.question,
            )

            self._conversation_service.append_assistant_message(
                session_id=session_id,
                message=(
                    error_message
                    if error_message
                    else str(rows)
                    if rows is not None
                    else "Request completed."
                ),
            )

            logger.info(
                "Workflow completed successfully. Error=%s",
                error_message,
            )

            return response

        except Exception:
            logger.exception("Unhandled exception while processing chat request.")

            return ChatResponse(
                question=request.question,
                error_message=_ERR_DATABASE,
            )

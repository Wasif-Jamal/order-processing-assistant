"""RAG tools used by the SQL Agent.

This module exposes LangChain tools for retrieving database schema metadata
from the Knowledge Base (Qdrant). The tools are thin wrappers around
``KnowledgeBaseService`` and contain no business logic.

Responsibilities:

* Retrieve relevant schema metadata for a natural language question.

The tool updates the shared LangGraph ``WorkflowState`` using
``Command(update=...)``.
"""

from __future__ import annotations
from typing_extensions import Annotated

from langchain_core.tools import tool
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId

from app.config.log_config import config as log_config
from app.services.knowledge_base_service import KnowledgeBaseService

logger = log_config.get_logger(__name__)


class RagTools:
    """Knowledge Base (RAG) tools for the SQL Agent."""

    def __init__(
        self,
        knowledge_base_service: KnowledgeBaseService,
    ) -> None:
        """Initialize RAG tools.

        Args:
            knowledge_base_service: Knowledge Base service.
        """
        self._knowledge_base_service = knowledge_base_service

        @tool
        def retrieve_schema(
            question: str,
            tool_call_id: Annotated[str, InjectedToolCallId],
            limit: int = 5,
        ) -> Command:
            """Retrieve relevant schema metadata.

            Searches the Qdrant Knowledge Base for schema information relevant
            to the user's question.

            Args:
                question: User question.
                limit: Maximum number of schema documents.

            Returns:
                Command updating the workflow state.
            """
            logger.info(
                "Searching Knowledge Base for schema context."
            )

            schema_context = self._knowledge_base_service.search_schema(
                question=question,
                limit=limit,
            )

            if not schema_context:
                logger.warning(
                    "No schema context found."
                )

                return Command(
                    update={
                        "schema_context": [],
                        "messages": [
                            ToolMessage(
                                content="No relevant schema information found.",
                                tool_call_id=tool_call_id,
                            )
                        ],
                    }
                )

            logger.info(
                "Retrieved %d schema document(s).",
                len(schema_context),
            )

            return Command(
                update={
                    "schema_context": schema_context,
                    "messages": [
                        ToolMessage(
                            content="Relevant schema information retrieved.",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )
        
        self.retrieve_schema = retrieve_schema
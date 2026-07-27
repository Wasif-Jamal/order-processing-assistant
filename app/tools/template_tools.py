"""Template tools used by the SQL Agent.

This module exposes LangChain tools for searching the curated SQL template
repository. The tools are thin wrappers around ``SQLTemplateService`` and
contain no business logic.

Responsibilities:

* Search for a validated SQL template matching the user's question.

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
from app.services.sql_template_service import SQLTemplateService

logger = log_config.get_logger(__name__)


class TemplateTools:
    """SQL template retrieval tools."""

    def __init__(
        self,
        sql_template_service: SQLTemplateService,
    ) -> None:
        """Initialize template tools.

        Args:
            sql_template_service: SQL template service.
        """
        self._template_service = sql_template_service

        @tool
        def retrieve_sql_template(
            question: str,
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            """Retrieve a SQL template matching the user's question.

            Searches the template vector store for the closest matching validated
            SQL template.

            Args:
                question: User question.

            Returns:
                Command updating the workflow state.
            """
            logger.info(
                "Searching SQL template repository for question: %s",
                question,
            )

            template = self._template_service.search_template(question)

            if template is None:
                logger.info("No SQL template found.")

                return Command(
                    update={
                        "messages": [
                            ToolMessage(
                                content="No SQL template found.",
                                tool_call_id=tool_call_id,
                            )
                        ]
                    }
                )

            logger.info(
                "Template '%s' selected.",
                template.name,
            )

            return Command(
                update={
                    "generated_sql": template.generated_sql,
                    "sql_source": "repository",
                    "messages": [
                        ToolMessage(
                            content="SQL template found.",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        self.retrieve_sql_template = retrieve_sql_template

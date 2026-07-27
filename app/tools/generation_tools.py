"""SQL generation tools used by the SQL Agent.

This module exposes LangChain tools for dynamically generating SQL using the
LLM. The tool is a thin wrapper around the language model and contains no
database or validation logic.

Responsibilities:

* Generate a SQL SELECT statement using the user question and retrieved
  schema context.

The tool updates the shared LangGraph ``WorkflowState`` using
``Command(update=...)``.
"""

from __future__ import annotations

from typing import Any
from typing_extensions import Annotated

from langchain_core.messages import HumanMessage
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId
from langchain_core.tools import tool
from langgraph.types import Command
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.log_config import config as log_config
from app.prompts.sql_prompt import SQL_SYSTEM_PROMPT


logger = log_config.get_logger(__name__)


class GenerationTools:
    """SQL generation tools."""

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
    ) -> None:
        """Initialize generation tools.

        Args:
            llm: Language model used for SQL generation.
        """
        self._llm = llm

        @tool
        def generate_sql(
            question: str,
            schema_context: str,
            tool_call_id: Annotated[str, InjectedToolCallId],
        ) -> Command:
            """Generate SQL from the user question.

            Args:
                question:
                    User question.

                schema_context:
                    Relevant schema metadata retrieved from RAG.

                tool_call_id:
                    LangGraph tool call identifier.

            Returns:
                Command updating WorkflowState.
            """

            logger.info("Generating SQL using LLM.")

            prompt = f"""
Schema Context
--------------
{schema_context}

User Question
-------------
{question}

Generate a single SQL Server SELECT statement.

Return ONLY the SQL query.
"""

            response = self._llm.invoke(
                [
                    HumanMessage(content=SQL_SYSTEM_PROMPT),
                    HumanMessage(content=prompt),
                ]
            )

            logger.debug(
                "Gemini response content type: %s",
                type(response.content),
            )

            logger.debug(
                "Gemini response content: %s",
                response.content,
            )

            sql = self._extract_text(response)

            # Remove markdown fences if present.
            if sql.startswith("```"):
                lines = [
                    line
                    for line in sql.splitlines()
                    if not line.startswith("```")
                ]
                sql = "\n".join(lines).strip()

            logger.info("SQL generated successfully.")

            return Command(
                update={
                    "generated_sql": sql,
                    "sql_explanation": None,
                    "messages": [
                        ToolMessage(
                            content="SQL generated successfully.",
                            tool_call_id=tool_call_id,
                        )
                    ],
                }
            )

        self.generate_sql = generate_sql

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Extract text content from LangChain LLM response.

        Newer versions of langchain-google-genai may return
        ``response.content`` as a list of content blocks instead of a string.

        Args:
            response:
                LangChain AIMessage response.

        Returns:
            Extracted plain text response.
        """

        content = response.content

        # Current LangChain behaviour: content is already a string.
        if isinstance(content, str):
            return content.strip()

        # Newer Gemini response format:
        # [
        #     {"type": "text", "text": "SELECT ..."}
        # ]
        if isinstance(content, list):
            extracted_parts = []

            for item in content:
                if isinstance(item, str):
                    extracted_parts.append(item)

                elif isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        extracted_parts.append(text)

                elif hasattr(item, "text"):
                    extracted_parts.append(item.text)

            return "\n".join(extracted_parts).strip()

        # Fallback
        return str(content).strip()
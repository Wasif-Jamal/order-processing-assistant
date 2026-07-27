"""Response Agent.

The ResponseAgent converts SQL query results into a concise, business-friendly
response. It is the final node in the LangGraph workflow.

The agent never generates SQL or executes database operations. It only formats
the workflow output into natural language and stores it in the workflow state.
"""

from typing import Any

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState
from app.prompts.response_prompt import RESPONSE_SYSTEM_PROMPT

logger = log_config.get_logger(__name__)


class ResponseAgent:
    """Generates the final business response."""

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
    ) -> None:
        """Initialize the ResponseAgent.

        Args:
            llm: Language model used for response generation.
        """
        self._llm = llm

    def node(
        self,
        state: WorkflowState,
    ) -> dict[str, Any]:
        """Generate the final business response.

        Args:
            state: Current workflow state.

        Returns:
            Updated workflow state containing ``final_response``.
        """
        logger.info("Generating final response.")

        if state.get("error_message"):
            return {
                "final_response": state["error_message"],
            }

        query_result = state.get("query_result")

        if query_result is None or query_result.row_count == 0:
            return {
                "final_response": "I couldn't find any records matching your request.",
            }

        message = HumanMessage(
            content=f"""
User Question:
{state["question"]}

SQL Explanation:
{state.get("sql_explanation")}

Rows Returned:
{query_result.row_count}

Query Result:
{query_result.rows}
"""
        )

        response = self._llm.invoke(
            [
                ("system", RESPONSE_SYSTEM_PROMPT),
                message,
            ]
        )

        logger.info("Business response generated.")

        return {
            "final_response": response.content,
        }

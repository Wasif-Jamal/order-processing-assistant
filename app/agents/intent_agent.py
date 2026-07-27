"""Intent Agent.

The IntentAgent is the first node in the Order Processing Assistant workflow.
It receives the user's natural-language question, identifies the business
intent, extracts entities, determines whether additional information is
required, and stores the results in the shared WorkflowState.

The agent never generates SQL or executes database queries.
"""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState
from app.prompts.intent_prompt import INTENT_PROMPT_TEMPLATE
from app.schemas.intent_schema import IntentResult

logger = log_config.get_logger(__name__)


class IntentAgent:
    """Detects user intent and extracts business entities.

    This is the first LangGraph node in the workflow. It classifies the user's
    request, extracts relevant entities, determines whether all required
    parameters are available, and updates the workflow state.
    """

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
    ) -> None:
        """Initialize the IntentAgent.

        Args:
            llm: Language model used for intent detection.
        """
        self._llm = llm

        self._parser = JsonOutputParser(
            pydantic_object=IntentResult,
        )

        self._prompt = PromptTemplate(
            template=INTENT_PROMPT_TEMPLATE,
            input_variables=["user_query"],
            partial_variables={
                "format_instructions": self._parser.get_format_instructions(),
            },
        )

        self._chain = self._prompt | self._llm | self._parser

        logger.info("IntentAgent initialized.")

    def analyze(
        self,
        user_query: str,
    ) -> IntentResult:
        """Analyze a natural-language query.

        Args:
            user_query: User's question.

        Returns:
            Structured intent detection result.
        """
        logger.info("Analyzing user intent.")

        raw_result = self._chain.invoke(
            {
                "user_query": user_query,
            }
        )

        result = IntentResult.model_validate(raw_result)

        logger.info(
            "Intent=%s ready_for_sql=%s",
            result.intent,
            result.ready_for_sql,
        )

        return result

    def node(
        self,
        state: WorkflowState,
    ) -> dict[str, Any]:
        """LangGraph node.

        Reads the user's question from the workflow state, performs intent
        detection, and writes the extracted information back into the state.

        Args:
            state: Current workflow state.

        Returns:
            Partial WorkflowState update.
        """
        logger.info("Running IntentAgent node.")

        result = self.analyze(state["question"])

        logger.info("IntentAgent completed.")

        return {
            "intent": result.intent,
            "entities": result.entities,
            "missing_parameters": result.missing_parameters,
            "follow_up_question": result.follow_up_question,
            "ready_for_sql": result.ready_for_sql,
        }

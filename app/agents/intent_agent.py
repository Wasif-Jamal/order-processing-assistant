"""Intent Agent.

The :class:`IntentAgent` is the first node in the Order Processing Assistant
SQL pipeline.  It receives a natural language user question, classifies the
business intent, extracts relevant entities, identifies missing required
parameters, and returns a structured :class:`~app.schemas.intent_schema.IntentResult`.

The agent does **not** generate SQL, access any database, or execute queries.
All of those concerns are handled by downstream components.
"""

from __future__ import annotations

import logging

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.prompts.intent_prompt import INTENT_PROMPT_TEMPLATE
from app.schemas.intent_schema import IntentResult

logger = logging.getLogger(__name__)


class IntentAgent:
    """Classifies user intent and extracts entities from a natural language query.

    The agent uses an LLM to:

    1. Classify the request into one of the supported :class:`~app.schemas.intent_schema.IntentEnum` values.
    2. Extract named entities such as ``customer_name``, ``order_id``, etc.
    3. Determine which required parameters are missing for the identified intent.
    4. Generate a user-friendly follow-up question when parameters are missing.

    The agent is stateless – each call to :meth:`analyze` is fully independent.

    Args:
        llm: A pre-configured LangChain Google Generative AI chat model.
    """

    def __init__(self, llm: ChatGoogleGenerativeAI) -> None:
        """Initialize the :class:`IntentAgent`.

        Args:
            llm: LangChain Google Generative AI model instance used for
                intent classification and entity extraction.
        """
        self._llm = llm
        self._parser: JsonOutputParser = JsonOutputParser(pydantic_object=IntentResult)

        self._prompt = PromptTemplate(
            template=INTENT_PROMPT_TEMPLATE,
            input_variables=["user_query"],
            partial_variables={
                "format_instructions": self._parser.get_format_instructions(),
            },
        )

        self._chain = self._prompt | self._llm | self._parser

        logger.info(
            "IntentAgent initialized (model=%s).",
            llm.__class__.__name__,
        )

    def analyze(self, user_query: str) -> IntentResult:
        """Analyze *user_query* and return a structured :class:`~app.schemas.intent_schema.IntentResult`.

        The method is synchronous and blocking.  It invokes the LangChain
        chain ``prompt | llm | parser`` and returns the parsed result.

        Args:
            user_query: The raw natural language question entered by the user.

        Returns:
            :class:`~app.schemas.intent_schema.IntentResult` containing the
            identified intent, extracted entities, any missing parameters, a
            readiness flag, and an optional follow-up question.

        Raises:
            ValueError: If the LLM returns output that cannot be parsed into
                an :class:`~app.schemas.intent_schema.IntentResult`.
        """
        logger.info("Analyzing intent for query: '%s'.", user_query)

        raw_result: dict = self._chain.invoke({"user_query": user_query})

        result = IntentResult.model_validate(raw_result)

        logger.info(
            "Intent detected: %s | ready_for_sql=%s | missing=%s.",
            result.intent.value,
            result.ready_for_sql,
            result.missing_parameters,
        )

        return result

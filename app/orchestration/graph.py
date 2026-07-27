"""Workflow graph for the Order Processing Assistant.

The workflow consists of three sequential agents:

1. IntentAgent
2. SqlAgent
3. ResponseAgent

After the IntentAgent completes, the graph checks whether additional user
information is required. If required, execution ends early and the assistant
asks the user for the missing information. Otherwise the workflow continues
through SQL execution and response generation.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.intent_agent import IntentAgent
from app.agents.response_agent import ResponseAgent
from app.agents.sql_agent import SqlAgent
from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState

from app.services.database_service import DatabaseService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.sql_cache_service import SQLCacheService
from app.services.sql_template_service import SQLTemplateService

logger = log_config.get_logger(__name__)


def _route_after_intent(state: WorkflowState) -> str:
    """Route the workflow after intent detection.

    If required parameters are missing, terminate the workflow so the API can
    return a clarification request. Otherwise continue to SQL processing.

    Args:
        state: Current workflow state.

    Returns:
        Next node name or END.
    """
    if state.get("missing_parameters"):
        logger.info("IntentAgent requested additional user information.")
        return END

    logger.info("IntentAgent completed successfully.")
    return "sql_agent"


class OrderProcessingGraph:
    """Builds the LangGraph workflow."""

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        sql_cache_service: SQLCacheService,
        sql_template_service: SQLTemplateService,
        knowledge_base_service: KnowledgeBaseService,
        database_service: DatabaseService,
    ) -> None:
        """Initialize the workflow builder.

        Args:
            llm: Shared language model used by all agents.
        """
        self._llm = llm
        self._sql_cache_service = sql_cache_service
        self._sql_template_service = sql_template_service
        self._knowledge_base_service = knowledge_base_service
        self._database_service = database_service

    def build(self) -> CompiledStateGraph:
        """Build and compile the workflow graph."""

        logger.info("Building workflow graph.")

        intent_agent = IntentAgent(self._llm)
        sql_agent = SqlAgent(
            llm=self._llm,
            sql_cache_service=self._sql_cache_service,
            sql_template_service=self._sql_template_service,
            knowledge_base_service=self._knowledge_base_service,
            database_service=self._database_service,
        )
        response_agent = ResponseAgent(self._llm)

        builder = StateGraph(WorkflowState)

        builder.add_node(
            "intent_agent",
            intent_agent.node,
        )

        builder.add_node(
            "sql_agent",
            sql_agent.node,
        )

        builder.add_node(
            "response_agent",
            response_agent.node,
        )

        builder.set_entry_point("intent_agent")

        builder.add_conditional_edges(
            "intent_agent",
            _route_after_intent,
        )

        builder.add_edge(
            "sql_agent",
            "response_agent",
        )

        builder.add_edge(
            "response_agent",
            END,
        )

        graph = builder.compile()

        logger.info("Workflow graph compiled successfully.")

        return graph

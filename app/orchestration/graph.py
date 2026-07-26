"""Workflow graph assembly.

``WorkflowGraph`` builds the LangGraph workflow for the Order Processing
Assistant. The graph currently consists of a single SQL Agent responsible for
retrieving SQL from the cache or template repository, generating SQL when
required, validating it, executing it, and preparing the workflow state.

The graph has been intentionally kept simple so additional agents can be added
without changing the API layer.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.sql_agent import SqlAgent
from app.config.env_config import settings
from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState

logger = log_config.get_logger(__name__)


class WorkflowGraph:
    """Build and compile the LangGraph workflow."""

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        retry_limit: int | None = None,
    ) -> None:
        """Initialize the workflow graph.

        Args:
            llm: Language model shared by all agents.
            retry_limit: Maximum SQL correction attempts.
        """
        self._llm = llm
        self._retry_limit = (
            retry_limit
            if retry_limit is not None
            else settings.sql_retry_limit
        )

        logger.info(
            "WorkflowGraph configured (retry_limit=%d)",
            self._retry_limit,
        )

    def build(self) -> CompiledStateGraph:
        """Compile and return the workflow graph.

        Returns:
            A compiled LangGraph workflow.
        """
        logger.info("Building workflow graph.")

        sql_agent = SqlAgent(
            llm=self._llm,
            retry_limit=self._retry_limit,
        )

        builder = StateGraph(WorkflowState)

        builder.add_node(
            "sql_agent",
            sql_agent.node,
        )

        builder.set_entry_point("sql_agent")

        builder.add_edge(
            "sql_agent",
            END,
        )

        graph = builder.compile()

        logger.info("Workflow graph compiled successfully.")

        return graph
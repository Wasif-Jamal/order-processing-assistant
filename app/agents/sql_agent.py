"""SQL Agent.

``SqlAgent`` is responsible for the complete SQL execution workflow of the
Order Processing Assistant. The agent retrieves SQL from the cache or template
repository when possible, generates SQL when required, validates every query,
executes it, and stores successful executions in the SQL cache.

The agent is implemented using LangChain's ``create_agent`` and is exposed as a
single LangGraph node.
"""

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.env_config import settings
from app.config.log_config import config as log_config
from app.orchestration.state import WorkflowState
from app.prompts.sql_prompt import SQL_SYSTEM_PROMPT
from app.tools.sql_tools import SqlTools

logger = log_config.get_logger(__name__)


class SqlAgent:
    """SQL Agent for the Order Processing Assistant."""

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        api_base_url: str | None = None,
        retry_limit: int | None = None,
    ) -> None:
        """Initialize the SQL Agent.

        Args:
            llm: Language model used by the agent.
            api_base_url: Base URL of the application.
            retry_limit: Maximum SQL self-correction attempts.
        """
        self._retry_limit = (
            retry_limit if retry_limit is not None else settings.sql_retry_limit
        )

        self._api_base_url = api_base_url or settings.api_base_url

        logger.info(
            "Initializing SqlAgent (retry_limit=%d)",
            self._retry_limit,
        )

        sql_tools = SqlTools(
            llm=llm,
            api_base_url=self._api_base_url,
        )

        self.node = create_agent(
            model=llm,
            tools=[
                sql_tools.retrieve_cached_sql,
                sql_tools.retrieve_sql_template,
                sql_tools.generate_sql,
                sql_tools.validate_sql,
                sql_tools.execute_sql,
            ],
            system_prompt=SQL_SYSTEM_PROMPT,
            state_schema=WorkflowState,
            name="sql_agent",
        ).with_config(
            {
                "recursion_limit": self._retry_limit * 5 + 10,
            }
        )

        logger.info("SqlAgent initialized successfully.")

"""
In-memory conversation history service.

This service maintains short-term conversation history for each user session.
The history is stored in memory and is keyed by the session ID.

Responsibilities:
    * Store conversation history for a session.
    * Retrieve conversation history.
    * Append user and assistant messages.
    * Clear history when a session ends.

This service is intended only for short-term memory during application
runtime. Conversation history will be lost when the application restarts.
"""

from __future__ import annotations

from collections import defaultdict

from langchain_core.messages import AIMessage
from langchain_core.messages import BaseMessage
from langchain_core.messages import HumanMessage

from app.config.log_config import config as log_config

logger = log_config.get_logger(__name__)


class ConversationService:
    """Manages in-memory conversation history."""

    def __init__(self) -> None:
        """Initialize the conversation store."""
        self._history: dict[str, list[BaseMessage]] = defaultdict(list)

    def get_history(
        self,
        session_id: str,
    ) -> list[BaseMessage]:
        """Return conversation history for a session.

        Args:
            session_id: Client session identifier.

        Returns:
            List of LangChain messages.
        """
        return list(self._history[session_id])

    def append_user_message(
        self,
        session_id: str,
        message: str,
    ) -> None:
        """Append a user message.

        Args:
            session_id: Client session identifier.
            message: User message.
        """
        logger.info(
            "Appending user message to session '%s'.",
            session_id,
        )

        self._history[session_id].append(HumanMessage(content=message))

    def append_assistant_message(
        self,
        session_id: str,
        message: str,
    ) -> None:
        """Append an assistant message.

        Args:
            session_id: Client session identifier.
            message: Assistant response.
        """
        logger.info(
            "Appending assistant message to session '%s'.",
            session_id,
        )

        self._history[session_id].append(AIMessage(content=message))

    def clear(
        self,
        session_id: str,
    ) -> None:
        """Clear conversation history for a session.

        Args:
            session_id: Client session identifier.
        """
        if session_id in self._history:
            del self._history[session_id]

            logger.info(
                "Conversation history cleared for session '%s'.",
                session_id,
            )

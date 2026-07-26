# app/schemas/intent_schema.py
"""Schemas for the Intent Agent.

The Intent Agent parses a user question and returns structured information
that downstream components (SQL Cache, Template Service, etc.) can act on.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class IntentEnum(str, Enum):
    """Supported intents for the Order Processing Assistant."""

    ORDER_STATUS = "order_status"
    CUSTOMER_ORDERS = "customer_orders"
    PENDING_SHIPMENTS = "pending_shipments"
    DELAYED_SHIPMENTS = "delayed_shipments"
    PRODUCT_LOOKUP = "product_lookup"
    LATEST_ORDER = "latest_order"
    MONTHLY_ORDERS = "monthly_orders"
    TOP_CUSTOMERS = "top_customers"


class IntentResult(BaseModel):
    """Result returned by the Intent Agent.

    Attributes:
        intent: The identified intent (one of :class:`IntentEnum`).
        entities: Mapping of extracted entity names to their values.
        missing_parameters: List of required entities that were not found.
        ready_for_sql: ``True`` when *all* required parameters are present.
        follow_up_question: Optional natural‑language follow‑up to ask the user for
            missing information.
    """

    intent: IntentEnum = Field(..., description="Identified user intent.")
    entities: Dict[str, str] = Field(
        default_factory=dict,
        description="Extracted entity name/value pairs.",
    )
    missing_parameters: List[str] = Field(
        default_factory=list,
        description="Names of required parameters that were not extracted.",
    )
    ready_for_sql: bool = Field(
        ..., description="Indicates whether the intent has all required data."
    )
    follow_up_question: Optional[str] = Field(
        None, description="Natural language question to request missing data."
    )

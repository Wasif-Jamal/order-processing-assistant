"""Order Pydantic schemas.

Defines request and response schemas for order data used throughout the
Order Processing application. These schemas are used to validate order
records during CSV transformation before they are persisted to the database.
"""

from datetime import date

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class OrderSchema(BaseModel):
    """Represents an order record.

    Attributes:
        order_id: Unique identifier for the order.
        order_date: Date the order was placed.
        customer_id: Identifier of the customer who placed the order.
        sales: Total sales amount for the order.
    """

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
        extra="forbid",
    )

    order_id: str = Field(
        ...,
        description="Unique order identifier.",
        max_length=20,
    )

    order_date: date = Field(
        ...,
        description="Date the order was placed.",
    )

    customer_id: str = Field(
        ...,
        description="Customer who placed the order.",
        max_length=20,
    )

    sales: float = Field(
        ...,
        description="Total sales amount for the order.",
        ge=0,
    )

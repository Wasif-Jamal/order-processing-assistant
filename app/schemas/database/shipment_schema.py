"""Shipment Pydantic schemas.

Defines request and response schemas for shipment data used throughout the
Order Processing application. These schemas are used to validate shipment
records during CSV transformation before they are persisted to the database.
"""

from datetime import date

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ShipmentSchema(BaseModel):
    """Represents a shipment record.

    Attributes:
        shipment_id: Unique identifier for the shipment.
        order_id: Identifier of the associated order.
        ship_date: Date the order was shipped.
        ship_mode: Shipping method used for the order.
    """

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
        extra="forbid",
    )

    shipment_id: int | None = Field(
        default=None,
        description="Unique shipment identifier.",
        ge=1,
    )

    order_id: str = Field(
        ...,
        description="Associated order identifier.",
        max_length=20,
    )

    ship_date: date = Field(
        ...,
        description="Date the order was shipped.",
    )

    ship_mode: str = Field(
        ...,
        description="Shipping method used for the order.",
        max_length=50,
    )

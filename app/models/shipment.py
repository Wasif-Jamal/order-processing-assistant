"""Shipment database model.

Defines the Shipment ORM model used by the Order Processing application.
A shipment represents the delivery information associated with an order.
Each order has exactly one shipment.
"""

from datetime import date

from sqlalchemy import Date
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class Shipment(Base):
    """Represents shipment information for an order.

    Attributes:
        shipment_id: Unique identifier for the shipment.
        order_id: Associated order identifier.
        ship_date: Date the order was shipped.
        ship_mode: Shipping method used.
        order: Associated order.
    """

    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        doc="Unique shipment identifier.",
    )

    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False,
        unique=True,
        index=True,
        doc="Associated order identifier.",
    )

    ship_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date the order was shipped.",
    )

    ship_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Shipping method used for the order.",
    )

    order: Mapped["Order"] = relationship(
        back_populates="shipment",
    )

    def __repr__(self) -> str:
        """Return the string representation of the shipment."""
        return f"Shipment(shipment_id={self.shipment_id}, order_id='{self.order_id}')"

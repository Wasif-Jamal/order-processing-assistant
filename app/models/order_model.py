"""Order database model.

Defines the Order ORM model used by the Order Processing application.
An order belongs to a single customer, contains one or more order items,
and has one associated shipment.
"""

from datetime import date

from sqlalchemy import DECIMAL
from sqlalchemy import Date
from sqlalchemy import String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base_model import Base


class Order(Base):
    """Represents a customer order.

    Attributes:
        order_id: Unique identifier for the order.
        order_date: Date the order was placed.
        customer_id: Customer who placed the order.
        customer: Associated customer.
        sales: Total sales amount for the order.
        order_items: Products included in the order.
        shipment: Shipment associated with the order.
    """

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        nullable=False,
        doc="Unique order identifier.",
    )

    order_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        doc="Date the order was placed.",
    )

    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.customer_id"),
        nullable=False,
        index=True,
        doc="Customer who placed the order.",
    )

    sales: Mapped[float] = mapped_column(
        DECIMAL(12, 2),
        nullable=False,
        default=0.0,
        doc="Total sales amount for the order.",
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="orders",
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )

    shipment: Mapped["Shipment"] = relationship(
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return the string representation of the order."""
        return f"Order(order_id='{self.order_id}', customer_id='{self.customer_id}')"

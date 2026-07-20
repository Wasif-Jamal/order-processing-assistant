"""Customer database model.

Defines the Customer ORM model used by the Order Processing application.
A customer can place multiple orders, resulting in a one-to-many
relationship between Customer and Order.
"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.order import Order


class Customer(Base):
    """Represents a customer in the order processing system.

    Attributes:
        customer_id: Unique identifier for the customer.
        customer_name: Full name of the customer.
        segment: Business segment of the customer.
        country: Country where the customer resides.
        city: Customer's city.
        state: Customer's state.
        postal_code: Customer's postal code.
        region: Geographic sales region.
        orders: Orders placed by the customer.
    """

    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        nullable=False,
        doc="Unique customer identifier.",
    )

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Customer's full name.",
    )

    segment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Business segment of the customer.",
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Customer's country.",
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Customer's city.",
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Customer's state.",
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Customer's postal code.",
    )

    region: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Customer's sales region.",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Return the string representation of the customer."""
        return (
            f"Customer("
            f"customer_id='{self.customer_id}', "
            f"customer_name='{self.customer_name}')"
        )

"""Order item database model.

Defines the OrderItem ORM model used by the Order Processing application.
An order item represents a single product purchased within an order and
acts as the junction table between orders and products.
"""

from sqlalchemy import DECIMAL
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base


class OrderItem(Base):
    """Represents a product purchased within an order.

    Attributes:
        order_item_id: Unique identifier for the order item.
        order_id: Identifier of the associated order.
        product_id: Identifier of the purchased product.
        quantity: Number of units purchased.
        sales: Total sales amount for the line item.
        discount: Discount applied to the line item.
        profit: Profit earned from the line item.
        order: Associated order.
        product: Associated product.
    """

    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Unique order item identifier.",
    )

    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.order_id"),
        nullable=False,
        index=True,
        doc="Associated order identifier.",
    )

    product_id: Mapped[str] = mapped_column(
        ForeignKey("products.product_id"),
        nullable=False,
        index=True,
        doc="Associated product identifier.",
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Quantity of the product purchased.",
    )

    sales: Mapped[float] = mapped_column(
        DECIMAL(12, 2),
        nullable=False,
        doc="Total sales amount for this order item.",
    )

    discount: Mapped[float] = mapped_column(
        DECIMAL(5, 2),
        nullable=False,
        default=0.00,
        doc="Discount applied to the order item.",
    )

    profit: Mapped[float] = mapped_column(
        DECIMAL(12, 2),
        nullable=False,
        doc="Profit earned from the order item.",
    )

    order: Mapped["Order"] = relationship(
        back_populates="order_items",
    )

    product: Mapped["Product"] = relationship(
        back_populates="order_items",
    )

    def __repr__(self) -> str:
        """Return the string representation of the order item."""
        return (
            f"OrderItem("
            f"order_item_id={self.order_item_id}, "
            f"order_id='{self.order_id}', "
            f"product_id='{self.product_id}')"
        )

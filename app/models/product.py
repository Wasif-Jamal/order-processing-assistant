"""Product database model.

Defines the Product ORM model used by the Order Processing application.
A product can appear in multiple order items, resulting in a one-to-many
relationship between Product and OrderItem.
"""

from sqlalchemy import DECIMAL
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.models.order_item import OrderItem


class Product(Base):
    """Represents a product in the product catalog.

    Attributes:
        product_id: Unique identifier for the product.
        category: Product category.
        sub_category: Product sub-category.
        product_name: Descriptive name of the product.
        order_items: Order items referencing this product.
    """

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        nullable=False,
        doc="Unique product identifier.",
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Product category.",
    )

    sub_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Product sub-category.",
    )

    product_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Product name.",
    )

    list_price: Mapped[float | None] = mapped_column(
        DECIMAL(10, 2),
        nullable=True,
        doc="Optional product list price.",
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        back_populates="product",
    )

    def __repr__(self) -> str:
        """Return the string representation of the product."""
        return (
            f"Product("
            f"product_id='{self.product_id}', "
            f"product_name='{self.product_name}')"
        )

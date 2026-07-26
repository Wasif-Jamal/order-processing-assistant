"""Order item Pydantic schemas.

Defines request and response schemas for order item data used throughout the
Order Processing application. These schemas are used to validate order item
records during CSV transformation before they are persisted to the database.
"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class OrderItemSchema(BaseModel):
    """Represents an order item record.

    Attributes:
        order_item_id: Unique identifier for the order item.
        order_id: Identifier of the associated order.
        product_id: Identifier of the associated product.
        quantity: Quantity of the product purchased.
        sales: Total sales amount for the order item.
        discount: Discount applied to the order item.
        profit: Profit earned from the order item.
    """

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
        extra="forbid",
    )

    order_item_id: int | None = Field(
        default=None,
        description="Unique order item identifier.",
        ge=1,
    )

    order_id: str = Field(
        ...,
        description="Associated order identifier.",
        max_length=20,
    )

    product_id: str = Field(
        ...,
        description="Associated product identifier.",
        max_length=20,
    )

    quantity: int = Field(
        ...,
        description="Quantity of the product purchased.",
        ge=1,
    )

    sales: float = Field(
        ...,
        description="Total sales amount for the order item.",
        ge=0,
    )

    discount: float = Field(
        ...,
        description="Discount applied to the order item.",
        ge=0,
        le=1,
    )

    profit: float = Field(
        ...,
        description="Profit earned from the order item.",
    )

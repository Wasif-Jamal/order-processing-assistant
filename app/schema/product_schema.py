"""Product Pydantic schemas.

Defines request and response schemas for product data used throughout the
Order Processing application. These schemas are used to validate product
records during CSV transformation before they are persisted to the database.
"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class ProductSchema(BaseModel):
    """Represents a product record.

    Attributes:
        product_id: Unique identifier for the product.
        category: Product category.
        sub_category: Product sub-category.
        product_name: Product name.
        list_price: Optional list price of the product.
    """

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
        extra="forbid",
    )

    product_id: str = Field(
        ...,
        description="Unique product identifier.",
        max_length=20,
    )

    category: str = Field(
        ...,
        description="Product category.",
        max_length=50,
    )

    sub_category: str = Field(
        ...,
        description="Product sub-category.",
        max_length=50,
    )

    product_name: str = Field(
        ...,
        description="Product name.",
        max_length=255,
    )

    list_price: float | None = Field(
        default=None,
        description="Optional list price of the product.",
        ge=0,
    )

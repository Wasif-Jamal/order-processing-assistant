"""Customer Pydantic schemas.

Defines request and response schemas for customer data used throughout the
Order Processing application. These schemas are used to validate customer
records during CSV transformation before they are persisted to the database.
"""

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class CustomerSchema(BaseModel):
    """Represents a customer record.

    Attributes:
        customer_id: Unique identifier for the customer.
        customer_name: Full name of the customer.
        segment: Customer segment.
        country: Customer country.
        city: Customer city.
        state: Customer state.
        postal_code: Customer postal code.
        region: Sales region.
    """

    model_config = ConfigDict(
        from_attributes=True,
        frozen=True,
        extra="forbid",
    )

    customer_id: str = Field(
        ...,
        description="Unique customer identifier.",
        max_length=20,
    )

    customer_name: str = Field(
        ...,
        description="Customer's full name.",
        max_length=100,
    )

    segment: str = Field(
        ...,
        description="Customer segment.",
        max_length=50,
    )

    country: str = Field(
        ...,
        description="Customer country.",
        max_length=100,
    )

    city: str = Field(
        ...,
        description="Customer city.",
        max_length=100,
    )

    state: str = Field(
        ...,
        description="Customer state.",
        max_length=100,
    )

    postal_code: str = Field(
        ...,
        description="Customer postal code.",
        max_length=20,
    )

    region: str = Field(
        ...,
        description="Sales region.",
        max_length=50,
    )

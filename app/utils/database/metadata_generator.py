"""Database schema metadata generator.

Automatically generates KnowledgeBaseSchema metadata objects by inspecting
SQLAlchemy ORM models and tables.
"""

from typing import Type

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase

from app.config.log_config import config
from app.models import Customer
from app.models import Order
from app.models import OrderItem
from app.models import Product
from app.models import Shipment
from app.models import SQLTemplate
from app.schemas.knowledge_base_schema import ColumnMetadata
from app.schemas.knowledge_base_schema import ForeignKeyMetadata
from app.schemas.knowledge_base_schema import KnowledgeBaseSchema

logger = config.get_logger(__name__)


class MetadataGenerator:
    """Generates KnowledgeBaseSchema metadata from SQLAlchemy models."""

    DEFAULT_SAMPLE_QUESTIONS: dict[str, list[str]] = {
        "customers": [
            "Find customer details by customer ID or name.",
            "Which segment or region does a customer belong to?",
            "List customers located in a specific city or state.",
        ],
        "orders": [
            "How many orders were placed in a specific date range?",
            "Find all orders placed by a specific customer.",
            "What is the total sales amount for orders in a region?",
        ],
        "order_items": [
            "What products were included in order ID?",
            "Calculate total quantity, discount, and profit for an order item.",
            "Find top items contributing to order revenue.",
        ],
        "products": [
            "Find product details by product ID or name.",
            "List products by category and sub-category.",
            "Which products generated the highest sales?",
        ],
        "shipments": [
            "Track shipment details and shipping mode for an order.",
            "When was an order shipped?",
            "Find orders shipped using a specific ship mode.",
        ],
        "sql_templates": [
            "Find pre-defined SQL query templates for business intent.",
            "Retrieve active validated SQL templates.",
        ],
    }

    MODEL_CLASSES: list[Type[DeclarativeBase]] = [
        Customer,
        Order,
        OrderItem,
        Product,
        Shipment,
        SQLTemplate,
    ]

    def generate_all_metadata(self) -> list[KnowledgeBaseSchema]:
        """Generate metadata objects for all registered application models.

        Returns:
            List of KnowledgeBaseSchema instances.
        """
        logger.info("Generating schema metadata for all SQLAlchemy models.")
        schemas = []
        for model in self.MODEL_CLASSES:
            schema = self.generate_table_metadata(model)
            schemas.append(schema)
        return schemas

    def generate_table_metadata(
        self,
        model: Type[DeclarativeBase],
    ) -> KnowledgeBaseSchema:
        """Generate metadata for a single SQLAlchemy ORM model.

        Args:
            model: Declarative SQLAlchemy model class.

        Returns:
            KnowledgeBaseSchema instance.
        """
        table_name = str(model.__tablename__)
        docstring = (model.__doc__ or "").strip().split("\n\n")[0]

        columns: list[ColumnMetadata] = []
        primary_keys: list[str] = []
        foreign_keys: list[ForeignKeyMetadata] = []

        mapper = inspect(model)

        for column in mapper.columns:
            col_name = column.name
            col_type = str(column.type)
            col_doc = (
                getattr(column, "doc", None) or getattr(column, "comment", None) or ""
            )

            is_pk = column.primary_key
            if is_pk:
                primary_keys.append(col_name)

            is_fk = len(column.foreign_keys) > 0
            fk_target_str = None

            if is_fk:
                for fk in column.foreign_keys:
                    target_table = fk.column.table.name
                    target_col = fk.column.name
                    fk_target_str = f"{target_table}.{target_col}"
                    foreign_keys.append(
                        ForeignKeyMetadata(
                            column=col_name,
                            target_table=target_table,
                            target_column=target_col,
                        )
                    )

            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=col_type,
                    description=col_doc,
                    is_primary_key=is_pk,
                    is_foreign_key=is_fk,
                    foreign_key_target=fk_target_str,
                )
            )

        sample_questions = self.DEFAULT_SAMPLE_QUESTIONS.get(table_name, [])

        return KnowledgeBaseSchema(
            table_name=table_name,
            description=docstring,
            columns=columns,
            primary_keys=primary_keys,
            foreign_keys=foreign_keys,
            sample_questions=sample_questions,
        )

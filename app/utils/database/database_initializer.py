"""Database initialization and one-time CSV loading.

Creates the database schema using the SQLAlchemy models and populates the
database from the Superstore CSV file exactly once. If the database has
already been seeded, the initialization process skips data loading.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import inspect
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.config.db_config import database
from app.config.env_config import settings
from app.config.log_config import config
from app.models import Customer
from app.models import Order
from app.models import OrderItem
from app.models import Product
from app.models import Shipment
from app.models.base import Base
from app.utils.database.validators import CSVValidator

logger = config.get_logger(__name__)


class DatabaseInitializer:
    """Initializes and seeds the application database.

    This class is responsible for:

    - Creating all database tables.
    - Loading the Superstore CSV.
    - Normalizing the dataset.
    - Validating records using Pydantic schemas.
    - Inserting records into the database.
    - Ensuring initialization only happens once.
    """

    def __init__(
        self,
        engine: Engine = database.engine,
    ) -> None:
        """Initialize the database initializer.

        Args:
            engine: SQLAlchemy database engine.
        """
        self._engine = engine

        self._session_factory = sessionmaker(
            bind=self._engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def initialize(self) -> None:
        """Initialize the database.

        This method is safe to call multiple times. It creates the database
        schema if necessary and loads the CSV only when the database has not
        already been seeded.
        """
        logger.info("Starting database initialization.")

        self._create_tables()

        if self._database_seeded():
            logger.info("Database already contains data. Skipping CSV import.")
            return

        with self._session_factory() as session:
            dataframe = self._read_csv()
            validator = CSVValidator()

            if not validator.validate(dataframe):
                raise ValueError("CSV validation failed.")
            self._load_csv(session, dataframe)

        logger.info("Database initialization completed successfully.")

    def _create_tables(self) -> None:
        """Create all database tables.

        SQLAlchemy creates only tables that do not already exist.
        """
        logger.info("Creating database tables if required.")

        Base.metadata.create_all(self._engine)

        logger.info("Database schema verified.")

    def _database_seeded(self) -> bool:
        """Determine whether the database has already been seeded.

        Returns:
            True if customer records already exist; otherwise False.
        """
        inspector = inspect(self._engine)

        if not inspector.has_table(Customer.__tablename__):
            return False

        with self._session_factory() as session:
            return session.scalar(select(Customer.customer_id).limit(1)) is not None

    def _read_csv(self) -> pd.DataFrame:
        """Read the Superstore CSV file.

        Returns:
            Loaded CSV as a Pandas DataFrame.

        Raises:
            FileNotFoundError:
                If the configured CSV file cannot be found.
        """
        csv_path = Path(settings.csv_path)

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: '{csv_path}'.")

        logger.info("Loading CSV from '%s'.", csv_path)

        dataframe = pd.read_csv(
            csv_path,
            dtype={"Postal Code": str},
            encoding="latin-1",
        )

        dataframe["Order Date"] = pd.to_datetime(
            dataframe["Order Date"],
            format="%m/%d/%Y",
        ).dt.date

        dataframe["Ship Date"] = pd.to_datetime(
            dataframe["Ship Date"],
            format="%m/%d/%Y",
        ).dt.date

        logger.info(
            "Successfully loaded %d rows.",
            len(dataframe),
        )

        return dataframe

    def _load_csv(
        self,
        session: Session,
        dataframe: pd.DataFrame,
    ) -> None:
        """Normalize and load the Superstore dataset.

        Args:
            session: Active SQLAlchemy session.
            dataframe: Source Superstore dataset.
        """
        self._load_customers(session, dataframe)
        self._load_products(session, dataframe)
        self._load_orders(session, dataframe)
        self._load_order_items(session, dataframe)
        self._load_shipments(session, dataframe)

        session.commit()

        logger.info("Database seeded successfully.")

    def _load_customers(
        self,
        session: Session,
        dataframe: pd.DataFrame,
    ) -> None:
        """Load customer records into the database.

        Args:
            session: Active SQLAlchemy session.
            dataframe: Source Superstore dataset.
        """
        logger.info("Loading customers.")

        customers = (
            dataframe[
                [
                    "Customer ID",
                    "Customer Name",
                    "Segment",
                    "Country",
                    "City",
                    "State",
                    "Postal Code",
                    "Region",
                ]
            ]
            .drop_duplicates(subset="Customer ID")
            .rename(
                columns={
                    "Customer ID": "customer_id",
                    "Customer Name": "customer_name",
                    "Segment": "segment",
                    "Country": "country",
                    "City": "city",
                    "State": "state",
                    "Postal Code": "postal_code",
                    "Region": "region",
                }
            )
        )

        customer_records = customers.to_dict("records")

        session.bulk_insert_mappings(
            Customer,
            customer_records,
        )

        logger.info(
            "Inserted %d customers.",
            len(customer_records),
        )

    def _load_products(
        self,
        session: Session,
        dataframe: pd.DataFrame,
    ) -> None:
        """Load product records into the database.

        Args:
            session: Active SQLAlchemy session.
            dataframe: Source Superstore dataset.
        """
        logger.info("Loading products.")

        products = (
            dataframe[
                [
                    "Product ID",
                    "Category",
                    "Sub-Category",
                    "Product Name",
                ]
            ]
            .drop_duplicates(subset="Product ID")
            .rename(
                columns={
                    "Product ID": "product_id",
                    "Category": "category",
                    "Sub-Category": "sub_category",
                    "Product Name": "product_name",
                }
            )
        )

        products["list_price"] = None

        product_records = products.to_dict("records")

        session.bulk_insert_mappings(
            Product,
            product_records,
        )

        logger.info(
            "Inserted %d products.",
            len(product_records),
        )

    def _load_orders(
        self,
        session: Session,
        dataframe: pd.DataFrame,
    ) -> None:
        """Load order records into the database.

        Args:
            session: Active SQLAlchemy session.
            dataframe: Source Superstore dataset.
        """
        logger.info("Loading orders.")

        orders = (
            dataframe.groupby("Order ID", as_index=False)
            .agg(
                {
                    "Order Date": "first",
                    "Customer ID": "first",
                    "Sales": "sum",
                }
            )
            .rename(
                columns={
                    "Order ID": "order_id",
                    "Order Date": "order_date",
                    "Customer ID": "customer_id",
                    "Sales": "sales",
                }
            )
        )

        order_records = orders.to_dict("records")

        session.bulk_insert_mappings(
            Order,
            order_records,
        )

        logger.info(
            "Inserted %d orders.",
            len(order_records),
        )

    def _load_order_items(
        self,
        session: Session,
        dataframe: pd.DataFrame,
    ) -> None:
        """Load order item records into the database.

        Args:
            session: Active SQLAlchemy session.
            dataframe: Source Superstore dataset.
        """
        logger.info("Loading order items.")

        order_items = dataframe[
            [
                "Order ID",
                "Product ID",
                "Quantity",
                "Sales",
                "Discount",
                "Profit",
            ]
        ].rename(
            columns={
                "Order ID": "order_id",
                "Product ID": "product_id",
                "Quantity": "quantity",
                "Sales": "sales",
                "Discount": "discount",
                "Profit": "profit",
            }
        )

        order_item_records = order_items.to_dict("records")

        session.bulk_insert_mappings(
            OrderItem,
            order_item_records,
        )

        logger.info(
            "Inserted %d order items.",
            len(order_item_records),
        )

    def _load_shipments(
        self,
        session: Session,
        dataframe: pd.DataFrame,
    ) -> None:
        """Load shipment records into the database.

        Args:
            session: Active SQLAlchemy session.
            dataframe: Source Superstore dataset.
        """
        logger.info("Loading shipments.")

        shipments = (
            dataframe[
                [
                    "Order ID",
                    "Ship Date",
                    "Ship Mode",
                ]
            ]
            .drop_duplicates(subset="Order ID")
            .rename(
                columns={
                    "Order ID": "order_id",
                    "Ship Date": "ship_date",
                    "Ship Mode": "ship_mode",
                }
            )
        )

        shipment_records = shipments.to_dict("records")

        session.bulk_insert_mappings(
            Shipment,
            shipment_records,
        )

        logger.info(
            "Inserted %d shipments.",
            len(shipment_records),
        )

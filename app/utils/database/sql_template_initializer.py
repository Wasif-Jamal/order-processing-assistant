"""SQL template startup initializer.

Seeds predefined curated SELECT SQL templates into SQL Server and Qdrant vector DB
on application startup. Idempotent: skips seeding if templates are already present.
"""

from app.config.db_config import DatabaseConfig
from app.config.db_config import database
from app.config.log_config import config
from app.models.sql_template_model import SQLTemplate
from app.repository.sql_template_repository import SQLTemplateRepository
from app.services.qdrant_service import QdrantService
from app.services.sql_template_service import SQLTemplateService

logger = config.get_logger(__name__)


class SQLTemplateInitializer:
    """Initializes predefined SELECT SQL templates into SQL Server and Qdrant."""

    PREDEFINED_TEMPLATES = [
        {
            "name": "orders_by_customer",
            "business_intent": "Get all orders placed by a specific customer",
            "description": "Retrieves all order records matching a given customer ID.",
            "natural_language_examples": "Find orders for customer CUST-100; Show all orders placed by customer; Retrieve order history for a customer",
            "sql_query": "SELECT order_id, order_date, customer_id, sales FROM orders WHERE customer_id = :customer_id ORDER BY order_date DESC;",
            "sql_explanation": "Queries orders table filtering by customer_id.",
            "parameters": "customer_id",
        },
        {
            "name": "order_details",
            "business_intent": "Get detailed breakdown of items in a specific order",
            "description": "Retrieves order headers, customer info, and order line items for an order ID.",
            "natural_language_examples": "Show order details for order ID 1001; Get line items and product details for an order; What products were in order 1002?",
            "sql_query": "SELECT o.order_id, o.order_date, c.customer_name, i.product_id, i.quantity, i.sales, i.discount, i.profit FROM orders o JOIN customers c ON o.customer_id = c.customer_id JOIN order_items i ON o.order_id = i.order_id WHERE o.order_id = :order_id;",
            "sql_explanation": "Joins orders, customers, and order_items to return detailed itemized order breakdown.",
            "parameters": "order_id",
        },
        {
            "name": "pending_shipments",
            "business_intent": "List all orders pending shipment",
            "description": "Finds all shipments that have not yet been shipped (ship_date is NULL).",
            "natural_language_examples": "Show pending shipments; List unshipped orders; Which orders have not been shipped yet?",
            "sql_query": "SELECT shipment_id, order_id, ship_mode FROM shipments WHERE ship_date IS NULL;",
            "sql_explanation": "Queries shipments table for records with NULL ship_date.",
            "parameters": None,
        },
        {
            "name": "delayed_shipments",
            "business_intent": "Identify shipments that took longer than expected to ship",
            "description": "Finds shipments where the difference between ship date and order date exceeds 5 days.",
            "natural_language_examples": "Show delayed shipments; Which orders took more than 5 days to ship?; Find late shipments",
            "sql_query": "SELECT s.shipment_id, s.order_id, s.ship_date, o.order_date, DATEDIFF(day, o.order_date, s.ship_date) AS days_to_ship FROM shipments s JOIN orders o ON s.order_id = o.order_id WHERE DATEDIFF(day, o.order_date, s.ship_date) > 5;",
            "sql_explanation": "Calculates days between order_date and ship_date and filters for delays greater than 5 days.",
            "parameters": None,
        },
        {
            "name": "latest_orders",
            "business_intent": "Retrieve the most recent orders placed in the system",
            "description": "Returns the top 10 most recent orders sorted by order date descending.",
            "natural_language_examples": "Show recent orders; List the top 10 latest orders; Find recent order transactions",
            "sql_query": "SELECT TOP 10 order_id, order_date, customer_id, sales FROM orders ORDER BY order_date DESC;",
            "sql_explanation": "Retrieves top 10 most recent order rows ordered by order_date descending.",
            "parameters": None,
        },
        {
            "name": "top_customers",
            "business_intent": "Identify highest spending customers",
            "description": "Returns top 10 customers sorted by cumulative sales amount.",
            "natural_language_examples": "Who are our top spending customers?; Show top 10 customers by revenue; List highest value customers",
            "sql_query": "SELECT TOP 10 c.customer_id, c.customer_name, SUM(o.sales) AS total_sales FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name ORDER BY total_sales DESC;",
            "sql_explanation": "Groups orders by customer and orders descending by total sum of sales.",
            "parameters": None,
        },
        {
            "name": "monthly_orders",
            "business_intent": "Summarize monthly order volumes and total revenue",
            "description": "Groups order records by year and month to display aggregate revenue and order counts.",
            "natural_language_examples": "Show monthly sales summary; Give me monthly order breakdown; What were monthly order volumes and totals?",
            "sql_query": "SELECT YEAR(order_date) AS order_year, MONTH(order_date) AS order_month, COUNT(order_id) AS total_orders, SUM(sales) AS total_sales FROM orders GROUP BY YEAR(order_date), MONTH(order_date) ORDER BY order_year DESC, order_month DESC;",
            "sql_explanation": "Aggregates orders by year and month returning counts and total sales sum.",
            "parameters": None,
        },
        {
            "name": "frequently_ordered_products",
            "business_intent": "Find most popular products by quantity sold",
            "description": "Returns top 10 products aggregated by sum of quantity ordered.",
            "natural_language_examples": "What are the most popular products?; List top 10 products by quantity sold; Which items are ordered most frequently?",
            "sql_query": "SELECT TOP 10 p.product_id, p.product_name, p.category, SUM(i.quantity) AS total_quantity FROM products p JOIN order_items i ON p.product_id = i.product_id GROUP BY p.product_id, p.product_name, p.category ORDER BY total_quantity DESC;",
            "sql_explanation": "Joins products and order_items, summing quantity ordered per product.",
            "parameters": None,
        },
        {
            "name": "orders_above_amount",
            "business_intent": "Filter high-value orders exceeding a specified dollar threshold",
            "description": "Returns orders with total sales greater than the specified minimum amount.",
            "natural_language_examples": "Find orders with sales over $1000; List high value orders above minimum amount; Show orders exceeding 500",
            "sql_query": "SELECT order_id, order_date, customer_id, sales FROM orders WHERE sales > :min_amount ORDER BY sales DESC;",
            "sql_explanation": "Filters orders table where total sales exceeds min_amount parameter.",
            "parameters": "min_amount",
        },
        {
            "name": "shipments_this_week",
            "business_intent": "List orders shipped in the past 7 days",
            "description": "Returns all shipments where ship_date is within the past 7 days.",
            "natural_language_examples": "Show shipments dispatched this week; List recent shipments from last 7 days; Find orders shipped this week",
            "sql_query": "SELECT s.shipment_id, s.order_id, s.ship_date, s.ship_mode FROM shipments s WHERE s.ship_date >= DATEADD(day, -7, GETDATE()) ORDER BY s.ship_date DESC;",
            "sql_explanation": "Filters shipments where ship_date is greater than or equal to current date minus 7 days.",
            "parameters": None,
        },
    ]

    def __init__(
        self,
        qdrant_service: QdrantService | None = None,
        sql_template_service: SQLTemplateService | None = None,
        sql_template_repository: SQLTemplateRepository | None = None,
        db_config: DatabaseConfig = database,
    ) -> None:
        """Initialize the SQL template initializer.

        Args:
            qdrant_service: Qdrant vector database service.
            sql_template_service: SQL template service.
            sql_template_repository: SQL template repository.
            db_config: Database configuration singleton.
        """
        self._qdrant_service = qdrant_service or QdrantService()
        self._repository = sql_template_repository or SQLTemplateRepository()
        self._template_service = sql_template_service or SQLTemplateService(
            qdrant_service=self._qdrant_service,
            sql_template_repository=self._repository,
            db_config=db_config,
        )
        self._db_config = db_config

    def initialize(self) -> None:
        """Initialize and seed predefined SELECT SQL templates into SQL Server and Qdrant.

        Safe to call multiple times. Skips seeding if templates already exist.
        """
        logger.info("Starting SQL Template initialization.")

        self._qdrant_service.ensure_collection_exists(
            QdrantService.SQL_TEMPLATES_COLLECTION
        )

        with self._db_config.get_session() as session:
            existing_templates = self._repository.get_all(session, active_only=False)
            if len(existing_templates) > 0:
                logger.info(
                    "SQL templates table already contains %d templates. Skipping initialization.",
                    len(existing_templates),
                )
                return

            logger.info(
                "Seeding %d predefined SELECT SQL templates into SQL Server and Qdrant.",
                len(self.PREDEFINED_TEMPLATES),
            )

            for t_data in self.PREDEFINED_TEMPLATES:
                template_model = SQLTemplate(
                    name=t_data["name"],
                    business_intent=t_data["business_intent"],
                    description=t_data["description"],
                    natural_language_examples=t_data["natural_language_examples"],
                    sql_query=t_data["sql_query"],
                    sql_explanation=t_data["sql_explanation"],
                    parameters=t_data.get("parameters"),
                    is_active=True,
                )

                created = self._repository.create(session, template_model)

                search_text = (
                    f"{created.business_intent}. "
                    f"{created.description}. "
                    f"Examples: {created.natural_language_examples}"
                )

                self._template_service.index_template_vector(
                    template_id=created.template_id,
                    search_text=search_text,
                    template_name=created.name,
                )

            logger.info("SQL Template initialization completed successfully.")

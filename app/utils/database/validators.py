"""CSV validation utilities.

Validates the structure of the Superstore CSV before it is loaded into the
database. The validator ensures that all required columns are present and that
the CSV contains data. This validation is performed once during application
startup before the database is seeded.
"""

from pandas import DataFrame

from app.config.log_config import config

logger = config.get_logger(__name__)


class CSVValidator:
    """Validates the Superstore CSV dataset."""

    REQUIRED_COLUMNS = {
        "Row ID",
        "Order ID",
        "Order Date",
        "Ship Date",
        "Ship Mode",
        "Customer ID",
        "Customer Name",
        "Segment",
        "Country",
        "City",
        "State",
        "Postal Code",
        "Region",
        "Product ID",
        "Category",
        "Sub-Category",
        "Product Name",
        "Sales",
        "Quantity",
        "Discount",
        "Profit",
    }

    def validate(self, dataframe: DataFrame) -> bool:
        """Validate the Superstore dataset.

        Validation checks:

        - The CSV is not empty.
        - All required columns exist.

        Args:
            dataframe: Loaded CSV data.

        Returns:
            True if the dataset is valid; otherwise False.
        """
        if dataframe.empty:
            logger.error("CSV validation failed: dataset is empty.")
            return False

        missing_columns = self.REQUIRED_COLUMNS.difference(dataframe.columns)

        if missing_columns:
            logger.error(
                "CSV validation failed. Missing columns: %s",
                sorted(missing_columns),
            )
            return False

        logger.info("CSV validation completed successfully.")

        return True

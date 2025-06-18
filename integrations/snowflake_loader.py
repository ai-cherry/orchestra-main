"""Snowflake data loader for Orchestra AI."""

import pandas as pd
import snowflake.connector
import structlog

from security.enhanced_secret_manager import secret_manager

logger = structlog.get_logger(__name__)

class SnowflakeLoader:
    """Utility class for loading data into Snowflake."""

    def __init__(self):
        self.account = secret_manager.get_secret("SNOWFLAKE_ACCOUNT")
        self.user = secret_manager.get_secret("SNOWFLAKE_USER")
        self.password = secret_manager.get_secret("SNOWFLAKE_PASSWORD")
        self.database = secret_manager.get_secret("SNOWFLAKE_DATABASE")
        self.schema = secret_manager.get_secret("SNOWFLAKE_SCHEMA", "PUBLIC")
        self.warehouse = secret_manager.get_secret("SNOWFLAKE_WAREHOUSE")
        self.conn = None

    def connect(self) -> None:
        """Establish connection to Snowflake."""
        try:
            self.conn = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                database=self.database,
                schema=self.schema,
                warehouse=self.warehouse,
            )
            logger.info("Connected to Snowflake", account=self.account)
        except Exception as exc:
            logger.error("Failed to connect to Snowflake", error=str(exc))
            raise

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            logger.info("Snowflake connection closed")

    def load_csv(self, table_name: str, csv_path: str) -> None:
        """Load a CSV file into a Snowflake table."""
        if not self.conn:
            raise RuntimeError("Snowflake connection not initialized")
        try:
            df = pd.read_csv(csv_path)
            columns = ",".join(df.columns)
            placeholder = ",".join(["%s"] * len(df.columns))

            cur = self.conn.cursor()
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (" +
                ",".join(f'{col} VARCHAR' for col in df.columns) + ")"
            )
            for _, row in df.iterrows():
                cur.execute(
                    f"INSERT INTO {table_name} ({columns}) VALUES ({placeholder})",
                    tuple(row.astype(str))
                )
            logger.info("Loaded CSV", table=table_name, rows=len(df))
        except Exception as exc:
            logger.error("Failed to load CSV", error=str(exc))
            raise

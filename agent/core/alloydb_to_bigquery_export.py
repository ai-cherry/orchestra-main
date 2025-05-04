"""
AlloyDB to BigQuery Export Script

This script performs hourly incremental exports of data from AlloyDB to BigQuery
for the AGI Baby Cherry project. It extracts data updated in the last hour from
the AlloyDB 'memories' table, saves it as Parquet files in Cloud Storage, and
loads it into BigQuery for analytical purposes, establishing a Single Source of Truth (SSOT).
"""

import os
import logging
import datetime
import subprocess
import psycopg2
import pandas as pd
from google.cloud import storage
from google.cloud import bigquery
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlloyDBToBigQueryExporter:
    """
    Class to handle incremental data export from AlloyDB to BigQuery.
    """
    def __init__(
        self,
        alloydb_host: str = "localhost",
        alloydb_port: int = 5432,
        alloydb_dbname: str = "agi_baby_cherry",
        alloydb_user: str = "postgres",
        alloydb_password: str = "",
        gcp_project_id: str = "agi-baby-cherry",
        gcs_bucket: str = "agi-baby-cherry-bucket",
        gcs_path: str = "backups",
        bq_dataset: str = "agent_truth",
        bq_table: str = "memories"
    ):
        """
        Initialize the exporter with connection and configuration parameters.
        
        Args:
            alloydb_host: Hostname of the AlloyDB server.
            alloydb_port: Port of the AlloyDB server.
            alloydb_dbname: Database name in AlloyDB.
            alloydb_user: Username for AlloyDB connection.
            alloydb_password: Password for AlloyDB connection.
            gcp_project_id: Google Cloud Project ID.
            gcs_bucket: Google Cloud Storage bucket for temporary storage.
            gcs_path: Path in GCS bucket to store Parquet files.
            bq_dataset: BigQuery dataset for SSOT.
            bq_table: BigQuery table for SSOT data.
        """
        self.alloydb_host = alloydb_host
        self.alloydb_port = alloydb_port
        self.alloydb_dbname = alloydb_dbname
        self.alloydb_user = alloydb_user
        self.alloydb_password = alloydb_password
        self.gcp_project_id = gcp_project_id
        self.gcs_bucket = gcs_bucket
        self.gcs_path = gcs_path
        self.bq_dataset = bq_dataset
        self.bq_table = bq_table
        self.alloydb_conn = None
        self.storage_client = None
        self.bq_client = None
        
    def connect(self) -> None:
        """
        Establish connections to AlloyDB, Google Cloud Storage, and BigQuery.
        """
        try:
            self.alloydb_conn = psycopg2.connect(
                host=self.alloydb_host,
                port=self.alloydb_port,
                dbname=self.alloydb_dbname,
                user=self.alloydb_user,
                password=self.alloydb_password,
                cursor_factory=RealDictCursor
            )
            self.alloydb_conn.autocommit = True
            logger.info("Connected to AlloyDB successfully.")
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to AlloyDB: {e}")
            raise
            
        try:
            self.storage_client = storage.Client(project=self.gcp_project_id)
            logger.info("Initialized Google Cloud Storage client.")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise
            
        try:
            self.bq_client = bigquery.Client(project=self.gcp_project_id)
            logger.info("Initialized BigQuery client.")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise
            
    def disconnect(self) -> None:
        """
        Close connections to AlloyDB.
        """
        if self.alloydb_conn:
            self.alloydb_conn.close()
            logger.info("Disconnected from AlloyDB.")
            
    def export_incremental_data(self, hours: int = 1) -> str:
        """
        Export data updated in the last specified number of hours from AlloyDB to Parquet file.
        
        Args:
            hours: Number of hours to look back for updated data.
            
        Returns:
            Path to the temporary Parquet file.
        """
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        query = """
            SELECT id, vector, data, version, checksum, created_at, updated_at
            FROM memories
            WHERE updated_at > %s
        """
        try:
            with self.alloydb_conn.cursor() as cur:
                cur.execute(query, (cutoff_time,))
                rows = cur.fetchall()
                if not rows:
                    logger.info("No new data to export.")
                    return ""
                
                df = pd.DataFrame(rows)
                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                temp_file = f"/tmp/memories_export_{timestamp}.parquet"
                df.to_parquet(temp_file, engine='pyarrow', index=False)
                logger.info(f"Exported {len(rows)} records to {temp_file}.")
                return temp_file
        except Exception as e:
            logger.error(f"Error exporting data from AlloyDB: {e}")
            raise
            
    def upload_to_gcs(self, local_file: str) -> str:
        """
        Upload the Parquet file to Google Cloud Storage.
        
        Args:
            local_file: Path to the local Parquet file.
            
        Returns:
            GCS URI of the uploaded file.
        """
        if not local_file:
            return ""
            
        bucket = self.storage_client.bucket(self.gcs_bucket)
        filename = os.path.basename(local_file)
        gcs_uri = f"{self.gcs_path}/{filename}"
        blob = bucket.blob(gcs_uri)
        
        try:
            blob.upload_from_filename(local_file)
            full_gcs_uri = f"gs://{self.gcs_bucket}/{gcs_uri}"
            logger.info(f"Uploaded {local_file} to {full_gcs_uri}.")
            return full_gcs_uri
        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            raise
        finally:
            # Clean up local file
            if os.path.exists(local_file):
                os.remove(local_file)
                logger.info(f"Removed temporary file {local_file}.")
                
    def load_to_bigquery(self, gcs_uri: str) -> None:
        """
        Load data from GCS Parquet file to BigQuery table.
        
        Args:
            gcs_uri: GCS URI of the Parquet file to load.
        """
        if not gcs_uri:
            logger.info("No GCS URI provided, skipping BigQuery load.")
            return
            
        table_id = f"{self.gcp_project_id}.{self.bq_dataset}.{self.bq_table}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True
        )
        
        try:
            load_job = self.bq_client.load_table_from_uri(
                gcs_uri, table_id, job_config=job_config
            )
            load_job.result()  # Wait for the job to complete
            logger.info(f"Loaded {load_job.output_rows} rows into {table_id}.")
        except Exception as e:
            logger.error(f"Error loading data to BigQuery: {e}")
            raise
            
    def run_export_cycle(self) -> None:
        """
        Run a complete export cycle: extract from AlloyDB, upload to GCS, load to BigQuery.
        """
        logger.info("Starting AlloyDB to BigQuery export cycle.")
        self.connect()
        try:
            local_file = self.export_incremental_data(hours=1)
            if local_file:
                gcs_uri = self.upload_to_gcs(local_file)
                self.load_to_bigquery(gcs_uri)
            else:
                logger.info("No data to export in this cycle.")
        finally:
            self.disconnect()
        logger.info("Completed AlloyDB to BigQuery export cycle.")

if __name__ == "__main__":
    # Load configuration from environment variables or defaults
    exporter = AlloyDBToBigQueryExporter(
        alloydb_host=os.getenv("ALLOYDB_HOST", "localhost"),
        alloydb_port=int(os.getenv("ALLOYDB_PORT", "5432")),
        alloydb_dbname=os.getenv("ALLOYDB_DBNAME", "agi_baby_cherry"),
        alloydb_user=os.getenv("ALLOYDB_USER", "postgres"),
        alloydb_password=os.getenv("ALLOYDB_PASSWORD", ""),
        gcp_project_id=os.getenv("GCP_PROJECT_ID", "agi-baby-cherry"),
        gcs_bucket=os.getenv("GCS_BUCKET", "agi-baby-cherry-bucket"),
        gcs_path=os.getenv("GCS_PATH", "backups"),
        bq_dataset=os.getenv("BQ_DATASET", "agent_truth"),
        bq_table=os.getenv("BQ_TABLE", "memories")
    )
    
    # Run the export cycle
    exporter.run_export_cycle()
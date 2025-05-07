-- BigQuery SSOT Validation Script for AGI Baby Cherry Project
-- This script defines a stored procedure to validate data consistency
-- between BigQuery dataset (agent_truth.memories) and Cloud Storage backups.

-- Create or replace the stored procedure for SSOT validation
CREATE OR REPLACE PROCEDURE `cherry-ai-project.agent_truth.validate_ssot`(
  gcs_uri STRING,
  bq_table STRING
)
BEGIN
  DECLARE row_count_bq INT64;
  DECLARE row_count_gcs INT64;
  DECLARE checksum_mismatch_count INT64;
  DECLARE validation_result STRING;

  -- Count rows in BigQuery table
  EXECUTE IMMEDIATE
    FORMAT('SELECT COUNT(*) FROM `%s`', bq_table)
  INTO row_count_bq;

  -- Load GCS Parquet files into a temporary table for comparison
  CREATE OR REPLACE TEMP TABLE temp_gcs_data AS
  SELECT *
  FROM EXTERNAL_QUERY(
    'SELECT * FROM PARQUET_FILES',
    FORMAT('SELECT * FROM read_parquet("%s")', gcs_uri)
  );

  -- Count rows in GCS data
  SELECT COUNT(*) INTO row_count_gcs FROM temp_gcs_data;

  -- Check for checksum mismatches between BigQuery and GCS data
  SET checksum_mismatch_count = (
    SELECT COUNT(*)
    FROM (
      SELECT id, checksum
      FROM `cherry-ai-project.agent_truth.memories`
    ) bq
    FULL OUTER JOIN (
      SELECT id, checksum
      FROM temp_gcs_data
    ) gcs
    ON bq.id = gcs.id
    WHERE bq.checksum != gcs.checksum OR bq.checksum IS NULL OR gcs.checksum IS NULL
  );

  -- Determine validation result
  IF row_count_bq = row_count_gcs AND checksum_mismatch_count = 0 THEN
    SET validation_result = 'SUCCESS: Data is consistent between BigQuery and GCS.';
  ELSE
    SET validation_result = FORMAT(
      'FAILURE: Data inconsistency detected. BigQuery rows: %d, GCS rows: %d, Checksum mismatches: %d',
      row_count_bq, row_count_gcs, checksum_mismatch_count
    );
  END IF;

  -- Log the validation result to a monitoring table
  INSERT INTO `cherry-ai-project.agent_truth.validation_log` (
    validation_time,
    result,
    bq_row_count,
    gcs_row_count,
    checksum_mismatches
  )
  VALUES (
    CURRENT_TIMESTAMP(),
    validation_result,
    row_count_bq,
    row_count_gcs,
    checksum_mismatch_count
  );

  -- Output the result for visibility
  SELECT validation_result AS validation_message;
END;

-- Create a table to store validation logs if it doesn't exist
CREATE TABLE IF NOT EXISTS `cherry-ai-project.agent_truth.validation_log` (
  validation_time TIMESTAMP,
  result STRING,
  bq_row_count INT64,
  gcs_row_count INT64,
  checksum_mismatches INT64
)
PARTITION BY DATE(validation_time);

-- Example call to the stored procedure (can be scheduled or run via CLI)
-- CALL `cherry-ai-project.agent_truth.validate_ssot`(
--   'gs://cherry-ai-project-bucket/backups/*.parquet',
--   'cherry-ai-project.agent_truth.memories'
-- );

-- Comment for documentation
COMMENT ON PROCEDURE `cherry-ai-project.agent_truth.validate_ssot` IS
'Stored procedure to validate data consistency between BigQuery SSOT table and GCS backups, logging results for monitoring.';
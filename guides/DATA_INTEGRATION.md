# Data Integration Guide

This project uses **Airbyte** for ETL/ELT pipelines. A sample connection to Snowflake is provided in `airbyte/snowflake_connection.yaml`.

1. Install Airbyte following the [official documentation](https://docs.airbyte.com/).
2. Import `airbyte/snowflake_connection.yaml` to create a connection.
3. Configure sources like Gong, Salesforce, or HubSpot and run the sync.
4. Data will be loaded into the Snowflake warehouse defined in your environment variables.

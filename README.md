# 🚀 PoC: YAML-Driven Airflow DAGs for S3 to Snowflake

## 📌 Overview
This project demonstrates a scalable, configuration-driven approach to data ingestion pipelines. It uses Apache Airflow to orchestrate data movement from S3/MinIO into Snowflake, with all pipeline definitions controlled through YAML configuration files.

### Key Features
- **Configuration-Driven Architecture**: Define new data pipelines without writing code
- **Automated DAG Generation**: Using dag-factory to create Airflow DAGs from YAML
- **Flexible Processing**: Support for multiple file formats (CSV, JSON, Parquet, Excel)
- **Local Development with MinIO**: Full S3-compatible environment for local testing
- **Snowflake Integration**: Ready-to-use operators for data loading into Snowflake

## 🏗️ Architecture

```
┌──────────────┐    ┌─────────────┐    ┌────────────┐    ┌────────────┐
│  S3 / MinIO  │───▶│ Airflow DAG │───▶│ Transform  │───▶│ Snowflake  │
│  (Data Lake) │    │ (YAML-Gen)  │    │ (Optional) │    │ (DWH)      │
└──────────────┘    └─────────────┘    └────────────┘    └────────────┘
```

- **Data Sources**: Files in S3/MinIO buckets (bronze, silver, iron)
- **Orchestration**: Airflow DAGs automatically generated from YAML configurations
- **Processing**: Optional data transformation using Pandas
- **Destination**: Snowflake tables/stages via direct loading

## 🔧 Quick Start
```bash
# Clone repo & set up the environment
git clone https://github.com/your-repo/s3_to_snowflake_poc.git
cd s3_to_snowflake_poc

# Start the environment
docker-compose up -d

# Access Airflow UI
open http://localhost:8080
# Login with: airflow / airflow
```

## 📂 Project Structure
```
├── dag_configs/                 # YAML configurations for pipeline definition
│   └── bronze_flatfile_example.yaml
├── dags/
│   ├── dag_factory_loader.py    # Loads YAML configs into Airflow DAGs
│   ├── simple_dag.py            # Example DAG for reference
│   └── test_minio_connection.py # Test DAG for MinIO connectivity
├── modules/
│   ├── data_processing.py       # Data transformation utilities
│   ├── s3_utils.py              # S3/MinIO interaction utilities
│   └── snowflake_utils.py       # Snowflake loading utilities
├── docker-compose.yaml          # Docker environment definition
└── Dockerfile                   # Custom Airflow image with dependencies
```

## 🔄 Workflow

1. **Define a Pipeline**: Create a YAML configuration in `dag_configs/`
2. **Start Airflow**: Run the Docker Compose setup
3. **DAG Generation**: DAGs are automatically created from YAML configs
4. **Data Ingestion**: Files from S3/MinIO are processed and loaded to Snowflake

## 📄 YAML Configuration

Example configuration for a simple ingestion pipeline:

```yaml
default_args:
  owner: "airflow"
  retries: 2
  retry_delay_min: 5
  start_date: 2024-03-15
schedule_interval: "@hourly"
description: "Ingests vendor data from S3/MinIO to Snowflake"
concurrency: 5
max_active_runs: 1
dagrun_timeout_sec: 3600
default_view: "grid"
orientation: "TB"
tags:
  - "s3"
  - "snowflake"
  - "vendor_data"

# Tasks
tasks:
  extract_from_s3:
    operator: PythonOperator
    python_callable_name: fetch_file_from_s3
    python_callable_file: /opt/airflow/modules/s3_utils.py
    op_kwargs:
      bucket_name: "bronze"
      file_key: "vendor_data/vendor_export.json"
      aws_conn_id: "aws_default"
    doc_md: |
      ### Extract Task
      Fetches JSON file from the bronze bucket in MinIO/S3.

  transform_data:
    operator: PythonOperator
    python_callable_name: transform_data
    python_callable_file: /opt/airflow/modules/data_processing.py
    op_kwargs:
      file_path: "{{ task_instance.xcom_pull(task_ids='extract_from_s3') }}"
      file_type: "json"
      schema: {
        "expected_columns": [
          {"name": "payload", "type": "variant", "enforce_not_null": true},
          {"name": "source_system", "type": "string", "enforce_not_null": true},
          {"name": "received_at", "type": "timestamp", "enforce_not_null": false}
        ]
      }
      output_format: "json"
      output_directory: "/tmp/vendor_data"
      filename: "vendor_export"
    dependencies: [extract_from_s3]
    doc_md: |
      ### Transform Task
      Processes vendor data, enforces schema, and prepares for Snowflake loading.

  load_to_snowflake:
    operator: custom.snowflake_utils.load_s3_to_snowflake
    task_id: load_to_snowflake
    s3_bucket: "silver"
    s3_key: "{{ task_instance.xcom_pull(task_ids='transform_data') }}"
    table_name: "VENDOR_DATA"
    stage_name: "S3_STAGE"
    file_format: "JSON_FORMAT"
    aws_conn_id: "aws_default"
    snowflake_conn_id: "snowflake_default"
    dependencies: [transform_data]
    doc_md: |
      ### Load Task
      Loads transformed data into Snowflake using the S3ToSnowflakeOperator.
```

## 📦 Local Development with MinIO (S3 Emulation)

This project uses **MinIO** to emulate AWS S3 locally, enabling development and testing without an actual AWS account.

- **MinIO Console:** [http://localhost:9001](http://localhost:9001)  
  - **Username:** `minio`  
  - **Password:** `minio123`
- **S3 API Endpoint:** [http://localhost:9000](http://localhost:9000)
- **Default Buckets:** `bronze`, `iron`, `silver`

### How It Works:
- The `minio` service runs MinIO, and the `minio-init` service creates required buckets and sets their policies automatically.
- Airflow uses the `aws_default` connection, which points to your MinIO instance.
- Connection settings: `endpoint_url=http://minio:9000` and `region_name=us-east-1`

### Testing with MinIO:
1. **Access the MinIO Console:** Open [http://localhost:9001](http://localhost:9001) and log in using the default credentials.
2. **Upload Test Files:** Navigate to a bucket (e.g., `bronze`) and upload test files.
3. **Run Your DAGs:** Airflow DAGs using S3 operations will interact with MinIO using the same S3 APIs as with AWS.

## 🔌 Connections Setup

### AWS/MinIO Connection
```bash
airflow connections add 'aws_default' \
    --conn-type 'aws' \
    --conn-login 'minio' \
    --conn-password 'minio123' \
    --conn-extra '{"endpoint_url": "http://minio:9000", "region_name": "us-east-1"}'
```

### Snowflake Connection
```bash
airflow connections add 'snowflake_default' \
    --conn-type 'snowflake' \
    --conn-host 'your-account.snowflakecomputing.com' \
    --conn-login 'username' \
    --conn-password 'password' \
    --conn-schema 'SCHEMA' \
    --conn-extra '{"database": "DB", "warehouse": "WH", "role": "ROLE"}'
```

## 🧪 Testing

Run the test DAG to verify MinIO connectivity:
```bash
docker-compose exec airflow-webserver airflow dags trigger improved_minio_test
```

## 📋 Prerequisites
- Docker & Docker Compose
- Basic understanding of Airflow and Snowflake

## 🔒 Security Note
This setup is intended for development only. For production:
- Use proper secrets management
- Configure secure connections
- Implement proper authorization controls
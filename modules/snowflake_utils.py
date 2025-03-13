from airflow.providers.snowflake.transfers.s3_to_snowflake import S3ToSnowflakeOperator
import structlog

logger = structlog.get_logger()

def load_s3_to_snowflake(task_id, s3_bucket, s3_key, table_name, stage_name, file_format, aws_conn_id, snowflake_conn_id):
    """
    Returns an Airflow task using `S3ToSnowflakeOperator`.
    """
    return S3ToSnowflakeOperator(
        task_id=task_id,
        snowflake_conn_id=snowflake_conn_id,
        stage=stage_name,
        file_format=file_format,
        table=table_name,
        s3_bucket=s3_bucket,
        s3_key=s3_key,
        aws_conn_id=aws_conn_id
    )
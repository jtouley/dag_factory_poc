import logging
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
import structlog

logger = structlog.get_logger()

def fetch_file_from_s3(bucket_name, file_key, aws_conn_id="aws_default"):
    """
    Fetches a file from S3 and returns its content as a string.
    """
    logger.info("Fetching file from S3", file_key=file_key, bucket=bucket_name)
    s3_hook = S3Hook(aws_conn_id=aws_conn_id)
    file_obj = s3_hook.get_key(file_key, bucket_name=bucket_name)
    
    if not file_obj:
        logger.error("File not found", file_key=file_key, bucket=bucket_name)
        raise FileNotFoundError(f"File {file_key} not found in {bucket_name}")
    
    return file_obj.get()["Body"].read().decode("utf-8")
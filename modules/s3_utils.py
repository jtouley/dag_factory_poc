import os
import time
import boto3
from airflow.hooks.base import BaseHook
import structlog

logger = structlog.get_logger()


def require_env(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Required environment variable {var_name} is not set.")
    return value


def fetch_file_from_s3(bucket_name, file_key, aws_conn_id="aws_default", timeout=30):
    """
    Fetches the content of a file from S3/MinIO and returns it as a string.

    This function has been updated to better handle MinIO connections.
    """
    start_time = time.time()
    logger.info("Starting fetch from S3/MinIO", file_key=file_key, bucket=bucket_name)

    try:
        # Get connection details from Airflow
        conn = BaseHook.get_connection(conn_id=aws_conn_id)
        extras = conn.extra_dejson

        # Get endpoint URL and region, checking both standard and legacy formats
        endpoint_url = extras.get("endpoint_url") or extras.get(
            "extra__aws__endpoint_url"
        )
        region = extras.get("region_name") or extras.get("extra__aws__region_name")

        # If not found in connection, try environment variables
        if not endpoint_url:
            endpoint_url = os.environ.get("MINIO_ENDPOINT")
        if not region:
            region = os.environ.get("AWS_DEFAULT_REGION")

        # Log connection details for debugging
        logger.info(
            "S3/MinIO connection details",
            endpoint=endpoint_url,
            region=region,
            access_key=conn.login,
        )

        # Create a direct boto3 session and client for better control
        session = boto3.session.Session(
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=region,
        )

        s3_client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            config=boto3.session.Config(signature_version="s3v4"),
        )

        # Fetch the object
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response["Body"].read().decode("utf-8")

        elapsed = time.time() - start_time
        logger.info("Successfully fetched file", file_key=file_key, elapsed=elapsed)
        return content

    except boto3.exceptions.Boto3Error as e:
        logger.error("Boto3 error", error=str(e), file_key=file_key, bucket=bucket_name)
        raise
    except Exception as e:
        logger.error(
            "Error fetching file", error=str(e), file_key=file_key, bucket=bucket_name
        )
        raise

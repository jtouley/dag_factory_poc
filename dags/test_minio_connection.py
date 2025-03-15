import logging
import os
import json
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
from datetime import datetime
import boto3

logger = logging.getLogger(__name__)


def print_connection_details():
    """Print connection details for debugging"""
    # Get the aws_default connection and print its details
    conn = BaseHook.get_connection(conn_id="aws_default")
    logger.info("Connection ID: aws_default")
    logger.info(f"Connection Type: {conn.conn_type}")
    logger.info(f"Host: {conn.host}")
    logger.info(f"Login: {conn.login}")
    logger.info(f"Password: {'*' * 8 if conn.password else 'Not set'}")
    logger.info(f"Port: {conn.port}")

    # Print environment variables
    logger.info(
        f"AWS_ACCESS_KEY_ID: {'Set' if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not set'}"
    )
    logger.info(
        f"AWS_SECRET_ACCESS_KEY: {'Set' if os.environ.get('AWS_SECRET_ACCESS_KEY') else 'Not set'}"
    )
    logger.info(
        f"AWS_DEFAULT_REGION: {os.environ.get('AWS_DEFAULT_REGION', 'Not set')}"
    )
    logger.info(f"MINIO_ENDPOINT: {os.environ.get('MINIO_ENDPOINT', 'Not set')}")

    # Print connection extras
    extras = conn.extra_dejson
    logger.info(f"Connection Extras: {json.dumps(extras, indent=2)}")

    # Check critical extras for MinIO
    endpoint_url = extras.get("endpoint_url") or extras.get("extra__aws__endpoint_url")
    region = extras.get("region_name") or extras.get("extra__aws__region_name")
    logger.info(f"Effective endpoint URL: {endpoint_url}")
    logger.info(f"Effective region: {region}")


def list_s3_buckets():
    """List all S3 buckets using boto3 directly"""
    try:
        # Read connection details to use with boto3
        conn = BaseHook.get_connection(conn_id="aws_default")
        extras = conn.extra_dejson

        # Get endpoint and region from extras
        endpoint_url = extras.get("endpoint_url") or extras.get(
            "extra__aws__endpoint_url"
        )
        region = extras.get("region_name") or extras.get("extra__aws__region_name")

        if not endpoint_url:
            endpoint_url = os.environ.get("MINIO_ENDPOINT")
            logger.info(f"Using endpoint from env: {endpoint_url}")

        # Create boto3 session
        session = boto3.session.Session(
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=region or os.environ.get("AWS_DEFAULT_REGION"),
        )

        # Create S3 client
        s3_client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            config=boto3.session.Config(signature_version="s3v4"),
        )

        # List buckets
        response = s3_client.list_buckets()
        buckets = [bucket["Name"] for bucket in response["Buckets"]]
        logger.info(f"Found buckets: {buckets}")

        # Try to list objects in each bucket
        for bucket in buckets:
            try:
                objects = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=5)
                if "Contents" in objects:
                    object_keys = [obj["Key"] for obj in objects["Contents"]]
                    logger.info(f"Objects in {bucket}: {object_keys}")
                else:
                    logger.info(f"No objects found in bucket {bucket}")
            except Exception as e:
                logger.error(f"Error listing objects in bucket {bucket}: {str(e)}")

        return buckets

    except Exception as e:
        logger.error(f"Error listing buckets: {str(e)}")
        raise


def create_test_file():
    """Create a test file in the bronze bucket"""
    try:
        conn = BaseHook.get_connection(conn_id="aws_default")
        extras = conn.extra_dejson

        # Get endpoint and region
        endpoint_url = extras.get("endpoint_url") or extras.get(
            "extra__aws__endpoint_url"
        )
        region = extras.get("region_name") or extras.get("extra__aws__region_name")

        # Create session and client
        session = boto3.session.Session(
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=region or os.environ.get("AWS_DEFAULT_REGION"),
        )

        s3_client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            config=boto3.session.Config(signature_version="s3v4"),
        )

        # Create test content
        test_content = "id,name,value\n1,test,100\n2,example,200\n"

        # Upload to S3/MinIO
        bucket = "bronze"
        key = "your-test-file.csv"

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=test_content.encode("utf-8"),
            ContentType="text/csv",
        )

        logger.info(f"Successfully created test file {key} in bucket {bucket}")
        return True

    except Exception as e:
        logger.error(f"Error creating test file: {str(e)}")
        raise


def fetch_test_file():
    """Fetch the test file using boto3 directly"""
    try:
        conn = BaseHook.get_connection(conn_id="aws_default")
        extras = conn.extra_dejson

        # Get endpoint and region
        endpoint_url = extras.get("endpoint_url") or extras.get(
            "extra__aws__endpoint_url"
        )
        region = extras.get("region_name") or extras.get("extra__aws__region_name")

        # Create session and client
        session = boto3.session.Session(
            aws_access_key_id=conn.login,
            aws_secret_access_key=conn.password,
            region_name=region or os.environ.get("AWS_DEFAULT_REGION"),
        )

        s3_client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            config=boto3.session.Config(signature_version="s3v4"),
        )

        # Fetch the object
        bucket = "bronze"
        key = "your-test-file.csv"

        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")

        logger.info(f"Successfully fetched file {key} from bucket {bucket}")
        logger.info(f"File content: {content}")

        return content

    except Exception as e:
        logger.error(f"Error fetching test file: {str(e)}")
        raise


def fetch_file_using_module():
    """Fetch test file using the s3_utils module"""
    from modules.s3_utils import fetch_file_from_s3

    try:
        content = fetch_file_from_s3(
            bucket_name="bronze", file_key="your-test-file.csv"
        )
        logger.info("Successfully fetched file using module")
        logger.info(f"Content: {content}")
        return content
    except Exception as e:
        logger.error(f"Error using s3_utils module: {str(e)}")
        raise


with DAG(
    dag_id="improved_minio_test",
    start_date=datetime(2024, 3, 14),
    schedule_interval=None,
    catchup=False,
    tags=["test", "minio"],
) as dag:
    connection_task = PythonOperator(
        task_id="print_connection_details",
        python_callable=print_connection_details,
    )

    buckets_task = PythonOperator(
        task_id="list_s3_buckets",
        python_callable=list_s3_buckets,
    )

    create_file_task = PythonOperator(
        task_id="create_test_file",
        python_callable=create_test_file,
    )

    fetch_task = PythonOperator(
        task_id="fetch_test_file",
        python_callable=fetch_test_file,
    )

    module_task = PythonOperator(
        task_id="fetch_file_using_module",
        python_callable=fetch_file_using_module,
    )

    connection_task >> buckets_task >> create_file_task >> fetch_task >> module_task

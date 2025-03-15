# File: dags/test_simple_dag.py
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

logger = logging.getLogger(__name__)


def simple_task():
    logger.info("Simple task is running!")
    return "Done"


with DAG(
    dag_id="test_simple_dag",
    start_date=datetime(2024, 3, 14),
    schedule_interval="@once",
    catchup=False,
) as dag:
    task = PythonOperator(
        task_id="simple_task",
        python_callable=simple_task,
    )

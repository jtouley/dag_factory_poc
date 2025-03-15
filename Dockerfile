FROM apache/airflow:2.10.5

# Set the AIRFLOW_VERSION (if needed)
ENV AIRFLOW_VERSION=2.10.5

# Copy the requirements file
COPY requirements-docker.txt /

# Install additional dependencies required for your project
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements-docker.txt
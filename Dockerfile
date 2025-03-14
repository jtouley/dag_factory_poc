# STAGE 1: Base Airflow Image
FROM apache/airflow:2.8.0-python3.10 AS base

USER root
WORKDIR /opt/airflow

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# STAGE 2: Install Airflow & Dependencies in Docker
FROM base AS dependencies

# Switch to airflow user before installing packages
USER airflow

# Install Airflow Providers inside Docker (NOT LOCALLY)
RUN pip install --no-cache-dir \
    apache-airflow-providers-amazon \
    apache-airflow-providers-snowflake \
    apache-airflow-providers-postgres \
    apache-airflow-providers-redis

# STAGE 3: Final Image
FROM base

# Copy dependencies from the previous stage
COPY --from=dependencies /home/airflow/.local /home/airflow/.local
ENV PATH="/home/airflow/.local/bin:$PATH"

# Ensure required directories exist before copying
RUN mkdir -p /opt/airflow/plugins /opt/airflow/dags /opt/airflow/config /opt/airflow/logs

# Copy DAGs, plugins, and config files
COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins
COPY config /opt/airflow/config

# Only change the owner, not the group
RUN chown -R airflow /opt/airflow

# Set Airflow working directory and user
WORKDIR /opt/airflow
USER airflow
# Start Airflow
CMD ["airflow", "standalone"]
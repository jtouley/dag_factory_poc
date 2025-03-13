import dagfactory

DAG_FACTORY_CONFIG = "/opt/airflow/dag_configs"  # Path to YAML configs

dag_factory = dagfactory.DagFactory(DAG_FACTORY_CONFIG)
dag_factory.generate_dags(globals())
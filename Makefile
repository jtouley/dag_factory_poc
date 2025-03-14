# ─────────────────────────────────────────────────
# 🔧 Makefile for Managing Airflow + S3 + Snowflake Project
# ─────────────────────────────────────────────────

# Default environment variables
ENV_FILE ?= .env
DOCKER_COMPOSE ?= docker-compose

# 📌 Show available commands
help:
	@echo "Usage: make [COMMAND]"
	@echo ""
	@echo "Commands:"
	@echo "  up            - Start Airflow in Docker"
	@echo "  down          - Stop Airflow & remove containers"
	@echo "  restart       - Restart Airflow containers"
	@echo "  logs          - View Airflow logs"
	@echo "  test          - Run all unit tests"
	@echo "  lint          - Run pre-commit hooks (black, flake8)"
	@echo "  env           - Generate .env file if missing"
	@echo "  destroy       - Stop and remove everything (volumes & metadata lost)"
	@echo "  init-db       - Initialize Airflow database"
	@echo "  create-admin  - Create an Airflow admin user"

# 🟢 Start Airflow in Docker
up: env
	$(DOCKER_COMPOSE) up -d

# 🔴 Stop Airflow
down:
	$(DOCKER_COMPOSE) down

# ♻️ Restart Airflow
restart:
	$(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) up -d

# 📜 View Airflow logs
logs:
	$(DOCKER_COMPOSE) logs -f

# ✅ Run all tests
test:
	pytest tests/

# 🛠 Run linting & formatting
lint:
	black . && flake8 .

# 📌 Generate .env file if missing
env:
	@if [ ! -f .env ]; then \
		echo "⚠️  .env file not found. Creating a default .env file..."; \
		echo "AIRFLOW_UID=50000" > .env; \
		echo "AIRFLOW_EXECUTOR=CeleryExecutor" >> .env; \
		echo "POSTGRES_USER=airflow" >> .env; \
		echo "POSTGRES_PASSWORD=airflow" >> .env; \
		echo "POSTGRES_DB=airflow" >> .env; \
		echo "REDIS_HOST=redis" >> .env; \
		echo "REDIS_PORT=6379" >> .env; \
		echo "AIRFLOW_ADMIN_USER=admin" >> .env; \
		echo "AIRFLOW_ADMIN_PASSWORD=admin" >> .env; \
		echo "✅ .env file created."; \
	else \
		echo "✅ .env file already exists."; \
	fi

# 📌 Initialize Airflow database
init-db:
	$(DOCKER_COMPOSE) exec airflow-webserver airflow db init

# 👤 Create an Airflow admin user
create-admin:
	$(DOCKER_COMPOSE) exec airflow-webserver airflow users create \
		--username ${AIRFLOW_ADMIN_USER} \
		--password ${AIRFLOW_ADMIN_PASSWORD} \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com

# 💥 Destroy all containers & volumes (use carefully)
destroy:
	$(DOCKER_COMPOSE) down --volumes --remove-orphans
	rm -rf logs airflow.db
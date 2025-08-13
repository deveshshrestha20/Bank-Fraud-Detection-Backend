# -------------------------------
# Makefile for Docker + Postgres
# -------------------------------

# --- Variables ---
COMPOSE_FILE = local.yml
POSTGRES_SERVICE = postgres
DB_USER = devesh
DB_NAME = bank_fraud_db


# -------------------------------
# Docker commands
# -------------------------------

build:
	docker compose -f $(COMPOSE_FILE) up --build -d --remove-orphans

up:
	docker compose -f $(COMPOSE_FILE) up

down:
	docker compose -f $(COMPOSE_FILE) down

config:
	docker compose -f $(COMPOSE_FILE) config

restart: down up

logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# -------------------------------
# Postgres commands
# -------------------------------
psql:
	docker compose -f $(COMPOSE_FILE) exec -it $(POSTGRES_SERVICE) psql -U $(DB_USER) -d $(DB_NAME)

db-shell: psql


# -------------------------------
# Alembic Migration commands
# -------------------------------

create_migrations:
	docker compose -f local.yml exec -it api alembic revision --autogenerate -m "$(name)"

upgrade_head:
	docker compose -f local.yml exec -it api alembic upgrade head

history:
	docker compose -f local.yml exec -it api alembic history

current_migration:
	docker compose -f local.yml exec -it api alembic current

downgrade:
	docker compose -f local.yml exec -it api alembic downgrade $(version)

network_inspect:
	docker network inspect bank_fraud_detection_local_nw
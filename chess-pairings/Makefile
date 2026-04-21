.PHONY: help compose down logs ps restart rebuild build-players-db update-swagger migrate

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

# Helpers
ENV ?= dev

ifeq ($(ENV),prod)
	ENV_FILE ?= .env.prod
	COMPOSE_FILES = -f docker-compose.yml -f docker-compose.prod.yml
else
	ENV_FILE ?= .env.dev
	COMPOSE_FILES = -f docker-compose.yml -f docker-compose.dev.yml
endif

COMPOSE_CMD = docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE)

define check_env
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "$(RED)Error: env file not found: $(ENV_FILE)$(NC)"; \
		echo "$(YELLOW)Create it with: cp .env.example $(ENV_FILE)$(NC)"; \
		exit 1; \
	fi
endef

help:
	@echo ""
	@echo "$(GREEN)╔══════════════════════════════════════╗$(NC)"
	@echo "$(GREEN)║          Chess Pairings              ║$(NC)"
	@echo "$(GREEN)╚══════════════════════════════════════╝$(NC)"
	@echo ""
	@echo "$(YELLOW)Usage: make <command>$(NC)"
	@echo ""
	@echo "$(YELLOW)Environment:$(NC)"
	@echo "  $(GREEN)ENV=dev$(NC)          Use local development configuration"
	@echo "  $(GREEN)ENV=prod$(NC)         Use production configuration override"
	@echo "  $(GREEN)ENV_FILE=.env.prod$(NC) Override the env file path"
	@echo ""
	@echo "$(YELLOW)Commands:$(NC)"
	@echo "  $(GREEN)compose$(NC)         Build images and start all containers in detached mode"
	@echo "  $(GREEN)restart$(NC)         Restart all containers preserving volumes"
	@echo "  $(GREEN)rebuild$(NC)         Rebuild images from scratch and restart containers"
	@echo "  $(GREEN)down$(NC)            Stop and remove containers (data volumes are preserved)"
	@echo "  $(GREEN)logs$(NC)            Follow live log output from all running containers"
	@echo "  $(GREEN)ps$(NC)              List containers and their current status"
	@echo "  $(GREEN)build-players-db$(NC) Rebuild catalog_player table from backend/data/players_list_foa.txt"
	@echo "  $(GREEN)migrate$(NC)         Run Alembic migrations on the backend container"
	@echo "  $(GREEN)update-swagger$(NC)  Fetch backend OpenAPI into frontend/src/api/swagger.yaml"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  cp .env.example .env.dev"
	@echo "  make compose"
	@echo "  cp .env.example .env.prod"
	@echo "  make compose ENV=prod"
	@echo "  make restart"
	@echo "  make rebuild"
	@echo "  make build-players-db"
	@echo "  make logs"
	@echo "  make down"
	@echo ""

compose:
	$(call check_env)
	@echo "$(GREEN)Starting application...$(NC)"
	$(COMPOSE_CMD) up -d --build

restart:
	$(call check_env)
	@echo "$(YELLOW)Restarting application...$(NC)"
	$(COMPOSE_CMD) down
	$(COMPOSE_CMD) up -d

rebuild:
	$(call check_env)
	@echo "$(YELLOW)Rebuilding images and restarting application...$(NC)"
	$(COMPOSE_CMD) build --no-cache
	$(COMPOSE_CMD) up -d --force-recreate

down:
	$(call check_env)
	@echo "$(YELLOW)Stopping application (volumes preserved)...$(NC)"
	$(COMPOSE_CMD) down

logs:
	$(call check_env)
	@echo "$(GREEN)Following logs (Ctrl+C to exit)...$(NC)"
	$(COMPOSE_CMD) logs -f

ps:
	$(call check_env)
	@echo "$(GREEN)Containers:$(NC)"
	$(COMPOSE_CMD) ps

build-players-db:
	$(call check_env)
	@echo "$(GREEN)Rebuilding catalog_player table from TXT file...$(NC)"
	$(COMPOSE_CMD) run --rm app python -m app.scripts.build_players_db

migrate:
	$(call check_env)
	@echo "$(GREEN)Running Alembic migrations...$(NC)"
	$(COMPOSE_CMD) run --rm app python -m app.scripts.migrate

update-swagger:
	curl http://localhost:8010/openapi.json -o frontend/src/api/swagger.yaml

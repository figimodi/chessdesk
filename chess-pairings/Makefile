.PHONY: help compose down logs ps restart rebuild build-players-db update-swagger

# Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m

# Helpers
ENV_FILE     = .env
COMPOSE_CMD  = docker-compose --env-file $(ENV_FILE)

define check_env
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "$(RED)Error: env file not found: $(ENV_FILE)$(NC)"; \
		echo "$(YELLOW)Create it with: cp .env.example .env$(NC)"; \
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
	@echo "$(YELLOW)Commands:$(NC)"
	@echo "  $(GREEN)compose$(NC)         Build images and start all containers in detached mode"
	@echo "  $(GREEN)restart$(NC)         Restart all containers preserving volumes"
	@echo "  $(GREEN)rebuild$(NC)         Rebuild images from scratch and restart containers"
	@echo "  $(GREEN)down$(NC)            Stop and remove containers (data volumes are preserved)"
	@echo "  $(GREEN)logs$(NC)            Follow live log output from all running containers"
	@echo "  $(GREEN)ps$(NC)              List containers and their current status"
	@echo "  $(GREEN)build-players-db$(NC) Rebuild catalog_player table from backend/data/players_list_foa.txt"
	@echo "  $(GREEN)update-swagger$(NC)  Fetch backend OpenAPI into frontend/src/api/swagger.yaml"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  cp .env.example .env"
	@echo "  make compose"
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

update-swagger:
	cd frontend && curl http://localhost:8010/openapi.json -o ./src/api/swagger.yaml

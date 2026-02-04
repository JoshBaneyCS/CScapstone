.PHONY: help build up down restart logs logs-backend logs-api logs-poker logs-gui logs-nginx logs-db clean shell-backend shell-api shell-db test-api status ps start stop prune psql db-init

.DEFAULT_GOAL := help

DB_USER ?= casino_admin
DB_NAME ?= casino_db

help:
	@echo "════════════════════════════════════════════════════════"
	@echo "  Dev Testing Environment - Available Commands"
	@echo "════════════════════════════════════════════════════════"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo "════════════════════════════════════════════════════════"

build: ## Build all Docker images
	@echo "Building Docker images..."
	docker compose build

up: ## Start all services (detached mode)
	@echo "Starting services..."
	docker compose up -d
	@echo ""
	@echo "Services started successfully!"
	@echo ""
	@echo "Access Points:"
	@echo "  Casino Web:     http://localhost (login/register/game)"
	@echo "  Go Backend:     http://localhost:8080"
	@echo "  Blackjack API:  http://localhost:8000"
	@echo "  Poker API:      http://localhost:8001"
	@echo "  noVNC Direct:   http://localhost:6080"
	@echo "  Postgres:       localhost:5432 (db: $(DB_NAME))"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs       View all logs"
	@echo "  make test-api   Test API endpoints"
	@echo ""

start: up ## Alias for 'up'

down: ## Stop all services
	@echo "Stopping services..."
	docker compose down

stop: down ## Alias for 'down'

restart: ## Restart all services
	@echo "Restarting services..."
	docker compose restart

logs: ## View logs from all services
	docker compose logs -f

logs-backend: ## View Go backend logs
	docker compose logs -f backend

logs-api: ## View Blackjack API logs
	docker compose logs -f blackjack-api

logs-poker: ## View Poker API logs
	docker compose logs -f poker-api

logs-gui: ## View GUI/VNC logs
	docker compose logs -f gui

logs-nginx: ## View nginx logs
	docker compose logs -f nginx

logs-db: ## View Postgres logs
	docker compose logs -f postgres

shell-backend: ## Get shell in backend container
	docker compose exec backend /bin/sh

shell-api: ## Get shell in Blackjack API container
	docker compose exec blackjack-api /bin/bash

shell-db: ## Get shell in Postgres container
	docker compose exec postgres /bin/sh

psql: ## Open psql in the Postgres container
	docker compose exec postgres psql -U $(DB_USER) -d $(DB_NAME)

db-init: ## Re-apply schema migration inside the Postgres container
	docker compose exec -T postgres psql -U $(DB_USER) -d $(DB_NAME) -f /docker-entrypoint-initdb.d/001_init.sql

test-api: ## Test API endpoints
	@echo "Testing APIs..."
	@echo ""
	@echo "Backend Health:"
	@curl -s http://localhost:8080/api/health | python3 -m json.tool || echo "Backend not responding"
	@echo ""
	@echo "Blackjack API:"
	@curl -s http://localhost:8000/ | python3 -m json.tool || echo "Blackjack API not responding"
	@echo ""
	@echo "Poker API:"
	@curl -s http://localhost:8001/ | python3 -m json.tool || echo "Poker API not responding"
	@echo ""

status: ## Show service status
	docker compose ps

ps: status ## Alias for 'status'

clean: ## Remove containers, images, and volumes
	@echo "Cleaning up..."
	docker compose down -v
	docker compose rm -f
	@echo "Removing images..."
	@docker rmi dev-testing-backend dev-testing-blackjack-api dev-testing-poker-api dev-testing-gui 2>/dev/null || true
	@echo "Cleanup complete!"

prune: clean ## Deep clean (remove everything including networks)
	@echo "Deep cleaning..."
	docker system prune -f
	@echo "Deep clean complete!"

.PHONY: help build up down restart logs logs-api logs-gui clean shell-api shell-gui test-api vnc status ps start stop prune

.DEFAULT_GOAL := help

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
	@echo "  Blackjack API:  http://localhost:8000"
	@echo "  API Docs:       http://localhost:8000/docs"
	@echo "  GUI (Web VNC):  http://localhost:6080/vnc.html"
	@echo "  GUI (VNC):      vnc://localhost:5900 (password: casino123)"
	@echo ""
	@echo "Useful commands:"
	@echo "  make logs       View all logs"
	@echo "  make vnc        Show VNC connection info"
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

logs-api: ## View API logs only
	docker compose logs -f blackjack-api

logs-gui: ## View GUI logs only
	docker compose logs -f gui

shell-api: ## Get shell in API container
	docker compose exec blackjack-api /bin/bash

shell-gui: ## Get shell in GUI container
	docker compose exec gui /bin/bash

test-api: ## Test API endpoints
	@echo "Testing Blackjack API..."
	@echo ""
	@echo "GET / (root endpoint):"
	@curl -s http://localhost:8000/ | python3 -m json.tool || echo "API not responding"
	@echo ""
	@echo "POST /blackjack/start (start game with \$$10 bet):"
	@curl -s -X POST http://localhost:8000/blackjack/start \
		-H "Content-Type: application/json" \
		-d '{"bet": 10}' | python3 -m json.tool || echo "Failed to start game"
	@echo ""
	@echo "GET /blackjack/state (get current state):"
	@curl -s http://localhost:8000/blackjack/state | python3 -m json.tool || echo "No active game"
	@echo ""

vnc: ## Show VNC connection information
	@echo "════════════════════════════════════════════════════════"
	@echo "  GUI VNC Access Information"
	@echo "════════════════════════════════════════════════════════"
	@echo ""
	@echo "Web Browser (Recommended):"
	@echo "   http://localhost:6080/vnc.html"
	@echo "   Click 'Connect' (password: casino123)"
	@echo ""
	@echo "VNC Client:"
	@echo "   vnc://localhost:5900"
	@echo "   Password: casino123"
	@echo ""
	@echo "VNC Clients by OS:"
	@echo "   macOS:   Built-in (Finder → Go → Connect to Server)"
	@echo "   Windows: RealVNC, TightVNC, or UltraVNC"
	@echo "   Linux:   Remmina, Vinagre, or TigerVNC"
	@echo ""
	@echo "════════════════════════════════════════════════════════"

status: ## Show service status
	docker compose ps

ps: status ## Alias for 'status'

clean: ## Remove containers, images, and volumes
	@echo "Cleaning up..."
	docker compose down -v
	docker compose rm -f
	@echo "Removing images..."
	@docker rmi dev-testing-blackjack-api dev-testing-gui 2>/dev/null || true
	@echo "Cleanup complete!"

prune: clean ## Deep clean (remove everything including networks)
	@echo "Deep cleaning..."
	docker system prune -f
	@echo "Deep clean complete!"

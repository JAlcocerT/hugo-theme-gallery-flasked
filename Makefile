# Default make goal
.DEFAULT_GOAL := help

.PHONY: setup-container
setup-container: ## Set up local hugo container (usage: make setup-container)
	docker build -t hugo_gallery .

.PHONY: build
build: ## Build Docker image (hugo_gallery)
	docker build -t hugo_gallery .

.PHONY: up
up: ## Start dev server on http://localhost:1319 using docker-compose-dev.yml
	docker compose -f docker-compose-dev.yml up -d

.PHONY: reup
reup: ## Recreate dev container after changes (rebuild image first if needed)
	docker compose -f docker-compose-dev.yml up -d --force-recreate

.PHONY: down
down: ## Stop and remove dev container
	docker compose -f docker-compose-dev.yml down

.PHONY: logs
logs: ## Tail logs of the dev container (tries hugo_container then hugo)
	- docker logs -f hugo_container || docker logs -f hugo

.PHONY: status
status: ## Show running container matching name 'hugo'
	docker ps --filter name=hugo

.PHONY: prod-build
prod-build: ## Build static site into exampleSite/public using docker-compose-prod.yml
	docker compose -f docker-compose-prod.yml run --rm hugo-build

.PHONY: prod-up
prod-up: ## Serve exampleSite/public at http://localhost:8087 using static-prod
	docker compose -f docker-compose-prod.yml up -d static-prod

.PHONY: prod-reup
prod-reup: ## Rebuild static site and restart static-prod
	$(MAKE) prod-build
	$(MAKE) prod-up

.PHONY: prod-down
prod-down: ## Stop production static server
	docker compose -f docker-compose-prod.yml down

.PHONY: prod-logs
prod-logs: ## Tail logs of production static server
	docker logs -f astro-prod

.PHONY: prod-status
prod-status: ## Show production containers
	docker ps --filter name=astro-prod --filter name=hugo-build

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z0-9_.-]+:.*?##/ {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Static server helpers (docker-compose.yml) ---
.PHONY: static-node-up
static-node-up: ## Serve public/ with Node http-server at http://localhost:8087
	docker compose -f docker-compose.yml up -d static-node

.PHONY: static-node-down
static-node-down: ## Stop Node static server
	docker compose -f docker-compose.yml down static-node || true

.PHONY: static-busybox-up
static-busybox-up: ## Serve public/ with BusyBox httpd at http://localhost:8088
	docker compose -f docker-compose.yml up -d static-busybox

.PHONY: static-busybox-down
static-busybox-down: ## Stop BusyBox static server
	docker compose -f docker-compose.yml down static-busybox || true

.PHONY: static-python-up
static-python-up: ## Serve public/ with Python http.server at http://localhost:8089
	docker compose -f docker-compose.yml up -d static-python

.PHONY: static-python-down
static-python-down: ## Stop Python static server
	docker compose -f docker-compose.yml down static-python || true

.PHONY: static-nginx-up
static-nginx-up: ## Serve public/ with Nginx at http://localhost:8090
	docker compose -f docker-compose.yml up -d static-nginx

.PHONY: static-nginx-down
static-nginx-down: ## Stop Nginx static server
	docker compose -f docker-compose.yml down static-nginx || true

.PHONY: static-caddy-up
static-caddy-up: ## Serve public/ with Caddy at http://localhost:8091
	docker compose -f docker-compose.yml up -d static-caddy

.PHONY: static-caddy-down
static-caddy-down: ## Stop Caddy static server
	docker compose -f docker-compose.yml down static-caddy || true
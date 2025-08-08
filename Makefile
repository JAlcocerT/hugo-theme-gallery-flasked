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
logs: ## Tail logs of the dev container
	docker logs -f hugo

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
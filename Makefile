# Default make goal
.DEFAULT_GOAL := help

.PHONY: setup-container
setup-container: ## Set up local hugo container (usage: make setup-container)
	docker build -t hugo_gallery .
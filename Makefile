.PHONY: help build up down logs rebuild clean restart shell \
	run-cnpj run-datasus run-inep \
	extract-cnpj transform-cnpj load-cnpj

build: ## Builds Docker images for the services
	docker-compose build

run: ## Starts containers in the background (detached mode)
	docker-compose up -d

down: ## Stops and removes containers, networks, and volumes
	docker-compose down -v

logs: ## Shows and tails logs from all containers
	docker-compose logs -f

rebuild: ## Rebuilds Docker images without using cache
	docker-compose build --no-cache

clean: ## Stops containers and removes local images created by Compose
	docker-compose down -v --rmi local

restart: ## Restarts all containers
	docker-compose down && docker-compose up -d

shell: ## Opens an interactive shell (bash) in the ETL container
	docker-compose exec etl bash

run-cnpj: ## Runs the full pipeline for Receita Federal (CNPJ) data
	docker-compose run --rm etl python src/jobs/pipeline_cnpj.py

run-datasus: ## Runs the full pipeline for DATASUS data
	docker-compose run --rm etl python src/jobs/pipeline_datasus.py

run-inep: ## Runs the full pipeline for INEP data (School Census, etc.)
	docker-compose run --rm etl python src/jobs/pipeline_inep.py

extract-cnpj: ## Runs ONLY the EXTRACTION step of the CNPJ pipeline
	docker-compose run --rm etl python src/jobs/pipeline_cnpj.py extract

transform-cnpj: ## Runs ONLY the TRANSFORMATION step of the CNPJ pipeline
	docker-compose run --rm etl python src/jobs/pipeline_cnpj.py transform

load-cnpj: ## Runs ONLY the LOAD step of the CNPJ pipeline
	docker-compose run --rm etl python src/jobs/pipeline_cnpj.py load

help: ## Shows this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'
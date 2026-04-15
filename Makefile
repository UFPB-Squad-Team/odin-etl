.PHONY: help build run down logs rebuild clean restart shell \
	run-censo \
	run-geocode-extract run-geocode-transform run-geocode-load run-geocode \
	run-geo-ingest run-bairro run-municipio run-geo-phase2 \
	run-education

build: ## Build Docker images
	docker-compose build

run: ## Start containers in detached mode
	docker-compose up -d

down: ## Stop and remove containers, networks, and volumes
	docker-compose down -v

logs: ## Tail logs from all containers
	docker-compose logs -f

rebuild: ## Rebuild Docker images without cache
	docker-compose build --no-cache

clean: ## Stop containers and remove local images
	docker-compose down -v --rmi local

restart: ## Restart all containers
	docker-compose down && docker-compose up -d

shell: ## Open an interactive shell in the ETL container
	docker-compose exec etl bash

run-censo: ## Run the full censo_pipeline (download -> filter -> parquet)
	docker-compose run --rm etl python -m src.jobs.01_education.censo_pipeline.main

run-geocode-extract: ## Run only the geocode extract step (filter PB from censo Silver)
	docker-compose run --rm etl python -m src.jobs.01_education.geocode_pipeline.extract

run-geocode-transform: ## Run only the geocode transform step (geocoding + checkpoint)
	docker-compose run --rm etl python -m src.jobs.01_education.geocode_pipeline.transform

run-geocode-load: ## Run only the geocode load step (insert into MongoDB)
	docker-compose run --rm etl python -m src.jobs.01_education.geocode_pipeline.load

run-geocode: ## Run the full geocode pipeline (extract -> transform -> load)
	docker-compose run --rm etl python -m src.jobs.01_education.geocode_pipeline.main

run-education: ## Run the full education job (all pipelines end-to-end)
	docker-compose run --rm etl python -m src.jobs.01_education.main

run-geo-ingest: ## Run Pipeline 3 — download IBGE shapefiles (sectors + municipalities)
	docker-compose run --rm etl python -m src.jobs.01_education.geo_ingest_pipeline.main

run-bairro: ## Run Pipeline 6 — spatial join + aggregate indicators by neighborhood
	docker-compose run --rm etl python -m src.jobs.01_education.bairro_pipeline.main

run-municipio: ## Run Pipeline 7 — spatial join + aggregate indicators by municipality
	docker-compose run --rm etl python -m src.jobs.01_education.municipio_pipeline.main

run-geo-phase2: ## Run all Phase 2 pipelines (geo-ingest + bairro + municipio)
	docker-compose run --rm etl python -m src.jobs.01_education.geo_ingest_pipeline.main
	docker-compose run --rm etl python -m src.jobs.01_education.bairro_pipeline.main
	docker-compose run --rm etl python -m src.jobs.01_education.municipio_pipeline.main

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

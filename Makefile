.PHONY: help build run down logs rebuild clean restart shell \
	run-censo \
	run-geocode-extract run-geocode-transform run-geocode-load run-geocode \
	run-geo-ingest run-bairro run-municipio run-geo-phase2 \
	run-education \
	docs-to-pdf docs-to-pdf-socioeconomico \
	prod-up prod-down prod-logs prod-deploy prod-shell prod-status

# ============================================================
# Desenvolvimento local
# ============================================================

build: ## Build Docker images (dev)
	docker compose build

run: ## Start MongoDB in detached mode (dev)
	docker compose up -d mongo

down: ## Stop and remove containers (dev)
	docker compose down

logs: ## Tail logs from all containers (dev)
	docker compose logs -f

rebuild: ## Rebuild Docker images without cache (dev)
	docker compose build --no-cache

clean: ## Stop containers and remove local images (dev)
	docker compose down -v --rmi local

restart: ## Restart all containers (dev)
	docker compose down && docker compose up -d

shell: ## Open an interactive shell in the ETL container (dev)
	docker compose run --rm etl bash

run-censo: ## Run the full censo_pipeline (download -> filter -> parquet)
	docker compose run --rm etl python -m src.jobs.education_jobs.censo_pipeline.main

run-geocode-extract: ## Run only the geocode extract step
	docker compose run --rm etl python -m src.jobs.education_jobs.geocode_pipeline.etl.extract

run-geocode-transform: ## Run only the geocode transform step
	docker compose run --rm etl python -m src.jobs.education_jobs.geocode_pipeline.etl.transform

run-geocode-load: ## Run only the geocode load step
	docker compose run --rm etl python -m src.jobs.education_jobs.geocode_pipeline.etl.load

run-geocode: ## Run the full geocode pipeline (extract -> transform -> load)
	docker compose run --rm etl python -m src.jobs.education_jobs.geocode_pipeline.main

run-geo-ingest: ## Process IBGE shapefiles (bairros + municipios) -> Silver
	docker compose run --rm etl python -m src.jobs.education_jobs.geo_ingest_pipeline.main

run-bairro: ## Aggregate indicators by neighborhood -> MongoDB bairro_indicadores
	docker compose run --rm etl python -m src.jobs.education_jobs.bairro_pipeline.main

run-municipio: ## Aggregate indicators by municipality -> MongoDB municipio_indicadores
	docker compose run --rm etl python -m src.jobs.education_jobs.municipio_pipeline.main

run-geo-phase2: ## Run geo-ingest + bairro + municipio in sequence
	docker compose run --rm etl python -m src.jobs.education_jobs.geo_ingest_pipeline.main
	docker compose run --rm etl python -m src.jobs.education_jobs.bairro_pipeline.main
	docker compose run --rm etl python -m src.jobs.education_jobs.municipio_pipeline.main

run-setor: ## Aggregate indicators by census sector -> MongoDB setor_indicadores
	docker compose run --rm etl python -m src.jobs.education_jobs.setor_pipeline.main

run-education: ## Run the full education job (all pipelines end-to-end)
	docker compose run --rm etl python -m src.jobs.education_jobs.main

docs-to-pdf-socioeconomico: ## Convert socioeconomic module docs to PDF
	@echo "🔄 Converting markdown files to PDF..."
	@if command -v pandoc >/dev/null 2>&1; then \
		echo "✅ Using Pandoc (best quality)"; \
		pandoc docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.md \
			-o docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.pdf \
			--pdf-engine=xelatex \
			-V geometry:margin=1in \
			-V fontsize=11pt \
			-V documentclass=article \
			-V lang=pt-BR \
			--toc \
			--highlight-style=tango && \
		pandoc docs/modulo-socioeconomico/PLANO_SPRINTS_SOCIOECONOMICO.md \
			-o docs/modulo-socioeconomico/PLANO_SPRINTS_SOCIOECONOMICO.pdf \
			--pdf-engine=xelatex \
			-V geometry:margin=1in \
			-V fontsize=11pt \
			-V documentclass=article \
			-V lang=pt-BR \
			--toc \
			--highlight-style=tango && \
		echo "✅ PDFs gerados com sucesso!"; \
	else \
		echo "❌ Pandoc não instalado. Instale com:"; \
		echo "   brew install pandoc"; \
		echo "   brew install --cask basictex"; \
		echo ""; \
		echo "Ou use o script Python:"; \
		echo "   python scripts/md_to_pdf_simple.py docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.md"; \
		exit 1; \
	fi

docs-to-pdf: ## Convert all documentation to PDF
	@echo "🔄 Converting all markdown documentation to PDF..."
	@python scripts/md_to_pdf_simple.py docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.md
	@python scripts/md_to_pdf_simple.py docs/modulo-socioeconomico/PLANO_SPRINTS_SOCIOECONOMICO.md
	@echo "✅ All PDFs generated!"

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Módulo Socioeconômico
# ============================================================

run-socioeconomico-extract: ## Run IBGE Censo 2022 extract (download datasets)
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.extract

run-socioeconomico-transform-municipio: ## Run transform for municipality level
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio.transform

run-socioeconomico-load-municipio: ## Run load for municipality level to MongoDB
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio.load

run-socioeconomico-transform-setor: ## Run transform for census sector level
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.setor.transform

run-socioeconomico-load-setor: ## Run load for census sector level to MongoDB
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.setor.load

run-socioeconomico-transform-bairro: ## Run transform for neighborhood level
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.bairro.transform

run-socioeconomico-load-bairro: ## Run load for neighborhood level to MongoDB
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.bairro.load

run-socioeconomico: ## Run the full socioeconomic module (all pipelines)
	docker compose run --rm etl python -m src.jobs.socioeconomico_jobs.main

validar-socioeconomico: ## Validate socioeconomic module (files, MongoDB, data quality)
	docker compose run --rm etl python scripts/validar_socioeconomico.py

# ============================================================
# Produção (usa docker-compose.prod.yml)
# ============================================================

PROD_COMPOSE = docker compose -f docker-compose.prod.yml

prod-up: ## Start MongoDB in production mode
	$(PROD_COMPOSE) up -d mongo

prod-down: ## Stop all production containers
	$(PROD_COMPOSE) down

prod-logs: ## Tail production logs
	$(PROD_COMPOSE) logs -f

prod-status: ## Show production containers status
	$(PROD_COMPOSE) ps

prod-deploy: ## Full deploy (build + start) on server
	./scripts/deploy.sh

prod-shell: ## Open shell in production ETL container
	$(PROD_COMPOSE) run --rm etl bash

prod-run-education: ## Run education pipeline in production
	$(PROD_COMPOSE) run --rm etl python -m src.jobs.education_jobs.main

prod-run-socioeconomico: ## Run socioeconomic pipeline in production
	$(PROD_COMPOSE) run --rm etl python -m src.jobs.socioeconomico_jobs.main

prod-validar: ## Validate socioeconomic data in production
	$(PROD_COMPOSE) run --rm etl python scripts/validar_socioeconomico.py

prod-mongo-ui: ## Start Mongo Express UI (access via SSH tunnel on port 8081)
	$(PROD_COMPOSE) --profile tools up -d mongo-express
	@echo "Acesse via SSH tunnel: ssh -L 8081:localhost:8081 usuario@servidor"
	@echo "Depois abra: http://localhost:8081"

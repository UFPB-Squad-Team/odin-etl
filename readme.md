# ODIN (Northeast Integrated Data Observatory) — ETL Pipelines

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Poetry](https://img.shields.io/badge/Poetry-deps%20manager-1f6feb.svg)](https://python-poetry.org/)
[![MongoDB](https://img.shields.io/badge/DB-MongoDB-47A248.svg)](https://www.mongodb.com/)
[![Status](https://img.shields.io/badge/Project-Active-success.svg)](#)
[![License](https://img.shields.io/badge/License-See%20LICENSE-informational.svg)](#license)

ODIN-ETL is the data engineering engine of ODIN, an open, reproducible, and extensible public observatory built by LEMA/UFPB. It automates extraction, standardization, and delivery of high-quality datasets from multiple Brazilian public sources for dashboards, analytics, and APIs.

Quick links:

- Stack
- Architecture
- [Data Architecture SDD (MVP PB / Educação)](docs/SDD_ARQUITETURA_DADOS_ODIN.md)
- Data Sources
- Quickstart (Docker or Poetry)
- Configuration
- Project Structure
- Common Tasks
- Contributing and License

## Why this repository

- Single source of truth for ingestion, harmonization, and curation.
- Reproducible pipelines with containerized runtime.
- Medallion architecture (Bronze → Silver → Gold) for governance and quality.

## Key objectives

- Geographic harmonization: street/ZIP → neighborhood → municipality (IBGE) → state → region.
- Key harmonization: consistent linkages across sources (e.g., CNPJ, INEP codes, CNES).
- Reproducibility and quality: audit-ready ETL/ELT with data validation routines.

## Data architecture (Medallion)

- Bronze (Raw): exact copies from the original sources, immutable, reprocessable.
- Silver (Clean): standardized, filtered, enriched; where harmonization happens.
- Gold (Curated): analytics-ready, subject-oriented aggregates for dashboards and APIs.

## Public data sources

- Receita Federal: Company registry (CNPJ).
- Portal da Transparência: Expenses, grants, and public finance.
- DATASUS: Health systems (CNES, SIH, SIA).
- INEP: Education (School Census, SAEB, IDEB).
- Ministério do Trabalho: Formal labor market (RAIS/CAGED).

## Tech stack

| Component                                 | Role                           | Notes                             |
| ----------------------------------------- | ------------------------------ | --------------------------------- |
| Python                                    | Core language                  | 3.11+ recommended                 |
| Poetry                                    | Dependency and venv management | Lockfile for deterministic builds |
| Docker + Compose                          | Containerized runtime          | Dev parity and easy onboarding    |
| Makefile                                  | Task automation                | Consistent DX across platforms    |
| MongoDB                                   | Operational datastore          | Dev/test instance via Compose     |
| pandas                                    | Data wrangling                 | Tabular transforms                |
| Requests/HTTPX                            | Ingestion                      | Robust downloads and APIs         |
| PyMongo/Motor                             | DB client                      | Interact with MongoDB             |
| Pydantic                                  | Data models/validation         | Schemas and type safety           |
| PyArrow/Parquet                           | Columnar storage               | Fast IO between layers            |
| Optional: ruff, black, pytest, pre-commit | Quality toolchain              | Lint, format, test hooks          |

Note: Some optional tools may not be enabled in this repo; adopt as needed.

## Prerequisites

- Docker and Docker Compose (Option A)
- Or: Python 3.11+, Poetry 1.6+, and a running MongoDB (local/Compose/Atlas) (Option B)
- Git, Make (recommended)

## Quickstart

Option A — Docker (recommended)

1. Copy environment file

- cp .env.example .env

2. Build and start

- docker compose up -d --build

3. Inspect logs

- docker compose logs -f etl

4. Open a shell inside the ETL container

- docker compose exec etl bash

5. Stop

- docker compose down

Option B — Poetry (local)

1. Ensure MongoDB available (e.g., Docker)

- docker run -d --name mongo -p 27017:27017 mongo:7

2. Setup virtualenv and install deps

- poetry install --no-root

3. Configure environment

- cp .env.example .env
- Edit MONGO_URI, MONGO_DB, DATA_DIR, etc.

4. Run a pipeline (replace with your job/module)

- poetry run python -m etl.jobs.<job_name>

5. Run tests (if available)

- poetry run pytest -q

## Configuration

Main environment variables (via .env):

- MONGO_URI: Mongo connection string (e.g., mongodb://mongo:27017).
- MONGO_DB: Database name for development.
- DATA_DIR: Local data lake root (e.g., ./data).
- TZ: Timezone (e.g., America/Recife).
- LOG_LEVEL: DEBUG, INFO, WARNING, ERROR.
- HTTP_TIMEOUT / HTTP_MAX_RETRIES: Robust downloads.
- PROXY_URL (optional): Corporate proxy.

Secrets: never commit credentials. Use .env and/or Docker secrets.

## Running pipelines

- Compose shell
- docker compose exec etl bash
- Invoke specific jobs
- python -m etl.jobs.<dataset> [--from <date>] [--to <date>] [--force]
- Example patterns (adjust to your module layout)
- python -m etl.jobs.receita_cnpj
- python -m etl.jobs.datasus.cnes
- python -m etl.jobs.inep.censo_escolar
- Reprocess Bronze → Silver → Gold
- python -m etl.flows.medallion --stage bronze
- python -m etl.flows.medallion --stage silver
- python -m etl.flows.medallion --stage gold

Tip: Prefer idempotent transformations and write-once Bronze files. Use partitioning by year/month for large sources.

## Project structure (illustrative)

- .
- ├─ docker/
- │ └─ etl.Dockerfile
- ├─ docker-compose.yml
- ├─ Makefile
- ├─ pyproject.toml
- ├─ .env.example
- ├─ src/
- │ ├─ etl/
- │ │ ├─ jobs/
- │ │ ├─ io/
- │ │ ├─ transforms/
- │ │ ├─ harmonization/
- │ │ └─ utils/
- └─ data/
- ├─ bronze/
- ├─ silver/
- └─ gold/

Note: Adjust paths and module names to your repository layout.

## Common tasks (Makefile)

If provided, typical targets include:

- make up: docker compose up -d --build
- make down: docker compose down
- make logs: docker compose logs -f etl
- make sh: docker compose exec etl bash
- make test: run tests
- make lint / make format: quality checks
- make etl job=<dataset>: run a specific pipeline

Run make help to list available commands.

## Data quality and governance

- Schema validation via typed models.
- Deterministic downloads with checksums when sources provide them.
- Row-level and aggregate validation checks in Silver/Gold.
- Provenance: keep source URLs, timestamps, and extraction metadata.

## Performance and reliability

- Chunked IO and columnar formats (Parquet/Arrow).
- Graceful retries and backoff on HTTP and IO.
- Cache intermediate artifacts when feasible.
- Partition data by source, year, and region.

## Troubleshooting

- Docker build fails: ensure network access and free disk space.
- Cannot reach MongoDB: confirm MONGO_URI and that mongo service is healthy.
- Permission issues on data/: grant write access to your user or container uid.
- Slow downloads: configure HTTP_TIMEOUT, HTTP_MAX_RETRIES, and use mirrors if available.

## Contributing

- Fork, create a feature branch, submit a PR with a clear description.
- Keep pipelines idempotent and documented.
- Add or update validation checks when changing schemas.
- Follow code style (black/ruff) and include tests where applicable.

## Acknowledgements

Built by LEMA/UFPB to strengthen open, high-quality data infrastructure for the Northeast of Brazil.

## License

See LICENSE for details.

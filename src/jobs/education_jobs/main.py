"""
Education Job — Unified Orchestrator

Runs the full education data pipeline end-to-end:

  Fase 1:
    1. censo_pipeline    — download, filter, save Silver parquet
    2. geocode_pipeline  — filter PB, geocode addresses, load into MongoDB

  Fase 2:
    3. geo_ingest_pipeline  — download IBGE shapefiles (Pipeline 3)
    4. bairro_pipeline      — spatial join + aggregate by neighborhood (Pipeline 6)
    5. municipio_pipeline   — spatial join + aggregate by municipality (Pipeline 7)

Run via:
    make run-education
    docker-compose run --rm etl python -m src.jobs.01_education.main
"""
import logging
from datetime import datetime

from src.jobs.education_jobs.censo_pipeline.main import run_pipeline as run_censo
from src.jobs.education_jobs.geocode_pipeline.main import run as run_geocode
from src.jobs.education_jobs.indicadores_base_dos_dados_pipeline.main import (
    run as run_indicadores,
)
from src.jobs.education_jobs.inep_resultados_pipeline.main import run as run_inep
from src.jobs.education_jobs.geo_ingest_pipeline.main import run as run_geo_ingest
from src.jobs.education_jobs.bairro_pipeline.main import run as run_bairro
from src.jobs.education_jobs.municipio_pipeline.main import run as run_municipio

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    logging.info("=== EDUCATION JOB STARTED ===")

    pipelines = [
        ("censo_pipeline", run_censo),
        ("indicadores_pipeline", run_indicadores),
        ("geocode_pipeline", run_geocode),
        # ("inep_resultados_pipeline", run_inep),  # Temporarily disabled: INEP URLs require verification
        # ("geo_ingest_pipeline", run_geo_ingest),  # Temporarily disabled: IBGE URLs require verification
        # ("bairro_pipeline", run_bairro),  # Depends on geo_ingest_pipeline (spatial join)
        # ("municipio_pipeline", run_municipio),  # Depends on geo_ingest_pipeline (spatial join)
    ]

    for nome, pipeline_fn in pipelines:
        t0 = datetime.now()
        logging.info(f"[{nome.upper()}] Starting...")
        try:
            pipeline_fn()
        except Exception as e:
            logging.error(f"[{nome.upper()}] Failed: {e}")
            raise
        elapsed = (datetime.now() - t0).total_seconds()
        logging.info(f"[{nome.upper()}] Completed in {elapsed:.1f}s")

    logging.info("=== EDUCATION JOB COMPLETED — Census + Geocode data in data/gold/ ===")


if __name__ == "__main__":
    run()

"""
Education Job — Unified Orchestrator

Runs the full education data pipeline end-to-end:
  1. censo_pipeline  — download, extract, filter, save Silver parquet
  2. geocode_pipeline — filter PB, geocode addresses, load into MongoDB

Run via:
    make run-education
    docker-compose run --rm etl python -m src.jobs.01_education.main
"""
import logging
from datetime import datetime

from src.jobs._01_education.censo_pipeline.main import run_pipeline as run_censo
from src.jobs._01_education.geocode_pipeline.main import run as run_geocode

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    logging.info("=== EDUCATION JOB STARTED ===")

    pipelines = [
        ("censo_pipeline", run_censo),
        ("geocode_pipeline", run_geocode),
    ]

    for name, pipeline_fn in pipelines:
        t0 = datetime.now()
        logging.info(f"[{name.upper()}] Starting...")
        try:
            pipeline_fn()
        except Exception as e:
            logging.error(f"[{name.upper()}] Failed: {e}")
            raise
        elapsed = (datetime.now() - t0).total_seconds()
        logging.info(f"[{name.upper()}] Completed in {elapsed:.1f}s")

    logging.info("=== EDUCATION JOB COMPLETED — data available in MongoDB ===")


if __name__ == "__main__":
    run()

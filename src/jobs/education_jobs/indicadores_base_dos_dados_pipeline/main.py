"""
Indicadores Base dos Dados Pipeline — Orchestrator

Runs extract → transform for INEP indicators from BigQuery.
No load step; merge happens in geocode_pipeline.
"""
import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.indicadores_base_dos_dados_pipeline.etl import (
    extract,
    transform,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    """Run extract → transform for INEP indicators."""
    logging.info("=== INDICADORES PIPELINE STARTED ===")
    storage = get_storage_backend()

    steps = [
        ("extract", lambda: extract.run(storage=storage)),
        ("transform", lambda: transform.run(storage=storage)),
    ]

    for step_name, step_fn in steps:
        t0 = datetime.now()
        logging.info(f"[{step_name.upper()}] Starting...")
        try:
            step_fn()
        except Exception as e:
            logging.error(f"[{step_name.upper()}] Failed: {e}")
            raise
        elapsed = (datetime.now() - t0).total_seconds()
        logging.info(f"[{step_name.upper()}] Completed in {elapsed:.1f}s")

    logging.info("=== INDICADORES PIPELINE COMPLETED ===")


if __name__ == "__main__":
    run()

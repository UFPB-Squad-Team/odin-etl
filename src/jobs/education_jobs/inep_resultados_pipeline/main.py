"""
INEP Resultados Pipeline — Orchestrator (Pipeline 2)

Runs the full INEP pipeline: extract -> transform -> load

This pipeline enriches the geocoded schools with IDEB and INSE indicators
from INEP open data, producing a complete school profile document in MongoDB.

Run via:
    make run-inep-resultados
    python -m src.jobs.education_jobs.inep_resultados_pipeline.main
"""
import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from .etl import extract, transform, load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    """Run the full INEP resultados pipeline: extract -> transform -> load."""
    logging.info("=== INEP RESULTADOS PIPELINE STARTED ===")
    storage = get_storage_backend()

    steps = [
        ("extract", lambda: extract.run(storage=storage)),
        ("transform", lambda: transform.run(storage=storage)),
        # ("load", lambda: load.run(storage=storage)),  # Uncomment when MongoDB is available
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

    logging.info("=== INEP RESULTADOS PIPELINE COMPLETED ===")


if __name__ == "__main__":
    run()


"""
Geo Ingest Pipeline — Orchestrator (Pipeline 3)

Downloads IBGE shapefiles for Paraiba and saves them as GeoParquet
in the Silver layer, ready for spatial joins in Pipelines 6 and 7.

Run via:
    make run-geo-ingest
"""
import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.geo_ingest_pipeline.etl import extract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage=None) -> None:
    storage = storage or get_storage_backend()
    logging.info("=== GEO INGEST PIPELINE STARTED ===")
    t0 = datetime.now()
    try:
        extract.run(storage=storage)
    except Exception as e:
        logging.error(f"[GEO INGEST] Failed: {e}")
        raise
    elapsed = (datetime.now() - t0).total_seconds()
    logging.info(f"=== GEO INGEST PIPELINE COMPLETED in {elapsed:.1f}s ===")


if __name__ == "__main__":
    run()

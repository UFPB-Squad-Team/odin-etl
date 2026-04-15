"""
Bairro Pipeline — Orchestrator (Pipeline 6)

Aggregates educational indicators per neighborhood (census sector)
and loads them into MongoDB for geospatial queries.

Run via:
    make run-bairro
"""
import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.bairro_pipeline.etl import extract, transform, load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage=None) -> None:
    storage = storage or get_storage_backend()
    logging.info("=== BAIRRO PIPELINE STARTED ===")

    t0 = datetime.now()
    try:
        gdf_escolas = extract.run(storage=storage)
        logging.info("[EXTRACT] Completed.")

        df_indicadores = transform.run(gdf_escolas=gdf_escolas, storage=storage)
        logging.info("[TRANSFORM] Completed.")

        load.run(df_indicadores=df_indicadores)
        logging.info("[LOAD] Completed.")
    except Exception as e:
        logging.error(f"Bairro pipeline failed: {e}")
        raise

    elapsed = (datetime.now() - t0).total_seconds()
    logging.info(f"=== BAIRRO PIPELINE COMPLETED in {elapsed:.1f}s ===")


if __name__ == "__main__":
    run()


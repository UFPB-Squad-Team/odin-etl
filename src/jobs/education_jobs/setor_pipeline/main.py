import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.setor_pipeline.etl import extract, transform, load

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")


def run(storage=None) -> None:
    storage = storage or get_storage_backend()
    logging.info("=== SETOR PIPELINE STARTED ===")
    t0 = datetime.now()

    try:
        gdf_escolas = extract.run(storage=storage)
        logging.info(f"[EXTRACT] {len(gdf_escolas)} escolas com coordenadas válidas.")

        df_indicadores = transform.run(gdf_escolas=gdf_escolas, storage=storage)
        logging.info(f"[TRANSFORM] {len(df_indicadores)} setores com escolas.")

        load.run(df_indicadores=df_indicadores)
        logging.info("[LOAD] Dados inseridos no MongoDB.")

    except Exception as e:
        logging.error(f"Setor pipeline falhou: {e}")
        raise

    elapsed = (datetime.now() - t0).total_seconds()
    logging.info(f"=== SETOR PIPELINE COMPLETED in {elapsed:.1f}s ===")


if __name__ == "__main__":
    run()

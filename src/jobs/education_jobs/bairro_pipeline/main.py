import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.bairro_pipeline.etl import transform, load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage=None) -> None:
    storage = storage or get_storage_backend()
    logging.info("=== BAIRRO PIPELINE STARTED ===")
    t0 = datetime.now()

    try:
        df_indicadores = transform.run(storage=storage)
        logging.info(f"[TRANSFORM] {len(df_indicadores)} bairros agregados.")

        load.run(df_indicadores=df_indicadores)
        logging.info("[LOAD] Dados inseridos no MongoDB.")
    except Exception as e:
        logging.error(f"Bairro pipeline falhou: {e}")
        raise

    elapsed = (datetime.now() - t0).total_seconds()
    logging.info(f"=== BAIRRO PIPELINE COMPLETED in {elapsed:.1f}s ===")


if __name__ == "__main__":
    run()

import logging
from datetime import datetime

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.inep_indicadores_pipeline.etl import extract, transform

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    """Executa extract → transform para todos os indicadores do INEP."""
    logging.info("=== INEP INDICADORES PIPELINE STARTED ===")
    storage = get_storage_backend()

    t0 = datetime.now()

    logging.info("[EXTRACT] Baixando indicadores do INEP...")
    dados = extract.run(storage=storage)

    logging.info("[TRANSFORM] Combinando e salvando Gold...")
    result = transform.run(dados=dados, storage=storage)

    elapsed = (datetime.now() - t0).total_seconds()

    if result.avisos:
        logging.warning("[AVISOS] %d aviso(s):", len(result.avisos))
        for a in result.avisos:
            logging.warning("  - %s", a)

    logging.info(
        "=== INEP INDICADORES PIPELINE COMPLETED in %.1fs — %d escolas ===",
        elapsed, result.escolas,
    )


if __name__ == "__main__":
    run()

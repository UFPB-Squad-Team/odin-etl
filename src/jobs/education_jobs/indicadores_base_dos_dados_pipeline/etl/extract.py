"""
Indicadores Base dos Dados Pipeline — Extract

Baixa dados de indicadores educacionais do INEP via BigQuery (Base dos Dados).
Foca em escolas do Nordeste.
"""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from src.jobs.education_jobs.indicadores_base_dos_dados_pipeline.config import (
    INDICADORES_QUERY_NORDESTE,
    INDICADORES_SILVER_FILENAME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage: StorageBackend = None):
    """Download INEP indicators from BigQuery and save to Silver parquet."""
    logging.info("--- STARTING INDICADORES EXTRACT ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    output_path = str(Path(paths["silver"]) / INDICADORES_SILVER_FILENAME)

    if Path(output_path).exists():
        logging.info(f"Cached Silver found at {output_path}. Reusing it and skipping BigQuery.")
        logging.info("--- INDICADORES EXTRACT COMPLETED (CACHED) ---")
        return

    billing_id = os.getenv("GOOGLE_BILLING_ID")
    if not billing_id:
        raise ValueError(
            "GOOGLE_BILLING_ID environment variable is not set. "
            "Check your .env file."
        )

    try:
        import basedosdados as bd
    except ImportError:
        raise ImportError(
            "basedosdados library not installed. "
            "Run: pip install basedosdados"
        )

    logging.info("Querying BigQuery for INEP indicators (Nordeste)...")
    df = bd.read_sql(query=INDICADORES_QUERY_NORDESTE, billing_project_id=billing_id)
    logging.info(f"Query completed. Records returned: {len(df)}")

    Path(paths["silver"]).mkdir(parents=True, exist_ok=True)
    storage.save_parquet(df, output_path)
    logging.info(f"Saved to Silver: {output_path}")
    logging.info("--- INDICADORES EXTRACT COMPLETED ---")


if __name__ == "__main__":
    run()

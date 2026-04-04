"""
Geocode Pipeline — Extract Step

Reads the Silver parquet produced by censo_pipeline, filters schools
from Paraiba (SG_UF == 'PB'), and saves the result to Silver for the
transform step.
"""
import logging
from pathlib import Path

from dotenv import load_dotenv

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _filter_data(df, filter_config: dict):
    """Apply UF, administrative dependency, and operational status filters."""
    logging.info("Applying filters...")
    df_filtered = df[
        (df["SG_UF"].isin(filter_config["filtro_uf"]))
        & (df["TP_DEPENDENCIA"].astype(int).isin(filter_config["filtro_dependencia_adm"]))
        & (df["TP_SITUACAO_FUNCIONAMENTO"].astype(int) == filter_config["filtro_situacao_funcionamento"])
    ].copy()
    logging.info(f"Filter applied: {len(df_filtered)} records selected.")
    return df_filtered


def run(storage: StorageBackend = None):
    """
    Extract schools from the censo Silver parquet, filter to PB only,
    and save the result to Silver for the transform step.
    """
    logging.info("--- STARTING GEOCODE EXTRACT ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    source_config = config["ingestion_sources"]["censo_escolar"]
    extract_config = config["geocode_pipeline"]["extract"]

    input_path = str(Path(paths["silver"]) / source_config["silver_output"])
    output_path = str(Path(paths["silver"]) / extract_config["silver_output"])

    logging.info(f"Reading censo Silver from: {input_path}")
    df_raw = storage.read_parquet(input_path)
    logging.info(f"Total records in censo Silver: {len(df_raw)}")

    df_filtered = _filter_data(df_raw, extract_config)

    logging.info(f"Saving PB schools to: {output_path}")
    storage.save_parquet(df_filtered, output_path)

    logging.info("--- GEOCODE EXTRACT COMPLETED ---")


if __name__ == "__main__":
    run()

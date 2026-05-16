"""
INEP Resultados Pipeline — Extract (Pipeline 2)

Downloads IDEB and INSE indicator files from INEP open data,
saves raw files to Bronze, and converts to Parquet in Silver.

Sources:
  - INSE 2023 (Indicador de Nível Socioeconômico)
  - IDEB 2023 — Anos Iniciais (escola)
  - IDEB 2023 — Anos Finais (escola)

All files are keyed by CO_ESCOLA, which maps to CO_ENTIDADE in the Censo.
"""
import logging
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Suppress SSL warnings (for MVP with verify=False)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from ..config import CO_ENTIDADE_KEY, build_source_paths

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _download_file(url: str, dest_path: str, storage: StorageBackend) -> None:
    """Download a file from URL and save to Bronze. Skips if already exists."""
    if Path(dest_path).exists():
        logging.info(f"File already exists, skipping download: {dest_path}")
        return

    logging.info(f"Downloading: {url}")
    # Note: verify=False disables SSL verification; should use verify=True in production
    response = requests.get(url, timeout=120, verify=False)
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Download failed — HTTP {response.status_code} for: {url}"
        )
    storage.save_zip(response.content, dest_path)
    logging.info(f"Saved to Bronze: {dest_path}")


def _process_inse(bronze_path: str, silver_path: str, target_filename: str, colunas: list) -> None:
    """Extract INSE from ZIP, read Excel, save as Parquet."""
    if Path(silver_path).exists():
        logging.info(f"Silver already exists, skipping: {silver_path}")
        return

    import zipfile
    with zipfile.ZipFile(bronze_path, "r") as zf:
        match = next((n for n in zf.namelist() if target_filename.lower() in n.lower()), None)
        if not match:
            # fallback: first xlsx inside zip
            match = next((n for n in zf.namelist() if n.endswith(".xlsx")), None)
        if not match:
            raise FileNotFoundError(f"No xlsx found inside {bronze_path}")
        with zf.open(match) as f:
            df = pd.read_excel(f, dtype=str)

    # Normalizar nome da coluna chave
    df = df.rename(columns={"CO_ESCOLA": CO_ENTIDADE_KEY})
    cols_finais = [CO_ENTIDADE_KEY] + [c for c in colunas if c != "CO_ESCOLA" and c in df.columns]
    df = df[cols_finais]

    Path(silver_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(silver_path, index=False)
    logging.info(f"INSE Silver saved: {silver_path} ({len(df)} records)")


def _process_ideb(bronze_path: str, silver_path: str, colunas: list) -> None:
    """Read IDEB Excel directly, save as Parquet."""
    if Path(silver_path).exists():
        logging.info(f"Silver already exists, skipping: {silver_path}")
        return

    # IDEB files have a header on row 9 (0-indexed)
    df = pd.read_excel(bronze_path, header=9, dtype=str)
    df = df.rename(columns={"CO_ESCOLA": CO_ENTIDADE_KEY})
    cols_finais = [CO_ENTIDADE_KEY] + [c for c in colunas if c != "CO_ESCOLA" and c in df.columns]
    df = df[cols_finais].dropna(subset=[CO_ENTIDADE_KEY])

    Path(silver_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(silver_path, index=False)
    logging.info(f"IDEB Silver saved: {silver_path} ({len(df)} records)")


def run(storage: StorageBackend = None) -> None:
    """Download and process INSE and IDEB files into Silver parquets."""
    logging.info("--- STARTING INEP RESULTADOS EXTRACT ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    sources = config["inep_resultados_pipeline"]["sources"]
    colunas = config["inep_resultados_pipeline"]["colunas"]

    # INSE
    inse_cfg = sources["inse"]
    inse_bronze, inse_silver = build_source_paths(paths, inse_cfg)
    _download_file(inse_cfg["url"], inse_bronze, storage)
    _process_inse(inse_bronze, inse_silver, inse_cfg["target_filename"], colunas["inse"])

    # IDEB Anos Iniciais
    ideb_ai_cfg = sources["ideb_anos_iniciais"]
    ideb_ai_bronze, ideb_ai_silver = build_source_paths(paths, ideb_ai_cfg)
    _download_file(ideb_ai_cfg["url"], ideb_ai_bronze, storage)
    _process_ideb(ideb_ai_bronze, ideb_ai_silver, colunas["ideb"])

    # IDEB Anos Finais
    ideb_af_cfg = sources["ideb_anos_finais"]
    ideb_af_bronze, ideb_af_silver = build_source_paths(paths, ideb_af_cfg)
    _download_file(ideb_af_cfg["url"], ideb_af_bronze, storage)
    _process_ideb(ideb_af_bronze, ideb_af_silver, colunas["ideb"])

    logging.info("--- INEP RESULTADOS EXTRACT COMPLETED ---")


if __name__ == "__main__":
    run()

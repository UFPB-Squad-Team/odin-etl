"""
INEP Resultados Pipeline — Transform (Pipeline 2)

Joins INSE and IDEB Silver parquets with the geocoded schools Gold parquet,
producing an enriched dataset with all indicators per school.

Join key: CO_ENTIDADE (Censo) == CO_ENTIDADE (INSE/IDEB after rename)

IDEB logic: a school can have Anos Iniciais, Anos Finais, or both.
We keep both as separate columns and let the API/dashboard decide
which to display based on the school's education levels.
"""
import logging
from pathlib import Path

import pandas as pd

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from ..config import (
    CO_ENTIDADE_KEY,
    IDEB_AF_RENAME_MAP,
    IDEB_AI_RENAME_MAP,
    INSE_RENAME_MAP,
    build_gold_path,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage: StorageBackend = None) -> pd.DataFrame:
    """
    Join geocoded schools with INSE and IDEB indicators.

    Returns:
        Enriched DataFrame with columns from Censo + INSE + IDEB.
    """
    logging.info("--- STARTING INEP RESULTADOS TRANSFORM ---")
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    sources = config["inep_resultados_pipeline"]["sources"]
    geocode_cfg = config["geocode_pipeline"]["transform"]

    # Base: escolas geocodificadas da PB
    escolas_path = str(Path(paths["gold"]) / geocode_cfg["gold_output"])
    logging.info(f"Reading geocoded schools from: {escolas_path}")
    df = storage.read_parquet(escolas_path)
    logging.info(f"Base: {len(df)} schools")

    # Join INSE
    inse_path = str(Path(paths["silver"]) / sources["inse"]["silver_output"])
    df_inse = storage.read_parquet(inse_path)
    df_inse = df_inse.rename(columns=INSE_RENAME_MAP)
    df = df.merge(df_inse[[CO_ENTIDADE_KEY, "inse_valor", "inse_classificacao"]],
                  on=CO_ENTIDADE_KEY, how="left")
    logging.info(f"After INSE join: {df['inse_valor'].notna().sum()} schools with INSE")

    # Join IDEB Anos Iniciais
    ideb_ai_path = str(Path(paths["silver"]) / sources["ideb_anos_iniciais"]["silver_output"])
    df_ideb_ai = storage.read_parquet(ideb_ai_path)
    df_ideb_ai = df_ideb_ai.rename(columns=IDEB_AI_RENAME_MAP)
    df = df.merge(
        df_ideb_ai[[CO_ENTIDADE_KEY, "ideb_anos_iniciais", "ideb_meta_anos_iniciais"]],
        on=CO_ENTIDADE_KEY, how="left"
    )

    # Join IDEB Anos Finais
    ideb_af_path = str(Path(paths["silver"]) / sources["ideb_anos_finais"]["silver_output"])
    df_ideb_af = storage.read_parquet(ideb_af_path)
    df_ideb_af = df_ideb_af.rename(columns=IDEB_AF_RENAME_MAP)
    df = df.merge(
        df_ideb_af[[CO_ENTIDADE_KEY, "ideb_anos_finais", "ideb_meta_anos_finais"]],
        on=CO_ENTIDADE_KEY, how="left"
    )

    logging.info(
        f"Enrichment complete: "
        f"{df['ideb_anos_iniciais'].notna().sum()} with IDEB AI, "
        f"{df['ideb_anos_finais'].notna().sum()} with IDEB AF"
    )

    # Save Gold
    gold_path = build_gold_path(paths, config["inep_resultados_pipeline"]["gold_output"])
    storage.save_parquet(df, gold_path)
    logging.info(f"Enriched Gold saved: {gold_path}")

    logging.info("--- INEP RESULTADOS TRANSFORM COMPLETED ---")
    return df


if __name__ == "__main__":
    run()

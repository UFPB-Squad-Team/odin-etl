"""
Municipio Pipeline — Load (Pipeline 7)

Upserts municipality indicators into MongoDB collection 'municipio_indicadores'.
Creates a 2dsphere index on the 'geometria' field for geospatial queries.
"""
import logging

import pandas as pd

from src.common.utils import load_config
from src.jobs.education_jobs.geo_aggregate_shared import upsert_dataframe

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(df_indicadores: pd.DataFrame) -> None:
    """
    Upsert municipality indicators into MongoDB.

    Args:
        df_indicadores: DataFrame with one row per municipality, including
                        'co_municipio' and 'geometria' fields.
    """
    config = load_config()
    colecao_nome = config["geo_pipeline"]["mongodb"]["colecao_municipios"]

    logging.info(f"Connecting to MongoDB collection: {colecao_nome}")
    resultado = upsert_dataframe(
        df=df_indicadores,
        collection_name=colecao_nome,
        key_field="co_municipio",
        geo_index_field="geometria",
    )

    if resultado is not None:
        logging.info(
            f"MongoDB upsert complete: "
            f"{resultado.upserted_count} inserted, "
            f"{resultado.modified_count} updated."
        )
    else:
        logging.warning("No municipality indicators to insert.")

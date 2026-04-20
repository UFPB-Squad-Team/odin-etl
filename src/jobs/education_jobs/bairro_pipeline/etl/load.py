import logging
import os

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(df_indicadores: pd.DataFrame) -> None:
    """
    Upsert de indicadores por bairro no MongoDB.

    Chave de upsert composta: { bairro, municipio }
    Índice geoespacial em 'centroide' para queries $geoNear e $geoWithin.

    Args:
        df_indicadores: DataFrame com uma linha por bairro.
    """
    load_dotenv()
    config = load_config()
    colecao_nome = config["geo_pipeline"]["mongodb"]["colecao_bairros"]

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    if not mongo_uri:
        raise ValueError("MONGO_URI não definido. Verifique seu .env.")
    if not db_name:
        raise ValueError("MONGO_DB_NAME não definido. Verifique seu .env.")

    logger.info(f"Conectando ao MongoDB — coleção: {colecao_nome}")
    client = MongoClient(mongo_uri)
    try:
        colecao = client[db_name][colecao_nome]

        # Índice geoespacial no centróide
        colecao.create_index([("centroide", "2dsphere")], sparse=True)
        # Índice único composto para upsert idempotente
        colecao.create_index(
            [("bairro", 1), ("municipio", 1)],
            unique=True,
            sparse=True,
        )

        operacoes = []
        for _, row in df_indicadores.iterrows():
            bairro = row.get("bairro")
            municipio = row.get("municipio")
            if not bairro or not municipio:
                continue

            doc = {k: v for k, v in row.to_dict().items() if pd.notna(v) or isinstance(v, dict)}
            operacoes.append(
                UpdateOne(
                    {"bairro": bairro, "municipio": municipio},
                    {"$set": doc},
                    upsert=True,
                )
            )

        if operacoes:
            resultado = colecao.bulk_write(operacoes, ordered=False)
            logger.info(
                f"Upsert concluído: {resultado.upserted_count} inseridos, "
                f"{resultado.modified_count} atualizados."
            )
        else:
            logger.warning("Nenhum indicador de bairro para inserir.")
    finally:
        client.close()

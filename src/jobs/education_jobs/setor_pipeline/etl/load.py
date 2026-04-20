"""
Setor Pipeline — Load

Upsert de indicadores por setor censitário na coleção MongoDB 'setor_indicadores'.

Schema do documento:
  cd_setor          — código único do setor (15 dígitos), chave de upsert
  nome_area         — bairro oficial (se existir) ou nome do município
  nm_bairro         — nome do bairro oficial (vazio para interior/rural)
  nm_municipio      — nome do município
  co_municipio      — código IBGE do município (7 dígitos)
  situacao          — "Urbana" ou "Rural"
  tipo_setor        — "comum", "aglomerado_subnormal", etc.
  tem_bairro_oficial — bool: true se o setor tem bairro delimitado pelo IBGE
  geometria         — GeoJSON Polygon (índice 2dsphere para $geoIntersects)
  total_escolas     — quantidade de escolas no setor
  total_matriculas  — soma de matrículas (fund + médio + infantil)
  pct_com_internet  — % de escolas com internet
  pct_com_biblioteca — % de escolas com biblioteca
  pct_com_lab_informatica — % de escolas com laboratório de informática
  pct_sem_acessibilidade  — % de escolas sem nenhuma acessibilidade
"""
import logging
import os

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

COLECAO = "setor_indicadores"


def run(df_indicadores: pd.DataFrame) -> None:
    """
    Upsert de indicadores por setor censitário no MongoDB.

    Chave de upsert: cd_setor (único por setor em toda a PB)
    Índice geoespacial: geometria (2dsphere) para queries $geoIntersects
    """
    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    if not mongo_uri:
        raise ValueError("MONGO_URI não definido. Verifique seu .env.")
    if not db_name:
        raise ValueError("MONGO_DB_NAME não definido. Verifique seu .env.")

    logger.info(f"Conectando ao MongoDB — coleção: {COLECAO}")
    client = MongoClient(mongo_uri)
    try:
        colecao = client[db_name][COLECAO]

        # Índice geoespacial para queries de rua ($geoIntersects)
        colecao.create_index([("geometria", "2dsphere")], sparse=True)
        # Índice único no código do setor
        colecao.create_index("cd_setor", unique=True, sparse=True)
        # Índice para busca por município
        colecao.create_index("co_municipio")
        # Índice para busca por nome de área (bairro ou município)
        colecao.create_index("nome_area")

        operacoes = []
        for _, row in df_indicadores.iterrows():
            cd_setor = row.get("cd_setor")
            if not cd_setor or pd.isna(cd_setor):
                continue

            # Montar documento limpo (sem NaN)
            doc = {}
            for k, v in row.to_dict().items():
                if isinstance(v, dict):
                    doc[k] = v  # GeoJSON geometry — manter sempre
                elif pd.notna(v):
                    doc[k] = v

            operacoes.append(
                UpdateOne(
                    {"cd_setor": str(cd_setor)},
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
            logger.warning("Nenhum setor para inserir.")
    finally:
        client.close()

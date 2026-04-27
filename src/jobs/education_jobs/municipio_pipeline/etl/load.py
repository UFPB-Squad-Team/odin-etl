import logging
import os
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _val(x: Any) -> Any:
    """Converte para tipo Python nativo, tratando NaN como None."""
    if x is None:
        return None
    if isinstance(x, dict):
        return x
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(x, "item"):
        return x.item()
    return x


def _int_val(x: Any) -> Optional[int]:
    v = _val(x)
    if v is None:
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _float_val(x: Any, decimais: int = 1) -> Optional[float]:
    v = _val(x)
    if v is None:
        return None
    try:
        return round(float(v), decimais)
    except (TypeError, ValueError):
        return None


def _construir_educacao(row: pd.Series) -> dict:
    """
    Constrói o sub-documento 'educacao' a partir de uma linha do DataFrame.
    Campos None são incluídos para limpar valores obsoletos via $set.
    """
    doc = {
        "totalEscolas": _int_val(row.get("total_escolas")),
        "totalMatriculas": _int_val(row.get("total_matriculas")),
        "totalBairros": _int_val(row.get("total_bairros")),
        "pctComInternet": _float_val(row.get("pct_com_internet")),
        "pctComBiblioteca": _float_val(row.get("pct_com_biblioteca")),
        "pctComLabInformatica": _float_val(row.get("pct_com_lab_informatica")),
        "pctSemAcessibilidade": _float_val(row.get("pct_sem_acessibilidade")),
    }

    ideb_ai = _float_val(row.get("media_ideb_anos_iniciais"), decimais=2)
    ideb_af = _float_val(row.get("media_ideb_anos_finais"), decimais=2)
    inse    = _float_val(row.get("media_inse"), decimais=2)

    if ideb_ai is not None:
        doc["mediaIdebAnosIniciais"] = ideb_ai
    if ideb_af is not None:
        doc["mediaIdebAnosFinals"] = ideb_af
    if inse is not None:
        doc["mediaInse"] = inse

    return doc


def run(df_indicadores: pd.DataFrame) -> None:
    """
    Upsert de indicadores educacionais por município no MongoDB.

    Estratégia de merge:
        - Chave de upsert: municipioIdIbge (compartilhada com socioeconômico)
        - $set cirúrgico: só atualiza 'educacao.*' + campos geo/identidade
        - Campo 'socioeconomico' não é tocado

    Args:
        df_indicadores: DataFrame produzido pelo transform (uma linha por município).
    """
    load_dotenv()
    config = load_config()
    colecao_nome = config["geo_pipeline"]["mongodb"]["colecao_municipios"]

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

        colecao.create_index([("centroide", "2dsphere")], sparse=True)
        colecao.create_index([("geometria", "2dsphere")], sparse=True)
        colecao.create_index("municipioIdIbge", unique=True, sparse=True)
        colecao.create_index("sg_uf", sparse=True)

        operacoes = []
        for _, row in df_indicadores.iterrows():
            municipio_id = _int_val(row.get("municipioIdIbge"))
            if municipio_id is None:
                continue

            educacao = _construir_educacao(row)

            campos_compartilhados = {
                "municipioIdIbge": municipio_id,
                "municipio": _val(row.get("municipio")),
                "sg_uf": _val(row.get("sg_uf")),
            }
            if _val(row.get("centroide")) is not None:
                campos_compartilhados["centroide"] = row["centroide"]
            if _val(row.get("geometria")) is not None:
                campos_compartilhados["geometria"] = row["geometria"]

            _CAMPOS_LEGADOS_MUN = [
                "total_escolas", "total_matriculas", "total_bairros",
                "pct_com_internet", "pct_com_biblioteca",
                "pct_com_lab_informatica", "pct_sem_acessibilidade",
                "media_ideb_anos_iniciais", "media_ideb_anos_finais", "media_inse",
            ]

            update = {
                "$set": {
                    **campos_compartilhados,
                    "educacao": educacao,
                },
                "$unset": {campo: "" for campo in _CAMPOS_LEGADOS_MUN},
            }

            operacoes.append(
                UpdateOne(
                    {"municipioIdIbge": municipio_id},
                    update,
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
            logger.warning("Nenhum indicador de município para inserir.")
    finally:
        client.close()

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
    doc = {
        "totalEscolas": _int_val(row.get("total_escolas")),
        "totalMatriculas": _int_val(row.get("total_matriculas")),
        "pctComInternet": _float_val(row.get("pct_com_internet")),
        "pctComBiblioteca": _float_val(row.get("pct_com_biblioteca")),
        "pctComLabInformatica": _float_val(row.get("pct_com_lab_informatica")),
        "pctSemAcessibilidade": _float_val(row.get("pct_sem_acessibilidade")),
    }
    for campo, col in [
        ("mediaIdebAnosIniciais", "media_ideb_anos_iniciais"),
        ("mediaIdebAnosFinals", "media_ideb_anos_finais"),
        ("mediaInse", "media_inse"),
    ]:
        v = _float_val(row.get(col), decimais=2)
        if v is not None:
            doc[campo] = v
    return doc


def run(df_indicadores: pd.DataFrame) -> None:
    """
    Upsert de indicadores educacionais por bairro no MongoDB.

    Chave de upsert: cd_bairro (código IBGE — alinhado com socioeconomico_jobs)
    $set cirúrgico em 'educacao' — não toca em 'socioeconomico'.
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

        colecao.create_index("cd_bairro", unique=True, sparse=True)
        colecao.create_index([("geometria", "2dsphere")], sparse=True)
        colecao.create_index([("centroide", "2dsphere")], sparse=True)
        colecao.create_index("cd_municipio")

        operacoes = []
        for _, row in df_indicadores.iterrows():
            cd_bairro = _val(row.get("cd_bairro_ibge") or row.get("cd_bairro") or row.get("CD_BAIRRO"))
            if cd_bairro is None:
                continue
            cd_bairro = str(cd_bairro)

            educacao = _construir_educacao(row)

            campos_compartilhados: dict = {
                "cd_bairro": cd_bairro,
                "educacao": educacao,
            }

            for dest, src in [
                ("nm_bairro", "bairro"),
                ("nm_municipio", "municipio"),
                ("cd_municipio", "municipioIdIbge"),
            ]:
                v = _val(row.get(src))
                if v is not None:
                    campos_compartilhados[dest] = str(v) if dest == "cd_municipio" else v

            if _val(row.get("geometria")) is not None:
                campos_compartilhados["geometria"] = row["geometria"]

            operacoes.append(
                UpdateOne(
                    {"cd_bairro": cd_bairro},
                    {"$set": campos_compartilhados},
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

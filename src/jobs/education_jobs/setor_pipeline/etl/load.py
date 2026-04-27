
import logging
import os
from typing import Any, Optional

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

COLECAO = "setor_indicadores"

_CAMPOS_ROOT = {
    "cd_setor", "co_municipio", "nm_municipio", "nome_area",
    "nm_bairro", "situacao", "tipo_setor", "tem_bairro_oficial", "geometria",
}

_CAMPOS_EDUCACAO = {
    "total_escolas": "totalEscolas",
    "total_matriculas": "totalMatriculas",
    "pct_com_internet": "pctComInternet",
    "pct_com_biblioteca": "pctComBiblioteca",
    "pct_com_lab_informatica": "pctComLabInformatica",
    "pct_sem_acessibilidade": "pctSemAcessibilidade",
    "media_ideb_anos_iniciais": "mediaIdebAnosIniciais",
    "media_ideb_anos_finais": "mediaIdebAnosFinals",
    "media_inse": "mediaInse",
}


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


def run(df_indicadores: pd.DataFrame) -> None:
    """
    Upsert de indicadores educacionais por setor no MongoDB.

    Chave de upsert: cd_setor
    $set cirúrgico em 'educacao' — não toca em 'socioeconomico'.
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

        colecao.create_index([("geometria", "2dsphere")], sparse=True)
        colecao.create_index("cd_setor", unique=True, sparse=True)
        colecao.create_index("co_municipio", name="idx_setor_indicadores_co_municipio")
        colecao.create_index("nome_area")

        operacoes = []
        for _, row in df_indicadores.iterrows():
            cd_setor = _val(row.get("cd_setor"))
            if not cd_setor:
                continue
            cd_setor = str(cd_setor)

            set_payload: dict = {}
            for campo in _CAMPOS_ROOT:
                v = _val(row.get(campo))
                if v is not None:
                    set_payload[campo] = v

            educacao = {}
            for col_src, col_dest in _CAMPOS_EDUCACAO.items():
                v = _val(row.get(col_src))
                if v is not None:
                    educacao[col_dest] = v

            if educacao:
                set_payload["educacao"] = educacao

            _CAMPOS_LEGADOS = [
                "total_escolas", "total_matriculas", "pct_com_internet",
                "pct_com_biblioteca", "pct_com_lab_informatica", "pct_sem_acessibilidade",
                "media_ideb_anos_iniciais", "media_ideb_anos_finais", "media_inse",
            ]
            unset_payload = {campo: "" for campo in _CAMPOS_LEGADOS}

            operacoes.append(
                UpdateOne(
                    {"cd_setor": cd_setor},
                    {"$set": set_payload, "$unset": unset_payload},
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

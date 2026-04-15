import pandas as pd
from ..config.columns import (
    COLUNAS_IDENTIFICACAO, COLUNAS_INFRA, COLUNAS_ACESSIBILIDADE,
    COLUNAS_TECNOLOGIA, COLUNAS_PROFISSIONAIS, COLUNAS_MATRICULAS,
    COLUNAS_DOCENTES, COLUNAS_SALAS, COLUNAS_TRANSPORTE,
)
from ..utils.logger import get_logger

logger = get_logger("Subdatasets")


def unique_columns(columns: list[str]) -> list[str]:
    return list(dict.fromkeys(columns))

def split_domains(df: pd.DataFrame):
    logger.info("Creating domain subdatasets...")

    datasets = {
        "identificacao": df[unique_columns(COLUNAS_IDENTIFICACAO + ["CO_ENTIDADE"] )],
        "infraestrutura": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_INFRA)],
        "acessibilidade": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_ACESSIBILIDADE)],
        "tecnologia": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_TECNOLOGIA)],
        "profissionais": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_PROFISSIONAIS)],
        "matriculas": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_MATRICULAS)],
        "docentes": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_DOCENTES)],
        "salas": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_SALAS)],
        "transporte": df[unique_columns(["NO_ENTIDADE", "CO_ENTIDADE", "SG_UF", "NO_MUNICIPIO"] + COLUNAS_TRANSPORTE)],
    }

    return datasets

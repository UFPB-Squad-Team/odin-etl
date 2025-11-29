import pandas as pd
from config.columns import *
from utils.logger import get_logger

logger = get_logger("Subdatasets")

def split_domains(df: pd.DataFrame):
    logger.info("Creating domain subdatasets...")

    datasets = {
        "identificacao": df[COLUNAS_IDENTIFICACAO + ["CO_ENTIDADE"]],
        "infraestrutura": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_INFRA],
        "acessibilidade": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_ACESSIBILIDADE],
        "tecnologia": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_TECNOLOGIA],
        "profissionais": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_PROFISSIONAIS],
        "matriculas": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_MATRICULAS],
        "docentes": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_DOCENTES],
        "salas": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_SALAS],
        "transporte": df[["NO_ENTIDADE"]+ ["CO_ENTIDADE"] + ["SG_UF"] + ["NO_MUNICIPIO"] + COLUNAS_TRANSPORTE],
    }

    return datasets

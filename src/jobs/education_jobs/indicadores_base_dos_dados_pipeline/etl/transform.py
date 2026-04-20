import logging
from pathlib import Path

import pandas as pd

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from src.jobs.education_jobs.indicadores_base_dos_dados_pipeline.config import (
    INDICADORES_GOLD_FILENAME,
    INDICADORES_SILVER_FILENAME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# Campos onde 0 é fisicamente impossível e portanto é sentinela de dado ausente.
# Baseado em análise estatística do dataset da PB (2024):
#   horas_aula_diarias: 97% zeros, range real [1.4, 22.2]
#   alunos_por_turma (EM): 91% zeros, range real [0.9, 36.6]
CAMPOS_ZERO_SENTINELA = {
    "horas_aula_diarias",
    "alunos_por_turma",
}


def _to_float(v, campo: str = "") -> float | None:
    """
    Converte valor para float ou None.
    Para campos onde 0 é sentinela, substitui 0.0 por None.
    """
    if pd.isna(v):
        return None
    val = float(v)
    if val == 0.0 and campo in CAMPOS_ZERO_SENTINELA:
        return None
    return val


def _mount_indicators_doc(row):
    """
    Transform a row from raw INEP data into nested indicators document.
    """
    def f(col, campo=""):
        return _to_float(row.get(col), campo)

    return {
        "ano": int(row["ano"]) if pd.notna(row.get("ano")) else None,
        "id_municipio": int(row["id_municipio"]) if pd.notna(row.get("id_municipio")) else None,
        "id_escola": str(row["id_escola"]) if pd.notna(row.get("id_escola")) else None,
        "localizacao": row.get("localizacao"),
        "rede": row.get("rede"),
        "icg_nivel_complexidade_gestao_escola": row.get("icg_nivel_complexidade_gestao_escola"),
        "educacao_infantil": {
            "alunos_por_turma": f("atu_ei", "alunos_por_turma"),
            "horas_aula_diarias": f("had_ei", "horas_aula_diarias"),
            "docentes_superior": f("dsu_ei"),
            "afd": f("afd_ei"),
        },
        "fundamental_anos_iniciais": {
            "alunos_por_turma": f("atu_ef_anos_iniciais", "alunos_por_turma"),
            "horas_aula_diarias": f("had_ef_anos_iniciais", "horas_aula_diarias"),
            "docentes_superior": f("dsu_ef_anos_iniciais"),
            "tdi": f("tdi_ef_anos_iniciais"),
            "taxa_aprovacao": f("taxa_aprovacao_ef_anos_iniciais"),
            "taxa_reprovacao": f("taxa_reprovacao_ef_anos_iniciais"),
            "taxa_abandono": f("taxa_abandono_ef_anos_iniciais"),
            "tnr": f("tnr_ef_anos_iniciais"),
            "afd": f("afd_ef_anos_iniciais"),
            "ied": f("ied_ef_anos_iniciais"),
        },
        "fundamental_anos_finais": {
            "alunos_por_turma": f("atu_ef_anos_finais", "alunos_por_turma"),
            "horas_aula_diarias": f("had_ef_anos_finais", "horas_aula_diarias"),
            "docentes_superior": f("dsu_ef_anos_finais"),
            "tdi": f("tdi_ef_anos_finais"),
            "taxa_aprovacao": f("taxa_aprovacao_ef_anos_finais"),
            "taxa_reprovacao": f("taxa_reprovacao_ef_anos_finais"),
            "taxa_abandono": f("taxa_abandono_ef_anos_finais"),
            "tnr": f("tnr_ef_anos_finais"),
            "afd": f("afd_ef_anos_finais"),
            "ied": f("ied_ef_anos_finais"),
        },
        "ensino_medio": {
            "alunos_por_turma": f("atu_em", "alunos_por_turma"),
            "horas_aula_diarias": f("had_em", "horas_aula_diarias"),
            "docentes_superior": f("dsu_em"),
            "tdi": f("tdi_em"),
            "taxa_aprovacao": f("taxa_aprovacao_em"),
            "taxa_reprovacao": f("taxa_reprovacao_em"),
            "taxa_abandono": f("taxa_abandono_em"),
            "tnr": f("tnr_em"),
            "afd": f("afd_em"),
            "ied": f("ied_em"),
        },
        "geo": {
            "type": "Point",
            "coordinates": [
                _to_float(row.get("longitude")),
                _to_float(row.get("latitude")),
            ],
        },
    }


def run(storage: StorageBackend = None):
    """Transform raw INEP indicators into nested Gold format."""
    logging.info("--- STARTING INDICADORES TRANSFORM ---")

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]

    input_path = str(Path(paths["silver"]) / INDICADORES_SILVER_FILENAME)
    output_path = str(Path(paths["gold"]) / INDICADORES_GOLD_FILENAME)

    logging.info(f"Reading Silver from: {input_path}")
    df = storage.read_parquet(input_path)
    logging.info(f"Total records: {len(df)}")

    logging.info("Transforming to nested JSON structure...")
    df_docs = df.apply(_mount_indicators_doc, axis=1)
    df_output = pd.DataFrame([doc for doc in df_docs])

    Path(paths["gold"]).mkdir(parents=True, exist_ok=True)
    storage.save_parquet(df_output, output_path)
    logging.info(f"Saved to Gold: {output_path}")
    logging.info("--- INDICADORES TRANSFORM COMPLETED ---")


if __name__ == "__main__":
    run()

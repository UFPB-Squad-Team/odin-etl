"""
Indicadores Base dos Dados Pipeline — Transform

Transforms raw INEP indicators into nested JSON structure:
- educacao_infantil, fundamental_anos_iniciais, fundamental_anos_finais, ensino_medio
- Each level contains: alunos_por_turma, horas_aula_diarias, docentes_superior, tdi, etc.
- Geo point with longitude/latitude coordinates.
"""
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


def _to_float(v):
    """Convert value to float or None."""
    return None if pd.isna(v) else float(v)


def _mount_indicators_doc(row):
    """
    Transform a row from raw INEP data into nested indicators document.
    Aggregates AFD and IED groups into single values per level.
    """
    return {
        "ano": int(row["ano"]) if pd.notna(row.get("ano")) else None,
        "id_municipio": int(row["id_municipio"]) if pd.notna(row.get("id_municipio")) else None,
        "id_escola": str(row["id_escola"]) if pd.notna(row.get("id_escola")) else None,
        "localizacao": row.get("localizacao"),
        "rede": row.get("rede"),
        "icg_nivel_complexidade_gestao_escola": row.get("icg_nivel_complexidade_gestao_escola"),
        "educacao_infantil": {
            "alunos_por_turma": _to_float(row.get("atu_ei")),
            "horas_aula_diarias": _to_float(row.get("had_ei")),
            "docentes_superior": _to_float(row.get("dsu_ei")),
            "afd": _to_float(row.get("afd_ei")),
        },
        "fundamental_anos_iniciais": {
            "alunos_por_turma": _to_float(row.get("atu_ef_anos_iniciais")),
            "horas_aula_diarias": _to_float(row.get("had_ef_anos_iniciais")),
            "docentes_superior": _to_float(row.get("dsu_ef_anos_iniciais")),
            "tdi": _to_float(row.get("tdi_ef_anos_iniciais")),
            "taxa_aprovacao": _to_float(row.get("taxa_aprovacao_ef_anos_iniciais")),
            "taxa_reprovacao": _to_float(row.get("taxa_reprovacao_ef_anos_iniciais")),
            "taxa_abandono": _to_float(row.get("taxa_abandono_ef_anos_iniciais")),
            "tnr": _to_float(row.get("tnr_ef_anos_iniciais")),
            "afd": _to_float(row.get("afd_ef_anos_iniciais")),
            "ied": _to_float(row.get("ied_ef_anos_iniciais")),
        },
        "fundamental_anos_finais": {
            "alunos_por_turma": _to_float(row.get("atu_ef_anos_finais")),
            "horas_aula_diarias": _to_float(row.get("had_ef_anos_finais")),
            "docentes_superior": _to_float(row.get("dsu_ef_anos_finais")),
            "tdi": _to_float(row.get("tdi_ef_anos_finais")),
            "taxa_aprovacao": _to_float(row.get("taxa_aprovacao_ef_anos_finais")),
            "taxa_reprovacao": _to_float(row.get("taxa_reprovacao_ef_anos_finais")),
            "taxa_abandono": _to_float(row.get("taxa_abandono_ef_anos_finais")),
            "tnr": _to_float(row.get("tnr_ef_anos_finais")),
            "afd": _to_float(row.get("afd_ef_anos_finais")),
            "ied": _to_float(row.get("ied_ef_anos_finais")),
        },
        "ensino_medio": {
            "alunos_por_turma": _to_float(row.get("atu_em")),
            "horas_aula_diarias": _to_float(row.get("had_em")),
            "docentes_superior": _to_float(row.get("dsu_em")),
            "tdi": _to_float(row.get("tdi_em")),
            "taxa_aprovacao": _to_float(row.get("taxa_aprovacao_em")),
            "taxa_reprovacao": _to_float(row.get("taxa_reprovacao_em")),
            "taxa_abandono": _to_float(row.get("taxa_abandono_em")),
            "tnr": _to_float(row.get("tnr_em")),
            "afd": _to_float(row.get("afd_em")),
            "ied": _to_float(row.get("ied_em")),
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

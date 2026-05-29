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
    """
    doc = {
        "totalEscolas": _int_val(row.get("total_escolas")),
        "totalMatriculas": _int_val(row.get("total_matriculas")),
        "totalBairros": _int_val(row.get("total_bairros")),
        "pctComAguaPotavel": _float_val(row.get("pct_com_agua_potavel")),
        "pctComEnergiaPublica": _float_val(row.get("pct_com_energia_publica")),
        "pctComEsgotoRedePublica": _float_val(row.get("pct_com_esgoto_rede_publica")),
        "pctComColetaLixo": _float_val(row.get("pct_com_coleta_lixo")),
        "pctComInternet": _float_val(row.get("pct_com_internet")),
        "pctComInternetAlunos": _float_val(row.get("pct_com_internet_alunos")),
        "pctComBiblioteca": _float_val(row.get("pct_com_biblioteca")),
        "pctComLaboratorioInformatica": _float_val(row.get("pct_com_laboratorio_informatica")),
        "pctComLaboratorioCiencias": _float_val(row.get("pct_com_laboratorio_ciencias")),
        "pctComQuadraEsportes": _float_val(row.get("pct_com_quadra_esportes")),
        "pctComCozinha": _float_val(row.get("pct_com_cozinha")),
        "pctComRefeitorio": _float_val(row.get("pct_com_refeitorio")),
        "pctSemAcessibilidade": _float_val(row.get("pct_sem_acessibilidade")),
        "mediaIdebAnosIniciais": _float_val(row.get("media_ideb_anos_iniciais"), decimais=2),
        "mediaIdebAnosFinals": _float_val(row.get("media_ideb_anos_finais"), decimais=2),
        "mediaIdebEnsinoMedio": _float_val(row.get("media_ideb_ensino_medio"), decimais=2),
        "mediaInse": _float_val(row.get("media_inse"), decimais=2),
        "mediaAfdAnosIniciais": _float_val(row.get("media_afd_anos_iniciais"), decimais=1),
        "mediaAfdAnosFinais": _float_val(row.get("media_afd_anos_finais"), decimais=1),
        "mediaAfdEnsinoMedio": _float_val(row.get("media_afd_ensino_medio"), decimais=1),
        "mediaTdiAnosIniciais": _float_val(row.get("media_tdi_anos_iniciais"), decimais=1),
        "mediaTdiAnosFinais": _float_val(row.get("media_tdi_anos_finais"), decimais=1),
        "mediaTdiEnsinoMedio": _float_val(row.get("media_tdi_ensino_medio"), decimais=1),
        "mediaTaxaAprovacaoAi": _float_val(row.get("media_taxa_aprovacao_ai"), decimais=1),
        "mediaTaxaAprovacaoAf": _float_val(row.get("media_taxa_aprovacao_af"), decimais=1),
        "mediaTaxaAprovacaoEm": _float_val(row.get("media_taxa_aprovacao_em"), decimais=1),
        "mediaTaxaAbandonoAi": _float_val(row.get("media_taxa_abandono_ai"), decimais=1),
        "mediaTaxaAbandonoAf": _float_val(row.get("media_taxa_abandono_af"), decimais=1),
        "mediaTaxaAbandonoEm": _float_val(row.get("media_taxa_abandono_em"), decimais=1),
        "mediaDocentesSuperiorAi": _float_val(row.get("media_docentes_superior_ai"), decimais=1),
        "mediaDocentesSuperiorAf": _float_val(row.get("media_docentes_superior_af"), decimais=1),
        "mediaDocentesSuperiorEm": _float_val(row.get("media_docentes_superior_em"), decimais=1),
        "mediaHorasAulaAi": _float_val(row.get("media_horas_aula_ai"), decimais=1),
        "mediaHorasAulaAf": _float_val(row.get("media_horas_aula_af"), decimais=1),
        "mediaHorasAulaEm": _float_val(row.get("media_horas_aula_em"), decimais=1),
        "mediaAlunosTurmaAi": _float_val(row.get("media_alunos_turma_ai"), decimais=1),
        "mediaAlunosTurmaAf": _float_val(row.get("media_alunos_turma_af"), decimais=1),
        "mediaAlunosTurmaEm": _float_val(row.get("media_alunos_turma_em"), decimais=1),
    }
    return {k: v for k, v in doc.items() if v is not None}


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
                "pct_com_laboratorio_informatica", "pct_sem_acessibilidade",
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

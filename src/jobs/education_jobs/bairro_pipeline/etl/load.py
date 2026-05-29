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

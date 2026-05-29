"""
Load — Bairro (IBGE Censo 2022)

Upsert dos indicadores socioeconômicos na coleção 'bairro_indicadores',
agrupados sob o campo 'socioeconomico', com geometria do GPKG.

Estrutura do documento:
    {
        cd_bairro: "2507507001",       # chave composta com cd_municipio
        cd_municipio: "2507507",
        nm_bairro: "Centro",
        nm_municipio: "João Pessoa",
        uf: "PB",
        geometria: { type: "MultiPolygon", ... },  # 2dsphere

        socioeconomico: {
            anoReferencia: 2022,
            fonte: "...",
            populacao: { ... },
            estruturaEtaria: { ... },
            raca: { ... },
            saneamento: { ... },
            educacaoPopulacao: { ... },
            familia: { ... },
        }
    }
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from shapely.geometry import mapping

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

_COLECAO   = "bairro_indicadores"
_GPKG_PATH = Path("data/silver/bairros_pb.gpkg")
_GOLD_PATH = Path("data/gold/bairro_socioeconomico_pb.parquet")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
    return int(v) if v is not None else None


def _float_val(x: Any, decimais: int = 1) -> Optional[float]:
    v = _val(x)
    if v is None:
        return None
    try:
        return round(float(v), decimais)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Geometrias
# ---------------------------------------------------------------------------

def _carregar_geometrias() -> Dict[str, dict]:
    """
    Carrega geometrias do GPKG e retorna {cd_bairro: geojson_dict}.
    O GPKG de bairros usa CD_BAIRRO como chave.
    """
    if not _GPKG_PATH.exists():
        logger.warning("GPKG não encontrado: %s — bairros sem geometria.", _GPKG_PATH)
        return {}

    logger.info("Carregando geometrias: %s", _GPKG_PATH)
    gdf = gpd.read_file(_GPKG_PATH)

    geometrias = {
        str(row["CD_BAIRRO"]): mapping(row["geometry"])
        for _, row in gdf.iterrows()
        if row["geometry"] is not None
    }
    logger.info("  %d geometrias carregadas", len(geometrias))
    return geometrias


# ---------------------------------------------------------------------------
# Documento
# ---------------------------------------------------------------------------

def _construir_socioeconomico(row: pd.Series) -> dict:
    return {
        "anoReferencia": _int_val(row.get("ano_referencia")),
        "fonte": _val(row.get("fonte")),
        "populacao": {
            "total": _int_val(row.get("total_populacao")),
            "totalDomiciliosParticulares": _int_val(row.get("total_domicilios_particulares")),
            "mediaMoradoresPorDomicilio": _float_val(row.get("media_moradores_por_domicilio")),
        },
        "estruturaEtaria": {
            "pctCriancas0a9": _float_val(row.get("pct_criancas_0_9")),
            "pctIdosos60Mais": _float_val(row.get("pct_idosos_60_mais")),
            "pctJovens15a29": _float_val(row.get("pct_jovens_15_29")),
            "pctAdultos30a59": _float_val(row.get("pct_adultos_30_59")),
            "razaoDependencia": _float_val(row.get("razao_dependencia")),
        },
        "genero": {
            "pctPopMasculina": _float_val(row.get("pct_pop_masculina")),
            "pctPopFeminina": _float_val(row.get("pct_pop_feminina")),
        },
        "raca": {
            "pctPretaParda": _float_val(row.get("pct_preta_parda")),
            "pctBranca": _float_val(row.get("pct_branca")),
            "pctIndigena": _float_val(row.get("pct_indigena")),
        },
        "saneamento": {
            "pctAguaRedeGeral":    _float_val(row.get("pct_agua_rede_geral")),
            "pctAguaInadequada":   _float_val(row.get("pct_agua_inadequada")),
            "pctAguaNaoEncanada":  _float_val(row.get("pct_agua_nao_encanada")),
            "pctEsgotoRedeGeral":  _float_val(row.get("pct_esgoto_rede_geral")),
            "pctEsgotoInadequado": _float_val(row.get("pct_esgoto_inadequado")),
            "pctLixoColetado":     _float_val(row.get("pct_lixo_coletado")),
            "pctLixoInadequado":   _float_val(row.get("pct_lixo_inadequado")),
            "pctDomSemBanheiro":   _float_val(row.get("pct_dom_sem_banheiro")),
        },
        "educacaoPopulacao": {
            "taxaAnalfabetismo15Mais": _float_val(row.get("taxa_analfabetismo_15_mais")),
        },
        "familia": {
            "pctResponsavelFeminino": _float_val(row.get("pct_responsavel_feminino")),
        },
        "mortalidade": {
            "totalObitosDomicilios": _int_val(row.get("total_obitos_domicilios")),
            "obitosInfantis0a4":     _int_val(row.get("obitos_infantis_0_4")),
        },
        "habitacao": {
            "pctDomImprovisado": _float_val(row.get("pct_dom_improvisado")),
            "pctDomSuperlotado": _float_val(row.get("pct_dom_superlotado")),
            "pctDomUnipessoal":  _float_val(row.get("pct_dom_unipessoal")),
            "pctDomTipoCasa":    _float_val(row.get("pct_dom_tipo_casa")),
            "pctDomTipoApto":    _float_val(row.get("pct_dom_tipo_apto")),
            "pctDomDegradado":   _float_val(row.get("pct_dom_degradado")),
        },
    }


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def run(df: Optional[pd.DataFrame] = None, storage=None) -> int:
    """
    Upsert dos indicadores socioeconômicos de bairro no MongoDB.

    Chave de upsert: cd_bairro (único por bairro na PB)
    $set cirúrgico em 'socioeconomico' — não toca em dados de educação.
    """
    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI")
    db_name   = os.getenv("MONGO_DB_NAME")
    if not mongo_uri:
        raise ValueError("MONGO_URI não definido. Verifique seu .env.")
    if not db_name:
        raise ValueError("MONGO_DB_NAME não definido. Verifique seu .env.")

    if df is None:
        from src.common.storage import get_storage_backend
        storage = storage or get_storage_backend()
        if not _GOLD_PATH.exists():
            raise FileNotFoundError(
                f"Gold não encontrado: {_GOLD_PATH}\n"
                "Execute o transform primeiro: make run-socioeconomico-transform-bairro"
            )
        logger.info("Carregando Gold: %s", _GOLD_PATH)
        df = storage.read_parquet(str(_GOLD_PATH))

    geometrias = _carregar_geometrias()

    logger.info("=" * 60)
    logger.info("LOAD — BAIRRO")
    logger.info("Registros: %d | Geometrias: %d", len(df), len(geometrias))
    logger.info("=" * 60)

    client = MongoClient(mongo_uri)
    try:
        colecao = client[db_name][_COLECAO]

        colecao.create_index("cd_bairro", unique=True, sparse=True)
        colecao.create_index("cd_municipio")
        colecao.create_index("uf", sparse=True)
        colecao.create_index([("geometria", "2dsphere")], sparse=True)

        operacoes = []
        sem_geom = 0

        for _, row in df.iterrows():
            cd_bairro = _val(row.get("CD_BAIRRO"))
            if cd_bairro is None:
                continue
            cd_bairro = str(cd_bairro)

            socioeconomico = _construir_socioeconomico(row)
            geom = geometrias.get(cd_bairro)
            if geom is None:
                sem_geom += 1

            set_payload: dict = {"socioeconomico": socioeconomico}
            if geom is not None:
                set_payload["geometria"] = geom

            # Sempre gravar nm_bairro no $set para garantir que o campo
            # exista mesmo em bairros sem escolas (que não passam pelo
            # pipeline de educação).
            nm_bairro = _val(row.get("NM_BAIRRO"))
            if nm_bairro is not None:
                set_payload["nm_bairro"] = nm_bairro

            update = {
                "$set": set_payload,
                "$setOnInsert": {
                    "cd_bairro":   cd_bairro,
                    "cd_municipio": _val(row.get("CD_MUN")),
                    "nm_municipio": _val(row.get("NM_MUN")),
                    "uf":          _val(row.get("uf")),
                },
            }

            operacoes.append(UpdateOne({"cd_bairro": cd_bairro}, update, upsert=True))

        if sem_geom:
            logger.warning("%d bairro(s) sem geometria no GPKG.", sem_geom)

        if not operacoes:
            logger.warning("Nenhuma operação gerada.")
            return 0

        resultado = colecao.bulk_write(operacoes, ordered=False)
        total = resultado.upserted_count + resultado.modified_count

        logger.info("=" * 60)
        logger.info("LOAD CONCLUÍDO")
        logger.info("  Inseridos  : %d", resultado.upserted_count)
        logger.info("  Atualizados: %d", resultado.modified_count)
        logger.info("  Total      : %d", total)
        logger.info("=" * 60)
        return total

    finally:
        client.close()


if __name__ == "__main__":
    run()

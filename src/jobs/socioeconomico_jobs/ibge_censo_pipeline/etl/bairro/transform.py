"""
Transform — Bairro (IBGE Censo 2022)

Mesma lógica do transform de município — só muda a granularidade.
Reutiliza integralmente as funções de indicadores.py.

Nota: o IBGE disponibiliza dados de bairro apenas para municípios com
bairros oficialmente delimitados.
"""
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml

from src.common.ibge_codes import sigla_uf_por_codigo_municipio
from src.common.storage import StorageBackend, get_storage_backend
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline import indicadores

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/ibge_censo.yml")


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load_config()

SILVER_DIR: Path = Path(_cfg["paths"]["silver"])
GOLD_OUTPUT: str = str(
    Path(_cfg["paths"]["gold"]) / "bairro_socioeconomico_nordeste.parquet"
)

_SILVER_INPUTS = {
    "basico": "ibge_censo2022_bairro_basico_nordeste.parquet",
    "demografia": "ibge_censo2022_bairro_demografia_nordeste.parquet",
    "cor_raca": "ibge_censo2022_bairro_cor_ou_raca_nordeste.parquet",
    "dom1": "ibge_censo2022_bairro_caracteristicas_domicilio1_nordeste.parquet",
    "dom2": "ibge_censo2022_bairro_caracteristicas_domicilio2_nordeste.parquet",
    "alfabetizacao": "ibge_censo2022_bairro_alfabetizacao_nordeste.parquet",
    "parentesco": "ibge_censo2022_bairro_parentesco_nordeste.parquet",
    "obitos": "ibge_censo2022_bairro_obitos_nordeste.parquet",
}

_CHAVE          = "CD_BAIRRO"
_COLUNA_AUXILIAR = "total_domicilios_particulares"


@dataclass
class TransformResult:
    df: pd.DataFrame
    bairros: int
    avisos: List[str] = field(default_factory=list)
    pop_total: float = 0.0


def _carregar_datasets(storage: StorageBackend) -> Dict[str, pd.DataFrame]:
    datasets = {}
    for nome, filename in _SILVER_INPUTS.items():
        path = str(SILVER_DIR / filename)
        if not Path(path).exists():
            raise FileNotFoundError(
                f"Arquivo Silver não encontrado: {path}\n"
                f"Execute o extract primeiro: make run-socioeconomico-extract"
            )
        datasets[nome] = storage.read_parquet(path)
        logger.info("  Carregado: %s (%d registros)", filename, len(datasets[nome]))
    return datasets


def _calcular_todos_indicadores(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    logger.info("Calculando indicadores...")

    # Prioridade 1
    ind_populacao  = indicadores.calcular_populacao(datasets["basico"])
    ind_etaria     = indicadores.calcular_estrutura_etaria(datasets["demografia"])
    ind_raca       = indicadores.calcular_raca(datasets["cor_raca"])
    ind_saneamento = indicadores.calcular_saneamento(datasets["dom2"], datasets["basico"])
    ind_alfa       = indicadores.calcular_alfabetizacao(datasets["alfabetizacao"])
    ind_familia    = indicadores.calcular_familia(datasets["parentesco"])

    # Prioridade 2
    ind_agua_inad   = indicadores.calcular_agua_inadequada(datasets["dom2"], datasets["basico"])
    ind_esgoto_inad = indicadores.calcular_esgoto_inadequado(datasets["dom2"], datasets["basico"])
    ind_lixo_inad   = indicadores.calcular_lixo_inadequado(datasets["dom2"], datasets["basico"])
    ind_dep         = indicadores.calcular_razao_dependencia(datasets["demografia"])
    ind_obitos      = indicadores.calcular_obitos(datasets["obitos"])
    ind_habitacao   = indicadores.calcular_habitacao(datasets["dom1"])

    # Prioridade 3
    ind_composicao  = indicadores.calcular_composicao_domiciliar(datasets["dom1"])
    ind_genero      = indicadores.calcular_genero_populacao(datasets["dom1"])
    ind_banheiro    = indicadores.calcular_saneamento_banheiro(datasets["dom2"], datasets["basico"])
    ind_encanamento = indicadores.calcular_agua_encanamento(datasets["dom2"], datasets["basico"])
    ind_raca_det    = indicadores.calcular_raca_detalhada(datasets["cor_raca"])
    ind_etaria_det  = indicadores.calcular_estrutura_etaria_detalhada(datasets["demografia"])

    df = ind_populacao
    for parcial in [
        ind_etaria, ind_raca, ind_saneamento, ind_alfa, ind_familia,
        ind_agua_inad, ind_esgoto_inad, ind_lixo_inad, ind_dep, ind_obitos, ind_habitacao,
        ind_composicao, ind_genero, ind_banheiro, ind_encanamento, ind_raca_det, ind_etaria_det,
    ]:
        df = df.merge(parcial, on=_CHAVE, how="outer")

    df = df.drop(columns=[_COLUNA_AUXILIAR], errors="ignore")

    meta_cols = [_CHAVE, "CD_MUN", "NM_MUN"]
    if "NM_BAIRRO" in datasets["basico"].columns:
        meta_cols.append("NM_BAIRRO")
    meta = datasets["basico"][meta_cols].copy()
    df = df.merge(meta, on=_CHAVE, how="left")

    logger.info("Merge concluído: %d bairros, %d colunas", len(df), len(df.columns))
    return df


def _validar_saida(df: pd.DataFrame) -> List[str]:
    avisos = []
    if len(df) == 0:
        avisos.append("Nenhum bairro encontrado — verifique o extract.")
    pop_total = df["total_populacao"].sum()
    if pop_total <= 0:
        avisos.append("População total zerada — verifique os dados do Silver.")
    return avisos


def _adicionar_metadados(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona metadados e deriva a UF a partir do código do município."""
    df = df.copy()
    df["ano_referencia"] = 2022
    df["fonte"] = "IBGE Censo Demográfico 2022"
    df["uf"] = df["CD_MUN"].map(sigla_uf_por_codigo_municipio)
    return df


def run(storage: Optional[StorageBackend] = None) -> TransformResult:
    storage = storage or get_storage_backend()

    logger.info("=" * 60)
    logger.info("TRANSFORM — BAIRRO")
    logger.info("=" * 60)

    logger.info("1/4 Carregando datasets do Silver...")
    datasets = _carregar_datasets(storage)

    logger.info("2/4 Calculando indicadores...")
    df = _calcular_todos_indicadores(datasets)

    logger.info("3/4 Adicionando metadados...")
    df = _adicionar_metadados(df)

    logger.info("4/4 Validando e salvando no Gold: %s", GOLD_OUTPUT)
    avisos = _validar_saida(df)
    for a in avisos:
        logger.warning("  - %s", a)

    storage.save_parquet(df, GOLD_OUTPUT)

    pop_total = df["total_populacao"].sum()
    logger.info("=" * 60)
    logger.info("TRANSFORM CONCLUÍDO — %d bairros | pop: %s | avisos: %d",
                len(df), f"{pop_total:,.0f}", len(avisos))
    logger.info("=" * 60)

    return TransformResult(df=df, bairros=len(df), avisos=avisos, pop_total=pop_total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
    run()

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml

from src.common.storage import StorageBackend, get_storage_backend
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline import indicadores

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/ibge_censo.yml")


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load_config()
_tcfg = _cfg["transform_municipio"]

SILVER_INPUTS: Dict[str, str] = _tcfg["silver_inputs"]
GOLD_OUTPUT: str = str(Path(_cfg["paths"]["gold"]) / _tcfg["gold_output"])
SILVER_DIR: Path = Path(_cfg["paths"]["silver"])
MUNICIPIOS_ESPERADOS: int = _tcfg["municipios_esperados"]
POP_TOTAL_MIN: float = _tcfg["pop_total_min"]
POP_TOTAL_MAX: float = _tcfg["pop_total_max"]

CONTRATOS_QUALIDADE: List[dict] = _tcfg["contratos_qualidade"]

_COLUNAS_NAO_INDICADORES = {"CD_MUN", "NM_MUN", "ano_referencia", "fonte", "uf"}

_COLUNA_AUXILIAR_SANEAMENTO = "total_domicilios_particulares"


@dataclass
class TransformResult:
    """
    Resultado do transform com dados e metadados de qualidade.

    Attributes:
        df:         DataFrame com os indicadores calculados.
        municipios: Número de municípios processados.
        avisos:     Avisos não-fatais encontrados na validação de saída.
        pop_total:  Soma da população total (benchmark rápido).
    """
    df: pd.DataFrame
    municipios: int
    avisos: List[str] = field(default_factory=list)
    pop_total: float = 0.0


def _carregar_datasets(storage: StorageBackend) -> Dict[str, pd.DataFrame]:
    """
    Carrega todos os Parquets Silver necessários para o transform.

    Raises:
        FileNotFoundError: se algum arquivo não existir no Silver.
    """
    datasets = {}
    for nome, filename in SILVER_INPUTS.items():
        path = str(SILVER_DIR / filename)
        if not Path(path).exists():
            raise FileNotFoundError(
                f"Arquivo Silver não encontrado: {path}\n"
                f"Execute o extract primeiro: make run-socioeconomico-extract"
            )
        datasets[nome] = storage.read_parquet(path)
        logger.info("  Carregado: %s (%d registros)", filename, len(datasets[nome]))

    return datasets



def _validar_entradas(datasets: Dict[str, pd.DataFrame]) -> None:
    """
    Valida shape e consistência dos datasets de entrada.

    Verifica:
    - Número de municípios (deve ser igual a municipios_esperados no config)
    - Consistência de CD_MUN entre todos os datasets
    - Ausência de duplicatas na chave CD_MUN

    Raises:
        ValueError: se qualquer validação falhar.
    """
    chaves_referencia = set(datasets["basico"]["CD_MUN"].tolist())

    for nome, df in datasets.items():
        _checar_contagem(nome, df)
        _checar_consistencia_chaves(nome, df, chaves_referencia)
        _checar_duplicatas(nome, df)

    logger.info("Validação de entradas OK: %d municípios em todos os datasets", MUNICIPIOS_ESPERADOS)


def _checar_contagem(nome: str, df: pd.DataFrame) -> None:
    n = len(df)
    if n != MUNICIPIOS_ESPERADOS:
        raise ValueError(
            f"Dataset '{nome}' tem {n} registros, esperado {MUNICIPIOS_ESPERADOS}. "
            f"Execute o extract novamente: make run-socioeconomico-extract"
        )


def _checar_consistencia_chaves(nome: str, df: pd.DataFrame, referencia: set) -> None:
    atual = set(df["CD_MUN"].tolist())
    diff = referencia.symmetric_difference(atual)
    if diff:
        raise ValueError(
            f"Dataset '{nome}' tem {len(diff)} municípios diferentes do basico. "
            f"Exemplos: {list(diff)[:5]}"
        )


def _checar_duplicatas(nome: str, df: pd.DataFrame) -> None:
    duplicatas = df["CD_MUN"].duplicated().sum()
    if duplicatas > 0:
        raise ValueError(
            f"Dataset '{nome}' tem {duplicatas} CD_MUN duplicados. "
            f"Dado corrompido — re-execute o extract."
        )


def _calcular_todos_indicadores(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Chama cada função de indicadores.py e faz merge sequencial por CD_MUN.

    Usa outer join para não perder municípios que eventualmente faltem
    em algum dataset — esses casos serão capturados pela validação de saída.
    """
    logger.info("Calculando indicadores...")

    # Prioridade 1
    ind_populacao  = indicadores.calcular_populacao(datasets["basico"])
    ind_etaria     = indicadores.calcular_estrutura_etaria(datasets["demografia"])
    ind_raca       = indicadores.calcular_raca(datasets["cor_raca"])
    ind_saneamento = indicadores.calcular_saneamento(datasets["dom2"], datasets["basico"])
    ind_alfa       = indicadores.calcular_alfabetizacao(datasets["alfabetizacao"])
    ind_familia    = indicadores.calcular_familia(datasets["parentesco"])

    # Prioridade 2
    ind_agua_inad    = indicadores.calcular_agua_inadequada(datasets["dom2"], datasets["basico"])
    ind_esgoto_inad  = indicadores.calcular_esgoto_inadequado(datasets["dom2"], datasets["basico"])
    ind_lixo_inad    = indicadores.calcular_lixo_inadequado(datasets["dom2"], datasets["basico"])
    ind_dep          = indicadores.calcular_razao_dependencia(datasets["demografia"])
    ind_obitos       = indicadores.calcular_obitos(datasets["obitos"])
    ind_habitacao    = indicadores.calcular_habitacao(datasets["dom1"])

    # Prioridade 3
    ind_composicao   = indicadores.calcular_composicao_domiciliar(datasets["dom1"])
    ind_genero       = indicadores.calcular_genero_populacao(datasets["dom1"])
    ind_banheiro     = indicadores.calcular_saneamento_banheiro(datasets["dom2"], datasets["basico"])
    ind_encanamento  = indicadores.calcular_agua_encanamento(datasets["dom2"], datasets["basico"])
    ind_raca_det     = indicadores.calcular_raca_detalhada(datasets["cor_raca"])
    ind_etaria_det   = indicadores.calcular_estrutura_etaria_detalhada(datasets["demografia"])

    df = ind_populacao
    for parcial in [
        ind_etaria, ind_raca, ind_saneamento, ind_alfa, ind_familia,
        ind_agua_inad, ind_esgoto_inad, ind_lixo_inad, ind_dep, ind_obitos, ind_habitacao,
        ind_composicao, ind_genero, ind_banheiro, ind_encanamento, ind_raca_det, ind_etaria_det,
    ]:
        df = df.merge(parcial, on="CD_MUN", how="outer")

    df = df.drop(columns=[_COLUNA_AUXILIAR_SANEAMENTO], errors="ignore")

    nomes = datasets["basico"][["CD_MUN", "NM_MUN"]].copy()
    df = df.merge(nomes, on="CD_MUN", how="left")

    logger.info("Merge concluído: %d municípios, %d colunas", len(df), len(df.columns))
    return df


def _adicionar_metadados(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas de rastreabilidade ao DataFrame final."""
    df = df.copy()
    df["ano_referencia"] = 2022
    df["fonte"]          = "IBGE Censo Demográfico 2022"
    df["uf"]             = "PB"
    return df


def _ordenar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reordena colunas para estrutura legível:
    identificação → indicadores → metadados.
    """
    colunas_id   = ["CD_MUN", "NM_MUN", "uf"]
    colunas_meta = ["ano_referencia", "fonte"]
    colunas_indicadores = [
        c for c in df.columns
        if c not in colunas_id + colunas_meta
    ]
    ordem = colunas_id + colunas_indicadores + colunas_meta
    return df[[c for c in ordem if c in df.columns]]


def _validar_saida(df: pd.DataFrame) -> List[str]:
    """
    Valida o DataFrame de saída contra os contratos de qualidade do config.

    Não lança exceção — retorna lista de avisos para que o chamador
    decida se aborta ou continua. Valores fora do range indicam mudança
    nos dados de entrada ou nas fórmulas.

    Returns:
        Lista de strings com avisos (vazia se tudo OK).
    """
    avisos: List[str] = []

    avisos += _checar_contagem_saida(df)
    avisos += _checar_nulos(df)
    avisos += _checar_ranges(df)
    avisos += _checar_consistencia_etaria(df)
    avisos += _checar_benchmark_populacao(df)

    return avisos


def _checar_contagem_saida(df: pd.DataFrame) -> List[str]:
    if len(df) != MUNICIPIOS_ESPERADOS:
        return [f"CRÍTICO: {len(df)} municípios no output, esperado {MUNICIPIOS_ESPERADOS}"]
    return []


def _checar_nulos(df: pd.DataFrame) -> List[str]:
    avisos = []
    for col in df.columns:
        if col in _COLUNAS_NAO_INDICADORES:
            continue
        nulos = df[col].isna().sum()
        if nulos > 0:
            avisos.append(f"Coluna '{col}' tem {nulos} valores nulos")
    return avisos


def _checar_ranges(df: pd.DataFrame) -> List[str]:
    avisos = []
    for contrato in CONTRATOS_QUALIDADE:
        col    = contrato["coluna"]
        minimo = contrato["min"]
        maximo = contrato["max"]

        if col not in df.columns:
            avisos.append(f"Coluna esperada ausente: '{col}'")
            continue

        valores = df[col].dropna()
        if valores.empty:
            avisos.append(f"Coluna '{col}' está completamente vazia")
            continue

        abaixo = (valores < minimo).sum()
        acima  = (valores > maximo).sum()

        if abaixo > 0:
            exemplos = df.loc[df[col] < minimo, ["NM_MUN", col]].head(3)
            avisos.append(
                f"'{col}': {abaixo} valor(es) abaixo do mínimo ({minimo}). "
                f"Exemplos: {exemplos.to_dict('records')}"
            )
        if acima > 0:
            exemplos = df.loc[df[col] > maximo, ["NM_MUN", col]].head(3)
            avisos.append(
                f"'{col}': {acima} valor(es) acima do máximo ({maximo}). "
                f"Exemplos: {exemplos.to_dict('records')}"
            )
    return avisos


def _checar_consistencia_etaria(df: pd.DataFrame) -> List[str]:
    """Soma de crianças 0-9 + idosos 60+ não pode ultrapassar 100%."""
    soma = df["pct_criancas_0_9"] + df["pct_idosos_60_mais"]
    invalidos = (soma > 100).sum()
    if invalidos > 0:
        return [f"pct_criancas_0_9 + pct_idosos_60_mais > 100% em {invalidos} município(s)"]
    return []


def _checar_benchmark_populacao(df: pd.DataFrame) -> List[str]:
    """
    Valida a soma da população total contra o benchmark da PB.

    v0001 conta domicílios particulares — diferença de ~85k para o
    total oficial do IBGE é esperada e está documentada no config.
    """
    pop_total = df["total_populacao"].sum()
    if not (POP_TOTAL_MIN <= pop_total <= POP_TOTAL_MAX):
        return [
            f"Pop total PB fora do range esperado "
            f"({POP_TOTAL_MIN:,.0f}–{POP_TOTAL_MAX:,.0f}): {pop_total:,.0f}. "
            f"Verifique se o filtro CD_UF==25 foi aplicado corretamente."
        ]
    return []


def run(storage: Optional[StorageBackend] = None) -> TransformResult:
    """
    Executa o transform completo: Silver → indicadores → validação → Gold.

    Falha explicitamente (ValueError/FileNotFoundError) se:
    - Algum arquivo Silver estiver ausente
    - O número de municípios for diferente do esperado
    - Houver duplicatas ou chaves inconsistentes entre datasets

    Emite avisos (sem falhar) se:
    - Algum indicador tiver valores fora dos ranges do config
    - Houver nulos inesperados no output

    Returns:
        TransformResult com DataFrame, contagem de municípios e avisos.
    """
    storage = storage or get_storage_backend()

    logger.info("=" * 60)
    logger.info("TRANSFORM — MUNICÍPIO SOCIOECONÔMICO")
    logger.info("=" * 60)

    logger.info("1/5 Carregando datasets do Silver...")
    datasets = _carregar_datasets(storage)

    logger.info("2/5 Validando entradas...")
    _validar_entradas(datasets)

    logger.info("3/5 Calculando indicadores...")
    df = _calcular_todos_indicadores(datasets)
    df = _adicionar_metadados(df)
    df = _ordenar_colunas(df)

    logger.info("4/5 Validando qualidade da saída...")
    avisos = _validar_saida(df)
    _logar_avisos(avisos)

    logger.info("5/5 Salvando no Gold: %s", GOLD_OUTPUT)
    storage.save_parquet(df, GOLD_OUTPUT)

    pop_total = df["total_populacao"].sum()
    _logar_resumo(df, pop_total, avisos)

    return TransformResult(
        df=df,
        municipios=len(df),
        avisos=avisos,
        pop_total=pop_total,
    )


def _logar_avisos(avisos: List[str]) -> None:
    if avisos:
        logger.warning("%d aviso(s) de qualidade encontrado(s):", len(avisos))
        for aviso in avisos:
            logger.warning("  - %s", aviso)
    else:
        logger.info("Validação de qualidade: sem avisos")


def _logar_resumo(df: pd.DataFrame, pop_total: float, avisos: List[str]) -> None:
    logger.info("=" * 60)
    logger.info("TRANSFORM CONCLUÍDO")
    logger.info("  Municípios : %d", len(df))
    logger.info("  Colunas    : %d", len(df.columns))
    logger.info("  Pop total  : %s", f"{pop_total:,.0f}")
    logger.info("  Avisos     : %d", len(avisos))
    logger.info("  Output     : %s", GOLD_OUTPUT)
    logger.info("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )
    result = run()
    if result.avisos:
        print(f"\n{len(result.avisos)} aviso(s) — verifique os logs acima.")
    else:
        print(f"\nTransform concluído: {result.municipios} municípios, pop={result.pop_total:,.0f}")

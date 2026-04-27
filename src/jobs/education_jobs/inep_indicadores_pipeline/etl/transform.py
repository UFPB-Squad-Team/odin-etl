import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.common.storage import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/inep_indicadores.yml")

_META_COLS = [
    "NU_ANO_CENSO", "NO_REGIAO", "SG_UF",
    "CO_MUNICIPIO", "NO_MUNICIPIO",
    "CO_ENTIDADE", "NO_ENTIDADE",
    "NO_CATEGORIA", "NO_DEPENDENCIA",
]


@dataclass
class TransformResult:
    df: pd.DataFrame
    escolas: int
    avisos: list[str] = field(default_factory=list)


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _to_float(value) -> Optional[float]:
    """Converte para float, retornando None para valores inválidos."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extrair_coluna(df: pd.DataFrame, col_name: Optional[str]) -> pd.Series:
    """Extrai coluna do DataFrame, retornando série de None se não existir."""
    if col_name and col_name in df.columns:
        return df[col_name].apply(_to_float)
    return pd.Series([None] * len(df), index=df.index)


def _combinar_fontes(
    dados: dict[str, pd.DataFrame],
    cfg: dict,
) -> pd.DataFrame:
    """
    Combina todos os DataFrames de fontes em um único DataFrame
    com o schema do Gold, usando CO_ENTIDADE como chave de join.

    Estratégia:
    - Começa com a lista de escolas do arquivo mais completo (DSU tem mais escolas)
    - Faz left join de cada fonte pela chave CO_ENTIDADE
    - Mapeia colunas para nomes canônicos do schema Gold
    """
    fontes_cfg = cfg["fontes"]
    schema = cfg["schema_gold"]

    if not dados:
        raise ValueError(
            "Nenhuma fonte disponível para transformar. "
            "Verifique se o extract foi executado com sucesso."
        )

    base_sigla = "dsu" if "dsu" in dados else list(dados.keys())[0]
    df_base = dados[base_sigla][_META_COLS].copy()
    df_base = df_base.drop_duplicates(subset=["CO_ENTIDADE"])
    logger.info("Base: %d escolas únicas (fonte: %s)", len(df_base), base_sigla)

    def _join_fonte(df_acc: pd.DataFrame, sigla: str, df_fonte: pd.DataFrame) -> pd.DataFrame:
        if sigla not in dados:
            return df_acc
        ind_cols = [c for c in df_fonte.columns if c not in _META_COLS]
        cols_keep = ["CO_ENTIDADE"] + ind_cols
        df_join = df_fonte[cols_keep].copy()
        df_join = df_join.drop_duplicates(subset=["CO_ENTIDADE"])
        return df_acc.merge(df_join, on="CO_ENTIDADE", how="left")

    df = df_base
    for sigla in dados:
        df = _join_fonte(df, sigla, dados[sigla])

    logger.info("Após joins: %d escolas, %d colunas", len(df), len(df.columns))
    return df


def _montar_documento(row: pd.Series, schema: dict) -> dict:
    """
    Monta o documento de indicadores no formato compatível com o pipeline antigo.
    Mesmo schema que o transform da Base dos Dados produzia.
    """
    def f(col_name: Optional[str]) -> Optional[float]:
        if not col_name:
            return None
        return _to_float(row.get(col_name))

    ei = schema.get("educacao_infantil", {})
    efi = schema.get("fundamental_anos_iniciais", {})
    eff = schema.get("fundamental_anos_finais", {})
    em = schema.get("ensino_medio", {})

    return {
        "ano": _to_float(row.get("NU_ANO_CENSO")),
        "id_municipio": row.get("CO_MUNICIPIO"),
        "id_escola": row.get("CO_ENTIDADE"),
        "localizacao": row.get("NO_CATEGORIA"),
        "rede": row.get("NO_DEPENDENCIA"),
        "icg_nivel_complexidade_gestao_escola": row.get("icg_nivel"),

        "ideb_anos_iniciais": _to_float(row.get(schema.get("ideb_anos_iniciais"))),
        "ideb_anos_finais":   _to_float(row.get(schema.get("ideb_anos_finais"))),
        "ideb_ensino_medio":  _to_float(row.get(schema.get("ideb_ensino_medio"))),

        "educacao_infantil": {
            "alunos_por_turma":   f(ei.get("alunos_por_turma")),
            "horas_aula_diarias": f(ei.get("horas_aula_diarias")),
            "docentes_superior":  f(ei.get("docentes_superior")),
            "afd":                f(ei.get("afd")),
        },
        "fundamental_anos_iniciais": {
            "alunos_por_turma":   f(efi.get("alunos_por_turma")),
            "horas_aula_diarias": f(efi.get("horas_aula_diarias")),
            "docentes_superior":  f(efi.get("docentes_superior")),
            "tdi":                f(efi.get("tdi")),
            "taxa_aprovacao":     f(efi.get("taxa_aprovacao")),
            "taxa_reprovacao":    f(efi.get("taxa_reprovacao")),
            "taxa_abandono":      f(efi.get("taxa_abandono")),
            "tnr":                f(efi.get("tnr")),
            "afd":                f(efi.get("afd")),
            "ied":                f(efi.get("ied")),
        },
        "fundamental_anos_finais": {
            "alunos_por_turma":   f(eff.get("alunos_por_turma")),
            "horas_aula_diarias": f(eff.get("horas_aula_diarias")),
            "docentes_superior":  f(eff.get("docentes_superior")),
            "tdi":                f(eff.get("tdi")),
            "taxa_aprovacao":     f(eff.get("taxa_aprovacao")),
            "taxa_reprovacao":    f(eff.get("taxa_reprovacao")),
            "taxa_abandono":      f(eff.get("taxa_abandono")),
            "tnr":                f(eff.get("tnr")),
            "afd":                f(eff.get("afd")),
            "ied":                f(eff.get("ied")),
        },
        "ensino_medio": {
            "alunos_por_turma":   f(em.get("alunos_por_turma")),
            "horas_aula_diarias": f(em.get("horas_aula_diarias")),
            "docentes_superior":  f(em.get("docentes_superior")),
            "tdi":                f(em.get("tdi")),
            "taxa_aprovacao":     f(em.get("taxa_aprovacao")),
            "taxa_reprovacao":    f(em.get("taxa_reprovacao")),
            "taxa_abandono":      f(em.get("taxa_abandono")),
            "tnr":                f(em.get("tnr")),
            "afd":                f(em.get("afd")),
            "ied":                f(em.get("ied")),
        },
    }


def _renomear_colunas(dados: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """
    Renomeia as colunas de cada fonte para os nomes canônicos do schema Gold.
    Ex: ATU.FUN_AI_CAT_0 → atu_efi
    """
    fontes_cfg = cfg["fontes"]
    renomeados = {}

    for sigla, df in dados.items():
        if sigla not in fontes_cfg:
            continue
        mapa = fontes_cfg[sigla]["colunas"]
        # Inverter: {col_original: nome_canonico}
        rename_map = {v: f"{sigla}_{k}" for k, v in mapa.items() if v in df.columns}
        renomeados[sigla] = df.rename(columns=rename_map)
        logger.debug("%s: renomeadas %d colunas", sigla, len(rename_map))

    return renomeados


def _validar_saida(df: pd.DataFrame, filtro_uf: str) -> list[str]:
    """Valida o DataFrame de saída contra contratos de qualidade."""
    avisos = []

    if len(df) == 0:
        avisos.append("CRÍTICO: DataFrame vazio")
        return avisos

    if "CO_ENTIDADE" not in df.columns:
        avisos.append("CRÍTICO: coluna CO_ENTIDADE ausente")

    if len(df) < 3_000:
        avisos.append(f"Poucas escolas: {len(df)} (esperado ~3.700 para PB)")

    if "SG_UF" in df.columns:
        outras_ufs = df[df["SG_UF"] != filtro_uf]["SG_UF"].unique()
        if len(outras_ufs) > 0:
            avisos.append(f"Escolas de outras UFs encontradas: {outras_ufs}")

    return avisos


def _calcular_afd_ied(dados: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """
    Calcula indicadores agregados para AFD e IED.

    AFD: % docentes adequados = soma dos grupos 1 e 2 (mais adequados)
    IED: % docentes regulares = soma dos níveis 1 e 2 (mais regulares)

    Isso mantém compatibilidade com o pipeline antigo que retornava
    um único valor por nível de ensino.
    """
    resultado = dict(dados)

    if "afd" in dados:
        df = dados["afd"].copy()
        for nivel, sufixo in [("ei", "ei"), ("efi", "efi"), ("eff", "eff"), ("em", "em")]:
            g1 = f"afd_{nivel}_g1"
            g2 = f"afd_{nivel}_g2"
            if g1 in df.columns and g2 in df.columns:
                df[f"afd_{sufixo}"] = (
                    pd.to_numeric(df[g1], errors="coerce").fillna(0) +
                    pd.to_numeric(df[g2], errors="coerce").fillna(0)
                ).where(df[g1].notna() | df[g2].notna(), None)
        resultado["afd"] = df

    if "ied" in dados:
        df = dados["ied"].copy()
        for nivel, sufixo in [("efi", "efi"), ("eff", "eff"), ("em", "em")]:
            n1 = f"ied_{nivel}_n1"
            n2 = f"ied_{nivel}_n2"
            if n1 in df.columns and n2 in df.columns:
                df[f"ied_{sufixo}"] = (
                    pd.to_numeric(df[n1], errors="coerce").fillna(0) +
                    pd.to_numeric(df[n2], errors="coerce").fillna(0)
                ).where(df[n1].notna() | df[n2].notna(), None)
        resultado["ied"] = df

    return resultado


def run(
    dados: Optional[dict[str, pd.DataFrame]] = None,
    storage: Optional[StorageBackend] = None,
) -> TransformResult:
    """
    Transforma os DataFrames de cada fonte no Gold de indicadores.

    Args:
        dados:   Dict {sigla: DataFrame} do extract. Se None, executa o extract.
        storage: Backend de armazenamento para salvar o Gold.

    Returns:
        TransformResult com DataFrame, contagem de escolas e avisos.
    """
    cfg = _load_config()
    storage = storage or get_storage_backend()
    filtro_uf = cfg["filtro_uf"]
    gold_path = str(Path(cfg["paths"]["gold"]) / cfg["gold_output"])

    logger.info("=" * 60)
    logger.info("TRANSFORM — Indicadores INEP")
    logger.info("=" * 60)

    if dados is None:
        from src.jobs.education_jobs.inep_indicadores_pipeline.etl.extract import run as run_extract
        dados = run_extract(storage=storage)

    logger.info("1/4 Renomeando colunas para schema canônico...")
    dados_renomeados = _renomear_colunas(dados, cfg)

    logger.info("   Calculando AFD e IED agregados (grupos 1+2)...")
    dados_renomeados = _calcular_afd_ied(dados_renomeados)

    logger.info("2/4 Combinando fontes por CO_ENTIDADE...")
    df_combinado = _combinar_fontes(dados_renomeados, cfg)

    logger.info("3/4 Montando documentos de indicadores...")
    schema = cfg["schema_gold"]
    docs = df_combinado.apply(lambda row: _montar_documento(row, schema), axis=1)
    df_gold = pd.DataFrame(list(docs))

    logger.info("4/4 Validando e salvando Gold: %s", gold_path)
    avisos = _validar_saida(df_combinado, filtro_uf)
    for a in avisos:
        logger.warning("  - %s", a)

    storage.save_parquet(df_gold, gold_path)

    logger.info("=" * 60)
    logger.info("TRANSFORM CONCLUÍDO — %d escolas | avisos: %d", len(df_gold), len(avisos))
    logger.info("=" * 60)

    return TransformResult(df=df_gold, escolas=len(df_gold), avisos=avisos)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
    run()

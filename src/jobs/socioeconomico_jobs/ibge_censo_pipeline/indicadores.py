import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Funções auxiliares internas
# ---------------------------------------------------------------------------

def _chave_geografica(df: pd.DataFrame) -> str:
    """
    Detecta automaticamente a coluna de chave geográfica do DataFrame.

    Ordem de prioridade: CD_SETOR > CD_BAIRRO > CD_MUN.
    Isso garante que a mesma função funciona para setor, bairro e município.

    Raises:
        ValueError: se nenhuma chave conhecida for encontrada.
    """
    for col in ("CD_SETOR", "CD_BAIRRO", "CD_MUN"):
        if col in df.columns:
            return col
    raise ValueError(
        f"Nenhuma chave geográfica encontrada. Esperado: CD_SETOR, CD_BAIRRO ou CD_MUN. "
        f"Colunas disponíveis: {list(df.columns[:10])}"
    )


def _to_num(df: pd.DataFrame, colunas: List[str]) -> pd.DataFrame:
    """
    Converte colunas para float, tratando vírgula decimal (padrão IBGE) e
    valores inválidos como NaN.

    O IBGE usa vírgula como separador decimal em algumas colunas (ex: v0005 = "2,9").
    Esta função normaliza isso antes de converter.

    Args:
        df:      DataFrame (não é modificado — retorna cópia)
        colunas: Nomes das colunas a converter

    Returns:
        DataFrame com as colunas convertidas para float.
    """
    df = df.copy()
    for col in colunas:
        if col not in df.columns:
            continue
        # Tratar vírgula decimal independente do dtype (object ou ArrowDtype do PyArrow)
        # O IBGE usa vírgula em algumas colunas (ex: v0005 = "2,9")
        try:
            df[col] = df[col].astype(str).str.replace(",", ".", regex=False)
        except Exception:
            pass
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _pct(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
    """
    Calcula percentual (0–100) com tratamento seguro de divisão por zero.

    Onde o denominador é zero ou NaN, retorna None (não 0 nem inf),
    para que a API possa distinguir "dado ausente" de "zero real".

    Args:
        numerador:   Série com os valores do numerador
        denominador: Série com os valores do denominador

    Returns:
        Série com percentuais arredondados a 1 casa decimal.
        Retorna None onde denominador <= 0 ou é NaN.
    """
    resultado = (numerador / denominador * 100).round(1)
    resultado = resultado.replace([np.inf, -np.inf], None)
    resultado = resultado.where(denominador > 0, None)
    return resultado


# ---------------------------------------------------------------------------
# Indicadores 1 e 2 — População e Domicílios
# ---------------------------------------------------------------------------

def calcular_populacao(df_basico: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de população e domicílios.

    Fonte: dataset 'basico'
    Silver: ibge_censo2022_{granularidade}_basico_pb.parquet

    Indicadores:
        total_populacao               — v0001: total de moradores
        total_domicilios_particulares — v0003: domicílios particulares (usado como
                                        denominador nos cálculos de saneamento)
        media_moradores_por_domicilio — v0005: média de moradores por domicílio
                                        ⚠️ usa vírgula decimal no CSV original

    Args:
        df_basico: DataFrame do arquivo 'basico'

    Returns:
        DataFrame com [chave_geografica, total_populacao,
                       total_domicilios_particulares, media_moradores_por_domicilio]
    """
    chave = _chave_geografica(df_basico)
    df = _to_num(df_basico, ["v0001", "v0003", "v0005"])

    resultado = df[[chave]].copy()
    resultado["total_populacao"] = df["v0001"].astype("Int64")
    resultado["total_domicilios_particulares"] = df["v0003"].astype("Int64")
    resultado["media_moradores_por_domicilio"] = df["v0005"].round(1)

    logger.info(
        f"calcular_populacao: {len(resultado)} registros | "
        f"pop total: {resultado['total_populacao'].sum():,}"
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicadores 3 e 4 — Estrutura Etária
# ---------------------------------------------------------------------------

def calcular_estrutura_etaria(df_demografia: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula percentuais de crianças (0–9 anos) e idosos (60+ anos).

    Fonte: dataset 'demografia'
    Silver: ibge_censo2022_{granularidade}_demografia_pb.parquet

    Mapeamento de variáveis (confirmado no dicionário IBGE):
        V01006 — Total de moradores (denominador)

        Estrutura do dataset de demografia (verificada no dicionário oficial):
            V01009..V01019 — faixas masculinas: 0-4, 5-9, 10-14, 15-19, 20-24,
                             25-29, 30-39, 40-49, 50-59, 60-69, 70+
            V01020..V01030 — faixas femininas: mesmas faixas
            V01031..V01041 — faixas TOTAIS (masc+fem): mesmas faixas

        Para os indicadores usamos as faixas TOTAIS (V01031..V01041):
            V01031 — 0 a 4 anos (total)
            V01032 — 5 a 9 anos (total)
            V01040 — 60 a 69 anos (total)
            V01041 — 70 anos ou mais (total)

    Indicadores:
        pct_criancas_0_9   — (V01031 + V01032) / V01006 × 100
        pct_idosos_60_mais — (V01040 + V01041) / V01006 × 100

    Args:
        df_demografia: DataFrame do arquivo 'demografia'

    Returns:
        DataFrame com [chave_geografica, pct_criancas_0_9, pct_idosos_60_mais]
    """
    chave = _chave_geografica(df_demografia)

    # Usar as faixas TOTAIS (V01031..V01041) — masc+fem juntos
    # Confirmado no dicionário IBGE: V01031=0-4, V01032=5-9, V01040=60-69, V01041=70+
    cols_0_9 = ["V01031", "V01032"]   # 0-4 e 5-9 anos (total)
    cols_60p = ["V01040", "V01041"]   # 60-69 e 70+ anos (total)
    todas    = ["V01006"] + cols_0_9 + cols_60p

    df = _to_num(df_demografia, todas)

    pop_0_9 = df[cols_0_9].sum(axis=1)
    pop_60p = df[cols_60p].sum(axis=1)
    total   = df["V01006"]

    resultado = df[[chave]].copy()
    resultado["pct_criancas_0_9"]   = _pct(pop_0_9, total)
    resultado["pct_idosos_60_mais"] = _pct(pop_60p, total)

    logger.info(
        f"calcular_estrutura_etaria: {len(resultado)} registros | "
        f"pct_criancas_0_9 média: {resultado['pct_criancas_0_9'].mean():.1f}% | "
        f"pct_idosos_60_mais média: {resultado['pct_idosos_60_mais'].mean():.1f}%"
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicador 5 — Cor/Raça
# ---------------------------------------------------------------------------

def calcular_raca(df_cor_raca: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o percentual de população preta + parda.

    Fonte: dataset 'cor_ou_raca'
    Silver: ibge_censo2022_{granularidade}_cor_ou_raca_pb.parquet

    Mapeamento de variáveis:
        V01317 — branca
        V01318 — preta
        V01319 — amarela
        V01320 — parda
        V01321 — indígena
        denominador = soma de todas as raças (V01317..V01321)

    Indicadores:
        pct_preta_parda — (V01318 + V01320) / total_raça × 100

    Args:
        df_cor_raca: DataFrame do arquivo 'cor_ou_raca'

    Returns:
        DataFrame com [chave_geografica, pct_preta_parda]
    """
    chave = _chave_geografica(df_cor_raca)

    cols = ["V01317", "V01318", "V01319", "V01320", "V01321"]
    df = _to_num(df_cor_raca, cols)

    preta_parda = df["V01318"] + df["V01320"]
    total_raca  = df[cols].sum(axis=1)

    resultado = df[[chave]].copy()
    resultado["pct_preta_parda"] = _pct(preta_parda, total_raca)

    logger.info(
        f"calcular_raca: {len(resultado)} registros | "
        f"pct_preta_parda média: {resultado['pct_preta_parda'].mean():.1f}%"
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicadores 6, 7 e 8 — Saneamento
# ---------------------------------------------------------------------------

def calcular_saneamento(
    df_domicilio2: pd.DataFrame,
    df_basico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula indicadores de saneamento básico: água, esgoto e lixo.

    ⚠️ ATENÇÃO — descobertas da EDA que diferem do plano original:
        1. V00001 não existe nos datasets — o denominador correto é v0003
           (domicílios particulares) do dataset 'basico'.
        2. V00397 e V00398 (lixo coletado) estão em domicilio2, não em domicilio3.
           O dataset domicilio3 não contém essas variáveis.

    Fonte: datasets 'caracteristicas_domicilio2' + 'basico'
    Silver: ibge_censo2022_{granularidade}_caracteristicas_domicilio2_pb.parquet
            ibge_censo2022_{granularidade}_basico_pb.parquet

    Mapeamento de variáveis:
        V00111 — domicílios com água da rede geral de distribuição
        V00309 — domicílios com esgoto via rede geral
        V00397 — domicílios com lixo coletado por serviço de limpeza
        V00398 — domicílios com lixo coletado em caçamba
        v0003  — total de domicílios particulares (denominador, vem do basico)

    Indicadores:
        pct_agua_rede_geral  — V00111 / v0003 × 100
        pct_esgoto_rede_geral — V00309 / v0003 × 100
        pct_lixo_coletado    — (V00397 + V00398) / v0003 × 100

    Args:
        df_domicilio2: DataFrame do arquivo 'caracteristicas_domicilio2'
        df_basico:     DataFrame do arquivo 'basico' (fornece o denominador v0003)

    Returns:
        DataFrame com [chave_geografica, pct_agua_rede_geral,
                       pct_esgoto_rede_geral, pct_lixo_coletado]
    """
    chave = _chave_geografica(df_domicilio2)

    df2 = _to_num(df_domicilio2, ["V00111", "V00309", "V00397", "V00398"])
    dfb = _to_num(df_basico, ["v0003"])

    denominador = df2[[chave]].merge(
        dfb[[chave, "v0003"]],
        on=chave,
        how="left",
    )["v0003"]

    resultado = df2[[chave]].copy()
    resultado["pct_agua_rede_geral"]   = _pct(df2["V00111"], denominador)
    resultado["pct_esgoto_rede_geral"] = _pct(df2["V00309"], denominador)
    resultado["pct_lixo_coletado"]     = _pct(df2["V00397"] + df2["V00398"], denominador)

    logger.info(
        f"calcular_saneamento: {len(resultado)} registros | "
        f"água: {resultado['pct_agua_rede_geral'].mean():.1f}% | "
        f"esgoto: {resultado['pct_esgoto_rede_geral'].mean():.1f}% | "
        f"lixo: {resultado['pct_lixo_coletado'].mean():.1f}%"
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicador 9 — Alfabetização
# ---------------------------------------------------------------------------

def calcular_alfabetizacao(df_alfabetizacao: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a taxa de analfabetismo para pessoas de 15 anos ou mais.

    Fonte: dataset 'alfabetizacao'
    Silver: ibge_censo2022_{granularidade}_alfabetizacao_pb.parquet

    Mapeamento de variáveis (confirmado no dicionário IBGE):
        V00901 — "15 anos ou mais, Morador não sabe ler e escrever"
                 ⚠️ O nome no dicionário é confuso — V00901 são os NÃO-alfabetizados.
        V00748..V00760 — "Pessoas alfabetizadas, [faixa 15+]" (13 faixas)
                         Somamos para obter o total de alfabetizados 15+.
        denominador = V00901 + soma(V00748..V00760)

    Indicadores:
        taxa_analfabetismo_15_mais — V00901 / (V00901 + alfabetizados_15+) × 100

    Args:
        df_alfabetizacao: DataFrame do arquivo 'alfabetizacao'

    Returns:
        DataFrame com [chave_geografica, taxa_analfabetismo_15_mais]
    """
    chave = _chave_geografica(df_alfabetizacao)

    # Colunas de alfabetizados por faixa etária 15+ (V00748 a V00760)
    cols_alfa_15p = [f"V00{i}" for i in range(748, 761)]  # V00748..V00760

    todas = ["V00901"] + cols_alfa_15p
    df = _to_num(df_alfabetizacao, todas)

    nao_alfabetizados = df["V00901"]
    alfabetizados_15p = df[cols_alfa_15p].sum(axis=1)
    total_15p = nao_alfabetizados + alfabetizados_15p

    resultado = df[[chave]].copy()
    resultado["taxa_analfabetismo_15_mais"] = _pct(nao_alfabetizados, total_15p)

    logger.info(
        f"calcular_alfabetizacao: {len(resultado)} registros | "
        f"taxa_analfabetismo_15_mais média: {resultado['taxa_analfabetismo_15_mais'].mean():.1f}%"
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicador 10 — Estrutura Familiar
# ---------------------------------------------------------------------------

def calcular_familia(df_parentesco: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o percentual de domicílios com responsável do sexo feminino.

    Fonte: dataset 'parentesco'
    Silver: ibge_censo2022_{granularidade}_parentesco_pb.parquet

    Mapeamento de variáveis (confirmado no dicionário IBGE):
        V01042 — "Pessoa responsável pelo domicílio" (total)
        V01063 — "Pessoa responsável pelo domicílio, Sexo feminino"

    Indicadores:
        pct_responsavel_feminino — V01063 / V01042 × 100

    Args:
        df_parentesco: DataFrame do arquivo 'parentesco'

    Returns:
        DataFrame com [chave_geografica, pct_responsavel_feminino]
    """
    chave = _chave_geografica(df_parentesco)

    df = _to_num(df_parentesco, ["V01042", "V01063"])

    resultado = df[[chave]].copy()
    resultado["pct_responsavel_feminino"] = _pct(df["V01063"], df["V01042"])

    logger.info(
        f"calcular_familia: {len(resultado)} registros | "
        f"pct_responsavel_feminino média: {resultado['pct_responsavel_feminino'].mean():.1f}%"
    )
    return resultado

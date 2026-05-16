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
    Busca case-insensitive e reconhece aliases do IBGE (ex: 'setor' = 'CD_SETOR').

    Raises:
        ValueError: se nenhuma chave conhecida for encontrada.
    """
    # Mapa: nome canônico → aliases aceitos (todos em uppercase para comparação)
    _ALIASES = {
        "CD_SETOR": {"CD_SETOR", "SETOR"},
        "CD_BAIRRO": {"CD_BAIRRO", "BAIRRO"},
        "CD_MUN":   {"CD_MUN", "MUN"},
    }
    colunas_upper = {col.upper(): col for col in df.columns}
    for chave_canonica, aliases in _ALIASES.items():
        for alias in aliases:
            if alias in colunas_upper:
                return colunas_upper[alias]
    raise ValueError(
        f"Nenhuma chave geográfica encontrada. Esperado: CD_SETOR, CD_BAIRRO ou CD_MUN. "
        f"Colunas disponíveis: {list(df.columns[:10])}"
    )


# Mapa de aliases → nome canônico (para normalização)
_ALIAS_PARA_CANONICO = {
    "setor": "CD_SETOR",
    "bairro": "CD_BAIRRO",
    "mun": "CD_MUN",
}


def _normalizar_chave(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renomeia a coluna de chave geográfica para o nome canônico (CD_SETOR, CD_BAIRRO, CD_MUN).
    Necessário porque o IBGE usa nomes inconsistentes entre datasets (ex: 'setor' vs 'CD_SETOR').
    """
    chave_atual = _chave_geografica(df)
    canonico = _ALIAS_PARA_CANONICO.get(chave_atual.lower(), chave_atual.upper())
    if chave_atual != canonico and canonico not in df.columns:
        return df.rename(columns={chave_atual: canonico})
    return df


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
    df_basico = _normalizar_chave(df_basico)
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
    df_demografia = _normalizar_chave(df_demografia)
    chave = _chave_geografica(df_demografia)
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
    df_cor_raca = _normalizar_chave(df_cor_raca)
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
    df_domicilio2 = _normalizar_chave(df_domicilio2)
    df_basico     = _normalizar_chave(df_basico)
    chave_dom2   = _chave_geografica(df_domicilio2)
    chave_basico = _chave_geografica(df_basico)

    df2 = _to_num(df_domicilio2, ["V00111", "V00309", "V00397", "V00398"])
    dfb = _to_num(df_basico, ["v0003"])

    # Agora ambos têm nomes canônicos — merge direto pela chave comum
    denominador = df2[[chave_dom2]].merge(
        dfb[[chave_basico, "v0003"]].rename(columns={chave_basico: chave_dom2}),
        on=chave_dom2,
        how="left",
    )["v0003"]

    resultado = df2[[chave_dom2]].copy()
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
    df_alfabetizacao = _normalizar_chave(df_alfabetizacao)
    chave = _chave_geografica(df_alfabetizacao)
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
    df_parentesco = _normalizar_chave(df_parentesco)
    chave = _chave_geografica(df_parentesco)

    df = _to_num(df_parentesco, ["V01042", "V01063"])

    resultado = df[[chave]].copy()
    resultado["pct_responsavel_feminino"] = _pct(df["V01063"], df["V01042"])

    logger.info(
        f"calcular_familia: {len(resultado)} registros | "
        f"pct_responsavel_feminino média: {resultado['pct_responsavel_feminino'].mean():.1f}%"
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicadores Prioridade 2 — Vulnerabilidade Hídrica e Sanitária
# ---------------------------------------------------------------------------

def calcular_agua_inadequada(
    df_domicilio2: pd.DataFrame,
    df_basico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula o percentual de domicílios com fonte de água inadequada.

    "Inadequada" = qualquer fonte que não seja rede geral ou poço artesiano:
    poço raso, fonte/nascente, carro-pipa, água de chuva, rio/açude, outra.

    Fonte: datasets 'caracteristicas_domicilio2' + 'basico'

    Mapeamento de variáveis:
        V00113 — poço raso / cacimba / cisterna
        V00114 — fonte / nascente / olho d'água
        V00115 — carro-pipa
        V00116 — água da chuva armazenada em cisterna
        V00117 — rio, açude, lago ou igarapé
        V00118 — outra forma
        v0003  — total de domicílios particulares (denominador, do basico)

    Indicadores:
        pct_agua_inadequada — Σ(V00113..V00118) / v0003 × 100

    EDA (município PB): média 21.8% | min 0.0% | max 73.7%
    """
    df_domicilio2 = _normalizar_chave(df_domicilio2)
    df_basico     = _normalizar_chave(df_basico)
    chave = _chave_geografica(df_domicilio2)
    chave_b = _chave_geografica(df_basico)

    cols_inad = ["V00113", "V00114", "V00115", "V00116", "V00117", "V00118"]
    df2 = _to_num(df_domicilio2, cols_inad)
    dfb = _to_num(df_basico, ["v0003"])

    denominador = df2[[chave]].merge(
        dfb[[chave_b, "v0003"]].rename(columns={chave_b: chave}),
        on=chave, how="left",
    )["v0003"]

    agua_inad = df2[cols_inad].sum(axis=1)

    resultado = df2[[chave]].copy()
    resultado["pct_agua_inadequada"] = _pct(agua_inad, denominador)

    logger.info(
        "calcular_agua_inadequada: %d registros | média: %.1f%%",
        len(resultado), resultado["pct_agua_inadequada"].mean(),
    )
    return resultado


def calcular_esgoto_inadequado(
    df_domicilio2: pd.DataFrame,
    df_basico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula o percentual de domicílios com esgotamento sanitário inadequado.

    "Inadequado" = fossa rudimentar, vala, rio/lago, outro ou sem banheiro.

    Fonte: datasets 'caracteristicas_domicilio2' + 'basico'

    Mapeamento de variáveis:
        V00311 — fossa rudimentar / buraco
        V00313 — vala a céu aberto
        V00314 — rio, lago, mar ou outro corpo d'água
        V00315 — outro escoadouro
        V00316 — não tinham banheiro nem sanitário
        v0003  — total de domicílios particulares (denominador)

    Indicadores:
        pct_esgoto_inadequado — Σ(V00311,V00313..V00316) / v0003 × 100

    EDA (município PB): média 18.0% | min 0.7% | max 77.2%
    """
    df_domicilio2 = _normalizar_chave(df_domicilio2)
    df_basico     = _normalizar_chave(df_basico)
    chave = _chave_geografica(df_domicilio2)
    chave_b = _chave_geografica(df_basico)

    cols_inad = ["V00311", "V00313", "V00314", "V00315", "V00316"]
    df2 = _to_num(df_domicilio2, cols_inad)
    dfb = _to_num(df_basico, ["v0003"])

    denominador = df2[[chave]].merge(
        dfb[[chave_b, "v0003"]].rename(columns={chave_b: chave}),
        on=chave, how="left",
    )["v0003"]

    esgoto_inad = df2[cols_inad].sum(axis=1)

    resultado = df2[[chave]].copy()
    resultado["pct_esgoto_inadequado"] = _pct(esgoto_inad, denominador)

    logger.info(
        "calcular_esgoto_inadequado: %d registros | média: %.1f%%",
        len(resultado), resultado["pct_esgoto_inadequado"].mean(),
    )
    return resultado


def calcular_lixo_inadequado(
    df_domicilio2: pd.DataFrame,
    df_basico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula o percentual de domicílios com destino inadequado do lixo.

    "Inadequado" = queimado, enterrado, jogado em terreno baldio ou outro.

    Fonte: datasets 'caracteristicas_domicilio2' + 'basico'
    ⚠️ Apesar do nome, V00399-V00402 estão em domicilio2, não em domicilio3.

    Mapeamento de variáveis:
        V00399 — lixo queimado na propriedade
        V00400 — lixo enterrado na propriedade
        V00401 — lixo jogado em terreno baldio, encosta ou área pública
        V00402 — outro destino do lixo
        v0003  — total de domicílios particulares (denominador)

    Indicadores:
        pct_lixo_inadequado — Σ(V00399..V00402) / v0003 × 100

    EDA (município PB): média 20.7% | min 0.5% | max 61.1%
    """
    df_domicilio2 = _normalizar_chave(df_domicilio2)
    df_basico     = _normalizar_chave(df_basico)
    chave = _chave_geografica(df_domicilio2)
    chave_b = _chave_geografica(df_basico)

    cols_inad = ["V00399", "V00400", "V00401", "V00402"]
    df2 = _to_num(df_domicilio2, cols_inad)
    dfb = _to_num(df_basico, ["v0003"])

    denominador = df2[[chave]].merge(
        dfb[[chave_b, "v0003"]].rename(columns={chave_b: chave}),
        on=chave, how="left",
    )["v0003"]

    lixo_inad = df2[cols_inad].sum(axis=1)

    resultado = df2[[chave]].copy()
    resultado["pct_lixo_inadequado"] = _pct(lixo_inad, denominador)

    logger.info(
        "calcular_lixo_inadequado: %d registros | média: %.1f%%",
        len(resultado), resultado["pct_lixo_inadequado"].mean(),
    )
    return resultado


def calcular_razao_dependencia(df_demografia: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a razão de dependência demográfica.

    Mede a proporção de pessoas em idade dependente (0-14 e 60+) em relação
    à população em idade ativa (15-59). Valores altos indicam maior pressão
    sobre a população economicamente ativa.

    Fonte: dataset 'demografia'

    Mapeamento de variáveis (faixas TOTAIS masc+fem):
        V01031 — 0 a 4 anos
        V01032 — 5 a 9 anos
        V01033 — 10 a 14 anos
        V01034 — 15 a 19 anos
        V01035 — 20 a 24 anos
        V01036 — 25 a 29 anos
        V01037 — 30 a 39 anos
        V01038 — 40 a 49 anos
        V01039 — 50 a 59 anos
        V01040 — 60 a 69 anos
        V01041 — 70 anos ou mais

    Indicadores:
        razao_dependencia — (pop_0_14 + pop_60+) / pop_15_59 × 100

    EDA (município PB): média 60.8 | min 48.8 | max 72.6
    Interpretação: 60.8 = para cada 100 pessoas em idade ativa, há ~61 dependentes.
    """
    df_demografia = _normalizar_chave(df_demografia)
    chave = _chave_geografica(df_demografia)

    cols = ["V01031", "V01032", "V01033",
            "V01034", "V01035", "V01036", "V01037", "V01038", "V01039",
            "V01040", "V01041"]
    df = _to_num(df_demografia, cols)

    pop_0_14  = df[["V01031", "V01032", "V01033"]].sum(axis=1)
    pop_15_59 = df[["V01034", "V01035", "V01036", "V01037", "V01038", "V01039"]].sum(axis=1)
    pop_60p   = df[["V01040", "V01041"]].sum(axis=1)

    resultado = df[[chave]].copy()
    resultado["razao_dependencia"] = _pct(pop_0_14 + pop_60p, pop_15_59)

    logger.info(
        "calcular_razao_dependencia: %d registros | média: %.1f",
        len(resultado), resultado["razao_dependencia"].mean(),
    )
    return resultado


def calcular_obitos(df_obitos: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de mortalidade a partir dos óbitos domiciliares.

    ⚠️ ATENÇÃO — interpretação correta:
        V01224 conta DOMICÍLIOS que tiveram pelo menos um óbito entre jan/2019
        e jul/2022, não o total de óbitos. É um proxy de mortalidade domiciliar,
        não uma taxa de mortalidade oficial.

    Fonte: dataset 'obitos'
    Silver: ibge_censo2022_{granularidade}_obitos_pb.parquet

    Mapeamento de variáveis:
        V01224 — domicílios com pelo menos um óbito (jan/2019–jul/2022)
        V01226 — óbitos masculinos
        V01227 — óbitos femininos
        V01228 — óbitos masculinos, 0 a 4 anos
        V01239 — óbitos femininos, 0 a 4 anos

    Indicadores:
        total_obitos_domicilios — V01224 (domicílios com óbito)
        obitos_infantis_0_4     — V01228 + V01239

    EDA (município PB):
        total_obitos_domicilios: média 364 | max 15.267 (João Pessoa)
        obitos_infantis_0_4: valores baixos, proxy de mortalidade infantil

    Args:
        df_obitos: DataFrame do arquivo 'obitos'

    Returns:
        DataFrame com [chave_geografica, total_obitos_domicilios, obitos_infantis_0_4]
    """
    df_obitos = _normalizar_chave(df_obitos)
    chave = _chave_geografica(df_obitos)

    df = _to_num(df_obitos, ["V01224", "V01228", "V01239"])

    resultado = df[[chave]].copy()
    resultado["total_obitos_domicilios"] = df["V01224"].astype("Int64")
    resultado["obitos_infantis_0_4"]     = (df["V01228"] + df["V01239"]).astype("Int64")

    logger.info(
        "calcular_obitos: %d registros | total_obitos_domicilios soma: %d",
        len(resultado), resultado["total_obitos_domicilios"].sum(),
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicadores Prioridade 2 — Habitação (fonte: caracteristicas_domicilio1)
# ---------------------------------------------------------------------------

def calcular_habitacao(df_domicilio1: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de condições habitacionais.

    Fonte: dataset 'caracteristicas_domicilio1'
    Silver: ibge_censo2022_{granularidade}_caracteristicas_domicilio1_pb.parquet

    Mapeamento de variáveis:
        V00001 — domicílios particulares permanentes ocupados (denominador)
        V00002 — domicílios particulares improvisados ocupados
        V00021 — dom. com 5 moradores
        V00022 — dom. com 6 moradores
        V00023 — dom. com 7 moradores
        V00024 — dom. com 8 moradores
        V00025 — dom. com 9 moradores
        V00026 — dom. com 10 ou mais moradores

    Indicadores:
        pct_dom_improvisado — V00002 / V00001 × 100
            Proxy de habitação precária (barracos, tendas, veículos, etc.)

        pct_dom_superlotado — Σ(V00021..V00026) / V00001 × 100
            Domicílios com 5 ou mais moradores — proxy de adensamento excessivo.
            O IBGE considera 5+ moradores como indicador de superlotação.
    """
    df_domicilio1 = _normalizar_chave(df_domicilio1)
    chave = _chave_geografica(df_domicilio1)

    cols_superlot = ["V00021", "V00022", "V00023", "V00024", "V00025", "V00026"]
    df = _to_num(df_domicilio1, ["V00001", "V00002"] + cols_superlot)

    denominador  = df["V00001"]
    improvisados = df["V00002"]
    superlotados = df[cols_superlot].sum(axis=1)

    resultado = df[[chave]].copy()
    resultado["pct_dom_improvisado"] = _pct(improvisados, denominador)
    resultado["pct_dom_superlotado"] = _pct(superlotados, denominador)

    logger.info(
        "calcular_habitacao: %d registros | improvisado: %.1f%% | superlotado: %.1f%%",
        len(resultado),
        resultado["pct_dom_improvisado"].mean(),
        resultado["pct_dom_superlotado"].mean(),
    )
    return resultado


# ---------------------------------------------------------------------------
# Indicadores Prioridade 3 — Composição Domiciliar e Vulnerabilidade
# ---------------------------------------------------------------------------

def calcular_composicao_domiciliar(df_domicilio1: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de composição domiciliar.

    Fonte: dataset 'caracteristicas_domicilio1'

    Mapeamento de variáveis:
        V00001 — domicílios particulares permanentes ocupados (denominador)
        V00017 — dom. com 1 morador (unipessoal)
        V00047 — dom. tipo casa
        V00049 — dom. tipo apartamento
        V00052 — dom. tipo estrutura degradada ou inacabada

    Indicadores:
        pct_dom_unipessoal — V00017 / V00001 × 100
        pct_dom_tipo_casa  — V00047 / V00001 × 100
        pct_dom_tipo_apto  — V00049 / V00001 × 100
        pct_dom_degradado  — V00052 / V00001 × 100
    """
    df_domicilio1 = _normalizar_chave(df_domicilio1)
    chave = _chave_geografica(df_domicilio1)

    cols = ["V00001", "V00017", "V00047", "V00049", "V00052"]
    df = _to_num(df_domicilio1, cols)

    denominador = df["V00001"]

    resultado = df[[chave]].copy()
    resultado["pct_dom_unipessoal"] = _pct(df["V00017"], denominador)
    resultado["pct_dom_tipo_casa"]  = _pct(df["V00047"], denominador)
    resultado["pct_dom_tipo_apto"]  = _pct(df["V00049"], denominador)
    resultado["pct_dom_degradado"]  = _pct(df["V00052"], denominador)

    logger.info(
        "calcular_composicao_domiciliar: %d registros | unipessoal: %.1f%% | casa: %.1f%% | apto: %.1f%%",
        len(resultado),
        resultado["pct_dom_unipessoal"].mean(),
        resultado["pct_dom_tipo_casa"].mean(),
        resultado["pct_dom_tipo_apto"].mean(),
    )
    return resultado


def calcular_genero_populacao(df_domicilio1: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a distribuição por gênero da população.

    Fonte: dataset 'caracteristicas_domicilio1'

    Mapeamento de variáveis:
        V00005 — total de moradores em dom. particulares permanentes
        V00011 — pessoas de sexo masculino em dom. particulares permanentes
        V00014 — pessoas de sexo feminino em dom. particulares permanentes

    Indicadores:
        pct_pop_masculina — V00011 / V00005 × 100
        pct_pop_feminina  — V00014 / V00005 × 100
    """
    df_domicilio1 = _normalizar_chave(df_domicilio1)
    chave = _chave_geografica(df_domicilio1)

    cols = ["V00005", "V00011", "V00014"]
    df = _to_num(df_domicilio1, cols)

    denominador = df["V00005"]

    resultado = df[[chave]].copy()
    resultado["pct_pop_masculina"] = _pct(df["V00011"], denominador)
    resultado["pct_pop_feminina"]  = _pct(df["V00014"], denominador)

    logger.info(
        "calcular_genero_populacao: %d registros | masc: %.1f%% | fem: %.1f%%",
        len(resultado),
        resultado["pct_pop_masculina"].mean(),
        resultado["pct_pop_feminina"].mean(),
    )
    return resultado


def calcular_saneamento_banheiro(
    df_domicilio2: pd.DataFrame,
    df_basico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula o percentual de domicílios sem banheiro.

    Fonte: datasets 'caracteristicas_domicilio2' + 'basico'

    Mapeamento de variáveis:
        V00238 — dom. que não tinham banheiro nem sanitário
        v0003  — total de domicílios particulares (denominador)

    Indicadores:
        pct_dom_sem_banheiro — V00238 / v0003 × 100
    """
    df_domicilio2 = _normalizar_chave(df_domicilio2)
    df_basico     = _normalizar_chave(df_basico)
    chave = _chave_geografica(df_domicilio2)
    chave_b = _chave_geografica(df_basico)

    df2 = _to_num(df_domicilio2, ["V00238"])
    dfb = _to_num(df_basico, ["v0003"])

    denominador = df2[[chave]].merge(
        dfb[[chave_b, "v0003"]].rename(columns={chave_b: chave}),
        on=chave, how="left",
    )["v0003"]

    resultado = df2[[chave]].copy()
    resultado["pct_dom_sem_banheiro"] = _pct(df2["V00238"], denominador)

    logger.info(
        "calcular_saneamento_banheiro: %d registros | média: %.1f%%",
        len(resultado), resultado["pct_dom_sem_banheiro"].mean(),
    )
    return resultado


def calcular_agua_encanamento(
    df_domicilio2: pd.DataFrame,
    df_basico: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula o percentual de domicílios onde a água não chega encanada.

    Fonte: datasets 'caracteristicas_domicilio2' + 'basico'

    Mapeamento de variáveis:
        V00201 — dom. onde água não chega encanada ao domicílio
        v0003  — total de domicílios particulares (denominador)

    Indicadores:
        pct_agua_nao_encanada — V00201 / v0003 × 100
    """
    df_domicilio2 = _normalizar_chave(df_domicilio2)
    df_basico     = _normalizar_chave(df_basico)
    chave = _chave_geografica(df_domicilio2)
    chave_b = _chave_geografica(df_basico)

    df2 = _to_num(df_domicilio2, ["V00201"])
    dfb = _to_num(df_basico, ["v0003"])

    denominador = df2[[chave]].merge(
        dfb[[chave_b, "v0003"]].rename(columns={chave_b: chave}),
        on=chave, how="left",
    )["v0003"]

    resultado = df2[[chave]].copy()
    resultado["pct_agua_nao_encanada"] = _pct(df2["V00201"], denominador)

    logger.info(
        "calcular_agua_encanamento: %d registros | média: %.1f%%",
        len(resultado), resultado["pct_agua_nao_encanada"].mean(),
    )
    return resultado


def calcular_raca_detalhada(df_cor_raca: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula percentuais detalhados por raça/cor.

    Fonte: dataset 'cor_ou_raca'

    Mapeamento de variáveis:
        V01317 — branca
        V01318 — preta
        V01319 — amarela
        V01320 — parda
        V01321 — indígena

    Indicadores:
        pct_branca   — V01317 / total × 100
        pct_indigena — V01321 / total × 100
    """
    df_cor_raca = _normalizar_chave(df_cor_raca)
    chave = _chave_geografica(df_cor_raca)

    cols = ["V01317", "V01318", "V01319", "V01320", "V01321"]
    df = _to_num(df_cor_raca, cols)

    total_raca = df[cols].sum(axis=1)

    resultado = df[[chave]].copy()
    resultado["pct_branca"]   = _pct(df["V01317"], total_raca)
    resultado["pct_indigena"] = _pct(df["V01321"], total_raca)

    logger.info(
        "calcular_raca_detalhada: %d registros | branca: %.1f%% | indígena: %.1f%%",
        len(resultado),
        resultado["pct_branca"].mean(),
        resultado["pct_indigena"].mean(),
    )
    return resultado


def calcular_estrutura_etaria_detalhada(df_demografia: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula faixas etárias detalhadas para análise demográfica.

    Fonte: dataset 'demografia'

    Mapeamento de variáveis (faixas TOTAIS masc+fem):
        V01033 — 10 a 14 anos
        V01034 — 15 a 19 anos
        V01035 — 20 a 24 anos
        V01036 — 25 a 29 anos
        V01037 — 30 a 39 anos
        V01038 — 40 a 49 anos
        V01039 — 50 a 59 anos
        V01006 — total de moradores (denominador)

    Indicadores:
        pct_jovens_15_29  — (V01034 + V01035 + V01036) / V01006 × 100
        pct_adultos_30_59 — (V01037 + V01038 + V01039) / V01006 × 100
    """
    df_demografia = _normalizar_chave(df_demografia)
    chave = _chave_geografica(df_demografia)

    cols = ["V01006", "V01034", "V01035", "V01036", "V01037", "V01038", "V01039"]
    df = _to_num(df_demografia, cols)

    total = df["V01006"]
    jovens_15_29  = df[["V01034", "V01035", "V01036"]].sum(axis=1)
    adultos_30_59 = df[["V01037", "V01038", "V01039"]].sum(axis=1)

    resultado = df[[chave]].copy()
    resultado["pct_jovens_15_29"]  = _pct(jovens_15_29, total)
    resultado["pct_adultos_30_59"] = _pct(adultos_30_59, total)

    logger.info(
        "calcular_estrutura_etaria_detalhada: %d registros | jovens 15-29: %.1f%% | adultos 30-59: %.1f%%",
        len(resultado),
        resultado["pct_jovens_15_29"].mean(),
        resultado["pct_adultos_30_59"].mean(),
    )
    return resultado

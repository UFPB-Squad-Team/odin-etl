"""
Aggregation utilities — compute education indicators per geographic group.

Contains the `calcular_indicadores()` function that aggregates school-level
metrics (infrastructure, IDEB, TDI, etc.) into per-group summaries.
"""
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def calcular_indicadores(
    df: pd.DataFrame,
    group_col: str,
    config: dict,
) -> pd.DataFrame:
    """
    Agrega indicadores educacionais por grupo geográfico (bairro, setor, município).

    Agrega dois tipos de métricas:
    1. Infraestrutura (Censo Escolar): percentual de escolas com cada recurso
    2. Desempenho (INEP): médias de IDEB, TDI, taxas de rendimento por nível de ensino

    Args:
        df:        DataFrame com registros de escolas já associados a polígonos.
        group_col: Coluna de agrupamento (ex: 'CD_BAIRRO', 'CD_SETOR', 'municipio_cep').
        config:    Seção 'colunas_metricas' do config_geocode.yml.

    Returns:
        DataFrame com uma linha por grupo e colunas de indicadores agregados.
    """
    colunas_matriculas = config["matriculas"]
    coluna_internet = config["internet"]
    coluna_biblioteca = config["biblioteca"]
    coluna_laboratorio_informatica = config["lab_informatica"]
    coluna_sem_acessibilidade = config["sem_acessibilidade"]

    colunas_infra = colunas_matriculas + [
        coluna_internet, coluna_biblioteca,
        coluna_laboratorio_informatica, coluna_sem_acessibilidade,
    ]
    colunas_infra_extras = [
        "IN_AGUA_POTAVEL", "IN_ENERGIA_REDE_PUBLICA", "IN_ESGOTO_REDE_PUBLICA",
        "IN_LIXO_SERVICO_COLETA", "IN_COZINHA", "IN_REFEITORIO",
        "IN_QUADRA_ESPORTES", "IN_LABORATORIO_CIENCIAS",
        "IN_INTERNET_ALUNOS", "IN_ACESSIBILIDADE_INEXISTENTE",
    ]
    for coluna in colunas_infra + colunas_infra_extras:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0).astype(int)

    colunas_desempenho = [
        "ideb_anos_iniciais", "ideb_anos_finais", "ideb_ensino_medio",
        "inse_valor",
        "afd_ei", "afd_efi", "afd_eff", "afd_em",
        "tdi_efi", "tdi_eff", "tdi_em",
        "taxa_aprovacao_efi", "taxa_aprovacao_eff", "taxa_aprovacao_em",
        "taxa_reprovacao_efi", "taxa_reprovacao_eff", "taxa_reprovacao_em",
        "taxa_abandono_efi", "taxa_abandono_eff", "taxa_abandono_em",
        "dsu_ei", "dsu_efi", "dsu_eff", "dsu_em",
        "had_ei", "had_efi", "had_eff", "had_em",
        "atu_ei", "atu_efi", "atu_eff", "atu_em",
    ]
    for coluna in colunas_desempenho:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    def _pct_escolas_com(grupo, coluna: str) -> float | None:
        if coluna not in grupo.columns:
            return None
        total = len(grupo)
        if total == 0:
            return None
        return round((grupo[coluna] == 1).sum() / total * 100, 1)

    def _media_indicador(grupo, coluna: str) -> float | None:
        if coluna not in grupo.columns:
            return None
        valores = grupo[coluna].dropna()
        if len(valores) == 0:
            return None
        return round(float(valores.mean()), 2)

    def _agregar_grupo(grupo):
        return pd.Series({
            "total_escolas": len(grupo),
            "total_matriculas": int(grupo[colunas_matriculas].sum().sum()),

            "pct_com_agua_potavel":          _pct_escolas_com(grupo, "IN_AGUA_POTAVEL"),
            "pct_com_energia_publica":       _pct_escolas_com(grupo, "IN_ENERGIA_REDE_PUBLICA"),
            "pct_com_esgoto_rede_publica":   _pct_escolas_com(grupo, "IN_ESGOTO_REDE_PUBLICA"),
            "pct_com_coleta_lixo":           _pct_escolas_com(grupo, "IN_LIXO_SERVICO_COLETA"),

            "pct_com_internet":              _pct_escolas_com(grupo, coluna_internet),
            "pct_com_internet_alunos":       _pct_escolas_com(grupo, "IN_INTERNET_ALUNOS"),
            "pct_com_biblioteca":            _pct_escolas_com(grupo, coluna_biblioteca),
            "pct_com_laboratorio_informatica": _pct_escolas_com(grupo, coluna_laboratorio_informatica),
            "pct_com_laboratorio_ciencias":  _pct_escolas_com(grupo, "IN_LABORATORIO_CIENCIAS"),
            "pct_com_quadra_esportes":       _pct_escolas_com(grupo, "IN_QUADRA_ESPORTES"),
            "pct_com_cozinha":               _pct_escolas_com(grupo, "IN_COZINHA"),
            "pct_com_refeitorio":            _pct_escolas_com(grupo, "IN_REFEITORIO"),

            "pct_sem_acessibilidade":        _pct_escolas_com(grupo, coluna_sem_acessibilidade),

            "media_ideb_anos_iniciais":      _media_indicador(grupo, "ideb_anos_iniciais"),
            "media_ideb_anos_finais":        _media_indicador(grupo, "ideb_anos_finais"),
            "media_ideb_ensino_medio":       _media_indicador(grupo, "ideb_ensino_medio"),

            "media_inse":                    _media_indicador(grupo, "inse_valor"),

            "media_afd_anos_iniciais":       _media_indicador(grupo, "afd_efi"),
            "media_afd_anos_finais":         _media_indicador(grupo, "afd_eff"),
            "media_afd_ensino_medio":        _media_indicador(grupo, "afd_em"),

            "media_tdi_anos_iniciais":       _media_indicador(grupo, "tdi_efi"),
            "media_tdi_anos_finais":         _media_indicador(grupo, "tdi_eff"),
            "media_tdi_ensino_medio":        _media_indicador(grupo, "tdi_em"),

            "media_taxa_aprovacao_ai":       _media_indicador(grupo, "taxa_aprovacao_efi"),
            "media_taxa_aprovacao_af":       _media_indicador(grupo, "taxa_aprovacao_eff"),
            "media_taxa_aprovacao_em":       _media_indicador(grupo, "taxa_aprovacao_em"),

            "media_taxa_abandono_ai":        _media_indicador(grupo, "taxa_abandono_efi"),
            "media_taxa_abandono_af":        _media_indicador(grupo, "taxa_abandono_eff"),
            "media_taxa_abandono_em":        _media_indicador(grupo, "taxa_abandono_em"),

            "media_docentes_superior_ei":    _media_indicador(grupo, "dsu_ei"),
            "media_docentes_superior_ai":    _media_indicador(grupo, "dsu_efi"),
            "media_docentes_superior_af":    _media_indicador(grupo, "dsu_eff"),
            "media_docentes_superior_em":    _media_indicador(grupo, "dsu_em"),

            "media_horas_aula_ai":           _media_indicador(grupo, "had_efi"),
            "media_horas_aula_af":           _media_indicador(grupo, "had_eff"),
            "media_horas_aula_em":           _media_indicador(grupo, "had_em"),

            "media_alunos_turma_ai":         _media_indicador(grupo, "atu_efi"),
            "media_alunos_turma_af":         _media_indicador(grupo, "atu_eff"),
            "media_alunos_turma_em":         _media_indicador(grupo, "atu_em"),
        })

    return df.groupby(group_col).apply(_agregar_grupo, include_groups=False).reset_index()

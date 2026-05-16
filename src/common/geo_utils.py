import logging

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, mapping


def escolas_para_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Convert a DataFrame with 'latitude' and 'longitude' columns into a
    GeoDataFrame with Point geometry and CRS WGS84 (EPSG:4326).

    Rows with null latitude or longitude are silently discarded before
    the conversion — they cannot be placed on a map.

    Args:
        df: DataFrame containing at least 'latitude' and 'longitude' columns.

    Returns:
        GeoDataFrame with a 'geometry' column (Point) and CRS EPSG:4326.
    """
    total = len(df)
    df_valido = df.dropna(subset=["latitude", "longitude"]).copy()
    descartados = total - len(df_valido)

    if descartados > 0:
        logging.info(
            f"{descartados} escola(s) descartada(s) por ausência de coordenadas "
            f"({len(df_valido)} restantes)."
        )

    geometria = [
        Point(lon, lat)
        for lon, lat in zip(df_valido["longitude"], df_valido["latitude"])
    ]

    return gpd.GeoDataFrame(df_valido, geometry=geometria, crs="EPSG:4326")


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

    O schema de saída é sempre uniforme — todos os campos presentes em todas as linhas,
    com None onde não há dados. Isso é necessário para o pandas 3.x, que cria MultiIndex
    quando grupos retornam Series com campos diferentes.

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

    # Converter colunas de infraestrutura para int (0/1), tratando ausentes como 0
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
    ]
    for coluna in colunas_desempenho:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    def _pct_escolas_com(grupo, coluna: str) -> float | None:
        """Percentual de escolas onde a coluna booleana é 1 (True)."""
        if coluna not in grupo.columns:
            return None
        total = len(grupo)
        if total == 0:
            return None
        return round((grupo[coluna] == 1).sum() / total * 100, 1)

    def _media_indicador(grupo, coluna: str) -> float | None:
        """Média de um indicador numérico, ignorando nulos."""
        if coluna not in grupo.columns:
            return None
        valores = grupo[coluna].dropna()
        if len(valores) == 0:
            return None
        return round(float(valores.mean()), 2)

    def _agregar_grupo(grupo):
        total_escolas = len(grupo)

        return pd.Series({
            # ── Totais ────────────────────────────────────────────────────────
            "total_escolas": total_escolas,
            "total_matriculas": int(grupo[colunas_matriculas].sum().sum()),

            # ── Infraestrutura básica ─────────────────────────────────────────
            "pct_com_agua_potavel":          _pct_escolas_com(grupo, "IN_AGUA_POTAVEL"),
            "pct_com_energia_publica":       _pct_escolas_com(grupo, "IN_ENERGIA_REDE_PUBLICA"),
            "pct_com_esgoto_rede_publica":   _pct_escolas_com(grupo, "IN_ESGOTO_REDE_PUBLICA"),
            "pct_com_coleta_lixo":           _pct_escolas_com(grupo, "IN_LIXO_SERVICO_COLETA"),

            # ── Infraestrutura pedagógica ─────────────────────────────────────
            "pct_com_internet":              _pct_escolas_com(grupo, coluna_internet),
            "pct_com_internet_alunos":       _pct_escolas_com(grupo, "IN_INTERNET_ALUNOS"),
            "pct_com_biblioteca":            _pct_escolas_com(grupo, coluna_biblioteca),
            "pct_com_laboratorio_informatica": _pct_escolas_com(grupo, coluna_laboratorio_informatica),
            "pct_com_laboratorio_ciencias":  _pct_escolas_com(grupo, "IN_LABORATORIO_CIENCIAS"),
            "pct_com_quadra_esportes":       _pct_escolas_com(grupo, "IN_QUADRA_ESPORTES"),
            "pct_com_cozinha":               _pct_escolas_com(grupo, "IN_COZINHA"),
            "pct_com_refeitorio":            _pct_escolas_com(grupo, "IN_REFEITORIO"),

            # ── Acessibilidade ────────────────────────────────────────────────
            "pct_sem_acessibilidade":        _pct_escolas_com(grupo, coluna_sem_acessibilidade),

            # ── IDEB 2023 ─────────────────────────────────────────────────────
            "media_ideb_anos_iniciais":      _media_indicador(grupo, "ideb_anos_iniciais"),
            "media_ideb_anos_finais":        _media_indicador(grupo, "ideb_anos_finais"),
            "media_ideb_ensino_medio":       _media_indicador(grupo, "ideb_ensino_medio"),

            # ── INSE ──────────────────────────────────────────────────────────
            "media_inse":                    _media_indicador(grupo, "inse_valor"),
        })

    return df.groupby(group_col).apply(_agregar_grupo, include_groups=False).reset_index()


def poligono_para_geojson(geometry) -> dict:
    """
    Convert a Shapely geometry (Polygon or MultiPolygon) to a GeoJSON dict.

    The returned dict is compatible with MongoDB's 2dsphere index and
    can be stored directly in a document field.

    Args:
        geometry: Shapely Polygon or MultiPolygon.

    Returns:
        Dict with keys 'type' and 'coordinates'.
    """
    return mapping(geometry)

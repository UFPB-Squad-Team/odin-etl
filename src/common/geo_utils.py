"""
Shared geospatial utilities for ODIN-ETL Pipelines 6 and 7.

These functions are intentionally kept small and focused so that
new developers can understand each one in isolation.
"""
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
    Aggregate educational metrics (Census + INEP) grouped by group_col.

    This function is agnostic to the aggregation level — pass
    'id_setor' for neighborhood-level or 'co_municipio' for
    municipality-level aggregation.

    Metrics aggregated:
    - Census: matrículas, internet, biblioteca, lab informática, acessibilidade
    - INEP: IDEB (anos iniciais/finais), INSE (nível socioeconômico)

    Args:
        df:        DataFrame with school records already joined to polygons.
        group_col: Column name to group by (e.g. 'id_setor' or 'co_municipio').
        config:    Dict from config_geocode.yml section 'colunas_metricas'.

    Returns:
        DataFrame with one row per group and aggregated indicator columns.
    """
    cols_matriculas = config["matriculas"]
    col_internet = config["internet"]
    col_biblioteca = config["biblioteca"]
    col_lab = config["lab_informatica"]
    col_sem_acess = config["sem_acessibilidade"]

    # Converter colunas numéricas para int, tratando valores ausentes como 0
    for col in cols_matriculas + [col_internet, col_biblioteca, col_lab, col_sem_acess]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Converter colunas INEP para float
    inep_cols = ["ideb_anos_iniciais", "ideb_anos_finais", "inse_valor"]
    for col in inep_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    def _agregar(grupo):
        total = len(grupo)
        agg_dict = {
            "total_escolas": total,
            "total_matriculas": int(grupo[cols_matriculas].sum().sum()),
            "pct_com_internet": round((grupo[col_internet] == 1).sum() / total * 100, 1),
            "pct_com_biblioteca": round((grupo[col_biblioteca] == 1).sum() / total * 100, 1),
            "pct_com_lab_informatica": round((grupo[col_lab] == 1).sum() / total * 100, 1),
            "pct_sem_acessibilidade": round((grupo[col_sem_acess] == 1).sum() / total * 100, 1),
        }
        # Agregar indicadores INEP (média)
        if "ideb_anos_iniciais" in grupo.columns:
            ideb_ai = grupo["ideb_anos_iniciais"].dropna()
            if len(ideb_ai) > 0:
                agg_dict["media_ideb_anos_iniciais"] = round(ideb_ai.mean(), 2)
        if "ideb_anos_finais" in grupo.columns:
            ideb_af = grupo["ideb_anos_finais"].dropna()
            if len(ideb_af) > 0:
                agg_dict["media_ideb_anos_finais"] = round(ideb_af.mean(), 2)
        if "inse_valor" in grupo.columns:
            inse = grupo["inse_valor"].dropna()
            if len(inse) > 0:
                agg_dict["media_inse"] = round(inse.mean(), 2)
        return pd.Series(agg_dict)

    return df.groupby(group_col).apply(_agregar).reset_index()


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

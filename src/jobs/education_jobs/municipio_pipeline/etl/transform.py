"""
Municipio Pipeline — Transform (Pipeline 7)

Performs a spatial join between geocoded schools (points) and
municipality polygons, then aggregates educational metrics per municipality.
"""
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.common.geo_utils import calcular_indicadores, poligono_para_geojson
from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(
    gdf_escolas: gpd.GeoDataFrame,
    storage: StorageBackend = None,
) -> pd.DataFrame:
    """
    Spatial join schools to municipalities and aggregate metrics per municipality.

    Args:
        gdf_escolas: GeoDataFrame of geocoded schools (CRS EPSG:4326).
        storage:     StorageBackend instance.

    Returns:
        DataFrame with one row per municipality and aggregated indicators.
    """
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    ibge = config["geo_pipeline"]["ibge"]
    metricas = config["geo_pipeline"]["colunas_metricas"]

    municipios_path = str(Path(paths["silver"]) / ibge["municipios_silver_output"])
    logging.info(f"Reading municipalities from: {municipios_path}")
    gdf_municipios = gpd.read_file(municipios_path)

    if gdf_escolas.crs.to_epsg() != 4326:
        gdf_escolas = gdf_escolas.to_crs("EPSG:4326")
    if gdf_municipios.crs.to_epsg() != 4326:
        gdf_municipios = gdf_municipios.to_crs("EPSG:4326")

    logging.info(f"Running spatial join: {len(gdf_escolas)} schools x {len(gdf_municipios)} municipalities...")
    gdf_joined = gpd.sjoin(gdf_escolas, gdf_municipios, how="inner", predicate="within")

    sem_poligono = len(gdf_escolas) - len(gdf_joined)
    if sem_poligono > 0:
        logging.warning(f"{sem_poligono} school(s) did not fall within any municipality polygon.")

    logging.info("Aggregating indicators by municipality...")
    df_indicadores = calcular_indicadores(
        df=gdf_joined,
        group_col="CD_MUN",
        config=metricas,
    )

    municipio_geo = gdf_municipios.set_index("CD_MUN")[["geometry", "NM_MUN"]]
    df_indicadores = df_indicadores.merge(municipio_geo, left_on="CD_MUN", right_index=True, how="left")
    df_indicadores = df_indicadores.rename(columns={
        "CD_MUN": "co_municipio",
        "NM_MUN": "nome_municipio",
    })
    df_indicadores["geometria"] = df_indicadores["geometry"].apply(poligono_para_geojson)
    df_indicadores = df_indicadores.drop(columns=["geometry"])

    logging.info(f"Aggregation complete: {len(df_indicadores)} municipalities with schools.")
    return df_indicadores

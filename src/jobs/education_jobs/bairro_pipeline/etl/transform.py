"""
Bairro Pipeline — Transform (Pipeline 6)

Performs a spatial join between geocoded schools (points) and census
sector polygons (bairros), then aggregates educational metrics per sector.
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
    Spatial join schools to census sectors and aggregate metrics per sector.

    Args:
        gdf_escolas: GeoDataFrame of geocoded schools (CRS EPSG:4326).
        storage:     StorageBackend instance.

    Returns:
        DataFrame with one row per sector and aggregated indicators.
    """
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    ibge = config["geo_pipeline"]["ibge"]
    metricas = config["geo_pipeline"]["colunas_metricas"]

    setores_path = str(Path(paths["silver"]) / ibge["setores_silver_output"])
    logging.info(f"Reading census sectors from: {setores_path}")
    gdf_setores = gpd.read_file(setores_path)

    # Garantir mesmo CRS
    if gdf_escolas.crs.to_epsg() != 4326:
        gdf_escolas = gdf_escolas.to_crs("EPSG:4326")
    if gdf_setores.crs.to_epsg() != 4326:
        gdf_setores = gdf_setores.to_crs("EPSG:4326")

    logging.info(f"Running spatial join: {len(gdf_escolas)} schools x {len(gdf_setores)} sectors...")
    gdf_joined = gpd.sjoin(gdf_escolas, gdf_setores, how="inner", predicate="within")

    sem_poligono = len(gdf_escolas) - len(gdf_joined)
    if sem_poligono > 0:
        logging.warning(f"{sem_poligono} school(s) did not fall within any sector polygon.")

    logging.info(f"Aggregating indicators by sector...")
    df_indicadores = calcular_indicadores(
        df=gdf_joined,
        group_col="CD_SETOR",
        config=metricas,
    )

    # Adicionar geometria GeoJSON e campos de município
    setor_geo = gdf_setores.set_index("CD_SETOR")[["geometry", "CD_MUN", "NM_MUN"]]
    df_indicadores = df_indicadores.merge(setor_geo, left_on="CD_SETOR", right_index=True, how="left")
    df_indicadores = df_indicadores.rename(columns={
        "CD_SETOR": "id_setor",
        "CD_MUN": "co_municipio",
        "NM_MUN": "nome_municipio",
    })
    df_indicadores["geometria"] = df_indicadores["geometry"].apply(poligono_para_geojson)
    df_indicadores = df_indicadores.drop(columns=["geometry"])

    logging.info(f"Aggregation complete: {len(df_indicadores)} sectors with schools.")
    return df_indicadores

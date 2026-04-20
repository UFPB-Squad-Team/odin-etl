"""
Setor Pipeline — Extract

Lê as escolas geocodificadas do Gold, extrai coordenadas válidas
e retorna um GeoDataFrame com geometria Point (WGS84).

Escolas com coordenadas placeholder (-999) são descartadas.
"""
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")


def _extrair_lat_lon(df_gold: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai CO_ENTIDADE, latitude e longitude do campo 'documento.localizacao'.
    Descarta escolas com coordenadas ausentes ou placeholder (-999).
    """
    registros = []
    for _, row in df_gold.iterrows():
        doc = row.get("documento")
        escola_id = row.get("escolaIdInep")
        if not isinstance(doc, dict):
            continue
        loc = doc.get("localizacao")
        if not isinstance(loc, dict):
            continue
        coords = loc.get("coordinates")
        if coords is None:
            continue
        coords = list(coords)
        if len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        if lon == -999.0 or lat == -999.0:
            continue
        registros.append({"CO_ENTIDADE": str(escola_id), "longitude": lon, "latitude": lat})

    df = pd.DataFrame(registros)
    logger.info(f"Escolas com coordenadas válidas: {len(df)} / {len(df_gold)}")
    return df


def run(storage: StorageBackend = None) -> gpd.GeoDataFrame:
    """
    Carrega escolas geocodificadas e retorna GeoDataFrame com CRS WGS84.
    """
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    geocode_cfg = config["geocode_pipeline"]["transform"]

    gold_path = str(Path(paths["gold"]) / geocode_cfg["gold_output"])
    logger.info(f"Lendo Gold geocodificado: {gold_path}")
    df_gold = storage.read_parquet(gold_path)

    df_coords = _extrair_lat_lon(df_gold)
    if df_coords.empty:
        raise ValueError("Nenhuma escola com coordenadas válidas encontrada.")

    geometria = [Point(lon, lat) for lon, lat in zip(df_coords["longitude"], df_coords["latitude"])]
    gdf = gpd.GeoDataFrame(df_coords, geometry=geometria, crs="EPSG:4326")
    return gdf

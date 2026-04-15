"""
Municipio Pipeline — Extract (Pipeline 7)

Same logic as bairro_pipeline/extract.py — reads geocoded schools
and returns a GeoDataFrame ready for municipal spatial join.
"""
import logging

import geopandas as gpd

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from src.jobs.education_jobs.geo_aggregate_shared import load_geocoded_schools_gdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage: StorageBackend = None) -> gpd.GeoDataFrame:
    """Load geocoded schools and return a GeoDataFrame with valid coordinates."""
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    transform_config = config["geocode_pipeline"]["transform"]
    df, gdf, gold_path = load_geocoded_schools_gdf(
        storage=storage,
        paths=paths,
        geocode_transform_config=transform_config,
    )

    logging.info(f"Reading geocoded schools from: {gold_path}")
    logging.info(f"Total records loaded: {len(df)}")
    return gdf

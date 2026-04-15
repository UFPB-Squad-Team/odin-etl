"""
Geo Ingest Pipeline — Extract (Pipeline 3)

Downloads the IBGE shapefiles for Paraiba (census sectors and municipalities),
reprojects to WGS84, and saves as GeoParquet in the Silver layer.

Idempotent: skips download if the Silver GeoParquet already exists.
"""
import logging
from pathlib import Path

import geopandas as gpd
import requests
from dotenv import load_dotenv

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from src.jobs.education_jobs.geo_ingest_pipeline.config import (
    PB_MUNICIPIOS_BRONZE_FILENAME,
    PB_SETORES_BRONZE_FILENAME,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _download_and_save_shapefile(
    url: str,
    bronze_zip_path: str,
    silver_parquet_path: str,
    storage: StorageBackend,
) -> None:
    """
    Download a ZIP shapefile from IBGE, reproject to WGS84, and save
    as GeoParquet. Skips if the Silver file already exists.
    """
    if Path(silver_parquet_path).exists():
        logging.info(f"Silver file already exists, skipping download: {silver_parquet_path}")
        return

    logging.info(f"Downloading shapefile from: {url}")
    response = requests.get(url, timeout=60)

    if response.status_code != 200:
        raise requests.HTTPError(
            f"IBGE download failed — HTTP {response.status_code} for URL: {url}"
        )

    storage.save_zip(response.content, bronze_zip_path)
    logging.info(f"ZIP saved to Bronze: {bronze_zip_path}")

    gdf = gpd.read_file(f"zip://{bronze_zip_path}")
    gdf = gdf.to_crs("EPSG:4326")
    logging.info(f"Reprojected to WGS84. {len(gdf)} polygons loaded.")

    Path(silver_parquet_path).parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(silver_parquet_path, driver="Parquet")
    logging.info(f"GeoParquet saved to Silver: {silver_parquet_path}")


def run(storage: StorageBackend = None) -> None:
    """Download IBGE shapefiles and save as GeoParquet in Silver."""
    logging.info("--- STARTING GEO INGEST EXTRACT ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    ibge = config["geo_pipeline"]["ibge"]

    _download_and_save_shapefile(
        url=ibge["setores_censitarios_url"],
        bronze_zip_path=str(Path(paths["bronze"]) / PB_SETORES_BRONZE_FILENAME),
        silver_parquet_path=str(Path(paths["silver"]) / ibge["setores_silver_output"]),
        storage=storage,
    )

    _download_and_save_shapefile(
        url=ibge["municipios_url"],
        bronze_zip_path=str(Path(paths["bronze"]) / PB_MUNICIPIOS_BRONZE_FILENAME),
        silver_parquet_path=str(Path(paths["silver"]) / ibge["municipios_silver_output"]),
        storage=storage,
    )

    logging.info("--- GEO INGEST EXTRACT COMPLETED ---")


if __name__ == "__main__":
    run()

import logging
from pathlib import Path

import geopandas as gpd
import requests

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# Shapefile de bairros colocado manualmente no bronze
BAIRROS_SHP_DIR = "data/bronze/PB_bairros_CD2022"
BAIRROS_SHP_FILE = "PB_bairros_CD2022.shp"


def _processar_shapefile_local(
    shp_path: str,
    silver_parquet_path: str,
) -> None:
    """
    Lê um shapefile local, reprojetam para WGS84 e salva como GeoPackage.
    Idempotente: pula se o Silver já existir (.gpkg ou .parquet).
    """
    gpkg_path = silver_parquet_path.replace(".parquet", ".gpkg")
    if Path(gpkg_path).exists() or Path(silver_parquet_path).exists():
        logging.info(f"Silver já existe, pulando: {gpkg_path}")
        return

    if not Path(shp_path).exists():
        raise FileNotFoundError(
            f"Shapefile não encontrado: {shp_path}\n"
            "Baixe a Malha de Bairros da PB do IBGE e coloque em data/bronze/PB_bairros_CD2022/"
        )

    logging.info(f"Lendo shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path, encoding="latin-1")
    logging.info(f"CRS original: {gdf.crs} — {len(gdf)} polígonos carregados.")

    gdf = gdf.to_crs("EPSG:4326")
    logging.info("Reprojetado para WGS84 (EPSG:4326).")

    Path(silver_parquet_path).parent.mkdir(parents=True, exist_ok=True)

    # Salvar como GeoPackage — mais compatível que GeoParquet
    # (GeoParquet requer GDAL com driver Parquet compilado)
    gpkg_path = silver_parquet_path.replace(".parquet", ".gpkg")
    gdf.to_file(gpkg_path, driver="GPKG")
    logging.info(f"GeoPackage salvo em Silver: {gpkg_path}")


def _download_shapefile_url(
    url: str,
    bronze_zip_path: str,
    silver_parquet_path: str,
    storage: StorageBackend,
) -> None:
    """Download de shapefile via URL e conversão para GeoParquet."""
    if Path(silver_parquet_path).exists():
        logging.info(f"Silver já existe, pulando download: {silver_parquet_path}")
        return

    logging.info(f"Baixando shapefile de: {url}")
    response = requests.get(url, timeout=60)
    if response.status_code != 200:
        raise requests.HTTPError(
            f"Download falhou — HTTP {response.status_code} para: {url}"
        )

    storage.save_zip(response.content, bronze_zip_path)
    logging.info(f"ZIP salvo em Bronze: {bronze_zip_path}")

    gdf = gpd.read_file(f"zip://{bronze_zip_path}")
    gdf = gdf.to_crs("EPSG:4326")
    logging.info(f"Reprojetado para WGS84. {len(gdf)} polígonos.")

    Path(silver_parquet_path).parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(silver_parquet_path, driver="Parquet")
    logging.info(f"GeoParquet salvo em Silver: {silver_parquet_path}")


def run(storage: StorageBackend = None) -> None:
    """Processa shapefiles do IBGE e salva como GeoParquet no Silver."""
    logging.info("--- STARTING GEO INGEST EXTRACT ---")

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    ibge = config["geo_pipeline"]["ibge"]

    # 1. Malha de Bairros — arquivo local (já baixado manualmente)
    bairros_shp = str(Path(BAIRROS_SHP_DIR) / BAIRROS_SHP_FILE)
    bairros_silver = str(Path(paths["silver"]) / ibge["bairros_silver_output"])
    _processar_shapefile_local(bairros_shp, bairros_silver)

    # 2. Malha de Setores Censitários — arquivo local (já baixado manualmente)
    setores_shp = "data/bronze/PB_setores_CD2022/PB_setores_CD2022.shp"
    setores_silver = str(Path(paths["silver"]) / ibge.get("setores_silver_output", "setores_pb.gpkg"))
    _processar_shapefile_local(setores_shp, setores_silver)

    # 3. Malha Municipal — download do IBGE (opcional)
    municipios_silver = str(Path(paths["silver"]) / ibge["municipios_silver_output"])
    if not Path(municipios_silver).exists():
        try:
            _download_shapefile_url(
                url=ibge["municipios_url"],
                bronze_zip_path=str(Path(paths["bronze"]) / "PB_Municipios_2022.zip"),
                silver_parquet_path=municipios_silver,
                storage=storage,
            )
        except Exception as e:
            logging.warning(f"Download da malha municipal falhou: {e}. Continuando sem ela.")
    else:
        logging.info(f"Malha municipal já existe: {municipios_silver}")

    logging.info("--- GEO INGEST EXTRACT COMPLETED ---")


if __name__ == "__main__":
    run()

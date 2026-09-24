"""
Geo Ingest Extract — Multi-UF (Nordeste)

Baixa shapefiles de bairros, setores censitários e municípios para os 9
estados do Nordeste, converte para GeoPackage (EPSG:4326) e salva no Silver.

Ao final, gera GeoPackages consolidados:
  - bairros_nordeste.gpkg
  - setores_nordeste.gpkg
  - municipios_nordeste.gpkg
"""
import logging
import subprocess
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

# URLs base do GeoFTP do IBGE — Censo 2022
# Estrutura confirmada em ago/2026: .../censo_2022/{setores,bairros}/shp/UF/{UF}_{camada}_CD2022.zip
_GEOFTP_SETORES = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/"
    "setores/shp/UF/{uf_upper}_setores_CD2022.zip"
)
_GEOFTP_BAIRROS = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022/"
    "bairros/shp/UF/{uf_upper}_bairros_CD2022.zip"
)
_GEOFTP_MUNICIPIOS = (
    "https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/"
    "malhas_municipais/municipio_2022/UFs/{uf_upper}/"
    "{uf_upper}_Municipios_2022.zip"
)

ESTADOS_NORDESTE = {
    "MA": "21",
    "PI": "22",
    "CE": "23",
    "RN": "24",
    "PB": "25",
    "PE": "26",
    "AL": "27",
    "SE": "28",
    "BA": "29",
}


def _download_zip(url: str, destino: Path, max_tentativas: int = 3) -> None:
    """Baixa um ZIP com retry e backoff exponencial usando curl."""
    for tentativa in range(1, max_tentativas + 1):
        try:
            logger.info("[%d/%d] Baixando: %s", tentativa, max_tentativas, url)
            result = subprocess.run(
                ["curl", "-skL", "-o", str(destino), url, "--max-time", "300"],
                capture_output=True,
                check=True,
            )
            if not destino.exists() or destino.stat().st_size < 1000:
                raise RuntimeError(f"Arquivo muito pequeno ou inexistente: {destino}")
            with zipfile.ZipFile(destino):
                pass
            tamanho_mb = destino.stat().st_size / (1024 * 1024)
            logger.info("  OK: %.1f MB → %s", tamanho_mb, destino.name)
            return
        except Exception as exc:
            logger.warning("  Tentativa %d falhou: %s", tentativa, exc)
            if destino.exists():
                destino.unlink()
            if tentativa < max_tentativas:
                import time
                time.sleep(2 ** tentativa)
            else:
                raise RuntimeError(
                    f"Falha ao baixar '{url}' após {max_tentativas} tentativas: {exc}"
                ) from exc


def _ler_shapefile_do_zip(zip_path: Path) -> gpd.GeoDataFrame:
    """Lê um shapefile de dentro de um ZIP, com encoding latin-1."""
    gdf = gpd.read_file(f"zip://{zip_path}", encoding="latin-1")
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


def _baixar_e_processar_camada(
    url_template: str,
    uf: str,
    bronze_dir: Path,
    nome_camada: str,
) -> gpd.GeoDataFrame | None:
    """
    Baixa shapefile de uma UF e retorna como GeoDataFrame WGS84.
    Retorna None se download falhar (continua com outras UFs).
    """
    uf_lower = uf.lower()
    uf_upper = uf.upper()
    url = url_template.format(uf_lower=uf_lower, uf_upper=uf_upper)
    zip_filename = f"{uf_upper}_{nome_camada}_2022.zip"
    zip_path = bronze_dir / zip_filename

    if zip_path.exists() and zip_path.stat().st_size > 1000:
        logger.info("Cache hit — Bronze: %s", zip_path.name)
    else:
        try:
            _download_zip(url, zip_path)
        except RuntimeError as e:
            logger.error("Não foi possível baixar %s para %s: %s", nome_camada, uf, e)
            return None

    try:
        gdf = _ler_shapefile_do_zip(zip_path)
        gdf["UF"] = uf_upper
        logger.info("  %s/%s: %d polígonos", uf_upper, nome_camada, len(gdf))
        return gdf
    except Exception as e:
        logger.error("Erro ao processar %s/%s: %s", uf_upper, nome_camada, e)
        return None


def _consolidar_e_salvar(
    gdfs: list[gpd.GeoDataFrame],
    output_path: Path,
    nome_camada: str,
) -> None:
    """Concatena GeoDataFrames e salva como GeoPackage consolidado."""
    if not gdfs:
        logger.error("Nenhum dado disponível para %s — GPKG não gerado.", nome_camada)
        return

    import pandas as pd
    gdf_consolidado = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs="EPSG:4326")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf_consolidado.to_file(output_path, driver="GPKG")
    logger.info(
        "GPKG consolidado salvo: %s (%d polígonos, %d UFs)",
        output_path.name, len(gdf_consolidado), len(set(gdf_consolidado["UF"])),
    )


def run(storage: StorageBackend = None) -> None:
    """
    Processa shapefiles do IBGE para os 9 estados do Nordeste.

    Gera:
      - data/silver/bairros_nordeste.gpkg
      - data/silver/setores_nordeste.gpkg
      - data/silver/municipios_nordeste.gpkg
    """
    logger.info("=" * 60)
    logger.info("GEO INGEST — Nordeste (9 UFs)")
    logger.info("=" * 60)

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    bronze_dir = Path(paths["bronze"])
    silver_dir = Path(paths["silver"])

    bronze_dir.mkdir(parents=True, exist_ok=True)
    silver_dir.mkdir(parents=True, exist_ok=True)

    # Output paths
    bairros_output = silver_dir / "bairros_nordeste.gpkg"
    setores_output = silver_dir / "setores_nordeste.gpkg"
    municipios_output = silver_dir / "municipios_nordeste.gpkg"

    # Verificar se já existem (idempotência)
    if bairros_output.exists() and setores_output.exists() and municipios_output.exists():
        logger.info("Todos os GPKGs consolidados já existem. Pulando download.")
        logger.info("  → %s", bairros_output)
        logger.info("  → %s", setores_output)
        logger.info("  → %s", municipios_output)
        return

    # Processar cada UF em paralelo (downloads)
    from concurrent.futures import ThreadPoolExecutor, as_completed

    gdfs_bairros = []
    gdfs_setores = []
    gdfs_municipios = []

    def _processar_uf_bairros(uf):
        return _baixar_e_processar_camada(_GEOFTP_BAIRROS, uf, bronze_dir, "bairros")

    def _processar_uf_setores(uf):
        return _baixar_e_processar_camada(_GEOFTP_SETORES, uf, bronze_dir, "setores")

    def _processar_uf_municipios(uf):
        return _baixar_e_processar_camada(_GEOFTP_MUNICIPIOS, uf, bronze_dir, "municipios")

    ufs = list(ESTADOS_NORDESTE.keys())

    # Download bairros em paralelo
    if not bairros_output.exists():
        logger.info("\n--- Baixando BAIRROS (paralelo, %d UFs) ---", len(ufs))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_processar_uf_bairros, uf): uf for uf in ufs}
            for future in as_completed(futures):
                gdf = future.result()
                if gdf is not None:
                    gdfs_bairros.append(gdf)

    # Download setores em paralelo
    if not setores_output.exists():
        logger.info("\n--- Baixando SETORES (paralelo, %d UFs) ---", len(ufs))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_processar_uf_setores, uf): uf for uf in ufs}
            for future in as_completed(futures):
                gdf = future.result()
                if gdf is not None:
                    gdfs_setores.append(gdf)

    # Download municípios em paralelo
    if not municipios_output.exists():
        logger.info("\n--- Baixando MUNICÍPIOS (paralelo, %d UFs) ---", len(ufs))
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_processar_uf_municipios, uf): uf for uf in ufs}
            for future in as_completed(futures):
                gdf = future.result()
                if gdf is not None:
                    gdfs_municipios.append(gdf)

    # Consolidar e salvar
    if gdfs_bairros:
        _consolidar_e_salvar(gdfs_bairros, bairros_output, "bairros")
    if gdfs_setores:
        _consolidar_e_salvar(gdfs_setores, setores_output, "setores")
    if gdfs_municipios:
        _consolidar_e_salvar(gdfs_municipios, municipios_output, "municipios")

    logger.info("\n" + "=" * 60)
    logger.info("GEO INGEST CONCLUÍDO")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()

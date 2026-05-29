import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from src.common.geo_utils import calcular_indicadores, poligono_para_geojson
from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

BAIRROS_GPKG = "data/silver/bairros_pb.gpkg"


def _extrair_coordenadas(df_gold: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai latitude e longitude do campo 'documento.localizacao.coordinates'
    e retorna DataFrame com CO_ENTIDADE, latitude, longitude.
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
        if coords is None or len(coords) < 2:
            continue
        coords = list(coords)
        lon, lat = coords[0], coords[1]
        if lat == -999.0 or lon == -999.0:
            continue
        registros.append({
            "CO_ENTIDADE": str(escola_id),
            "longitude": float(lon),
            "latitude": float(lat),
        })
    return pd.DataFrame(registros)


def _escolas_para_geodataframe(df_coords: pd.DataFrame) -> gpd.GeoDataFrame:
    """Converte DataFrame com lat/lon para GeoDataFrame WGS84."""
    geometria = [Point(lon, lat) for lon, lat in zip(df_coords["longitude"], df_coords["latitude"])]
    return gpd.GeoDataFrame(df_coords, geometry=geometria, crs="EPSG:4326")


def run(storage: StorageBackend = None) -> pd.DataFrame:
    """
    Agrega indicadores educacionais por bairro via spatial join com shapefile IBGE.

    Returns:
        DataFrame com uma linha por bairro e colunas de indicadores + geometria GeoJSON.
    """
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    metricas = config["geo_pipeline"]["colunas_metricas"]
    geocode_cfg = config["geocode_pipeline"]["transform"]

    gold_path = str(Path(paths["gold"]) / geocode_cfg["gold_output"])
    logger.info(f"Lendo Gold geocodificado de: {gold_path}")
    df_gold = storage.read_parquet(gold_path)
    logger.info(f"Total de registros no Gold: {len(df_gold)}")

    df_coords = _extrair_coordenadas(df_gold)
    logger.info(f"Escolas com coordenadas válidas: {len(df_coords)}")

    if df_coords.empty:
        raise ValueError("Nenhuma escola com coordenadas válidas encontrada no Gold.")

    gdf_escolas = _escolas_para_geodataframe(df_coords)

    if not Path(BAIRROS_GPKG).exists():
        raise FileNotFoundError(
            f"GeoPackage de bairros não encontrado: {BAIRROS_GPKG}\n"
            "Execute primeiro: poetry run python -m src.jobs.education_jobs.geo_ingest_pipeline.main"
        )

    logger.info(f"Carregando malha de bairros IBGE de: {BAIRROS_GPKG}")
    gdf_bairros = gpd.read_file(BAIRROS_GPKG)
    if gdf_bairros.crs.to_epsg() != 4326:
        gdf_bairros = gdf_bairros.to_crs("EPSG:4326")
    logger.info(f"Polígonos de bairros carregados: {len(gdf_bairros)}")

    # 3. Spatial join: escola (ponto) → bairro (polígono)
    logger.info("Executando spatial join escolas × bairros...")
    gdf_joined = gpd.sjoin(gdf_escolas, gdf_bairros, how="inner", predicate="within")

    sem_bairro = len(gdf_escolas) - len(gdf_joined)
    if sem_bairro > 0:
        logger.warning(f"{sem_bairro} escola(s) fora de qualquer polígono de bairro.")
    logger.info(f"Escolas associadas a bairros: {len(gdf_joined)}")

    silver_path = str(Path(paths["silver"]) / config["geocode_pipeline"]["extract"]["silver_output"])
    logger.info(f"Carregando Silver do censo de: {silver_path}")
    df_censo = storage.read_parquet(silver_path)
    df_censo["CO_ENTIDADE"] = df_censo["CO_ENTIDADE"].astype(str)
    if "SG_UF" in df_censo.columns:
        df_censo = df_censo[df_censo["SG_UF"] == "PB"].copy()

    ideb_rows = []
    for _, row in df_gold.iterrows():
        doc = row.get("documento")
        escola_id = row.get("escolaIdInep")
        if not isinstance(doc, dict):
            continue
        ind = doc.get("indicadores") or {}
        efi = ind.get("fundamentalAnosIniciais") or {}
        eff = ind.get("fundamentalAnosFinais") or {}
        em = ind.get("ensinoMedio") or {}
        ei = ind.get("educacaoInfantil") or {}
        ideb_rows.append({
            "CO_ENTIDADE": str(escola_id),
            "ideb_anos_iniciais": ind.get("idebAnosIniciais"),
            "ideb_anos_finais":   ind.get("idebAnosFinais"),
            "ideb_ensino_medio":  ind.get("idebEnsinoMedio"),
            "afd_efi": efi.get("afd"),
            "afd_eff": eff.get("afd"),
            "afd_em":  em.get("afd"),
            "tdi_efi": efi.get("tdi"),
            "tdi_eff": eff.get("tdi"),
            "tdi_em":  em.get("tdi"),
            "taxa_aprovacao_efi": efi.get("taxa_aprovacao"),
            "taxa_aprovacao_eff": eff.get("taxa_aprovacao"),
            "taxa_aprovacao_em":  em.get("taxa_aprovacao"),
            "taxa_abandono_efi": efi.get("taxa_abandono"),
            "taxa_abandono_eff": eff.get("taxa_abandono"),
            "taxa_abandono_em":  em.get("taxa_abandono"),
            "dsu_ei":  ei.get("docentes_superior"),
            "dsu_efi": efi.get("docentes_superior"),
            "dsu_eff": eff.get("docentes_superior"),
            "dsu_em":  em.get("docentes_superior"),
            "had_efi": efi.get("horas_aula_diarias"),
            "had_eff": eff.get("horas_aula_diarias"),
            "had_em":  em.get("horas_aula_diarias"),
            "atu_efi": efi.get("alunos_por_turma"),
            "atu_eff": eff.get("alunos_por_turma"),
            "atu_em":  em.get("alunos_por_turma"),
        })
    if ideb_rows:
        df_ideb = pd.DataFrame(ideb_rows)
        df_censo = df_censo.merge(df_ideb, on="CO_ENTIDADE", how="left")
        logger.info(f"Indicadores INEP adicionados: {df_ideb['ideb_anos_iniciais'].notna().sum()} escolas com dados")

    df_joined_censo = gdf_joined.merge(df_censo, on="CO_ENTIDADE", how="left")
    logger.info(f"Escolas com dados do censo após join: {df_joined_censo['CO_ENTIDADE'].notna().sum()}")

    logger.info("Calculando indicadores por bairro...")
    df_indicadores = calcular_indicadores(
        df=df_joined_censo,
        group_col="CD_BAIRRO",
        config=metricas,
    )

    bairro_meta = gdf_bairros.set_index("CD_BAIRRO")[["NM_BAIRRO", "NM_MUN", "CD_MUN", "geometry"]]
    df_final = df_indicadores.merge(bairro_meta, left_on="CD_BAIRRO", right_index=True, how="left")

    df_final = df_final.rename(columns={
        "CD_BAIRRO": "cd_bairro_ibge",
        "NM_BAIRRO": "bairro",
        "NM_MUN": "municipio",
        "CD_MUN": "municipioIdIbge",
    })

    df_final["geometria"] = df_final["geometry"].apply(
        lambda g: poligono_para_geojson(g) if g is not None and not pd.isna(g) else None
    )
    df_final = df_final.drop(columns=["geometry"], errors="ignore")

    logger.info(f"Agregação por bairro concluída: {len(df_final)} bairros com escolas.")
    return df_final

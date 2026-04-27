import json
import logging
from pathlib import Path

import pandas as pd

from src.common.cep_lookup import enriquecer_com_cep
from src.common.geo_utils import calcular_indicadores
from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

MUNICIPIOS_GEOJSON = "data/silver/geojs-25-mun (1).json"


def _carregar_poligonos_municipios() -> dict:
    """
    Carrega o GeoJSON de municípios da PB e retorna um dict
    {codigo_ibge: geometry_dict} para lookup rápido.

    Geometrias inválidas (ex: Polygon com anéis não contidos) são
    corrigidas via Shapely antes de retornar.
    """
    if not Path(MUNICIPIOS_GEOJSON).exists():
        logger.warning(f"GeoJSON de municípios não encontrado: {MUNICIPIOS_GEOJSON}. Usando apenas centróides.")
        return {}

    with open(MUNICIPIOS_GEOJSON, encoding="utf-8") as f:
        geojson = json.load(f)

    try:
        from shapely.geometry import shape, mapping
        from shapely.validation import make_valid
        use_shapely = True
    except ImportError:
        use_shapely = False
        logger.warning("Shapely não disponível — geometrias inválidas não serão corrigidas.")

    poligonos = {}
    corrigidos = 0
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        codigo = str(props.get("id", "")).strip()
        geometry = feature.get("geometry")
        if not codigo or not geometry:
            continue

        if use_shapely:
            try:
                geom = shape(geometry)
                if not geom.is_valid:
                    geom = make_valid(geom)
                    corrigidos += 1
                geometry = mapping(geom)
            except Exception as e:
                logger.warning(f"Não foi possível corrigir geometria do município {codigo}: {e}")

        poligonos[codigo] = geometry

    if corrigidos > 0:
        logger.info(f"Geometrias corrigidas via Shapely: {corrigidos}")
    logger.info(f"Polígonos municipais carregados: {len(poligonos)} municípios.")
    return poligonos


def run(storage: StorageBackend = None) -> pd.DataFrame:
    """
    Agrega indicadores educacionais por município.

    Returns:
        DataFrame com uma linha por município e colunas:
            municipio, municipioIdIbge, sg_uf, centroide,
            total_bairros, total_escolas, total_matriculas,
            pct_com_internet, pct_com_biblioteca,
            pct_com_lab_informatica, pct_sem_acessibilidade
    """
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    metricas = config["geo_pipeline"]["colunas_metricas"]
    geocode_cfg = config["geocode_pipeline"]["transform"]
    cep_path = config.get("cep_pipeline", {}).get("cep_path", "data/gold/cep.json")

    # 1. Carregar escolas — usar Silver do geocode extract (tem CO_CEP)
    escolas_path = str(Path(paths["gold"]) / geocode_cfg["gold_output"])
    df_gold = storage.read_parquet(escolas_path)

    if "documento" in df_gold.columns and "CO_CEP" not in df_gold.columns:
        df_censo_path = str(Path(paths["silver"]) / config["geocode_pipeline"]["extract"]["silver_output"])
        df_escolas = storage.read_parquet(df_censo_path)
        logger.info(f"Usando Silver do geocode extract: {len(df_escolas)} escolas")
    else:
        df_escolas = df_gold

    # Extrair IDEB do Gold geocodificado e adicionar como colunas planas
    if "documento" in df_gold.columns:
        ideb_rows = []
        for _, row in df_gold.iterrows():
            doc = row.get("documento")
            escola_id = row.get("escolaIdInep")
            if not isinstance(doc, dict):
                continue
            ind = doc.get("indicadores") or {}
            ideb_rows.append({
                "CO_ENTIDADE": str(escola_id),
                "ideb_anos_iniciais": ind.get("idebAnosIniciais"),
                "ideb_anos_finais":   ind.get("idebAnosFinais"),
            })
        if ideb_rows:
            df_ideb = pd.DataFrame(ideb_rows)
            df_escolas = df_escolas.merge(df_ideb, on="CO_ENTIDADE", how="left")
            logger.info("IDEB adicionado: %d escolas com ideb_anos_iniciais",
                        df_ideb["ideb_anos_iniciais"].notna().sum())

    # 2. Enriquecer com município padronizado via CEP
    df = enriquecer_com_cep(df_escolas, cep_path=cep_path)

    sem_municipio = df["municipio_cep"].isna().sum()
    if sem_municipio > 0:
        logger.warning(f"{sem_municipio} escola(s) sem município identificado via CEP.")
    df = df.dropna(subset=["municipio_cep"]).copy()

    # 3. Calcular métricas por município
    logger.info("Calculando indicadores por município...")
    df_indicadores = calcular_indicadores(
        df=df,
        group_col="municipio_cep",
        config=metricas,
    )

    # 4. Recuperar metadados e centróide por município
    municipio_meta = df.groupby("municipio_cep").agg(
        municipioIdIbge=("id_mundv_cep", "first"),
        sg_uf=("sg_uf", "first") if "sg_uf" in df.columns else ("SG_UF", "first"),
        total_bairros=("bairro_cep", pd.Series.nunique),
        lat_media=("lat_cep", "mean"),
        lon_media=("lon_cep", "mean"),
    ).reset_index()

    df_final = df_indicadores.merge(municipio_meta, on="municipio_cep", how="left")
    df_final = df_final.rename(columns={"municipio_cep": "municipio"})

    # 5. Montar centróide GeoJSON
    df_final["centroide"] = df_final.apply(
        lambda row: {
            "type": "Point",
            "coordinates": [round(float(row["lon_media"]), 7), round(float(row["lat_media"]), 7)]
        } if pd.notna(row.get("lat_media")) and pd.notna(row.get("lon_media")) else None,
        axis=1,
    )
    df_final = df_final.drop(columns=["lat_media", "lon_media"], errors="ignore")

    # 6. Adicionar polígono real do GeoJSON de municípios
    poligonos = _carregar_poligonos_municipios()
    if poligonos:
        df_final["geometria"] = df_final["municipioIdIbge"].apply(
            lambda cod: poligonos.get(str(int(cod))) if pd.notna(cod) else None
        )
        com_poligono = df_final["geometria"].notna().sum()
        logger.info(f"Polígonos associados: {com_poligono}/{len(df_final)} municípios.")
    else:
        df_final["geometria"] = None

    logger.info(f"Agregação por município concluída: {len(df_final)} municípios com escolas.")
    return df_final

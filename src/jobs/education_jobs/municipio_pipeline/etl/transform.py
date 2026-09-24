import logging
from pathlib import Path

import geopandas as gpd
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

MUNICIPIOS_GPKG = "data/silver/municipios_nordeste.gpkg"


def _carregar_poligonos_municipios() -> dict:
    """
    Carrega o GeoPackage de municípios do Nordeste e retorna um dict
    {codigo_ibge: geometry_dict} para lookup rápido.

    Geometrias inválidas são corrigidas via Shapely antes de retornar.
    """
    if not Path(MUNICIPIOS_GPKG).exists():
        logger.warning(f"GeoPackage de municípios não encontrado: {MUNICIPIOS_GPKG}. Usando apenas centróides.")
        return {}

    try:
        from shapely.geometry import shape, mapping
        from shapely.validation import make_valid
        use_shapely = True
    except ImportError:
        use_shapely = False
        logger.warning("Shapely não disponível — geometrias inválidas não serão corrigidas.")

    logger.info(f"Carregando GeoPackage de municípios: {MUNICIPIOS_GPKG}")
    gdf = gpd.read_file(MUNICIPIOS_GPKG)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    poligonos = {}
    corrigidos = 0

    # Tentar identificar a coluna de código do município
    col_codigo = None
    for candidate in ["CD_MUN", "CD_GEOCMU", "CD_GEOCODM", "GEOCODIGO", "codarea"]:
        if candidate in gdf.columns:
            col_codigo = candidate
            break

    if col_codigo is None:
        logger.warning("Nenhuma coluna de código de município identificada no GPKG. Colunas: %s", list(gdf.columns))
        return {}

    for _, row in gdf.iterrows():
        codigo = str(row[col_codigo]).strip()
        geometry = row.get("geometry")
        if not codigo or geometry is None:
            continue

        if use_shapely:
            try:
                geom = shape(mapping(geometry))
                if not geom.is_valid:
                    geom = make_valid(geom)
                    corrigidos += 1
                geom_dict = mapping(geom)
            except Exception as e:
                logger.warning(f"Não foi possível corrigir geometria do município {codigo}: {e}")
                geom_dict = mapping(geometry)
        else:
            geom_dict = mapping(geometry)

        poligonos[codigo] = geom_dict

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

    # 1. Carregar escolas
    escolas_path = str(Path(paths["gold"]) / geocode_cfg["gold_output"])
    df_gold = storage.read_parquet(escolas_path)

    if "documento" in df_gold.columns and "CO_CEP" not in df_gold.columns:
        df_censo_path = str(Path(paths["silver"]) / config["geocode_pipeline"]["extract"]["silver_output"])
        df_escolas = storage.read_parquet(df_censo_path)
        logger.info(f"Usando Silver do geocode extract: {len(df_escolas)} escolas")
    else:
        df_escolas = df_gold

    # Extrair IDEB do Gold geocodificado
    if "documento" in df_gold.columns:
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
            df_escolas = df_escolas.merge(df_ideb, on="CO_ENTIDADE", how="left")
            logger.info("Indicadores INEP adicionados: %d escolas com dados",
                        df_ideb["ideb_anos_iniciais"].notna().sum())

    # 2. Município direto do Censo Escolar (CO_MUNICIPIO/NO_MUNICIPIO — 100% preenchido)
    # Não dependemos mais de CEP: o código IBGE do município vem no próprio microdado.
    if "CO_MUNICIPIO" not in df_escolas.columns:
        raise ValueError("CO_MUNICIPIO ausente no Silver do censo — necessário para agregação municipal.")

    df = df_escolas.copy()
    df["CO_MUNICIPIO"] = df["CO_MUNICIPIO"].astype(str).str.strip()

    # Merge coordenadas geocodificadas para calcular centróide médio por município
    if "documento" in df_gold.columns:
        coord_rows = []
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
            lon, lat = coords[0], coords[1]
            if lat == -999.0 or lon == -999.0:
                continue
            coord_rows.append({"CO_ENTIDADE": str(escola_id), "lat_geo": float(lat), "lon_geo": float(lon)})
        if coord_rows:
            df_coords = pd.DataFrame(coord_rows)
            df = df.merge(df_coords, on="CO_ENTIDADE", how="left")

    sem_municipio = df["CO_MUNICIPIO"].isna().sum()
    if sem_municipio > 0:
        logger.warning(f"{sem_municipio} escola(s) sem CO_MUNICIPIO.")
    df = df.dropna(subset=["CO_MUNICIPIO"]).copy()

    # 3. Calcular métricas por município
    logger.info("Calculando indicadores por município (chave: CO_MUNICIPIO)...")
    df_indicadores = calcular_indicadores(
        df=df,
        group_col="CO_MUNICIPIO",
        config=metricas,
    )

    # 4. Recuperar metadados e centróide por município
    agg_spec = {
        "municipio": ("NO_MUNICIPIO", "first"),
        "sg_uf": ("SG_UF", "first"),
    }
    if "lat_geo" in df.columns:
        agg_spec["lat_media"] = ("lat_geo", "mean")
        agg_spec["lon_media"] = ("lon_geo", "mean")

    municipio_meta = df.groupby("CO_MUNICIPIO").agg(**agg_spec).reset_index()
    municipio_meta = municipio_meta.rename(columns={"CO_MUNICIPIO": "municipioIdIbge"})

    df_indicadores = df_indicadores.rename(columns={"CO_MUNICIPIO": "municipioIdIbge"})
    df_final = df_indicadores.merge(municipio_meta, on="municipioIdIbge", how="left")

    # 5. Montar centróide GeoJSON (média das coordenadas das escolas)
    if "lat_media" in df_final.columns:
        df_final["centroide"] = df_final.apply(
            lambda row: {
                "type": "Point",
                "coordinates": [round(float(row["lon_media"]), 7), round(float(row["lat_media"]), 7)]
            } if pd.notna(row.get("lat_media")) and pd.notna(row.get("lon_media")) else None,
            axis=1,
        )
        df_final = df_final.drop(columns=["lat_media", "lon_media"], errors="ignore")
    else:
        df_final["centroide"] = None

    # 6. Adicionar polígono real do GeoPackage de municípios
    poligonos = _carregar_poligonos_municipios()
    if poligonos:
        def _lookup_poligono(cod):
            if pd.isna(cod):
                return None
            cod_str = str(cod).strip()
            # Tentar match direto e também sem eventual sufixo decimal
            return poligonos.get(cod_str) or poligonos.get(cod_str.split(".")[0])
        df_final["geometria"] = df_final["municipioIdIbge"].apply(_lookup_poligono)
        com_poligono = df_final["geometria"].notna().sum()
        logger.info(f"Polígonos associados: {com_poligono}/{len(df_final)} municípios.")
    else:
        df_final["geometria"] = None

    # Converter municipioIdIbge para int (schema espera número)
    df_final["municipioIdIbge"] = pd.to_numeric(df_final["municipioIdIbge"], errors="coerce").astype("Int64")

    logger.info(f"Agregação por município concluída: {len(df_final)} municípios com escolas.")
    return df_final

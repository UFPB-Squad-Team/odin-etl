"""
Setor Pipeline — Transform

Realiza spatial join entre escolas (pontos) e setores censitários (polígonos),
depois agrega indicadores educacionais por setor.

Decisões de design baseadas na EDA:
  - 9.639 setores cobrem 100% da PB (urbano + rural)
  - Setores com NM_BAIRRO preenchido → cidades grandes (36.2% dos setores)
  - Setores sem NM_BAIRRO → interior/rural → identificados por CD_SETOR + NM_MUN
  - Setores tipo 0 (comum) e 1 (aglomerado subnormal) são os relevantes para escolas
  - Tipos especiais (prisões, hospitais, aldeias) são mantidos mas sinalizados

O campo 'nome_area' no documento final é:
  - NM_BAIRRO se preenchido (ex: "Centro")
  - NM_MUN se não tiver bairro (ex: "Água Branca")
Isso garante que todo setor tem um nome legível para o usuário.
"""
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.common.geo_utils import calcular_indicadores, poligono_para_geojson
from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

SETORES_GPKG = "data/silver/setores_pb.gpkg"

# Tipos de setor que fazem sentido receber indicadores de escolas
TIPOS_VALIDOS = {"0", "1"}  # comum e aglomerado subnormal


def _carregar_setores() -> gpd.GeoDataFrame:
    """Carrega o GeoPackage de setores censitários do Silver."""
    if not Path(SETORES_GPKG).exists():
        raise FileNotFoundError(
            f"GeoPackage de setores não encontrado: {SETORES_GPKG}\n"
            "Execute: poetry run python -m src.jobs.education_jobs.geo_ingest_pipeline.main"
        )
    logger.info(f"Carregando setores censitários: {SETORES_GPKG}")
    gdf = gpd.read_file(SETORES_GPKG)
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    logger.info(f"Setores carregados: {len(gdf)} polígonos")
    return gdf


def _montar_nome_area(row: pd.Series) -> str:
    """
    Retorna o nome legível da área para o usuário:
    - Bairro oficial se disponível e não vazio (cidades grandes)
    - Nome do município caso contrário (interior/rural)
    """
    bairro = row.get("NM_BAIRRO")
    municipio = row.get("NM_MUN")

    # Tratar None, NaN e string vazia como ausente
    bairro_str = str(bairro).strip() if bairro is not None and not (isinstance(bairro, float)) else ""
    municipio_str = str(municipio).strip() if municipio is not None and not (isinstance(municipio, float)) else ""

    return bairro_str if bairro_str and bairro_str.lower() != "nan" else municipio_str


def run(
    gdf_escolas: gpd.GeoDataFrame,
    storage: StorageBackend = None,
) -> pd.DataFrame:
    """
    Spatial join escolas × setores censitários e agrega indicadores por setor.

    Args:
        gdf_escolas: GeoDataFrame de escolas com coordenadas válidas (CRS WGS84).
        storage:     StorageBackend para leitura do Silver do censo.

    Returns:
        DataFrame com uma linha por setor que contém escolas, pronto para o load.
    """
    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    metricas = config["geo_pipeline"]["colunas_metricas"]

    # 1. Carregar setores censitários
    gdf_setores = _carregar_setores()

    # Garantir mesmo CRS
    if gdf_escolas.crs.to_epsg() != 4326:
        gdf_escolas = gdf_escolas.to_crs("EPSG:4326")

    # 2. Spatial join: escola (ponto) → setor (polígono)
    logger.info(f"Spatial join: {len(gdf_escolas)} escolas × {len(gdf_setores)} setores...")
    gdf_joined = gpd.sjoin(gdf_escolas, gdf_setores, how="inner", predicate="within")

    sem_setor = len(gdf_escolas) - len(gdf_joined)
    if sem_setor > 0:
        logger.warning(f"{sem_setor} escola(s) fora de qualquer setor censitário.")
    logger.info(f"Escolas associadas a setores: {len(gdf_joined)}")

    # 3. Carregar Silver do censo para obter colunas de infraestrutura/matrículas
    silver_path = str(Path(paths["silver"]) / config["geocode_pipeline"]["extract"]["silver_output"])
    df_censo = storage.read_parquet(silver_path)
    df_censo["CO_ENTIDADE"] = df_censo["CO_ENTIDADE"].astype(str)

    # Extrair IDEB do Gold geocodificado e adicionar ao censo
    gold_path = str(Path(paths["gold"]) / config["geocode_pipeline"]["transform"]["gold_output"])
    if Path(gold_path).exists():
        df_gold = storage.read_parquet(gold_path)
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
            logger.info("Indicadores INEP adicionados: %d escolas com dados",
                        df_ideb["ideb_anos_iniciais"].notna().sum())

    # Join com dados do censo
    df_joined = gdf_joined.merge(df_censo, on="CO_ENTIDADE", how="left")
    logger.info(f"Escolas com dados do censo: {df_joined['CO_ENTIDADE'].notna().sum()}")

    # 4. Agregar métricas por setor censitário
    logger.info("Calculando indicadores por setor...")
    df_indicadores = calcular_indicadores(
        df=df_joined,
        group_col="CD_SETOR",
        config=metricas,
    )

    # 5. Recuperar metadados do setor (nome, município, tipo, situação, polígono)
    setor_meta = gdf_setores.set_index("CD_SETOR")[[
        "NM_BAIRRO", "NM_MUN", "CD_MUN", "SITUACAO", "CD_TIPO", "geometry"
    ]].copy()

    df_final = df_indicadores.merge(setor_meta, left_on="CD_SETOR", right_index=True, how="left")

    # 6. Montar campos semânticos
    df_final["nome_area"] = df_final.apply(_montar_nome_area, axis=1)
    df_final["tem_bairro_oficial"] = df_final["NM_BAIRRO"].apply(
        lambda v: bool(v and str(v).strip() and str(v).strip().lower() != "nan")
    )
    df_final["tipo_setor"] = df_final["CD_TIPO"].map({
        "0": "comum",
        "1": "aglomerado_subnormal",
        "4": "embarcacao",
        "5": "aldeia_indigena",
        "6": "penitenciaria",
        "7": "asilo_orfanato",
        "8": "hospital_clinica",
        "9": "outro_especial",
    }).fillna("outro")

    df_final = df_final.rename(columns={
        "CD_SETOR": "cd_setor",
        "NM_BAIRRO": "nm_bairro",
        "NM_MUN": "nm_municipio",
        "CD_MUN": "co_municipio",
        "SITUACAO": "situacao",
    })

    # Limpar strings "nan" que vêm de campos vazios do shapefile
    for col in ["nm_bairro", "nm_municipio", "nome_area"]:
        if col in df_final.columns:
            df_final[col] = df_final[col].apply(
                lambda v: None if (v is None or str(v).strip().lower() in ("nan", "")) else str(v).strip()
            )

    # 7. Converter polígono para GeoJSON
    df_final["geometria"] = df_final["geometry"].apply(
        lambda g: poligono_para_geojson(g) if g is not None and not pd.isna(g) else None
    )
    df_final = df_final.drop(columns=["geometry", "CD_TIPO"], errors="ignore")

    logger.info(
        f"Agregação por setor concluída: {len(df_final)} setores com escolas "
        f"({df_final['tem_bairro_oficial'].sum()} com bairro oficial, "
        f"{(~df_final['tem_bairro_oficial']).sum()} sem bairro)"
    )
    return df_final

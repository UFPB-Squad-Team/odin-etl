"""
Spatial utilities — point-to-polygon operations and GeoDataFrame helpers.

Handles CRS normalization, GeoDataFrame construction from lat/lon,
and chunked spatial joins for memory-efficient processing.
"""
import logging
from typing import Optional

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, mapping

logger = logging.getLogger(__name__)


def escolas_para_geodataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Convert a DataFrame with 'latitude' and 'longitude' columns into a
    GeoDataFrame with Point geometry and CRS WGS84 (EPSG:4326).

    Rows with null latitude or longitude are silently discarded.
    """
    total = len(df)
    df_valido = df.dropna(subset=["latitude", "longitude"]).copy()
    descartados = total - len(df_valido)

    if descartados > 0:
        logger.info(
            "%d escola(s) descartada(s) por ausência de coordenadas (%d restantes).",
            descartados, len(df_valido),
        )

    geometria = [
        Point(lon, lat)
        for lon, lat in zip(df_valido["longitude"], df_valido["latitude"])
    ]

    return gpd.GeoDataFrame(df_valido, geometry=geometria, crs="EPSG:4326")


def poligono_para_geojson(geometry, simplify_tolerance: float = 0.0) -> dict:
    """
    Convert a Shapely geometry to a GeoJSON dict compatible with MongoDB 2dsphere.

    Repairs invalid geometries (duplicate vertices, self-intersections) that the
    2dsphere index rejects, using make_valid + buffer(0) as fallback.

    Args:
        geometry:           Shapely Polygon/MultiPolygon.
        simplify_tolerance: If > 0, simplify the geometry (Douglas-Peucker) to
                            reduce vertex count and storage size. Tolerance is in
                            degrees (~0.0001 ≈ 11m). 0 disables simplification.
    """
    if geometry is None:
        return None

    geom = geometry

    # Simplificar para reduzir tamanho (menos vértices) — preserva topologia
    if simplify_tolerance > 0:
        try:
            simplified = geom.simplify(simplify_tolerance, preserve_topology=True)
            if not simplified.is_empty:
                geom = simplified
        except Exception:
            pass

    # Reparar geometrias inválidas (duplicate vertices, self-intersection)
    if not geom.is_valid:
        try:
            from shapely.validation import make_valid
            geom = make_valid(geom)
        except Exception:
            try:
                geom = geom.buffer(0)
            except Exception:
                pass

    return mapping(geom)


def spatial_join_por_uf(
    gdf_pontos: gpd.GeoDataFrame,
    gdf_poligonos: gpd.GeoDataFrame,
    coluna_uf_pontos: str = "SG_UF",
    coluna_uf_poligonos: Optional[str] = None,
    predicate: str = "within",
) -> gpd.GeoDataFrame:
    """
    Spatial join chunked por UF para controle de memória.

    Em vez de fazer um sjoin de 75k pontos × 180k polígonos (que pode
    consumir >6GB de RAM), processa cada UF separadamente e concatena.

    Args:
        gdf_pontos:           GeoDataFrame de pontos (escolas).
        gdf_poligonos:        GeoDataFrame de polígonos (setores/bairros).
        coluna_uf_pontos:     Coluna de UF nos pontos.
        coluna_uf_poligonos:  Coluna de UF nos polígonos (se None, usa CD_MUN[:2]).
        predicate:            Predicado espacial ('within', 'intersects').

    Returns:
        GeoDataFrame resultado da concatenação de todos os joins por UF.
    """
    if coluna_uf_pontos not in gdf_pontos.columns:
        logger.warning(
            "Coluna '%s' não encontrada nos pontos. Fazendo join direto (sem chunking).",
            coluna_uf_pontos,
        )
        return gpd.sjoin(gdf_pontos, gdf_poligonos, how="inner", predicate=predicate)

    ufs = sorted(gdf_pontos[coluna_uf_pontos].dropna().unique())
    logger.info("Spatial join chunked: %d UFs, %d pontos, %d polígonos",
                len(ufs), len(gdf_pontos), len(gdf_poligonos))

    resultados = []
    total_associados = 0

    for uf in ufs:
        pontos_uf = gdf_pontos[gdf_pontos[coluna_uf_pontos] == uf]
        if pontos_uf.empty:
            continue

        # Filtrar polígonos pela UF
        if coluna_uf_poligonos and coluna_uf_poligonos in gdf_poligonos.columns:
            poligonos_uf = gdf_poligonos[gdf_poligonos[coluna_uf_poligonos] == uf]
        elif "CD_MUN" in gdf_poligonos.columns:
            from src.common.ibge_codes import CODIGO_UF_PARA_SIGLA
            # Inverter o mapa: sigla → código
            sigla_para_codigo = {v: k for k, v in CODIGO_UF_PARA_SIGLA.items()}
            cod_uf = sigla_para_codigo.get(uf, "")
            poligonos_uf = gdf_poligonos[
                gdf_poligonos["CD_MUN"].astype(str).str[:2] == cod_uf
            ]
        elif "UF" in gdf_poligonos.columns:
            poligonos_uf = gdf_poligonos[gdf_poligonos["UF"] == uf]
        else:
            poligonos_uf = gdf_poligonos

        if poligonos_uf.empty:
            logger.warning("  %s: nenhum polígono encontrado — pulando", uf)
            continue

        joined = gpd.sjoin(pontos_uf, poligonos_uf, how="inner", predicate=predicate)
        total_associados += len(joined)
        logger.info("  %s: %d pontos → %d associados", uf, len(pontos_uf), len(joined))
        resultados.append(joined)

    if not resultados:
        logger.warning("Nenhum ponto associado a polígonos!")
        return gpd.GeoDataFrame()

    gdf_resultado = gpd.GeoDataFrame(pd.concat(resultados, ignore_index=True), crs="EPSG:4326")
    sem_match = len(gdf_pontos) - total_associados
    if sem_match > 0:
        logger.info("  Total associados: %d | Sem match: %d", total_associados, sem_match)

    return gdf_resultado

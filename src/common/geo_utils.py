"""
Geo utilities — backward-compatible facade.

Re-exports from spatial_utils and aggregation_utils for existing imports.
New code should import directly from the specific module.
"""
from src.common.spatial_utils import (
    escolas_para_geodataframe,
    poligono_para_geojson,
    spatial_join_por_uf,
)
from src.common.aggregation_utils import calcular_indicadores

__all__ = [
    "escolas_para_geodataframe",
    "poligono_para_geojson",
    "spatial_join_por_uf",
    "calcular_indicadores",
]

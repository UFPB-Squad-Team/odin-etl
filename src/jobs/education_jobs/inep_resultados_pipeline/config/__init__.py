"""Configuration exports for INEP Resultados pipeline."""

from .settings import (
    CO_ENTIDADE_KEY,
    COLLECTION_NAME,
    IDEB_AF_RENAME_MAP,
    IDEB_AI_RENAME_MAP,
    INSE_RENAME_MAP,
    build_gold_path,
    build_source_paths,
)

__all__ = [
    "CO_ENTIDADE_KEY",
    "COLLECTION_NAME",
    "INSE_RENAME_MAP",
    "IDEB_AI_RENAME_MAP",
    "IDEB_AF_RENAME_MAP",
    "build_source_paths",
    "build_gold_path",
]

"""Configuration helpers and constants for INEP Resultados pipeline."""

from pathlib import Path

CO_ENTIDADE_KEY = "CO_ENTIDADE"
COLLECTION_NAME = "escolas"

INSE_RENAME_MAP = {
    "INSE_VALOR_ABSOLUTO": "inse_valor",
    "INSE_CLASSIFICACAO": "inse_classificacao",
}

IDEB_AI_RENAME_MAP = {
    "VL_OBSERVADO_2023": "ideb_anos_iniciais",
    "VL_META_2023": "ideb_meta_anos_iniciais",
}

IDEB_AF_RENAME_MAP = {
    "VL_OBSERVADO_2023": "ideb_anos_finais",
    "VL_META_2023": "ideb_meta_anos_finais",
}


def build_source_paths(paths_cfg: dict, source_cfg: dict) -> tuple[str, str]:
    """Return (bronze_path, silver_path) for a source config."""
    bronze_path = str(Path(paths_cfg["bronze"]) / source_cfg["output_filename"])
    silver_path = str(Path(paths_cfg["silver"]) / source_cfg["silver_output"])
    return bronze_path, silver_path


def build_gold_path(paths_cfg: dict, output_filename: str) -> str:
    """Return full Gold path for a pipeline output file."""
    return str(Path(paths_cfg["gold"]) / output_filename)

"""
Shared utilities for ODIN-ETL pipelines.
"""
import logging
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from unidecode import unidecode

load_dotenv()


def load_config(config_path: str = "config/config_geocode.yml") -> dict:
    """
    Load a YAML configuration file and return it as a dictionary.

    Args:
        config_path: Path relative to the project root.

    Returns:
        Parsed configuration dictionary.
    """
    try:
        full_path = Path(__file__).resolve().parents[2] / config_path
        with open(full_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {full_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        raise


def normalize_text_for_matching(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Normalize a text column for reliable merges: removes accents,
    special characters, extra spaces, and converts to uppercase.

    Args:
        df: Input DataFrame.
        column_name: Name of the column to normalize.

    Returns:
        DataFrame with an additional column `{column_name}_normalized`.
    """
    logging.info(f"Normalizing text column: {column_name}")
    df_copy = df.copy()
    temp = df_copy[column_name].astype(str).str.upper().apply(unidecode)
    temp = (
        temp.str.replace(r"[-.!?'`()*]", "", regex=True)
        .str.strip()
        .str.replace(r"\s+", "", regex=True)
    )
    df_copy[f"{column_name}_normalized"] = temp
    return df_copy

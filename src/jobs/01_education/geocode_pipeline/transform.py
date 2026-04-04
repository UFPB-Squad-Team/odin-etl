"""
Geocode Pipeline — Transform Step

Reads the Silver parquet from extract, geocodes each unique address
using a pluggable geocode_fn, saves incremental checkpoints, and
writes the final Gold parquet.

The geocode_fn is injected by the caller (main.py), keeping this
module decoupled from any specific geocoding provider.
"""
import logging
from pathlib import Path
from typing import Callable

import pandas as pd
from dotenv import load_dotenv

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# Type alias for the pluggable geocoding function
GeocodeFunction = Callable[[str], tuple[float, float] | None]


def _build_address_column(df: pd.DataFrame, columns: list, final_col: str) -> pd.DataFrame:
    """Concatenate address fields into a single string column and deduplicate."""
    df_addr = df[columns].copy()
    df_addr[final_col] = (
        df_addr["DS_ENDERECO"].astype(str)
        + ", " + df_addr["NU_ENDERECO"].astype(str)
        + ", " + df_addr["NO_BAIRRO"].astype(str)
        + ", " + df_addr["NO_MUNICIPIO"].astype(str)
        + ", " + df_addr["SG_UF"].astype(str)
        + ", " + df_addr["CO_CEP"].astype(str)
    )
    df_addr = df_addr.drop_duplicates(subset=[final_col]).reset_index(drop=True)
    logging.info(f"Unique addresses to geocode: {len(df_addr)}")
    return df_addr


def _load_checkpoint(checkpoint_path: str, address_col: str) -> tuple[pd.DataFrame, set]:
    """Return already-processed DataFrame and set of completed addresses."""
    if Path(checkpoint_path).exists():
        df_done = pd.read_parquet(checkpoint_path)
        done_addresses = set(df_done[address_col].dropna().unique())
        logging.info(f"Checkpoint found: {len(done_addresses)} addresses already geocoded.")
        return df_done, done_addresses
    logging.info("No checkpoint found. Starting from scratch.")
    return pd.DataFrame(), set()


def run(geocode_fn: GeocodeFunction, storage: StorageBackend = None):
    """
    Geocode all unique school addresses from the Silver parquet.

    Args:
        geocode_fn: Callable that receives an address string and returns
                    (latitude, longitude) or None if not found.
        storage:    StorageBackend instance (defaults to get_storage_backend()).
    """
    logging.info("--- STARTING GEOCODE TRANSFORM ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    transform_config = config["geocode_pipeline"]["transform"]
    extract_config = config["geocode_pipeline"]["extract"]

    input_path = str(Path(paths["silver"]) / extract_config["silver_output"])
    gold_path = str(Path(paths["gold"]) / transform_config["gold_output"])
    checkpoint_path = str(Path(paths["checkpoints"]) / transform_config["checkpoint_output"])
    address_col = transform_config["coluna_endereco_final"]
    batch_size = transform_config.get("batch_size", 100)

    logging.info(f"Reading Silver from: {input_path}")
    df_full = storage.read_parquet(input_path)

    df_addresses = _build_address_column(
        df_full,
        columns=transform_config["colunas_endereco"],
        final_col=address_col,
    )

    df_done, done_addresses = _load_checkpoint(checkpoint_path, address_col)
    df_pending = df_addresses[~df_addresses[address_col].isin(done_addresses)].copy()
    logging.info(f"Addresses pending geocoding: {len(df_pending)}")

    if not df_pending.empty:
        results = []
        for i, (_, row) in enumerate(df_pending.iterrows(), start=1):
            address = row[address_col]
            try:
                result = geocode_fn(address)
                lat, lon = result if result else (None, None)
            except Exception as e:
                logging.debug(f"Geocoding failed for '{address}': {e}")
                lat, lon = None, None

            results.append({"latitude": lat, "longitude": lon})

            # Save checkpoint every batch_size records
            if i % batch_size == 0:
                df_batch = df_pending.iloc[:i].copy()
                df_batch[["latitude", "longitude"]] = pd.DataFrame(results)
                df_checkpoint = pd.concat([df_done, df_batch], ignore_index=True)
                Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
                df_checkpoint.to_parquet(checkpoint_path, index=False)
                logging.info(f"Checkpoint saved: {i}/{len(df_pending)} processed.")

        df_pending[["latitude", "longitude"]] = pd.DataFrame(results)
        df_final = pd.concat([df_done, df_pending], ignore_index=True)

        # Final checkpoint save
        Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        df_final.to_parquet(checkpoint_path, index=False)
    else:
        df_final = df_done
        logging.info("All addresses already geocoded. Nothing to process.")

    logging.info(f"Saving Gold to: {gold_path}")
    storage.save_parquet(df_final, gold_path)
    logging.info("--- GEOCODE TRANSFORM COMPLETED ---")


if __name__ == "__main__":
    # When run directly, a placeholder geocode_fn is used.
    # In production, main.py injects the real implementation.
    def _placeholder(address: str):
        logging.warning(f"Placeholder geocoder called for: {address}")
        return None

    run(geocode_fn=_placeholder)

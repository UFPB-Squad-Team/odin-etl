import logging
from pathlib import Path
from typing import Callable

import pandas as pd
from dotenv import load_dotenv

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from src.jobs.education_jobs.geocode_pipeline.document_builder import (
    _build_school_document,
    _clean_value,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# Type alias for the pluggable geocoding function
GeocodeFunction = Callable[[str], tuple[float, float] | None]


def _load_existing_geocoded(existing_geocoded_path: str) -> pd.DataFrame | None:
    """Load pre-geocoded data if file exists (e.g., from previous full geocoding runs)."""
    if Path(existing_geocoded_path).exists():
        try:
            df = pd.read_parquet(existing_geocoded_path)
            # Ensure CO_ENTIDADE is string for merge compatibility
            df["CO_ENTIDADE"] = df["CO_ENTIDADE"].astype(str)
            logging.info(
                f"✓ Loaded existing geocoded data: {len(df)} records "
                f"from {Path(existing_geocoded_path).name}"
            )
            return df
        except Exception as e:
            logging.warning(f"Could not load existing geocoded data: {e}")
            return None
    return None


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


def _load_latest_indicators(indicators_path: str) -> pd.DataFrame | None:
    path = Path(indicators_path)
    if not path.exists():
        logging.info(f"No indicadores gold found at {indicators_path}. Skipping merge.")
        return None

    try:
        df_indicators = pd.read_parquet(path)
        if "id_escola" not in df_indicators.columns:
            logging.warning("Indicators parquet does not contain id_escola. Skipping merge.")
            return None

        df_indicators = df_indicators.copy()
        df_indicators["CO_ENTIDADE"] = df_indicators["id_escola"].astype(str)
        if "ano" in df_indicators.columns:
            df_indicators = df_indicators.sort_values(["CO_ENTIDADE", "ano"])
        else:
            df_indicators = df_indicators.sort_values(["CO_ENTIDADE"])

        df_latest = df_indicators.drop_duplicates(subset=["CO_ENTIDADE"], keep="last").copy()
        drop_columns = {"CO_ENTIDADE", "id_escola", "geo"}
        indicator_columns = [column for column in df_latest.columns if column not in drop_columns]

        df_latest["indicadores_base_dados"] = df_latest[indicator_columns].apply(lambda row: _clean_value(row.to_dict()), axis=1)
        return df_latest[["CO_ENTIDADE", "indicadores_base_dados"]]
    except Exception as e:
        logging.warning(f"Could not load indicators gold data: {e}")
        return None


def run(geocode_fn: GeocodeFunction, storage: StorageBackend = None):
    """
    Geocode all schools from the Silver parquet, using existing geocoded data
    as the primary source, with fallback to geocode_fn for new addresses.

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
    indicators_path = str(Path(paths["gold"]) / "indicadores_base_dos_dados.parquet")

    # Path to pre-geocoded data
    existing_geocoded_path = "data/silver/escolas_nordeste_geocoded.parquet"

    logging.info(f"Reading Silver from: {input_path}")
    df_schools = storage.read_parquet(input_path)
    logging.info(f"Total schools to process: {len(df_schools)}")

    df_schools["CO_ENTIDADE"] = df_schools["CO_ENTIDADE"].astype(str)

    df_geocoded_existing = _load_existing_geocoded(existing_geocoded_path)

    if df_geocoded_existing is not None:
        df_schools = df_schools.merge(
            df_geocoded_existing[["CO_ENTIDADE", "latitude", "longitude"]],
            on="CO_ENTIDADE",
            how="left",
        )

        n_with_coords = df_schools["latitude"].notna().sum()
        n_pending = df_schools["latitude"].isna().sum()
        logging.info(
            f"✓ Merged existing geocoded data: {n_with_coords} schools matched, "
            f"{n_pending} schools still pending"
        )
    else:
        df_schools[["latitude", "longitude"]] = None, None
        logging.info("No existing geocoded dataset found. Will use geocode_fn for all schools.")

    df_pending = df_schools[df_schools["latitude"].isna()].copy()

    if not df_pending.empty:
        logging.info(f"Processing {len(df_pending)} schools with geocode_fn...")

        df_pending[address_col] = (
            df_pending["DS_ENDERECO"].astype(str)
            + ", " + df_pending["NU_ENDERECO"].astype(str)
            + ", " + df_pending["NO_BAIRRO"].astype(str)
            + ", " + df_pending["NO_MUNICIPIO"].astype(str)
            + ", " + df_pending["SG_UF"].astype(str)
            + ", " + df_pending["CO_CEP"].astype(str)
        )

        df_addresses = _build_address_column(
            df_pending,
            columns=transform_config["colunas_endereco"],
            final_col=address_col,
        )[[address_col]].copy()

        df_done, done_addresses = _load_checkpoint(checkpoint_path, address_col)
        df_to_process = df_addresses[~df_addresses[address_col].isin(done_addresses)].copy()
        logging.info(f"Addresses pending geocoding: {len(df_to_process)}")

        if not df_to_process.empty:
            results = []
            for i, (_, row) in enumerate(df_to_process.iterrows(), start=1):
                address = row[address_col]
                try:
                    result = geocode_fn(address)
                    lat, lon = result if result else (None, None)
                except Exception as e:
                    logging.debug(f"Geocoding failed for '{address}': {e}")
                    lat, lon = None, None

                results.append({"latitude": lat, "longitude": lon})

                if i % batch_size == 0:
                    df_batch = df_to_process.iloc[:i].copy()
                    df_batch[["latitude", "longitude"]] = pd.DataFrame(results)
                    df_checkpoint = pd.concat([df_done, df_batch], ignore_index=True)
                    Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
                    df_checkpoint.to_parquet(checkpoint_path, index=False)
                    logging.info(f"Checkpoint saved: {i}/{len(df_to_process)} processed.")

            df_to_process[["latitude", "longitude"]] = pd.DataFrame(results)
            df_from_api = pd.concat([df_done, df_to_process], ignore_index=True)
            df_from_api = df_from_api.drop_duplicates(subset=[address_col], keep="last")

            Path(checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
            df_from_api.to_parquet(checkpoint_path, index=False)
        else:
            df_from_api = df_done.copy()

        if not df_from_api.empty and address_col in df_from_api.columns:
            for idx, row in df_pending.iterrows():
                addr = row[address_col]
                api_result = df_from_api[df_from_api[address_col] == addr]
                if not api_result.empty:
                    df_schools.at[idx, "latitude"] = api_result.iloc[0]["latitude"]
                    df_schools.at[idx, "longitude"] = api_result.iloc[0]["longitude"]

    df_final = df_schools.copy()

    df_indicators_latest = _load_latest_indicators(indicators_path)
    if df_indicators_latest is not None and not df_indicators_latest.empty:
        df_final = df_final.merge(df_indicators_latest, on="CO_ENTIDADE", how="left")
        logging.info(
            f"✓ Merged indicators data: {df_final['indicadores_base_dados'].notna().sum()} schools enriched"
        )

    df_output = pd.DataFrame(
        {
            "escolaIdInep": df_final["CO_ENTIDADE"].astype(str),
            "documento": df_final.apply(_build_school_document, axis=1),
        }
    )

    logging.info(f"Total schools with coordinates: {df_final['latitude'].notna().sum()} / {len(df_final)}")
    logging.info(f"Saving Gold to: {gold_path}")
    storage.save_parquet(df_output, gold_path)
    logging.info("--- GEOCODE TRANSFORM COMPLETED ---")


if __name__ == "__main__":
    # When run directly, a placeholder geocode_fn is used.
    # In production, main.py injects the real implementation.
    def _placeholder(address: str):
        logging.warning(f"Placeholder geocoder called for: {address}")
        return None

    run(geocode_fn=_placeholder)

import logging
import os
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import numpy as np
from dotenv import load_dotenv
from pymongo import MongoClient, ReplaceOne

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

COLLECTION_NAME = "escolas"


def _is_valid_co_entidade(value) -> bool:
    return pd.notna(value) and str(value).strip() != ""


def _is_missing(value) -> bool:
    if value is None:
        return True

    if isinstance(value, (dict, list, tuple, np.ndarray)):
        return False

    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def _sanitize_value(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, nested_value in value.items():
            sanitized = _sanitize_value(nested_value)
            if not _is_missing(sanitized):
                cleaned[key] = sanitized
        return cleaned

    if isinstance(value, list):
        cleaned_list = [_sanitize_value(item) for item in value]
        return [item for item in cleaned_list if not _is_missing(item)]

    if isinstance(value, tuple):
        cleaned_list = [_sanitize_value(item) for item in value]
        return [item for item in cleaned_list if not _is_missing(item)]

    if isinstance(value, np.ndarray):
        cleaned_list = [_sanitize_value(item) for item in value.tolist()]
        return [item for item in cleaned_list if not _is_missing(item)]

    if _is_missing(value):
        return None

    return value


def _to_camel_case(key: str) -> str:
    parts = str(key).split("_")
    if len(parts) == 1:
        return key
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _camelize_keys(value):
    if isinstance(value, dict):
        return {
            _to_camel_case(key): _camelize_keys(nested_value)
            for key, nested_value in value.items()
            if not _is_missing(nested_value)
        }

    if isinstance(value, list):
        return [_camelize_keys(item) for item in value if not _is_missing(item)]

    if isinstance(value, tuple):
        return [_camelize_keys(item) for item in value if not _is_missing(item)]

    if isinstance(value, np.ndarray):
        return [_camelize_keys(item) for item in value.tolist() if not _is_missing(item)]

    return value


def _first_non_missing(*values):
    for value in values:
        if _is_valid_co_entidade(value):
            return value
    return None


def _extract_document(row: pd.Series) -> dict:
    document = row.get("documento")
    if isinstance(document, dict):
        cleaned = _sanitize_value(document)
        indicadores = cleaned.get("indicadores")
        if isinstance(indicadores, dict):
            cleaned["indicadores"] = _camelize_keys(indicadores)
            ano = cleaned["indicadores"].get("anoReferencia")
            if ano is not None:
                try:
                    cleaned["indicadores"]["anoReferencia"] = int(float(ano))
                except Exception:
                    pass
            municipio = cleaned["indicadores"].get("municipioIdIbge")
            if municipio is not None:
                try:
                    cleaned["indicadores"]["municipioIdIbge"] = int(float(municipio))
                except Exception:
                    pass
        return cleaned

    return _sanitize_value(row.dropna().to_dict())


def _infer_db_name_from_uri(mongo_uri: str) -> str | None:
    """Infer database name from URI path (e.g. mongodb+srv://.../mydb?...)."""
    try:
        parsed = urlparse(mongo_uri)
        db_name = parsed.path.lstrip("/").strip()
        return db_name or None
    except Exception:
        return None


def _get_mongo_client() -> tuple:
    """Return (MongoClient, db_name). db_name can come from env or URI path."""
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")

    if not mongo_uri:
        raise ValueError(
            "MONGO_URI environment variable is not set. "
            "Check your .env file."
        )

    if not db_name:
        db_name = _infer_db_name_from_uri(mongo_uri)

    if not db_name:
        raise ValueError(
            "MONGO_DB_NAME environment variable is not set and no database was found in MONGO_URI. "
            "Check your .env file."
        )
    return MongoClient(mongo_uri), db_name


def run(storage: StorageBackend = None):
    """
    Load geocoded schools from Gold parquet into MongoDB.

    Uses upsert on CO_ENTIDADE to ensure idempotency — running this
    step multiple times will not create duplicate documents.
    """
    logging.info("--- STARTING GEOCODE LOAD ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    transform_config = config["geocode_pipeline"]["transform"]

    gold_path = str(Path(paths["gold"]) / transform_config["gold_output"])

    logging.info(f"Reading Gold from: {gold_path}")
    df = storage.read_parquet(gold_path)
    logging.info(f"Total records to load: {len(df)}")

    client, db_name = _get_mongo_client()
    try:
        db = client[db_name]
        collection = db[COLLECTION_NAME]

        collection.delete_many(
            {
                "$and": [
                    {
                        "$or": [
                            {"CO_ENTIDADE": {"$exists": False}},
                            {"CO_ENTIDADE": None},
                            {"CO_ENTIDADE": ""},
                        ]
                    },
                    {
                        "$or": [
                            {"escolaIdInep": {"$exists": False}},
                            {"escolaIdInep": None},
                            {"escolaIdInep": ""},
                        ]
                    },
                ]
            }
        )

        collection.create_index("CO_ENTIDADE", unique=True, sparse=True)
        collection.create_index("escolaIdInep", unique=True, sparse=True)

        operations = []
        for _, row in df.iterrows():
            document = _extract_document(row)
            school_key = _first_non_missing(row.get("escolaIdInep"), row.get("CO_ENTIDADE"), document.get("escolaIdInep"))
            if not _is_valid_co_entidade(school_key):
                continue

            if not document.get("localizacao"):
                continue

            key_value = str(school_key).strip()
            operations.append(
                ReplaceOne(
                    {
                        "$or": [
                            {"CO_ENTIDADE": key_value},
                            {"escolaIdInep": key_value},
                        ]
                    },
                    document,
                    upsert=True,
                )
            )

        if operations:
            result = collection.bulk_write(operations, ordered=False)
            logging.info(
                f"MongoDB upsert complete: "
                f"{result.upserted_count} inserted, "
                f"{result.modified_count} updated."
            )
        else:
            logging.warning("No valid records to insert (missing CO_ENTIDADE, lat, or lon).")

    finally:
        client.close()

    logging.info("--- GEOCODE LOAD COMPLETED ---")


if __name__ == "__main__":
    run()

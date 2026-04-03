"""
Geocode Pipeline — Load Step

Reads the Gold parquet produced by transform and upserts each school
document into MongoDB using CO_ENTIDADE as the unique key.
"""
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

COLLECTION_NAME = "escolas"


def _get_mongo_client() -> tuple:
    """Return (MongoClient, db_name). Raises ValueError if env vars are missing."""
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")

    if not mongo_uri:
        raise ValueError(
            "MONGO_URI environment variable is not set. "
            "Check your .env file."
        )
    if not db_name:
        raise ValueError(
            "MONGO_DB_NAME environment variable is not set. "
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

        # Ensure unique index on CO_ENTIDADE for idempotent upserts
        collection.create_index("CO_ENTIDADE", unique=True)

        operations = [
            UpdateOne(
                {"CO_ENTIDADE": row["CO_ENTIDADE"]},
                {"$set": row.dropna().to_dict()},
                upsert=True,
            )
            for _, row in df.iterrows()
            if pd.notna(row.get("CO_ENTIDADE"))
            and pd.notna(row.get("latitude"))
            and pd.notna(row.get("longitude"))
        ]

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

"""
INEP Resultados Pipeline — Load (Pipeline 2)

Reads the enriched Gold parquet (Censo + INSE + IDEB) and upserts
each school document into MongoDB, enriching the existing documents
created by geocode_pipeline.

Upsert key: CO_ENTIDADE (keeps data consistent across pipelines)
"""
import logging
import os
from urllib.parse import urlparse

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config
from ..config import CO_ENTIDADE_KEY, COLLECTION_NAME, build_gold_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

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
    Load enriched schools (Censo + INSE + IDEB) into MongoDB.

    Uses upsert on CO_ENTIDADE to enrich existing documents from
    geocode_pipeline with IDEB/INSE indicators.
    """
    logging.info("--- STARTING INEP RESULTADOS LOAD ---")
    load_dotenv()

    storage = storage or get_storage_backend()
    config = load_config()
    paths = config["paths"]
    gold_output = config["inep_resultados_pipeline"]["gold_output"]

    gold_path = build_gold_path(paths, gold_output)

    logging.info(f"Reading enriched Gold from: {gold_path}")
    df = storage.read_parquet(gold_path)
    logging.info(f"Total enriched records: {len(df)}")

    client, db_name = _get_mongo_client()
    try:
        db = client[db_name]
        collection = db[COLLECTION_NAME]

        # Ensure unique index on CO_ENTIDADE for idempotent upserts
        collection.create_index("CO_ENTIDADE", unique=True)

        operations = [
            UpdateOne(
                {CO_ENTIDADE_KEY: row[CO_ENTIDADE_KEY]},
                {"$set": row.dropna().to_dict()},
                upsert=True,
            )
            for _, row in df.iterrows()
            if pd.notna(row.get(CO_ENTIDADE_KEY))
        ]

        if operations:
            result = collection.bulk_write(operations, ordered=False)
            logging.info(
                f"MongoDB upsert complete: "
                f"{result.upserted_count} inserted, "
                f"{result.modified_count} updated."
            )
        else:
            logging.warning("No valid records to insert (missing CO_ENTIDADE).")

    finally:
        client.close()

    logging.info("--- INEP RESULTADOS LOAD COMPLETED ---")


if __name__ == "__main__":
    run()

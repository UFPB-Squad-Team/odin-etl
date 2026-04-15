"""
Shared helpers for geo-aggregate pipelines (bairro/municipio).

The goal is to keep duplicated operational logic in one place while
preserving each pipeline's business-specific behavior.
"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from src.common.geo_utils import escolas_para_geodataframe
from src.common.storage import StorageBackend


def load_geocoded_schools_gdf(
    *,
    storage: StorageBackend,
    paths: dict,
    geocode_transform_config: dict,
):
    """Read geocoded schools parquet and return a GeoDataFrame with valid points."""
    gold_path = str(Path(paths["gold"]) / geocode_transform_config["gold_output"])
    df = storage.read_parquet(gold_path)
    return df, escolas_para_geodataframe(df), gold_path


def upsert_dataframe(
    *,
    df: pd.DataFrame,
    collection_name: str,
    key_field: str,
    geo_index_field: str = "geometria",
):
    """Generic Mongo bulk upsert used by aggregate geo pipelines."""
    load_dotenv()

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    if not mongo_uri:
        raise ValueError("MONGO_URI not set. Check your .env file.")
    if not db_name:
        raise ValueError("MONGO_DB_NAME not set. Check your .env file.")

    client = MongoClient(mongo_uri)
    try:
        collection = client[db_name][collection_name]
        collection.create_index([(geo_index_field, "2dsphere")])

        operations = [
            UpdateOne(
                {key_field: row[key_field]},
                {"$set": row.to_dict()},
                upsert=True,
            )
            for _, row in df.iterrows()
        ]

        if operations:
            result = collection.bulk_write(operations, ordered=False)
            return result
        return None
    finally:
        client.close()

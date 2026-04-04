import io
import os
import zipfile
from pathlib import Path
from typing import Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class StorageBackend(Protocol):
    """Interface for all storage operations in ODIN-ETL pipelines."""

    def save_parquet(self, df: pd.DataFrame, path: str) -> None:
        """Persist a DataFrame as a Parquet file at the given path."""
        ...

    def read_parquet(self, path: str) -> pd.DataFrame:
        """Load a Parquet file from the given path into a DataFrame."""
        ...

    def save_zip(self, content: bytes, path: str) -> None:
        """Write raw bytes to a file at the given path."""
        ...

    def read_file_from_zip(self, zip_path: str, target_filename: str) -> bytes:
        """Open a ZIP archive and return the contents of target_filename."""
        ...


class LocalBackend:
    """
    Concrete StorageBackend that persists files on the local filesystem.
    Parent directories are created automatically.
    """

    def save_parquet(self, df: pd.DataFrame, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)

    def read_parquet(self, path: str) -> pd.DataFrame:
        if not Path(path).exists():
            raise FileNotFoundError(f"Parquet file not found: {path}")
        return pd.read_parquet(path)

    def save_zip(self, content: bytes, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)

    def read_file_from_zip(self, zip_path: str, target_filename: str) -> bytes:
        if not Path(zip_path).exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            match = next((n for n in zf.namelist() if target_filename in n), None)
            if match is None:
                raise FileNotFoundError(
                    f"'{target_filename}' not found inside ZIP '{zip_path}'"
                )
            return zf.read(match)


class R2Backend:
    """
    Stub for Cloudflare R2 storage — to be implemented when migrating from local.

    Set STORAGE_BACKEND=r2 in .env and implement each method using boto3
    with the R2 endpoint:
        boto3.client("s3", endpoint_url=os.getenv("R2_ENDPOINT_URL"), ...)
    """

    def save_parquet(self, df: pd.DataFrame, path: str) -> None:
        raise NotImplementedError("R2Backend.save_parquet not yet implemented")

    def read_parquet(self, path: str) -> pd.DataFrame:
        raise NotImplementedError("R2Backend.read_parquet not yet implemented")

    def save_zip(self, content: bytes, path: str) -> None:
        raise NotImplementedError("R2Backend.save_zip not yet implemented")

    def read_file_from_zip(self, zip_path: str, target_filename: str) -> bytes:
        raise NotImplementedError("R2Backend.read_file_from_zip not yet implemented")


def get_storage_backend() -> StorageBackend:
    """
    Factory that returns the appropriate StorageBackend based on the
    STORAGE_BACKEND environment variable.

    Values:
        local (default) — LocalBackend (filesystem)
        r2              — R2Backend (Cloudflare R2, requires implementation)
    """
    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    if backend == "r2":
        return R2Backend()
    return LocalBackend()

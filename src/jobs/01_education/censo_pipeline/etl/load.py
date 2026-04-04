import pandas as pd
from .utils.logger import get_logger
from .utils.paths import ensure_dir

logger = get_logger("Loader")


def save_main_dataset(df: pd.DataFrame, path: str):
    ensure_dir(path.rsplit("/", 1)[0])
    df.to_parquet(path, index=False)
    logger.info(f"Main dataset saved at: {path}")


def save_subdatasets(datasets: dict, base_path: str):
    ensure_dir(base_path)
    for name, subdf in datasets.items():
        output = f"{base_path}/{name}.parquet"
        subdf.to_parquet(output, index=False)
        logger.info(f"Saved subdataset: {output}")

import pandas as pd
from ..utils.logger import get_logger
from ..utils.paths import ensure_dir

logger = get_logger("Loader")


def log_dataframe_preview(name: str, df: pd.DataFrame, max_rows: int = 5):
    logger.info(f"{name} shape: {df.shape}")
    logger.info(f"{name} columns: {list(df.columns)}")
    logger.info(f"{name} head({max_rows}): {df.head(max_rows).to_dict(orient='records')}")


def save_main_dataset(df: pd.DataFrame, path: str):
    ensure_dir(path.rsplit("/", 1)[0])
    log_dataframe_preview("Main dataset", df)
    df.to_parquet(path, index=False)
    logger.info(f"Main dataset saved at: {path}")


def save_subdatasets(datasets: dict, base_path: str):
    ensure_dir(base_path)
    for name, subdf in datasets.items():
        output = f"{base_path}/{name}.parquet"
        log_dataframe_preview(f"Subdataset {name}", subdf)
        subdf.to_parquet(output, index=False)
        logger.info(f"Saved subdataset: {output}")

import os
import pandas as pd

from .etl.downloader import download_zip
from .etl.extract import extract_zip
from .etl.transform import filter_chunk
from .etl.load import save_main_dataset, save_subdatasets
from .etl.subdatasets import split_domains
from .utils.logger import get_logger
from .config.settings import ZIP_URL, ZIP_PATH, EXTRACT_DIR, CHUNKSIZE, OUTPUT_DIR, MAIN_OUTPUT
from .config.columns import COLUNAS_TOTAIS

logger = get_logger("Main")


def find_basica_csv(directory: str) -> str:
    for root, _, files in os.walk(directory):
        for f in files:
            if "basica" in f.lower() and f.endswith(".csv"):
                return os.path.join(root, f)
    raise FileNotFoundError(f"CSV 'basica' not found in: {directory}")


def run_pipeline():
    logger.info("Starting censo_pipeline...")

    download_zip(ZIP_URL, ZIP_PATH)
    extract_zip(ZIP_PATH, EXTRACT_DIR)

    csv_path = find_basica_csv(EXTRACT_DIR)
    logger.info(f"CSV found: {csv_path}")

    chunks = []
    for chunk in pd.read_csv(
        csv_path,
        sep=";",
        dtype=str,
        encoding="latin1",
        chunksize=CHUNKSIZE,
        usecols=lambda col: col in COLUNAS_TOTAIS,
    ):
        chunk = filter_chunk(chunk)
        chunks.append(chunk)

    df_final = pd.concat(chunks, ignore_index=True)
    logger.info(f"Total records after filter: {len(df_final)}")

    save_main_dataset(df_final, MAIN_OUTPUT)

    subdatasets = split_domains(df_final)
    save_subdatasets(subdatasets, f"{OUTPUT_DIR}/subdatasets")

    logger.info("censo_pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()

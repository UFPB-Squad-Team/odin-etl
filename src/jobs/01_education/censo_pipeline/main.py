import pandas as pd
import os

from etl.downloader import download_zip
from etl.extract import extract_zip
from etl.transform import filter_chunk
from etl.load import save_main_dataset, save_subdatasets
from etl.subdatasets import split_domains
from utils.logger import get_logger
from config.settings import *
from config.columns import COLUNAS_TOTAIS

logger = get_logger("Main")

def find_basica_csv(directory):
    for root, _, files in os.walk(directory):
        for f in files:
            if "basica" in f.lower() and f.endswith(".csv"):
                return os.path.join(root, f)
    raise FileNotFoundError("CSV 'basica' not found.")

def run_pipeline():
    logger.info("Starting ETL pipeline...")

    # 1. Download
    download_zip(ZIP_URL, ZIP_PATH)

    # 2. Extract
    extract_zip(ZIP_PATH, EXTRACT_DIR)

    # 3. Locate CSV
    csv_path = find_basica_csv(EXTRACT_DIR)
    logger.info(f"CSV found: {csv_path}")

    # 4. Read in chunks
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

    # 5. Save main dataset
    save_main_dataset(df_final, MAIN_OUTPUT)

    # 6. Generate subdatasets
    subdatasets = split_domains(df_final)
    save_subdatasets(subdatasets, f"{OUTPUT_DIR}/subdatasets")

    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    run_pipeline()

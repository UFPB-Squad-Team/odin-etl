import os
import zipfile
from utils.logger import get_logger

logger = get_logger("Extractor")

def extract_zip(zip_path: str, extract_to: str):
    if os.path.exists(extract_to):
        logger.info("Extraction directory exists. Skipping.")
        return

    logger.info("Extracting ZIP...")

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_to)

    logger.info("Extraction complete.")

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logger import get_logger
from utils.file_utils import file_exists
import os

logger = get_logger("downloader")

def download_zip(url: str, path: str):
    logger.info("Checking if ZIP exists...")

    if file_exists(path):
        logger.info("ZIP already downloaded. Skipping.")
        return

    logger.info("Downloading ZIP with retry strategy...")

    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        with session.get(url, stream=True, timeout=30, headers=headers) as r:
            r.raise_for_status()

            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)

        logger.info("Download completed!")

    except Exception as e:
        logger.error(f"Error downloading ZIP: {e}")
        if file_exists(path):
            logger.warning("Removing corrupted ZIP.")
            os.remove(path)
        raise


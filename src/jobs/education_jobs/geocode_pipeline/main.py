"""
Geocode Pipeline — Orchestrator

Runs the full geocode pipeline: extract -> transform -> load.

The geocoding provider is configured here and injected into transform,
keeping the transform step decoupled from any specific API.

To switch geocoding providers, change the geocode_fn below.
"""
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from src.common.storage import get_storage_backend
from src.jobs.education_jobs.geocode_pipeline.etl import extract, transform, load

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _get_geocode_fn():
    """
    Return the geocoding function to be injected into transform.

    If GOOGLE_API_KEY is not set, returns a placeholder geocoder that
    returns symbolic coordinates (-999, -999) for all addresses.
    This allows the pipeline to progress with dummy coordinates for testing.

    To use real geocoding, set GOOGLE_API_KEY in .env.
    """
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    
    if not api_key:
        logging.warning("[GEOCODE] GOOGLE_API_KEY not set. Using placeholder geocoder (all coords = -999, -999)")
        
        def geocode_placeholder(address: str) -> tuple[float, float] | None:
            """Placeholder geocoder for testing without Google API."""
            return (-999.0, -999.0)
        
        return geocode_placeholder

    from geopy.geocoders import GoogleV3
    import time

    def geocode_google(address: str) -> tuple[float, float] | None:
        try:
            geolocator = GoogleV3(api_key=api_key)
            time.sleep(0.05)  # avoid rate limiting
            location = geolocator.geocode(address, timeout=10)
            if location:
                return location.latitude, location.longitude
            return None
        except Exception as e:
            logging.debug(f"Geocoding error for '{address}': {e}")
            return None

    return geocode_google


def run():
    """Run the full geocode pipeline: extract -> transform -> load."""
    logging.info("=== GEOCODE PIPELINE STARTED ===")
    storage = get_storage_backend()
    geocode_fn = _get_geocode_fn()

    steps = [
        ("extract", lambda: extract.run(storage=storage)),
        ("transform", lambda: transform.run(geocode_fn=geocode_fn, storage=storage)),
        ("load", lambda: load.run(storage=storage)),
    ]

    for step_name, step_fn in steps:
        t0 = datetime.now()
        logging.info(f"[{step_name.upper()}] Starting...")
        try:
            step_fn()
        except Exception as e:
            logging.error(f"[{step_name.upper()}] Failed: {e}")
            raise
        elapsed = (datetime.now() - t0).total_seconds()
        logging.info(f"[{step_name.upper()}] Completed in {elapsed:.1f}s")

    logging.info("=== GEOCODE PIPELINE COMPLETED ===")


if __name__ == "__main__":
    run()


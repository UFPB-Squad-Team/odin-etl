import pandas as pd
from config.settings import TARGET_REGION
from utils.logger import get_logger

logger = get_logger("Transformer")

def filter_chunk(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk[chunk["NO_REGIAO"].str.upper() == TARGET_REGION]
    return chunk

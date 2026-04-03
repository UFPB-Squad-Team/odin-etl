ZIP_URL = "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2024.zip"
ZIP_PATH = "data/bronze/censo_2024.zip"
EXTRACT_DIR = "data/bronze/microdados_censo_escolar_2024"
TARGET_REGION = "NORDESTE"

CHUNKSIZE = 200_000
OUTPUT_DIR = "data/silver"
MAIN_OUTPUT = f"{OUTPUT_DIR}/censo_nordeste_2024.parquet"

import os
import zipfile
import pandas as pd
import logging
import requests

# -----------------------------
# CONFIGURAÇÃO DO LOG
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

# -----------------------------
# CONFIGURAÇÕES DO PIPELINE
# -----------------------------
ZIP_URL = "https://download.inep.gov.br/microdados/microdados_censo_escolar_2024.zip"
ZIP_PATH = "microdados_2024.zip"
EXTRACT_DIR = "microdados_2024"

TARGET_REGION = "NORDESTE"

# Colunas essenciais
ESSENTIAL_COLUMNS = [
    "NO_REGIAO", "SG_UF", "NO_MUNICIPIO", "CO_MUNICIPIO",
    "NO_ENTIDADE", "CO_ENTIDADE"
]

# Palavras-chave para filtrar colunas relevantes
KEYWORDS = [
    "IN_", "QT_", "TP_", "CO_", "NO_", "SG_",
    "MAT", "TUR", "DOC", "ALUNO"
]


# -----------------------------
# FUNÇÃO 1 - Download
# -----------------------------
def download_zip(url: str, dest: str):
    import time
    import requests

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "*/*",
        "Connection": "keep-alive"
    }

    if os.path.exists(dest):
        logging.info("ZIP already exists. Skipping download.")
        return

    logging.info("Downloading ZIP file with safe method...")

    # Tentativas automáticas
    for attempt in range(1, 10):
        try:
            with requests.get(url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()

                # Primeiro valida se não é HTML (erro do INEP)
                content_type = r.headers.get("Content-Type", "")
                if "text/html" in content_type:
                    raise ValueError("O servidor retornou HTML, indicando bloqueio do download.")

                total_length = int(r.headers.get("Content-Length", 0))
                logging.info(f"File size reported: {total_length/1024/1024:.2f} MB")

                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)

            logging.info("Download complete.")
            return

        except Exception as e:
            logging.warning(f"Download failed (Attempt {attempt}/5): {e}")
            time.sleep(2)

    raise ConnectionError("Failed to download ZIP after 5 attempts.")



# -----------------------------
# FUNÇÃO 2 - Extração do ZIP
# -----------------------------
def extract_zip(zip_path: str, extract_to: str):
    if os.path.exists(extract_to):
        logging.info("Extraction folder already exists. Skipping extraction.")
        return

    logging.info("Extracting ZIP...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_to)

    logging.info("Extraction complete.")


# -----------------------------
# FUNÇÃO 3 - Localizar CSV
# -----------------------------
def find_csv(directory: str):
    logging.info("Searching for CSV files inside extracted directory...")

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv") and "basica" in file.lower():
                full_path = os.path.join(root, file)
                logging.info(f"Using CSV file: {full_path}")
                return full_path

    raise FileNotFoundError("CSV file for basic education not found.")


# -----------------------------
# FUNÇÃO 4 - Carregar CSV e detectar colunas
# -----------------------------
def load_and_detect_columns(csv_path: str):
    logging.info("Detecting columns from CSV header...")

    df = pd.read_csv(csv_path, sep=";", encoding="latin1", dtype=str, low_memory=False)
    df.columns = df.columns.str.strip()

    logging.info(f"Detected {len(df.columns)} columns. CSV fully loaded.")
    return df


# -----------------------------
# FUNÇÃO 5 - Filtrar região alvo
# -----------------------------
def filter_region(df: pd.DataFrame, region: str):
    logging.info(f"Filtering rows to include only the {region} Region...")

    filtered = df[df["NO_REGIAO"].str.upper() == region.upper()]

    logging.info(f"Filtered {len(filtered)} rows by NO_REGIAO = '{region}'.")
    return filtered


# -----------------------------
# FUNÇÃO 6 - Selecionar colunas relevantes
# -----------------------------
def select_relevant_columns(df: pd.DataFrame):
    logging.info("Selecting relevant columns...")

    selected_cols = [
        col for col in df.columns
        if any(key in col for key in KEYWORDS)
    ]

    final_cols = list(dict.fromkeys(ESSENTIAL_COLUMNS + selected_cols))

    logging.info(f"Selecting {len(final_cols)} relevant columns.")

    return df[final_cols]


# -----------------------------
# PIPELINE PRINCIPAL
# -----------------------------
def run_pipeline():
    logging.info("Starting Censo Escolar ETL pipeline (Target: Nordeste)...")

    # Download
    download_zip(ZIP_URL, ZIP_PATH)

    # Extract
    extract_zip(ZIP_PATH, EXTRACT_DIR)

    # Locate CSV
    csv_path = find_csv(EXTRACT_DIR)

    # Load data
    df = load_and_detect_columns(csv_path)

    # Filter
    df_nordeste = filter_region(df, TARGET_REGION)

    # Select columns
    df_final = select_relevant_columns(df_nordeste)

    logging.info("Pipeline completed successfully.")
    logging.info(f"Final DataFrame size (Nordeste): {df_final.shape[0]} rows. Columns: {df_final.shape[1]}")

    logging.info("\n=== PREVIEW OF FILTERED DATA ===")
    print(df_final.head(2))

    return df_final


# -----------------------------
# EXECUTAR PIPELINE
# -----------------------------
if __name__ == "__main__":
    df_final = run_pipeline()

    

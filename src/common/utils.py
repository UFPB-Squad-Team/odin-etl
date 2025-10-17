import io
import logging
import os
import zipfile
from pathlib import Path
from typing import Dict

import boto3
import pandas as pd
import yaml
from dotenv import load_dotenv
from unidecode import unidecode

load_dotenv()


def load_config(config_path: str = "config/config_geocode.yml") -> dict:
    """
    Carrega um arquivo de configuração YAML e o retorna como dicionario
    @args: config_path (o caminho para o arquivo de configuração)
    @returns: um dicionário com as configurações carregadas.
    """
    try:
        full_path = Path(__file__).resolve().parents[2] / config_path
        with open(full_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Arquivo de configuração não encontrado em: {full_path}")
        raise
    except Exception as e:
        logging.error(f"Erro ao carregar o arquivo de configuração: {e}")
        raise


def normalize_text_for_matching(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """
    Normaliza uma coluna de texto para facilitar merges, removendo acentos,
    caracteres especiais, espaços e convertendo para maiúsculas.
    """
    logging.info(f"Normalizando texto da coluna: {column_name}")

    df_copy = df.copy()

    temp_series = df_copy[column_name].astype(str).str.upper().apply(unidecode)
    temp_series = (
        temp_series.str.replace("[-.!?'`()*]", "", regex=True)
        .str.replace("MIXING CENTER", "")
        .str.strip()
        .str.replace(r"\s+", "", regex=True)
    )
    df_copy[f"{column_name}_normalized"] = temp_series
    return df_copy


def get_s3_storage_options() -> Dict:
    """Retorna um dicionário com as credenciais da AWS para o Pandas."""
    return {
        "key": os.getenv("AWS_ACCESS_KEY_ID"),
        "secret": os.getenv("AWS_SECRET_ACCESS_KEY"),
    }


def read_zipped_file_from_s3(
    bucket_name: str, s3_zip_key: str, target_filename: str, read_params: dict
) -> pd.DataFrame:
    """Baixa um arquivo ZIP do S3, encontra um arquivo específico e o carrega em um DataFrame."""
    logging.info(f"Lendo '{target_filename}' de dentro do ZIP '{s3_zip_key}'...")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION"),
    )

    zip_obj = s3.get_object(Bucket=bucket_name, Key=s3_zip_key)
    buffer = io.BytesIO(zip_obj["Body"].read())

    with zipfile.ZipFile(buffer) as zf:
        full_target_path = next(
            (s for s in zf.namelist() if target_filename in s), None
        )
        if not full_target_path:
            raise FileNotFoundError(
                f"Arquivo '{target_filename}' não encontrado dentro do ZIP '{s3_zip_key}'"
            )

        with zf.open(full_target_path) as target_file:
            if target_filename.lower().endswith(".csv"):
                return pd.read_csv(target_file, **read_params)
            elif target_filename.lower().endswith((".xls", ".xlsx")):
                return pd.read_excel(target_file, **read_params)
            else:
                raise ValueError("Formato de arquivo não suportado.")

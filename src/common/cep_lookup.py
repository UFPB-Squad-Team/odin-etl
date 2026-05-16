import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def carregar_cep(cep_path: str) -> pd.DataFrame:
    """
    Carrega o dataset de CEPs e retorna um DataFrame indexado por CEP.

    Colunas relevantes retornadas:
        cep, bairro, municipio, id_mundv, sg_uf, latitude, longitude
    """
    path = Path(cep_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset de CEPs não encontrado em: {cep_path}\n"
            "Coloque o arquivo cep.json em data/gold/ ou ajuste o path no config."
        )

    logger.info(f"Carregando dataset de CEPs de: {cep_path}")
    df_cep = pd.read_json(cep_path)

    df_cep["cep"] = df_cep["cep"].astype(str).str.zfill(8)

    colunas = ["cep", "bairro", "municipio", "id_mundv", "sg_uf", "latitude", "longitude"]
    colunas_disponiveis = [c for c in colunas if c in df_cep.columns]
    df_cep = df_cep[colunas_disponiveis].copy()

    df_cep = df_cep.drop_duplicates(subset=["cep"], keep="first")

    logger.info(f"Dataset de CEPs carregado: {len(df_cep)} CEPs únicos.")
    return df_cep


def enriquecer_com_cep(df_escolas: pd.DataFrame, cep_path: str) -> pd.DataFrame:
    """
    Enriquece o DataFrame de escolas com bairro padronizado e centróide via join por CEP.

    Para escolas sem match de CEP, os campos ficam nulos — não são descartadas.

    Args:
        df_escolas: DataFrame com coluna CO_CEP (do Censo Escolar).
        cep_path:   Caminho para o arquivo cep.json.

    Returns:
        DataFrame original com colunas adicionais:
            bairro_cep, municipio_cep, id_mundv_cep,
            lat_cep, lon_cep
    """
    # Normalizar CO_CEP para string com 8 dígitos
    df = df_escolas.copy()
    df["_cep_join"] = (
        df["CO_CEP"]
        .astype(str)
        .str.replace(r"\D", "", regex=True)  # remove traços e espaços
        .str.zfill(8)
    )

    df_cep_renamed = df_cep.rename(columns={
        "bairro": "bairro_cep",
        "municipio": "municipio_cep",
        "id_mundv": "id_mundv_cep",
        "latitude": "lat_cep",
        "longitude": "lon_cep",
    })

    df_merged = df.merge(
        df_cep_renamed[["cep", "bairro_cep", "municipio_cep", "id_mundv_cep", "lat_cep", "lon_cep"]],
        left_on="_cep_join",
        right_on="cep",
        how="left",
    ).drop(columns=["_cep_join", "cep"], errors="ignore")

    matched = df_merged["bairro_cep"].notna().sum()
    unmatched = len(df_merged) - matched
    logger.info(f"Join por CEP: {matched} escolas com bairro identificado, {unmatched} sem match.")

    return df_merged

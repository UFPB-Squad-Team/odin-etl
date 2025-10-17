import logging

import pandas as pd
from dotenv import load_dotenv

from src.common.utils import (
    get_s3_storage_options,
    load_config,
    read_zipped_file_from_s3,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

def _filter_data(df: pd.DataFrame, filter_config: dict) -> pd.DataFrame:
    """Aplica filtros de UF, dependência e situação no DataFrame."""
    logging.info("Aplicando filtros para selecionar o escopo dos dados...")
    df_filtered = df[
        (df["SG_UF"].isin(filter_config["filtro_uf"])) 
        & (df["TP_DEPENDENCIA"].isin(filter_config["filtro_dependencia_adm"]))
        & (
            df["TP_SITUACAO_FUNCIONAMENTO"]
            == filter_config["filtro_situacao_funcionamento"]
        )
    ].copy()
    logging.info(f"Filtros aplicados. {len(df_filtered)} registros selecionados.")
    return df_filtered

def run():
    """
    Orquestra a extração do Censo Escolar do S3, aplica filtros e
    salva o resultado na camada 'intermediate' do S3.
    """
    logging.info("--- INICIANDO JOB DE EXTRAÇÃO (PIPELINE DE ESCOLAS) DO S3 ---")

    load_dotenv()
    config = load_config()
    s3_config = config["s3"]
    source_config = config["ingestion_sources"]["censo_escolar"]
    geocode_config = config["geocode_pipeline"]["extract"]

    try:
        df_raw = read_zipped_file_from_s3(
            bucket_name=s3_config["bucket_name"],
            s3_zip_key=f"{s3_config['raw_folder']}/{source_config['output_filename']}",
            target_filename=source_config["target_filename_in_zip"],
            read_params={
                "delimiter": geocode_config["csv_delimiter"],
                "encoding": geocode_config["csv_encoding"],
                "on_bad_lines": "skip",
                "low_memory": False,
            },
        )

        df_filtered = _filter_data(df_raw, filter_config=geocode_config)

        output_s3_path = f"s3://{s3_config['bucket_name']}/{s3_config['intermediate_folder']}/escolas_nordeste.parquet"
        storage_options = get_s3_storage_options()

        logging.info(f"Salvando arquivo intermediário no S3 em: {output_s3_path}")
        df_filtered.to_parquet(
            output_s3_path, index=False, storage_options=storage_options
        )

        logging.info("--- JOB DE EXTRAÇÃO (S3) FINALIZADO COM SUCESSO ---")

    except Exception as e:
        logging.error(f"Falha na execução do job de extração do S3: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run()

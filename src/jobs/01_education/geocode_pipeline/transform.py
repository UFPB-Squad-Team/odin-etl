import os
import logging
import pandas as pd
from functools import partial
from dotenv import load_dotenv
from pandarallel import pandarallel

from src.common.utils import load_config, get_s3_storage_options

# Inicialização
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
pandarallel.initialize(progress_bar=True, use_memory_fs=False)

def _get_api_key() -> str:
    """Carrega e valida a chave da API do Google das variáveis de ambiente."""
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("Chave GOOGLE_API_KEY não encontrada! Verifique seu arquivo .env.")
    return api_key

def geocode_google_process(endereco: str, api_key: str) -> pd.Series:
    """
    Função autossuficiente para geocodificação.
    Executada em paralelo pelo Pandarallel.
    """
    try:
        # Importações locais para garantir que cada processo tenha seus objetos
        from geopy.geocoders import GoogleV3
        import time
        
        geolocator = GoogleV3(api_key=api_key)
        time.sleep(0.05) 
        location = geolocator.geocode(endereco, timeout=10)
        
        if location:
            # Retorna uma Series para ser desempacotada pelo apply
            return pd.Series([location.latitude, location.longitude])
        return pd.Series([None, None])
    except Exception as e:
        logging.debug(f"Erro ao geocodificar '{endereco}': {e}")
        return pd.Series([None, None])

def create_address_dataframe(df: pd.DataFrame, columns: list, final_col_name: str) -> pd.DataFrame:
    """
    Filtra colunas, cria a coluna de endereço completo e remove duplicatas.
    """
    logging.info("Preparando DataFrame de endereços...")
    
    # 1. Seleção de Colunas
    df_endereco = df[columns].copy()

    # 2. Criação da Coluna de Endereço Completo
    address_parts = [
        df_endereco["DS_ENDERECO"].astype(str) + ", " + df_endereco["NU_ENDERECO"].astype(str),
        df_endereco["NO_BAIRRO"],
        df_endereco["NO_MUNICIPIO"],
        df_endereco["SG_UF"],
        df_endereco["CO_CEP"]
    ]
    df_endereco[final_col_name] = address_parts[0]
    for part in address_parts[1:]:
        df_endereco[final_col_name] = df_endereco[final_col_name] + ", " + part.astype(str)
        
    # 3. Remoção de Duplicatas e Reset de Índice
    df_endereco = df_endereco.drop_duplicates(subset=[final_col_name]).reset_index(drop=True)
    
    logging.info(f"DataFrame de endereços únicos pronto. Total de {len(df_endereco)} endereços.")
    return df_endereco

def manage_progress(df_input: pd.DataFrame, checkpoint_path: str, address_col_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Gerencia a lógica de leitura para retomar o progresso de um arquivo local.
    
    Args:
        df_input: O DataFrame com todos os endereços únicos a serem processados.
        local_path: O caminho local do arquivo de progresso (checkpoint).
        address_col_name: O nome da coluna que contém o endereço completo (chave de deduplicação).
    """
    if os.path.exists(checkpoint_path):
        logging.info(f"\nArquivo de progresso encontrado em: '{checkpoint_path}'. Retomando...")
        df_ja_processado = pd.read_parquet(checkpoint_path)
        
        enderecos_completos = df_ja_processado[address_col_name].dropna().unique()
        logging.info(f"{len(enderecos_completos)} endereços já foram geocodificados com sucesso.")
        
        # Filtra o DataFrame inicial pelo que AINDA NÃO foi processado
        df_para_processar = df_input[~df_input[address_col_name].isin(enderecos_completos)].copy()
    else:
        logging.info("\nNenhum arquivo de progresso encontrado. Começando do zero.")
        df_ja_processado = pd.DataFrame()
        df_para_processar = df_input.copy()

    logging.info(f"Total de endereços a processar nesta execução: {len(df_para_processar)}")
    return df_ja_processado, df_para_processar

def run():
    """
    Orquestra o processo de Transformação e Geocodificação.
    """
    logging.info("--- INICIANDO JOB DE GEOCODIFICAÇÃO (TRANSFORM) ---")

    # Carregamento e Configuração
    config = load_config()
    s3_config = config["s3"]
    geocode_config = config["escolas_pipeline"]["transform"]
    paths_config = config["paths"]
    
    try:
        google_api_key = _get_api_key()
        
        # 1. Leitura do Arquivo Intermediário (Output do Extract)
        input_s3_path = f"s3://{s3_config['bucket_name']}/{paths_config['intermediate_escolas_nordeste']}"
        logging.info(f"Lendo dados de entrada do S3: {input_s3_path}")
        df_full = pd.read_parquet(
            input_s3_path, 
            storage_options=get_s3_storage_options()
        )
        
        # 2. Preparação do DataFrame de Endereços
        df_endereco_inicial = create_address_dataframe(
            df_full, 
            columns=geocode_config["colunas_endereco"],
            final_col_name=geocode_config["coluna_endereco_final"]
        )

        # 3. Gerenciamento do Progresso (Leitura de checkpoint)
        df_ja_processado, df_para_processar = manage_progress(
            df_endereco_inicial, 
            checkpoint_path=geocode_config["checkpoint_output_path"]
        )

        # 4. Execução da Geocodificação
        if not df_para_processar.empty:
            logging.info(f"\nIniciando geocodificação paralela para {len(df_para_processar)} endereços...")
            
            # Cria a função com a chave da API "congelada" para o parallel_apply
            geocode_with_key = partial(geocode_google_process, api_key=google_api_key)
            
            # Aplica a função em paralelo e desempacota os resultados
            resultados = df_para_processar[geocode_config["coluna_endereco_final"]].parallel_apply(geocode_with_key)
            
            df_para_processar[['latitude', 'longitude']] = resultados
            
            logging.info("Geocodificação desta leva concluída.")
            
            # 5. Concatena e Salva o Checkpoint
            df_final = pd.concat([df_ja_processado, df_para_processar], ignore_index=True)
            logging.info(f"Salvando checkpoint em: {geocode_config['checkpoint_output_path']}")
            df_final.to_parquet(geocode_config["checkpoint_output_path"], index=False)

        else:
            df_final = df_ja_processado
            logging.info("Nenhum endereço novo para processar. O trabalho já está concluído!")
        
        # 6. Salvamento Final no S3 (Camada Processed)
        output_s3_path = f"s3://{s3_config['bucket_name']}/{s3_config['processed_folder']}/escolas_nordeste_geocoded.parquet"
        logging.info(f"\nSalvando resultado final no S3 (Processed): {output_s3_path}")
        df_final.to_parquet(
            output_s3_path, 
            index=False, 
            storage_options=get_s3_storage_options()
        )
        
        logging.info("--- JOB DE GEOCODIFICAÇÃO (TRANSFORM) FINALIZADO COM SUCESSO ---")

    except Exception as e:
        logging.error(f"Falha na execução do job de geocodificação: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run()
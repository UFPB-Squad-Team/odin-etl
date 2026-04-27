import logging
import os
from typing import Any, Dict

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, UpdateOne
from pymongo.errors import BulkWriteError

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

def _val(x: Any) -> Any:
    """Converte para tipo Python nativo, tratando NaN como None."""
    if pd.isna(x):
        return None
    if isinstance(x, (int, float)):
        return float(x) if isinstance(x, float) else int(x)
    return x

def _construir_documento_municipio(row: pd.Series) -> Dict[str, Any]:
    """
    Constrói o sub-documento com indicadores socioeconômicos a partir de uma linha do DataFrame.
    Agrupa os indicadores por tema (população, saneamento, etc).
    """
    return {
        "populacao": {
            "total": _val(row.get('total_populacao')),
            "totalDomicilios": _val(row.get('total_domicilios')),
            "mediaMoradoresPorDomicilio": _val(row.get('media_moradores_por_domicilio')),
        },
        "estruturaEtaria": {
            "pctCriancas0a9": _val(row.get('pct_criancas_0_9')),
            "pctIdosos60Mais": _val(row.get('pct_idosos_60_mais')),
        },
        "raca": {
            "pctPretaParda": _val(row.get('pct_preta_parda')),
        },
        "saneamento": {
            "pctAguaRedeGeral": _val(row.get('pct_agua_rede_geral')),
            "pctEsgotoRedeGeral": _val(row.get('pct_esgoto_rede_geral')),
            "pctLixoColetado": _val(row.get('pct_lixo_coletado')),
        },
        "educacao": {
            "taxaAnalfabetismo15Mais": _val(row.get('taxa_analfabetismo_15_mais')),
        },
        "familia": {
            "pctResponsavelFeminino": _val(row.get('pct_responsavel_feminino')),
        },
    }

def run(storage: StorageBackend = None) -> int:
    """
    Upsert de indicadores socioeconômicos por município no MongoDB.

    Estratégia de merge:
        - Chave de upsert: municipioIdIbge (compartilhada com outros domínios)
        - $set cirúrgico: atualiza apenas os campos base e os sub-documentos detalhados acima
        - Evita sobrescrever sub-documentos de outros pipelines (como 'educacao')

    Args:
        storage: Instância do StorageBackend para leitura dos dados em parquet.
    """
    load_dotenv()
    config = load_config()
    storage = storage or get_storage_backend()
    
    logger.info("=" * 60)
    logger.info("[LOAD] — MUNICÍPIO SOCIOECONÔMICO")
    logger.info("=" * 60)

    gold_file = config.get("transform_municipio", {}).get("gold_output", "municipio_socioeconomico_pb.parquet")
    gold_path = f"data/gold/{gold_file}"
    
    try:
        df = storage.read_parquet(gold_path)
        logger.info(f"Carregando {len(df)} municípios da camada Gold...")
    except Exception as e:
        logger.error(f"Falha ao ler o arquivo Gold em {gold_path}: {e}")
        raise

    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB_NAME")
    colecao_nome = config.get("geo_pipeline", {}).get("mongodb", {}).get("colecao_municipios", "municipio_indicadores")
    
    if not mongo_uri or not db_name:
        raise ValueError("MONGO_URI ou MONGO_DB_NAME não definidos no .env.")

    logger.info(f"Conectando ao MongoDB: Banco '{db_name}' | Coleção '{colecao_nome}'")
    client = MongoClient(mongo_uri)
    
    try:
        db = client[db_name]
        collection = db[colecao_nome]

        collection.create_index([("municipioIdIbge", ASCENDING)], unique=True)
        collection.create_index([("uf", ASCENDING)])

        operacoes = []
        
        for _, row in df.iterrows():
            municipio_id = int(row['CD_MUN'])
            
            campos_base = {
                "municipioIdIbge": municipio_id,
                "uf": _val(row.get('uf')),
                "anoReferencia": _val(row.get('ano_referencia')),
                "fonte": _val(row.get('fonte')),
            }
            
            dados_socioeconomicos = _construir_documento_municipio(row)
            documento_final = {**campos_base, **dados_socioeconomicos}

            operacoes.append(
                UpdateOne(
                    {"municipioIdIbge": municipio_id},
                    {"$set": documento_final},
                    upsert=True
                )
            )

        if operacoes:
            try:
                resultado = collection.bulk_write(operacoes, ordered=False)
                total_processado = resultado.upserted_count + resultado.modified_count
                
                logger.info(f"Inserções novas: {resultado.upserted_count}")
                logger.info(f"Atualizações realizadas: {resultado.modified_count}")
                
            except BulkWriteError as e:
                logger.error(f"Erro no bulk write MongoDB: {e.details}")
                raise
        else:
            logger.warning("Nenhum município processado. DataFrame vazio.")
            return 0

        total_docs = collection.count_documents({})
        logger.info(f"Total de documentos na coleção: {total_docs}")

        return total_processado

    finally:
        client.close()

if __name__ == "__main__":
    run()
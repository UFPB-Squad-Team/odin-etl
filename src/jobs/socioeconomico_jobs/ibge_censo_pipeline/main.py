"""
Orquestrador do pipeline IBGE Censo 2022.
"""
import logging

logger = logging.getLogger(__name__)


def run():
    """
    Executa o pipeline completo: Extract → Transform → Load para todas as granularidades.
    """
    logger.info("Iniciando pipeline IBGE Censo 2022...")
    
    # TODO: Implementar nas próximas tasks
    # from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import extract
    # from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio import transform, load
    # from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.setor import transform, load
    # from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.bairro import transform, load
    
    logger.info("Pipeline IBGE Censo 2022 concluído.")


if __name__ == "__main__":
    run()

import logging

from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.main import run as run_ibge_censo

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    """
    Executa todos os pipelines do módulo socioeconômico em sequência.
    """
    logger.info("=" * 60)
    logger.info("INICIANDO MÓDULO SOCIOECONÔMICO")
    logger.info("=" * 60)
    
    try:
        run_ibge_censo()
        logger.info(" Módulo socioeconômico concluído com sucesso!")
    except Exception as e:
        logger.error(f" Erro no módulo socioeconômico: {e}")
        raise


if __name__ == "__main__":
    run()

import logging

from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import extract
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio import transform as transform_municipio
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio import load as load_municipio
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.setor import transform as transform_setor
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.setor import load as load_setor
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.bairro import transform as transform_bairro
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.bairro import load as load_bairro

logger = logging.getLogger(__name__)


def run_municipio() -> None:
    """Extract → Transform → Load para município."""
    logger.info("🏙️  Pipeline MUNICÍPIO — iniciando...")
    extract.run(granularidades=["municipio"])
    result = transform_municipio.run()
    logger.info("   %d municípios | pop: %s", result.municipios, f"{result.pop_total:,.0f}")
    total = load_municipio.run(df=result.df)
    logger.info("   %d documentos no MongoDB", total)
    logger.info("✅ Pipeline MUNICÍPIO concluído.")


def run_setor() -> None:
    """Extract → Transform → Load para setor censitário."""
    logger.info("🗺️  Pipeline SETOR — iniciando...")
    extract.run(granularidades=["setor"])
    result = transform_setor.run()
    logger.info("   %d setores | pop: %s", result.setores, f"{result.pop_total:,.0f}")
    total = load_setor.run(df=result.df)
    logger.info("   %d documentos no MongoDB", total)
    logger.info("✅ Pipeline SETOR concluído.")


def run_bairro() -> None:
    """Extract → Transform → Load para bairro."""
    logger.info("🏘️  Pipeline BAIRRO — iniciando...")
    extract.run(granularidades=["bairro"])
    result = transform_bairro.run()
    logger.info("   %d bairros | pop: %s", result.bairros, f"{result.pop_total:,.0f}")
    total = load_bairro.run(df=result.df)
    logger.info("   %d documentos no MongoDB", total)
    logger.info("✅ Pipeline BAIRRO concluído.")


def run() -> None:
    """Executa o pipeline completo para todas as granularidades."""
    logger.info("=" * 60)
    logger.info("PIPELINE IBGE CENSO 2022")
    logger.info("=" * 60)

    run_municipio()
    run_setor()
    run_bairro()

    logger.info("=" * 60)
    logger.info("✅ PIPELINE IBGE CENSO 2022 CONCLUÍDO")
    logger.info("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )
    run()

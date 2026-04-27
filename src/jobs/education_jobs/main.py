import logging
from datetime import datetime

from src.jobs.education_jobs.censo_pipeline.main import run_pipeline as run_censo
from src.jobs.education_jobs.geocode_pipeline.main import run as run_geocode
from src.jobs.education_jobs.inep_indicadores_pipeline.main import run as run_indicadores  # substituiu Base dos Dados
from src.jobs.education_jobs.geo_ingest_pipeline.main import run as run_geo_ingest
from src.jobs.education_jobs.bairro_pipeline.main import run as run_bairro
from src.jobs.education_jobs.municipio_pipeline.main import run as run_municipio
from src.jobs.education_jobs.setor_pipeline.main import run as run_setor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run():
    logging.info("=== EDUCATION JOB STARTED ===")

    pipelines = [
        ("censo_pipeline", run_censo),
        ("indicadores_pipeline", run_indicadores),
        ("geocode_pipeline", run_geocode),
        ("geo_ingest_pipeline", run_geo_ingest),  # processa shapefile de bairros e setores IBGE
        ("bairro_pipeline", run_bairro),           # agrega por bairro via spatial join
        ("municipio_pipeline", run_municipio),     # agrega por município via CEP
        ("setor_pipeline", run_setor),             # agrega por setor censitário (cobertura total PB)
        # ("inep_resultados_pipeline", run_inep),  # URLs INEP pendentes de verificação
    ]

    for nome, pipeline_fn in pipelines:
        t0 = datetime.now()
        logging.info(f"[{nome.upper()}] Starting...")
        try:
            pipeline_fn()
        except Exception as e:
            logging.error(f"[{nome.upper()}] Failed: {e}")
            raise
        elapsed = (datetime.now() - t0).total_seconds()
        logging.info(f"[{nome.upper()}] Completed in {elapsed:.1f}s")

    logging.info("=== EDUCATION JOB COMPLETED — dados disponíveis no MongoDB (escolas, bairro_indicadores, municipio_indicadores) ===")


if __name__ == "__main__":
    run()

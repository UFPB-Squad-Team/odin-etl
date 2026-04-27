import io
import logging
import subprocess
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.common.storage import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/inep_indicadores.yml")

_SENTINELA_AUSENTE = "--"


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass(frozen=True)
class FonteConfig:
    """Configuração imutável de uma fonte de indicador."""
    sigla: str
    descricao: str
    url: str
    ano: int
    header_row: int
    colunas: dict
    chave_escola: str = "CO_ENTIDADE"


def _build_fontes(cfg: dict) -> dict[str, FonteConfig]:
    return {
        sigla: FonteConfig(
            sigla=dados["sigla"],
            descricao=dados["descricao"],
            url=dados["url"],
            ano=dados["ano"],
            header_row=dados["header_row"],
            colunas=dados["colunas"],
            chave_escola=dados.get("chave_escola", "CO_ENTIDADE"),
        )
        for sigla, dados in cfg["fontes"].items()
    }


def _baixar_com_retry(url: str, destino: Path, max_tentativas: int = 3) -> None:
    """
    Baixa arquivo com retry e backoff exponencial usando curl.

    Usa curl em vez de urllib porque o servidor do INEP tem certificado
    que o Python não aceita por padrão no macOS/Linux sem configuração extra.
    curl lida com isso nativamente.
    """
    for tentativa in range(1, max_tentativas + 1):
        try:
            logger.info("[%d/%d] Baixando: %s", tentativa, max_tentativas, url)
            inicio = time.monotonic()
            result = subprocess.run(
                ["curl", "-skL", "-o", str(destino), url, "--max-time", "300"],
                capture_output=True,
                check=True,
            )
            duracao = time.monotonic() - inicio
            tamanho = destino.stat().st_size if destino.exists() else 0
            logger.info(
                "Download concluído: %.1f MB em %.1fs → %s",
                tamanho / 1e6, duracao, destino.name,
            )
            try:
                with zipfile.ZipFile(destino):
                    pass
            except zipfile.BadZipFile:
                raise RuntimeError(f"Arquivo baixado não é um ZIP válido: {destino.name}")
            return
        except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
            logger.warning("Tentativa %d falhou: %s", tentativa, exc)
            if destino.exists():
                destino.unlink()
            if tentativa < max_tentativas:
                espera = 2 ** tentativa
                logger.info("Aguardando %ds...", espera)
                time.sleep(espera)
            else:
                raise RuntimeError(
                    f"Falha ao baixar '{destino.name}' após {max_tentativas} tentativas."
                ) from exc


def _extrair_xlsx_do_zip(zip_path: Path) -> bytes:
    """Extrai o primeiro XLSX encontrado dentro do ZIP."""
    with zipfile.ZipFile(zip_path) as z:
        xlsx_files = [f for f in z.namelist() if f.lower().endswith(".xlsx")]
        if not xlsx_files:
            raise FileNotFoundError(f"Nenhum XLSX encontrado em {zip_path.name}")
        with z.open(xlsx_files[0]) as f:
            return f.read()


def _ler_xlsx_inep(xlsx_bytes: bytes, header_row: int, filtro_uf: str) -> pd.DataFrame:
    """
    Lê o XLSX do INEP, aplica o header correto e filtra pela UF.

    Tratamentos aplicados (descobertos na EDA):
    - Header row varia por arquivo (8, 9 ou 10)
    - Sentinela '--' → None (escola sem aquela etapa de ensino)
    - Filtra pela UF configurada
    """
    df = pd.read_excel(
        io.BytesIO(xlsx_bytes),
        header=header_row,
        dtype=str,
    )

    df = df.replace(_SENTINELA_AUSENTE, None)

    if "SG_UF" in df.columns:
        df = df[df["SG_UF"] == filtro_uf].copy()
        logger.info("  Registros %s: %d", filtro_uf, len(df))
    else:
        logger.warning("  Coluna SG_UF não encontrada — mantendo todos os registros")

    return df


def baixar_fonte(
    fonte: FonteConfig,
    bronze_dir: Path,
    filtro_uf: str,
    filtro_dependencias: Optional[list[str]] = None,
    storage: Optional[StorageBackend] = None,
) -> pd.DataFrame:
    """
    Baixa uma fonte do INEP e retorna DataFrame filtrado pela UF e dependência.
    """
    bronze_dir.mkdir(parents=True, exist_ok=True)
    zip_path = bronze_dir / f"{fonte.sigla}_{fonte.ano}_ESCOLAS.zip"

    if zip_path.exists():
        logger.info("Cache hit — Bronze: %s (%.1f MB)", zip_path.name, zip_path.stat().st_size / 1e6)
    else:
        _baixar_com_retry(fonte.url, zip_path)

    logger.info("Extraindo XLSX: %s", zip_path.name)
    xlsx_bytes = _extrair_xlsx_do_zip(zip_path)

    logger.info("Lendo com header_row=%d, filtro_uf=%s", fonte.header_row, filtro_uf)
    df = _ler_xlsx_inep(xlsx_bytes, fonte.header_row, filtro_uf)

    # Filtrar dependências administrativas (ex: excluir privadas)
    if filtro_dependencias and "NO_DEPENDENCIA" in df.columns:
        antes = len(df)
        df = df[df["NO_DEPENDENCIA"].isin(filtro_dependencias)].copy()
        logger.info("  Filtro dependência %s: %d → %d registros", filtro_dependencias, antes, len(df))

    # Normalizar chave para CO_ENTIDADE (IDEB usa ID_ESCOLA)
    if fonte.chave_escola != "CO_ENTIDADE" and fonte.chave_escola in df.columns:
        df = df.rename(columns={fonte.chave_escola: "CO_ENTIDADE"})
        logger.info("  Chave renomeada: %s → CO_ENTIDADE", fonte.chave_escola)

    return df


def run(
    fontes_selecionadas: Optional[list[str]] = None,
    storage: Optional[StorageBackend] = None,
) -> dict[str, pd.DataFrame]:
    """
    Executa o extract de todas as fontes configuradas.

    Args:
        fontes_selecionadas: Lista de siglas a processar (None = todas)
        storage:             Backend de armazenamento

    Returns:
        Dict {sigla: DataFrame} com dados de cada fonte filtrados pela UF.
    """
    cfg = _load_config()
    storage = storage or get_storage_backend()
    fontes = _build_fontes(cfg)
    bronze_dir = Path(cfg["paths"]["bronze"])
    filtro_uf = cfg["filtro_uf"]
    filtro_dependencias = cfg.get("filtro_dependencias")

    if fontes_selecionadas:
        fontes = {k: v for k, v in fontes.items() if k in fontes_selecionadas}

    logger.info("=" * 60)
    logger.info("EXTRACT — Indicadores INEP")
    logger.info("Fontes: %s | UF: %s", list(fontes.keys()), filtro_uf)
    logger.info("=" * 60)

    resultados: dict[str, pd.DataFrame] = {}
    erros: list[str] = []

    for sigla, fonte in fontes.items():
        logger.info("\n[%s] %s", sigla, fonte.descricao)
        try:
            df = baixar_fonte(fonte, bronze_dir, filtro_uf, filtro_dependencias, storage)
            resultados[sigla] = df
            logger.info("  ✅ %d registros", len(df))
        except Exception as exc:
            logger.error("  ❌ Erro em %s: %s", sigla, exc)
            erros.append(f"{sigla}: {exc}")

    logger.info("\n%s", "=" * 60)
    logger.info("EXTRACT CONCLUÍDO — %d/%d fontes", len(resultados), len(fontes))
    if erros:
        logger.warning("Erros: %s", erros)
    logger.info("=" * 60)

    return resultados


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
    run()

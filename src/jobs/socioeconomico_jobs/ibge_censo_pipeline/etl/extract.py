import ftplib
import io
import logging
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import yaml

from src.common.storage import StorageBackend, get_storage_backend

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path("config/ibge_censo.yml")


def _load_config() -> dict:
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


_cfg = _load_config()


@dataclass(frozen=True)
class FtpConfig:
    host: str
    base_dir: str
    timeout: int
    max_tentativas: int


@dataclass(frozen=True)
class GranularidadeConfig:
    ftp_dir: str
    prefixo_arquivo: str


def _build_ftp_config() -> FtpConfig:
    ftp = _cfg["ftp"]
    return FtpConfig(
        host=ftp["host"],
        base_dir=ftp["base_dir"],
        timeout=ftp["timeout_segundos"],
        max_tentativas=ftp["max_tentativas"],
    )


def _build_granularidade_map() -> Dict[str, GranularidadeConfig]:
    return {
        nome: GranularidadeConfig(**valores)
        for nome, valores in _cfg["granularidades"].items()
    }


FTP = _build_ftp_config()
GRANULARIDADES: Dict[str, GranularidadeConfig] = _build_granularidade_map()
DATASETS: List[str] = _cfg["datasets"]
NOMES_COM_DATA: Dict[str, str] = _cfg["nomes_com_data"]
FILTRO_UF: List[str] = _cfg["filtro_uf"]
CSV_ENCODING: str = _cfg["csv"]["encoding"]
CSV_SEPARADOR: str = _cfg["csv"]["separador"]
BRONZE_DIR: Path = Path(_cfg["paths"]["bronze"])
SILVER_DIR: Path = Path(_cfg["paths"]["silver"])


def _resolver_nome_zip(prefixo: str, dataset: str) -> str:
    """
    Retorna o nome correto do ZIP no FTP.

    Alguns arquivos têm sufixo de data (ex: _20250417). O mapeamento
    está em config/ibge_censo.yml → nomes_com_data. Se o IBGE publicar
    uma nova versão, atualize o YAML — sem tocar no código.
    """
    chave = f"{prefixo}_{dataset}_BR"
    return NOMES_COM_DATA.get(chave, f"{chave}.zip")


def _conectar_ftp() -> ftplib.FTP:
    """Abre uma conexão FTP anônima com o servidor do IBGE."""
    ftp = ftplib.FTP(FTP.host, timeout=FTP.timeout)
    ftp.login()
    return ftp


def _baixar_bytes_ftp(caminho_ftp: str) -> bytes:
    """Baixa um arquivo do FTP e retorna seu conteúdo como bytes."""
    ftp = _conectar_ftp()
    try:
        buf = io.BytesIO()
        ftp.retrbinary(f"RETR {caminho_ftp}", buf.write)
        return buf.getvalue()
    finally:
        ftp.quit()


def _baixar_com_retry(caminho_ftp: str, destino: Path) -> None:
    """
    Baixa um arquivo do FTP com retry e backoff exponencial.

    Usamos ftplib em vez de urllib porque o servidor do IBGE às vezes
    rejeita conexões HTTP mas aceita FTP nativo.

    Args:
        caminho_ftp: Caminho completo no servidor FTP.
        destino:     Onde salvar o arquivo localmente.
    """
    for tentativa in range(1, FTP.max_tentativas + 1):
        try:
            logger.info(
                "[%d/%d] Baixando: %s%s",
                tentativa, FTP.max_tentativas, FTP.host, caminho_ftp,
            )
            inicio = time.monotonic()
            conteudo = _baixar_bytes_ftp(caminho_ftp)
            destino.write_bytes(conteudo)

            duracao = time.monotonic() - inicio
            tamanho_mb = len(conteudo) / (1024 * 1024)
            logger.info("Download concluído: %.1f MB em %.1fs → %s", tamanho_mb, duracao, destino.name)
            return

        except Exception as exc:
            logger.warning("Tentativa %d falhou: %s", tentativa, exc)
            if destino.exists():
                destino.unlink()

            if tentativa < FTP.max_tentativas:
                espera = 2 ** tentativa  # backoff: 2s, 4s, 8s
                logger.info("Aguardando %ds antes de tentar novamente...", espera)
                time.sleep(espera)
            else:
                raise RuntimeError(
                    f"Falha ao baixar '{destino.name}' após {FTP.max_tentativas} tentativas. "
                    f"Último erro: {exc}"
                ) from exc




def _ler_csv_do_zip(zip_path: Path) -> pd.DataFrame:
    """Extrai e lê o primeiro CSV encontrado dentro de um ZIP do IBGE."""
    with zipfile.ZipFile(zip_path, "r") as z:
        csvs = [nome for nome in z.namelist() if nome.endswith(".csv")]
        if not csvs:
            raise FileNotFoundError(f"Nenhum CSV encontrado em {zip_path.name}")

        csv_interno = csvs[0]
        logger.info("CSV interno: %s", csv_interno)

        with z.open(csv_interno) as f:
            return pd.read_csv(
                f,
                sep=CSV_SEPARADOR,
                encoding=CSV_ENCODING,
                dtype=str,         
                low_memory=False,  
            )


_COLUNAS_UF_PRIORIDADE = ["CD_UF", "CD_MUN", "CD_SETOR", "CD_BAIRRO", "setor"]


def _coluna_case_insensitive(df: pd.DataFrame, nome: str) -> str | None:
    """Retorna o nome real da coluna no DataFrame, ignorando maiúsculas/minúsculas."""
    nome_upper = nome.upper()
    for col in df.columns:
        if col.upper() == nome_upper:
            return col
    return None


def _filtrar_uf(df: pd.DataFrame, dataset: str, granularidade: str) -> pd.DataFrame:
    """
    Filtra o DataFrame para as UFs configuradas em FILTRO_UF.

    Tenta CD_UF → CD_MUN → CD_SETOR → CD_BAIRRO → setor nessa ordem,
    CD_UF faz match exato; nas demais, os dois primeiros dígitos identificam a UF.
    """
    for nome_coluna in _COLUNAS_UF_PRIORIDADE:
        coluna = _coluna_case_insensitive(df, nome_coluna)
        if coluna is None:
            continue

        if nome_coluna == "CD_UF":
            filtrado = df[df[coluna].isin(FILTRO_UF)].copy()
        else:
            filtrado = df[df[coluna].str[:2].isin(FILTRO_UF)].copy()

        pct = len(filtrado) / len(df) * 100 if len(df) > 0 else 0
        logger.info(
            "Registros UFs=%s via %s: %d (%.1f%% do Brasil)",
            FILTRO_UF, coluna, len(filtrado), pct,
        )
        return filtrado

    logger.warning(
        "Nenhuma coluna de UF encontrada em '%s' (%s). "
        "Mantendo todos os registros — verifique o dicionário de dados do IBGE.",
        dataset, granularidade,
    )
    return df


def _salvar_silver(df: pd.DataFrame, dataset: str, granularidade: str, storage: StorageBackend) -> str:
    """Persiste o DataFrame filtrado como Parquet no Silver e retorna o caminho."""
    nome_arquivo = f"ibge_censo2022_{granularidade}_{dataset}_nordeste.parquet"
    caminho = str(SILVER_DIR / nome_arquivo)
    storage.save_parquet(df, caminho)
    logger.info("Salvo no Silver: %s (%d registros, %d colunas)", nome_arquivo, len(df), len(df.columns))
    return caminho


def _extrair_e_filtrar(
    zip_path: Path,
    dataset: str,
    granularidade: str,
    storage: StorageBackend,
) -> str:
    """
    Extrai o CSV do ZIP, filtra pelas UFs alvo e salva como Parquet no Silver.

    Args:
        zip_path:      Caminho do ZIP no Bronze.
        dataset:       Nome do dataset (ex: 'basico').
        granularidade: 'municipio', 'setor' ou 'bairro'.
        storage:       Backend de armazenamento.

    Returns:
        Caminho do Parquet salvo no Silver.
    """
    logger.info("Extraindo: %s", zip_path.name)

    df = _ler_csv_do_zip(zip_path)
    logger.info("Registros (Brasil): %d", len(df))

    df = _filtrar_uf(df, dataset, granularidade)

    if df.empty:
        logger.warning(
            "Nenhum registro das UFs=%s encontrado em %s (%s)!",
            FILTRO_UF,
            dataset,
            granularidade,
        )

    return _salvar_silver(df, dataset, granularidade, storage)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def baixar_dataset(
    dataset: str,
    granularidade: str,
    storage: Optional[StorageBackend] = None,
) -> str:
    """
    Baixa um dataset do IBGE e salva no Silver como Parquet filtrado por UF.

    Fluxo:
        1. Resolve o nome correto do ZIP no FTP.
        2. Verifica cache no Bronze (evita re-download).
        3. Baixa via FTP com retry e backoff.
        4. Extrai CSV, filtra UF, salva Parquet no Silver.

    Args:
        dataset:       Um dos datasets definidos em config/ibge_censo.yml.
        granularidade: 'municipio', 'setor' ou 'bairro'.
        storage:       Backend de armazenamento (usa padrão se None).

    Returns:
        Caminho do Parquet salvo no Silver.

    Raises:
        ValueError:   Se dataset ou granularidade forem inválidos.
        RuntimeError: Se o download falhar após todas as tentativas.
    """
    if dataset not in DATASETS:
        raise ValueError(f"Dataset inválido: '{dataset}'. Opções: {DATASETS}")
    if granularidade not in GRANULARIDADES:
        raise ValueError(f"Granularidade inválida: '{granularidade}'. Opções: {list(GRANULARIDADES)}")

    storage = storage or get_storage_backend()
    gran_cfg = GRANULARIDADES[granularidade]

    zip_filename = _resolver_nome_zip(gran_cfg.prefixo_arquivo, dataset)
    bronze_path = BRONZE_DIR / zip_filename
    bronze_path.parent.mkdir(parents=True, exist_ok=True)

    if bronze_path.exists():
        tamanho_mb = bronze_path.stat().st_size / (1024 * 1024)
        logger.info("Cache hit — Bronze: %s (%.1f MB)", bronze_path.name, tamanho_mb)
    else:
        caminho_ftp = f"{FTP.base_dir}/{gran_cfg.ftp_dir}/{zip_filename}"
        _baixar_com_retry(caminho_ftp, bronze_path)

    return _extrair_e_filtrar(bronze_path, dataset, granularidade, storage)


def baixar_dicionario(storage: Optional[StorageBackend] = None) -> str:
    """
    Baixa o dicionário oficial de variáveis do IBGE Censo 2022 e salva no Bronze.

    O dicionário mapeia cada código de variável (ex: V00901) para sua descrição
    completa. É usado durante a EDA para confirmar o mapeamento em indicadores.py.

    Returns:
        Caminho do Parquet salvo no Bronze.
    """
    storage = storage or get_storage_backend()

    dic_cfg = _cfg["dicionario"]
    output_path = str(BRONZE_DIR / dic_cfg["bronze_output"])

    if Path(output_path).exists():
        logger.info("Cache hit — dicionário já existe: %s", output_path)
        return output_path

    xlsx_filename = dic_cfg["filename"]
    caminho_ftp = f"{FTP.base_dir}/{xlsx_filename}"

    logger.info("Baixando dicionário de dados: %s", xlsx_filename)

    buf = io.BytesIO(_baixar_bytes_ftp(caminho_ftp))
    buf.seek(0)
    df = pd.read_excel(buf, sheet_name=dic_cfg["sheet_name"])

    storage.save_parquet(df, output_path)
    logger.info("Dicionário salvo: %s (%d variáveis)", output_path, len(df))
    return output_path


def run(
    granularidades: Optional[List[str]] = None,
    datasets: Optional[List[str]] = None,
    storage: Optional[StorageBackend] = None,
) -> Dict[str, List[str]]:
    """
    Executa o extract completo: baixa todos os datasets para todas as granularidades.

    Parâmetros opcionais permitem rodar apenas um subconjunto — útil para
    desenvolvimento sem precisar baixar tudo.

    Args:
        granularidades: Granularidades a processar. Padrão: todas do config.
        datasets:       Datasets a baixar. Padrão: todos do config.
        storage:        Backend de armazenamento (usa padrão se None).

    Returns:
        Dict com listas de caminhos Parquet por granularidade.
        Ex: {'municipio': ['data/silver/ibge_censo2022_municipio_basico_nordeste.parquet', ...]}

    Exemplo de uso parcial:
        >>> run(granularidades=['municipio'], datasets=['basico'])
    """
    granularidades = granularidades or list(GRANULARIDADES.keys())
    datasets = datasets or DATASETS
    storage = storage or get_storage_backend()

    total_esperado = len(granularidades) * len(datasets)
    logger.info("=" * 60)
    logger.info("EXTRACT — IBGE CENSO 2022")
    logger.info("Granularidades : %s", granularidades)
    logger.info("Datasets       : %s", datasets)
    logger.info("Total esperado : %d arquivos", total_esperado)
    logger.info("=" * 60)

    resultados: Dict[str, List[str]] = {g: [] for g in granularidades}
    erros: List[str] = []

    for granularidade in granularidades:
        logger.info("Granularidade: %s", granularidade.upper())
        for dataset in datasets:
            try:
                path = baixar_dataset(dataset, granularidade, storage)
                resultados[granularidade].append(path)
            except Exception as exc:
                msg = f"{granularidade}/{dataset}: {exc}"
                logger.error("ERRO — %s", msg)
                erros.append(msg)

    _logar_resumo(resultados, erros, total_esperado)
    return resultados


def _logar_resumo(
    resultados: Dict[str, List[str]],
    erros: List[str],
    total_esperado: int,
) -> None:
    total_ok = sum(len(v) for v in resultados.values())
    logger.info("=" * 60)
    logger.info("EXTRACT CONCLUÍDO — %d/%d arquivos gerados", total_ok, total_esperado)
    for gran, paths in resultados.items():
        logger.info("  %-12s %d arquivos", gran, len(paths))
    if erros:
        logger.warning("Erros (%d):", len(erros))
        for erro in erros:
            logger.warning("  - %s", erro)
    logger.info("=" * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )
    run()

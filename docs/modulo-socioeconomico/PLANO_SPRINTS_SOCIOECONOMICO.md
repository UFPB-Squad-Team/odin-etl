# Plano de Sprints — Módulo Socioeconômico IBGE 2022

> **Equipe:** 3 pessoas  
> **Prazo:** 2-3 sprints (otimista: 2 sprints)  
> **Objetivo:** Agregar indicadores socioeconômicos do IBGE Censo 2022 nas granularidades setor/bairro/município

---

## Estratégia Geral

**Paralelização máxima:** As 3 granularidades (setor, bairro, município) compartilham a mesma lógica de cálculo de indicadores. Podemos dividir o trabalho por granularidade desde o início.

**Reutilização de código:** Criar funções compartilhadas para cálculo de indicadores — cada granularidade apenas muda a fonte de dados (arquivo CSV diferente).

**Priorização:** Implementar primeiro os 10 indicadores de Prioridade 1 (essenciais), depois expandir se houver tempo.

---

## Sprint 1 — Fundação e Município (5 dias úteis)

**Objetivo:** Infraestrutura base + pipeline de município completo (mais simples)

### 👤 Pessoa 1 — Infraestrutura e Extract (2 dias)

**Task 1.1 — Setup do módulo socioeconômico** (4h)

**📋 Objetivo:** Criar toda a estrutura de pastas e arquivos base do novo módulo, seguindo os padrões do projeto ODIN-ETL.

**📁 Arquivos a Criar:**

```
src/jobs/socioeconomico_jobs/
├── __init__.py
├── main.py
└── ibge_censo_pipeline/
    ├── __init__.py
    ├── main.py
    └── etl/
        ├── __init__.py
        ├── extract.py
        ├── municipio/
        │   ├── __init__.py
        │   ├── transform.py
        │   └── load.py
        ├── setor/
        │   ├── __init__.py
        │   ├── transform.py
        │   └── load.py
        └── bairro/
            ├── __init__.py
            ├── transform.py
            └── load.py
```

**📝 Implementação Passo-a-Passo:**

1. **Criar estrutura de diretórios:**

```bash
mkdir -p src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl
```

2. **Criar `src/jobs/socioeconomico_jobs/__init__.py`:**

```python
"""
Módulo Socioeconômico — ODIN-ETL

Agrega indicadores socioeconômicos do IBGE Censo 2022 por setor censitário,
bairro e município da Paraíba.
"""
```

3. **Criar `src/jobs/socioeconomico_jobs/main.py`:**

```python
"""
Orquestrador principal do módulo socioeconômico.
"""
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
        logger.info("✅ Módulo socioeconômico concluído com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro no módulo socioeconômico: {e}")
        raise


if __name__ == "__main__":
    run()
```

4. **Criar `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/__init__.py`:**

```python
"""
Pipeline IBGE Censo 2022 — Indicadores Socioeconômicos
"""
```

5. **Criar `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/main.py`:**

```python
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
    # from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import transform_municipio
    # from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import load_municipio

    logger.info("Pipeline IBGE Censo 2022 concluído.")


if __name__ == "__main__":
    run()
```

6. **Criar `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/__init__.py`:**

```python
"""
Módulo ETL do pipeline IBGE Censo 2022.
"""
```

7. **Criar arquivos ETL vazios (serão implementados nas próximas tasks):**

```bash
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/extract.py
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/transform_municipio.py
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/transform_setor.py
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/transform_bairro.py
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/load_municipio.py
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/load_setor.py
touch src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/load_bairro.py
```

8. **Adicionar ao `Makefile` (no final do arquivo):**

```makefile
# ============================================================
# Módulo Socioeconômico
# ============================================================

.PHONY: run-socioeconomico-extract
run-socioeconomico-extract:
	@echo "🔽 Executando Extract — IBGE Censo 2022..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.extract

.PHONY: run-socioeconomico-transform-municipio
run-socioeconomico-transform-municipio:
	@echo "🔄 Executando Transform — Município..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.transform_municipio

.PHONY: run-socioeconomico-load-municipio
run-socioeconomico-load-municipio:
	@echo "💾 Executando Load — Município..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.load_municipio

.PHONY: run-socioeconomico-transform-setor
run-socioeconomico-transform-setor:
	@echo "🔄 Executando Transform — Setor..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.transform_setor

.PHONY: run-socioeconomico-load-setor
run-socioeconomico-load-setor:
	@echo "💾 Executando Load — Setor..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.load_setor

.PHONY: run-socioeconomico-transform-bairro
run-socioeconomico-transform-bairro:
	@echo "🔄 Executando Transform — Bairro..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.transform_bairro

.PHONY: run-socioeconomico-load-bairro
run-socioeconomico-load-bairro:
	@echo "💾 Executando Load — Bairro..."
	poetry run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.load_bairro

.PHONY: run-socioeconomico
run-socioeconomico:
	@echo "🚀 Executando pipeline socioeconômico completo..."
	poetry run python -m src.jobs.socioeconomico_jobs.main
```

**✅ Validação:**

```bash
# 1. Verificar estrutura de pastas
ls -R src/jobs/socioeconomico_jobs/

# 2. Testar imports
poetry run python -c "from src.jobs.socioeconomico_jobs import main; print('✅ Import OK')"

# 3. Testar Makefile
make run-socioeconomico

# Deve executar sem erros (ainda não faz nada, mas não deve quebrar)
```

**🎯 Resultado Esperado:**

- Estrutura de pastas criada
- Todos os `__init__.py` no lugar
- Makefile com 8 novos targets funcionando
- Comando `make run-socioeconomico` executa sem erros

**⚠️ Problemas Comuns:**

- **Erro de import:** Verifique se todos os `__init__.py` foram criados
- **Makefile não reconhece target:** Verifique indentação (deve usar TAB, não espaços)
- **ModuleNotFoundError:** Execute comandos a partir da raiz do projeto

**Task 1.2 — Extract: Download dos ZIPs do IBGE** (4h)

**📋 Objetivo:** Baixar dados do FTP do IBGE, extrair CSVs, filtrar apenas PB e salvar no Silver como Parquet.

**📚 Referência:** Veja `src/jobs/education_jobs/censo_pipeline/etl/extract.py` para entender o padrão de extract do projeto.

**📁 Arquivo a Implementar:** `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/extract.py`

**🔑 Conceitos Importantes:**

- **Por que usar funções e não classes?** Extract é uma operação stateless (não precisa guardar estado entre chamadas). Funções são mais simples e diretas.
- **Por que Parquet?** Mais eficiente que CSV (compressão, tipos de dados, leitura parcial).
- **Por que filtrar na extract?** Reduz tamanho dos arquivos no Silver (só guardamos PB, não Brasil inteiro).

**📝 Implementação Completa:**

```python
"""
Extract — IBGE Censo 2022

Baixa agregados por setor/bairro/município do FTP do IBGE,
filtra apenas Paraíba (CD_UF == 25) e salva no Silver como Parquet.
"""
import logging
import time
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)

# URLs base do FTP IBGE (atualizar se mudarem)
FTP_BASE_URL = "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Previa_da_Amostra/Agregados_por_Setores_Censitarios/csv"

# Datasets a baixar (7 arquivos temáticos)
DATASETS = [
    "basico",
    "demografia",
    "cor_ou_raca",
    "caracteristicas_domicilio2",
    "caracteristicas_domicilio3",
    "alfabetizacao",
    "obitos",
]

# Código IBGE da Paraíba
CD_UF_PB = "25"


def _download_com_retry(url: str, destino: Path, max_tentativas: int = 3) -> None:
    """
    Baixa arquivo com retry e backoff exponencial.

    Args:
        url: URL do arquivo
        destino: Caminho local para salvar
        max_tentativas: Número máximo de tentativas

    Raises:
        Exception: Se todas as tentativas falharem
    """
    for tentativa in range(1, max_tentativas + 1):
        try:
            logger.info(f"Tentativa {tentativa}/{max_tentativas}: Baixando {url}")
            inicio = time.time()
            urlretrieve(url, destino)
            duracao = time.time() - inicio
            tamanho_mb = destino.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Download concluído: {tamanho_mb:.2f} MB em {duracao:.1f}s")
            return
        except Exception as e:
            logger.warning(f"❌ Tentativa {tentativa} falhou: {e}")
            if tentativa < max_tentativas:
                espera = 2 ** tentativa  # Backoff exponencial: 2s, 4s, 8s
                logger.info(f"Aguardando {espera}s antes de tentar novamente...")
                time.sleep(espera)
            else:
                raise Exception(f"Falha após {max_tentativas} tentativas: {e}")


def _extrair_e_filtrar_csv(
    zip_path: Path,
    dataset_name: str,
    granularidade: str,
    storage: StorageBackend,
) -> str:
    """
    Extrai CSV do ZIP, filtra apenas PB e salva como Parquet no Silver.

    Args:
        zip_path: Caminho do arquivo ZIP baixado
        dataset_name: Nome do dataset (ex: 'basico', 'demografia')
        granularidade: 'setor', 'bairro' ou 'municipio'
        storage: Backend de armazenamento

    Returns:
        Caminho do arquivo Parquet salvo no Silver
    """
    logger.info(f"Extraindo e filtrando {dataset_name} ({granularidade})...")

    with zipfile.ZipFile(zip_path, 'r') as z:
        # Encontrar o CSV dentro do ZIP (pode ter nome diferente)
        csv_files = [f for f in z.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise FileNotFoundError(f"Nenhum CSV encontrado em {zip_path}")

        csv_name = csv_files[0]
        logger.info(f"Lendo CSV: {csv_name}")

        with z.open(csv_name) as csv_file:
            # Ler CSV com encoding latin-1 (padrão IBGE)
            df = pd.read_csv(csv_file, encoding='latin-1', sep=';', dtype=str)

            total_antes = len(df)
            logger.info(f"Total de registros (Brasil): {total_antes}")

            # Filtrar apenas Paraíba
            if 'CD_UF' in df.columns:
                df = df[df['CD_UF'] == CD_UF_PB].copy()
            else:
                logger.warning(f"Coluna CD_UF não encontrada em {dataset_name}. Assumindo que já está filtrado.")

            total_depois = len(df)
            logger.info(f"Total de registros (PB): {total_depois}")

            if total_depois == 0:
                logger.warning(f"⚠️ Nenhum registro da PB encontrado em {dataset_name}!")

            # Salvar no Silver como Parquet
            output_filename = f"ibge_censo2022_{granularidade}_{dataset_name}_pb.parquet"
            output_path = f"data/silver/{output_filename}"
            storage.write_parquet(df, output_path)

            logger.info(f"✅ Salvo: {output_path} ({len(df)} registros)")
            return output_path


def download_ibge_dataset(
    dataset_name: str,
    granularidade: str,
    storage: StorageBackend = None,
) -> str:
    """
    Baixa um dataset do IBGE para uma granularidade específica.

    Args:
        dataset_name: Nome do dataset ('basico', 'demografia', etc.)
        granularidade: 'setor', 'bairro' ou 'municipio'
        storage: Backend de armazenamento (opcional)

    Returns:
        Caminho do arquivo Parquet salvo no Silver

    Example:
        >>> download_ibge_dataset('basico', 'municipio')
        'data/silver/ibge_censo2022_municipio_basico_pb.parquet'
    """
    storage = storage or get_storage_backend()

    # Mapear granularidade para nome no FTP IBGE
    granularidade_map = {
        'setor': 'Setores_Censitarios',
        'bairro': 'Bairros',
        'municipio': 'Municipios',
    }

    if granularidade not in granularidade_map:
        raise ValueError(f"Granularidade inválida: {granularidade}. Use: setor, bairro ou municipio")

    if dataset_name not in DATASETS:
        raise ValueError(f"Dataset inválido: {dataset_name}. Use um de: {DATASETS}")

    # Construir URL (ajustar conforme estrutura real do FTP)
    # Exemplo: https://ftp.ibge.gov.br/.../Agregados_por_Municipios_basico_BR.zip
    ftp_granularidade = granularidade_map[granularidade]
    zip_filename = f"Agregados_por_{ftp_granularidade}_{dataset_name}_BR.zip"
    url = f"{FTP_BASE_URL}/{zip_filename}"

    # Baixar para Bronze
    bronze_path = Path("data/bronze") / zip_filename
    bronze_path.parent.mkdir(parents=True, exist_ok=True)

    # Verificar se já existe (evitar re-download)
    if bronze_path.exists():
        logger.info(f"Arquivo já existe no Bronze: {bronze_path}. Pulando download.")
    else:
        _download_com_retry(url, bronze_path)

    # Extrair, filtrar e salvar no Silver
    return _extrair_e_filtrar_csv(bronze_path, dataset_name, granularidade, storage)


def run(storage: StorageBackend = None) -> dict:
    """
    Executa extract completo: baixa todos os datasets para todas as granularidades.

    Returns:
        Dict com caminhos dos arquivos salvos por granularidade
    """
    storage = storage or get_storage_backend()

    logger.info("=" * 60)
    logger.info("INICIANDO EXTRACT — IBGE CENSO 2022")
    logger.info("=" * 60)

    resultados = {
        'municipio': [],
        'setor': [],
        'bairro': [],
    }

    for granularidade in ['municipio', 'setor', 'bairro']:
        logger.info(f"\n📊 Processando granularidade: {granularidade.upper()}")
        for dataset in DATASETS:
            try:
                path = download_ibge_dataset(dataset, granularidade, storage)
                resultados[granularidade].append(path)
            except Exception as e:
                logger.error(f"❌ Erro ao processar {dataset} ({granularidade}): {e}")
                # Continuar com próximo dataset mesmo se um falhar

    logger.info("\n" + "=" * 60)
    logger.info("EXTRACT CONCLUÍDO")
    logger.info(f"Município: {len(resultados['municipio'])} arquivos")
    logger.info(f"Setor: {len(resultados['setor'])} arquivos")
    logger.info(f"Bairro: {len(resultados['bairro'])} arquivos")
    logger.info("=" * 60)

    return resultados


if __name__ == "__main__":
    run()
```

**✅ Validação:**

```bash
# 1. Testar download de um dataset
poetry run python -c "
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.extract import download_ibge_dataset
path = download_ibge_dataset('basico', 'municipio')
print(f'✅ Arquivo salvo: {path}')
"

# 2. Verificar arquivo no Silver
ls -lh data/silver/ibge_censo2022_municipio_basico_pb.parquet

# 3. Inspecionar dados
poetry run python -c "
import pandas as pd
df = pd.read_parquet('data/silver/ibge_censo2022_municipio_basico_pb.parquet')
print(f'Registros: {len(df)}')
print(f'Colunas: {list(df.columns)}')
print(df.head())
"

# 4. Executar extract completo
make run-socioeconomico-extract
```

**🎯 Resultado Esperado:**

- 21 arquivos Parquet no Silver (7 datasets × 3 granularidades)
- Cada arquivo contém apenas dados da PB
- Município: ~225 registros por dataset
- Setor: ~2.243 registros por dataset
- Bairro: ~194 registros por dataset

**⚠️ Problemas Comuns:**

- **URL não encontrada (404):** Verifique estrutura do FTP IBGE (pode ter mudado). Acesse manualmente: `https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/`
- **Encoding error:** CSVs do IBGE usam `latin-1`, não `utf-8`
- **Coluna CD_UF não existe:** Alguns datasets podem usar nome diferente. Ajuste o filtro.
- **ZIP vazio ou corrompido:** Delete o arquivo no Bronze e tente novamente

**Entrega:** Arquivos Parquet no Silver prontos para transform

---

### 👤 Pessoa 2 — Funções de Cálculo de Indicadores (2 dias)

**Task 1.3 — Biblioteca de indicadores compartilhada** (8h)

**📋 Objetivo:** Criar funções reutilizáveis para calcular os 10 indicadores prioritários a partir dos dados brutos do IBGE.

**📚 Referência:** Veja `src/common/geo_utils.py` função `calcular_indicadores()` para entender o padrão de cálculo de métricas do projeto.

**📁 Arquivo a Criar:** `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/indicadores.py`

**🔑 Conceitos Importantes:**

- **Por que funções separadas?** Cada função calcula um tema (população, saneamento, etc.). Isso facilita testes e manutenção.
- **Por que retornar DataFrame?** Permite fazer merge fácil depois. Cada função retorna `[chave_geografica, indicador1, indicador2, ...]`.
- **Como tratar divisão por zero?** Use `pd.Series.replace([np.inf, -np.inf], None)` ou verifique denominador antes.

**📊 Mapeamento de Variáveis IBGE:**

Consulte `docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.md` para ver as fórmulas completas e códigos das variáveis.

**📝 Implementação Completa:**

```python
"""
Biblioteca de Cálculo de Indicadores Socioeconômicos — IBGE Censo 2022

Funções reutilizáveis para calcular indicadores derivados a partir dos
agregados brutos do IBGE. Cada função recebe DataFrames com variáveis
brutas e retorna DataFrame com indicadores calculados.

Referência: docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.md
"""
import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _identificar_chave_geografica(df: pd.DataFrame) -> str:
    """
    Identifica qual coluna usar como chave geográfica (setor, bairro ou município).

    Args:
        df: DataFrame com dados do IBGE

    Returns:
        Nome da coluna chave ('CD_SETOR', 'CD_BAIRRO' ou 'CD_MUN')
    """
    if 'CD_SETOR' in df.columns:
        return 'CD_SETOR'
    elif 'CD_BAIRRO' in df.columns:
        return 'CD_BAIRRO'
    elif 'CD_MUN' in df.columns:
        return 'CD_MUN'
    else:
        raise ValueError("Nenhuma chave geográfica encontrada (CD_SETOR, CD_BAIRRO ou CD_MUN)")


def _converter_para_numerico(df: pd.DataFrame, colunas: List[str]) -> pd.DataFrame:
    """
    Converte colunas para numérico, tratando valores inválidos como NaN.

    Args:
        df: DataFrame
        colunas: Lista de nomes de colunas

    Returns:
        DataFrame com colunas convertidas
    """
    df = df.copy()
    for col in colunas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _calcular_percentual_seguro(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
    """
    Calcula percentual tratando divisão por zero.

    Args:
        numerador: Série com valores do numerador
        denominador: Série com valores do denominador

    Returns:
        Série com percentuais (0-100), None onde denominador é zero
    """
    resultado = (numerador / denominador * 100).round(1)
    resultado = resultado.replace([np.inf, -np.inf], None)
    resultado = resultado.where(denominador > 0, None)
    return resultado


def calcular_populacao(df_basico: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de população e domicílios.

    Indicadores:
    - total_populacao: População total (V0001)
    - total_domicilios: Total de domicílios (V0002)
    - media_moradores_por_domicilio: Média de moradores por domicílio (V0005)

    Args:
        df_basico: DataFrame com dados do arquivo 'basico'

    Returns:
        DataFrame com colunas [chave_geografica, total_populacao, total_domicilios, media_moradores_por_domicilio]
    """
    chave = _identificar_chave_geografica(df_basico)

    df = _converter_para_numerico(df_basico, ['V0001', 'V0002', 'V0005'])

    resultado = df[[chave]].copy()
    resultado['total_populacao'] = df['V0001'].astype('Int64')  # Int64 suporta NA
    resultado['total_domicilios'] = df['V0002'].astype('Int64')
    resultado['media_moradores_por_domicilio'] = df['V0005'].round(1)

    logger.info(f"✅ Indicadores de população calculados: {len(resultado)} registros")
    return resultado


def calcular_estrutura_etaria(df_demografia: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de estrutura etária.

    Indicadores:
    - pct_criancas_0_9: % de crianças de 0 a 9 anos
    - pct_idosos_60_mais: % de idosos com 60 anos ou mais

    Fórmulas:
    - pop_0_4 = V01009 (masc) + V01027 (fem)
    - pop_5_9 = V01010 (masc) + V01028 (fem)
    - pop_60+ = V01021..V01026 (masc) + V01039..V01041 (fem)
    - total = V01006

    Args:
        df_demografia: DataFrame com dados do arquivo 'demografia'

    Returns:
        DataFrame com colunas [chave_geografica, pct_criancas_0_9, pct_idosos_60_mais]
    """
    chave = _identificar_chave_geografica(df_demografia)

    # Colunas de faixas etárias (masculino + feminino)
    cols_0_4 = ['V01009', 'V01027']
    cols_5_9 = ['V01010', 'V01028']
    cols_60_mais_masc = ['V01021', 'V01022', 'V01023', 'V01024', 'V01025', 'V01026']
    cols_60_mais_fem = ['V01039', 'V01040', 'V01041']

    todas_cols = ['V01006'] + cols_0_4 + cols_5_9 + cols_60_mais_masc + cols_60_mais_fem
    df = _converter_para_numerico(df_demografia, todas_cols)

    resultado = df[[chave]].copy()

    # Calcular populações por faixa
    pop_0_4 = df[cols_0_4].sum(axis=1)
    pop_5_9 = df[cols_5_9].sum(axis=1)
    pop_0_9 = pop_0_4 + pop_5_9

    pop_60_mais = df[cols_60_mais_masc + cols_60_mais_fem].sum(axis=1)

    total_pop = df['V01006']

    # Calcular percentuais
    resultado['pct_criancas_0_9'] = _calcular_percentual_seguro(pop_0_9, total_pop)
    resultado['pct_idosos_60_mais'] = _calcular_percentual_seguro(pop_60_mais, total_pop)

    logger.info(f"✅ Indicadores de estrutura etária calculados: {len(resultado)} registros")
    return resultado


def calcular_raca(df_cor_raca: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de cor/raça.

    Indicadores:
    - pct_preta_parda: % de população preta + parda

    Fórmulas:
    - preta = V01318
    - parda = V01320
    - total = V01317 + V01318 + V01319 + V01320 + V01321 (branca + preta + amarela + parda + indígena)

    Args:
        df_cor_raca: DataFrame com dados do arquivo 'cor_ou_raca'

    Returns:
        DataFrame com colunas [chave_geografica, pct_preta_parda]
    """
    chave = _identificar_chave_geografica(df_cor_raca)

    cols = ['V01317', 'V01318', 'V01319', 'V01320', 'V01321']
    df = _converter_para_numerico(df_cor_raca, cols)

    resultado = df[[chave]].copy()

    preta_parda = df['V01318'] + df['V01320']
    total = df[cols].sum(axis=1)

    resultado['pct_preta_parda'] = _calcular_percentual_seguro(preta_parda, total)

    logger.info(f"✅ Indicadores de raça calculados: {len(resultado)} registros")
    return resultado


def calcular_saneamento_agua(df_domicilio2: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de abastecimento de água.

    Indicadores:
    - pct_agua_rede_geral: % de domicílios com água da rede geral

    Fórmulas:
    - agua_rede = V00111
    - total_dom = V00001

    Args:
        df_domicilio2: DataFrame com dados do arquivo 'caracteristicas_domicilio2'

    Returns:
        DataFrame com colunas [chave_geografica, pct_agua_rede_geral]
    """
    chave = _identificar_chave_geografica(df_domicilio2)

    df = _converter_para_numerico(df_domicilio2, ['V00111', 'V00001'])

    resultado = df[[chave]].copy()
    resultado['pct_agua_rede_geral'] = _calcular_percentual_seguro(df['V00111'], df['V00001'])

    logger.info(f"✅ Indicadores de água calculados: {len(resultado)} registros")
    return resultado


def calcular_saneamento_esgoto(df_domicilio2: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de esgotamento sanitário.

    Indicadores:
    - pct_esgoto_rede_geral: % de domicílios com esgoto na rede geral

    Fórmulas:
    - esgoto_rede = V00309
    - total_dom = V00001

    Args:
        df_domicilio2: DataFrame com dados do arquivo 'caracteristicas_domicilio2'

    Returns:
        DataFrame com colunas [chave_geografica, pct_esgoto_rede_geral]
    """
    chave = _identificar_chave_geografica(df_domicilio2)

    df = _converter_para_numerico(df_domicilio2, ['V00309', 'V00001'])

    resultado = df[[chave]].copy()
    resultado['pct_esgoto_rede_geral'] = _calcular_percentual_seguro(df['V00309'], df['V00001'])

    logger.info(f"✅ Indicadores de esgoto calculados: {len(resultado)} registros")
    return resultado


def calcular_saneamento_lixo(df_domicilio3: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de coleta de lixo.

    Indicadores:
    - pct_lixo_coletado: % de domicílios com lixo coletado (serviço + caçamba)

    Fórmulas:
    - lixo_coletado = V00397 (serviço) + V00398 (caçamba)
    - total_dom = V00001

    Args:
        df_domicilio3: DataFrame com dados do arquivo 'caracteristicas_domicilio3'

    Returns:
        DataFrame com colunas [chave_geografica, pct_lixo_coletado]
    """
    chave = _identificar_chave_geografica(df_domicilio3)

    df = _converter_para_numerico(df_domicilio3, ['V00397', 'V00398', 'V00001'])

    resultado = df[[chave]].copy()

    lixo_coletado = df['V00397'] + df['V00398']
    resultado['pct_lixo_coletado'] = _calcular_percentual_seguro(lixo_coletado, df['V00001'])

    logger.info(f"✅ Indicadores de lixo calculados: {len(resultado)} registros")
    return resultado


def calcular_alfabetizacao(df_alfabetizacao: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de alfabetização.

    Indicadores:
    - taxa_analfabetismo_15_mais: % de pessoas não alfabetizadas com 15 anos ou mais

    Nota: O arquivo 'alfabetizacao' tem estrutura complexa. Esta é uma implementação
    simplificada. Ajustar conforme estrutura real do CSV.

    Args:
        df_alfabetizacao: DataFrame com dados do arquivo 'alfabetizacao'

    Returns:
        DataFrame com colunas [chave_geografica, taxa_analfabetismo_15_mais]
    """
    chave = _identificar_chave_geografica(df_alfabetizacao)

    # TODO: Ajustar colunas conforme dicionário real do IBGE
    # Exemplo simplificado (verificar nomes reais das variáveis)
    resultado = df_alfabetizacao[[chave]].copy()
    resultado['taxa_analfabetismo_15_mais'] = None  # Placeholder

    logger.warning("⚠️ Cálculo de alfabetização não implementado. Ajustar variáveis conforme dicionário IBGE.")
    return resultado


def calcular_familia(df_parentesco: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula indicadores de estrutura familiar.

    Indicadores:
    - pct_responsavel_feminino: % de domicílios com responsável feminino

    Nota: O arquivo 'parentesco' não está nos 7 datasets básicos. Esta função
    é um placeholder para Sprint 3.

    Args:
        df_parentesco: DataFrame com dados do arquivo 'parentesco'

    Returns:
        DataFrame com colunas [chave_geografica, pct_responsavel_feminino]
    """
    chave = _identificar_chave_geografica(df_parentesco)

    resultado = df_parentesco[[chave]].copy()
    resultado['pct_responsavel_feminino'] = None  # Placeholder

    logger.warning("⚠️ Cálculo de família não implementado. Dataset 'parentesco' não está nos 7 básicos.")
    return resultado
```

**✅ Validação:**

```bash
# 1. Testar função de população
poetry run python -c "
import pandas as pd
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.indicadores import calcular_populacao

# Carregar dados reais
df_basico = pd.read_parquet('data/silver/ibge_censo2022_municipio_basico_pb.parquet')
resultado = calcular_populacao(df_basico)

print(f'Registros: {len(resultado)}')
print(resultado.head())
print(f'População total PB: {resultado[\"total_populacao\"].sum():,}')
"

# 2. Testar todas as funções
poetry run python -c "
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline import indicadores
import pandas as pd

# Carregar dados
df_basico = pd.read_parquet('data/silver/ibge_censo2022_municipio_basico_pb.parquet')
df_demografia = pd.read_parquet('data/silver/ibge_censo2022_municipio_demografia_pb.parquet')
df_cor_raca = pd.read_parquet('data/silver/ibge_censo2022_municipio_cor_ou_raca_pb.parquet')
df_domicilio2 = pd.read_parquet('data/silver/ibge_censo2022_municipio_caracteristicas_domicilio2_pb.parquet')
df_domicilio3 = pd.read_parquet('data/silver/ibge_censo2022_municipio_caracteristicas_domicilio3_pb.parquet')

# Testar cada função
pop = indicadores.calcular_populacao(df_basico)
etaria = indicadores.calcular_estrutura_etaria(df_demografia)
raca = indicadores.calcular_raca(df_cor_raca)
agua = indicadores.calcular_saneamento_agua(df_domicilio2)
esgoto = indicadores.calcular_saneamento_esgoto(df_domicilio2)
lixo = indicadores.calcular_saneamento_lixo(df_domicilio3)

print('✅ Todas as funções executaram sem erros')
"
```

**🎯 Resultado Esperado:**

- Cada função retorna DataFrame com chave geográfica + indicadores
- Percentuais entre 0 e 100
- Nenhum valor infinito (divisão por zero tratada)
- População total da PB ~4 milhões (validar com dados oficiais)

**⚠️ Problemas Comuns:**

- **KeyError em variável:** Nome da coluna mudou. Consulte dicionário IBGE atualizado.
- **Valores infinitos:** Divisão por zero não tratada. Use `_calcular_percentual_seguro()`.
- **Tipos errados:** Use `_converter_para_numerico()` antes de calcular.
- **Alfabetização/Família retornam None:** Esses datasets têm estrutura complexa. Implementar na Sprint 3.

**Entrega:** Biblioteca de funções testável e reutilizável

---

### 👤 Pessoa 3 — Transform e Load Município (3 dias)

**Task 1.4 — Transform município** (4h)

**📋 Objetivo:** Ler os Parquets do Silver, calcular todos os indicadores usando a biblioteca, fazer merge e salvar no Gold.

**📚 Referência:** Veja `src/jobs/education_jobs/municipio_pipeline/etl/transform.py` para entender o padrão de transform do projeto.

**📁 Arquivo a Implementar:** `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/municipio/transform.py`

**🔑 Conceitos Importantes:**

- **Por que fazer merge?** Cada função de indicador retorna um DataFrame. Precisamos juntar todos pela chave geográfica.
- **Como fazer merge?** Use `pd.merge()` com `how='outer'` para não perder municípios que faltam em algum dataset.
- **O que fazer com NaN?** Deixe como está — indica dado não disponível. A API pode decidir como tratar.

**📝 Implementação Completa:**

```python
"""
Transform — Município (IBGE Censo 2022)

Calcula indicadores socioeconômicos agregados por município da Paraíba.
"""
import logging
from pathlib import Path

import pandas as pd

from src.common.storage import StorageBackend, get_storage_backend
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline import indicadores

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage: StorageBackend = None) -> pd.DataFrame:
    """
    Calcula indicadores socioeconômicos por município.

    Returns:
        DataFrame com uma linha por município e colunas:
            CD_MUN, total_populacao, total_domicilios, media_moradores_por_domicilio,
            pct_criancas_0_9, pct_idosos_60_mais, pct_preta_parda,
            pct_agua_rede_geral, pct_esgoto_rede_geral, pct_lixo_coletado,
            taxa_analfabetismo_15_mais, pct_responsavel_feminino
    """
    storage = storage or get_storage_backend()

    logger.info("=" * 60)
    logger.info("TRANSFORM — MUNICÍPIO")
    logger.info("=" * 60)

    # 1. Carregar dados do Silver
    logger.info("Carregando dados do Silver...")

    silver_path = Path("data/silver")

    df_basico = storage.read_parquet(str(silver_path / "ibge_censo2022_municipio_basico_pb.parquet"))
    df_demografia = storage.read_parquet(str(silver_path / "ibge_censo2022_municipio_demografia_pb.parquet"))
    df_cor_raca = storage.read_parquet(str(silver_path / "ibge_censo2022_municipio_cor_ou_raca_pb.parquet"))
    df_domicilio2 = storage.read_parquet(str(silver_path / "ibge_censo2022_municipio_caracteristicas_domicilio2_pb.parquet"))
    df_domicilio3 = storage.read_parquet(str(silver_path / "ibge_censo2022_municipio_caracteristicas_domicilio3_pb.parquet"))
    df_alfabetizacao = storage.read_parquet(str(silver_path / "ibge_censo2022_municipio_alfabetizacao_pb.parquet"))

    logger.info(f"Municípios no basico: {len(df_basico)}")

    # 2. Calcular indicadores usando a biblioteca
    logger.info("Calculando indicadores...")

    ind_populacao = indicadores.calcular_populacao(df_basico)
    ind_etaria = indicadores.calcular_estrutura_etaria(df_demografia)
    ind_raca = indicadores.calcular_raca(df_cor_raca)
    ind_agua = indicadores.calcular_saneamento_agua(df_domicilio2)
    ind_esgoto = indicadores.calcular_saneamento_esgoto(df_domicilio2)
    ind_lixo = indicadores.calcular_saneamento_lixo(df_domicilio3)
    # ind_alfabetizacao = indicadores.calcular_alfabetizacao(df_alfabetizacao)  # TODO: implementar
    # ind_familia = indicadores.calcular_familia(df_parentesco)  # TODO: dataset não disponível

    # 3. Fazer merge de todos os indicadores
    logger.info("Fazendo merge dos indicadores...")

    df_final = ind_populacao

    for ind_df in [ind_etaria, ind_raca, ind_agua, ind_esgoto, ind_lixo]:
        df_final = df_final.merge(ind_df, on='CD_MUN', how='outer')

    # 4. Adicionar metadados
    df_final['ano_referencia'] = 2022
    df_final['fonte'] = 'IBGE Censo 2022'
    df_final['uf'] = 'PB'

    # 5. Ordenar colunas (chave primeiro, depois indicadores, depois metadados)
    colunas_ordenadas = ['CD_MUN', 'uf'] + [
        col for col in df_final.columns
        if col not in ['CD_MUN', 'uf', 'ano_referencia', 'fonte']
    ] + ['ano_referencia', 'fonte']

    df_final = df_final[colunas_ordenadas]

    # 6. Validar dados
    logger.info("Validando dados...")

    total_municipios = len(df_final)
    municipios_com_populacao = df_final['total_populacao'].notna().sum()
    populacao_total_pb = df_final['total_populacao'].sum()

    logger.info(f"Total de municípios: {total_municipios}")
    logger.info(f"Municípios com população: {municipios_com_populacao}")
    logger.info(f"População total PB: {populacao_total_pb:,.0f}")

    if total_municipios != 223:  # PB tem 223 municípios
        logger.warning(f"⚠️ Esperado 223 municípios, encontrado {total_municipios}")

    if populacao_total_pb < 3_500_000 or populacao_total_pb > 5_000_000:
        logger.warning(f"⚠️ População total fora do esperado (~4 milhões): {populacao_total_pb:,.0f}")

    # 7. Salvar no Gold
    output_path = "data/gold/municipio_socioeconomico_pb.parquet"
    storage.write_parquet(df_final, output_path)

    logger.info(f"✅ Dados salvos: {output_path}")
    logger.info("=" * 60)

    return df_final


if __name__ == "__main__":
    run()
```

**✅ Validação:**

```bash
# 1. Executar transform
make run-socioeconomico-transform-municipio

# 2. Inspecionar resultado
poetry run python -c "
import pandas as pd
df = pd.read_parquet('data/gold/municipio_socioeconomico_pb.parquet')

print(f'Municípios: {len(df)}')
print(f'Colunas: {list(df.columns)}')
print(f'\nPrimeiros registros:')
print(df.head())

print(f'\nEstatísticas:')
print(df[['total_populacao', 'pct_agua_rede_geral', 'pct_esgoto_rede_geral']].describe())

print(f'\nMunicípios com maior população:')
print(df.nlargest(5, 'total_populacao')[['CD_MUN', 'total_populacao']])
"

# 3. Verificar João Pessoa (código 2507507)
poetry run python -c "
import pandas as pd
df = pd.read_parquet('data/gold/municipio_socioeconomico_pb.parquet')
jp = df[df['CD_MUN'] == '2507507']
print('João Pessoa:')
print(jp.T)
"
```

**🎯 Resultado Esperado:**

- 223 municípios no Gold
- População total PB: ~4 milhões
- João Pessoa: ~800 mil habitantes
- Percentuais entre 0 e 100
- Alguns NaN em indicadores não implementados (alfabetização, família)

**⚠️ Problemas Comuns:**

- **Menos de 223 municípios:** Algum dataset do Silver está incompleto. Verifique extract.
- **População muito diferente:** Erro nas variáveis IBGE. Consulte dicionário oficial.
- **Merge perdeu dados:** Use `how='outer'` no merge para manter todos os municípios.

---

**Task 1.5 — Load município no MongoDB** (4h)

**📋 Objetivo:** Ler Parquet do Gold, converter para formato de documento MongoDB e fazer upsert na collection.

**📚 Referência:** Veja `src/jobs/education_jobs/bairro_pipeline/etl/load.py` para entender o padrão de load do projeto.

**📁 Arquivo a Implementar:** `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/municipio/load.py`

**🔑 Conceitos Importantes:**

- **Por que upsert?** Permite re-executar o pipeline sem duplicar dados. Se o município já existe, atualiza; senão, insere.
- **Como estruturar o documento?** Agrupe indicadores por tema (população, saneamento, etc.) para facilitar queries.
- **Por que criar índices?** Acelera queries. Índice único em `municipioIdIbge` garante que não há duplicatas.

**📝 Implementação Completa:**

```python
"""
Load — Município (IBGE Censo 2022)

Carrega indicadores socioeconômicos de município no MongoDB.
"""
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from pymongo import MongoClient, ASCENDING
from pymongo.errors import BulkWriteError

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _converter_para_documento(row: pd.Series) -> Dict[str, Any]:
    """
    Converte uma linha do DataFrame para documento MongoDB.

    Args:
        row: Linha do DataFrame com indicadores

    Returns:
        Documento MongoDB estruturado por tema
    """
    # Função auxiliar para converter valores (tratar NaN)
    def _val(x):
        if pd.isna(x):
            return None
        if isinstance(x, (int, float)):
            return float(x) if isinstance(x, float) else int(x)
        return x

    return {
        "municipioIdIbge": int(row['CD_MUN']),
        "uf": row['uf'],
        "anoReferencia": int(row['ano_referencia']),
        "fonte": row['fonte'],

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
    Carrega indicadores de município no MongoDB.

    Returns:
        Número de documentos inseridos/atualizados
    """
    storage = storage or get_storage_backend()
    config = load_config()

    logger.info("=" * 60)
    logger.info("LOAD — MUNICÍPIO")
    logger.info("=" * 60)

    # 1. Carregar dados do Gold
    gold_path = "data/gold/municipio_socioeconomico_pb.parquet"
    df = storage.read_parquet(gold_path)

    logger.info(f"Carregando {len(df)} municípios do Gold...")

    # 2. Conectar no MongoDB
    mongo_uri = config.get("mongodb", {}).get("uri", "mongodb://localhost:27017/")
    db_name = config.get("mongodb", {}).get("database", "odin")
    collection_name = "municipio_socioeconomico"

    logger.info(f"Conectando no MongoDB: {db_name}.{collection_name}")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # 3. Criar índices
    logger.info("Criando índices...")
    collection.create_index([("municipioIdIbge", ASCENDING)], unique=True)
    collection.create_index([("uf", ASCENDING)])

    # 4. Converter para documentos e fazer upsert
    logger.info("Fazendo upsert dos documentos...")

    documentos = []
    for _, row in df.iterrows():
        doc = _converter_para_documento(row)
        documentos.append(doc)

    # Upsert em batch
    operacoes = []
    for doc in documentos:
        operacoes.append({
            "replaceOne": {
                "filter": {"municipioIdIbge": doc["municipioIdIbge"]},
                "replacement": doc,
                "upsert": True,
            }
        })

    try:
        resultado = collection.bulk_write(operacoes, ordered=False)

        inseridos = resultado.upserted_count
        atualizados = resultado.modified_count

        logger.info(f"✅ Documentos inseridos: {inseridos}")
        logger.info(f"✅ Documentos atualizados: {atualizados}")

    except BulkWriteError as e:
        logger.error(f"❌ Erro no bulk write: {e.details}")
        raise

    # 5. Validar
    total_docs = collection.count_documents({})
    logger.info(f"Total de documentos na collection: {total_docs}")

    # Mostrar exemplo
    exemplo = collection.find_one({"municipioIdIbge": 2507507})  # João Pessoa
    if exemplo:
        logger.info(f"\nExemplo (João Pessoa):")
        logger.info(f"  População: {exemplo['populacao']['total']:,}")
        logger.info(f"  Água rede geral: {exemplo['saneamento']['pctAguaRedeGeral']}%")
        logger.info(f"  Esgoto rede geral: {exemplo['saneamento']['pctEsgotoRedeGeral']}%")

    logger.info("=" * 60)

    client.close()
    return inseridos + atualizados


if __name__ == "__main__":
    run()
```

**✅ Validação:**

```bash
# 1. Executar load
make run-socioeconomico-load-municipio

# 2. Verificar no MongoDB
poetry run python -c "
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['odin']
collection = db['municipio_socioeconomico']

print(f'Total de documentos: {collection.count_documents({})}')

# Buscar João Pessoa
jp = collection.find_one({'municipioIdIbge': 2507507})
print(f'\nJoão Pessoa:')
print(f'  População: {jp[\"populacao\"][\"total\"]:,}')
print(f'  Água: {jp[\"saneamento\"][\"pctAguaRedeGeral\"]}%')
print(f'  Esgoto: {jp[\"saneamento\"][\"pctEsgotoRedeGeral\"]}%')

# Listar municípios com pior saneamento
print(f'\nMunicípios com menor % de água encanada:')
piores = collection.find().sort('saneamento.pctAguaRedeGeral', 1).limit(5)
for doc in piores:
    print(f'  {doc[\"municipioIdIbge\"]}: {doc[\"saneamento\"][\"pctAguaRedeGeral\"]}%')
"

# 3. Testar query geoespacial (se tiver geometria)
# TODO: Adicionar geometria na Sprint 2
```

**🎯 Resultado Esperado:**

- 223 documentos na collection `municipio_socioeconomico`
- João Pessoa com ~800 mil habitantes
- Índice único em `municipioIdIbge` criado
- Queries funcionando (busca por ID, ordenação por indicador)

**⚠️ Problemas Comuns:**

- **Erro de conexão MongoDB:** Verifique se MongoDB está rodando (`docker-compose up -d`)
- **Duplicate key error:** Índice único já existe com dados diferentes. Delete a collection e rode novamente.
- **Valores None em tudo:** Conversão de NaN falhou. Verifique função `_val()`.
- **Config não encontrada:** Adicione seção `mongodb` no `config/config_geocode.yml`

**Entrega:** Pipeline de município completo e funcional

---

### 🎯 Checkpoint Sprint 1 (último dia)

**Task 1.6 — Orquestração e Testes End-to-End** (4h)

**📋 Objetivo:** Conectar todas as etapas do pipeline de município e validar funcionamento completo.

**📁 Arquivos a Modificar:**

- `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/main.py`
- `src/jobs/socioeconomico_jobs/main.py`

**📝 Implementação:**

1. **Atualizar `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/main.py`:**

```python
"""
Orquestrador do pipeline IBGE Censo 2022.
"""
import logging

from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import extract
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import transform_municipio
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl import load_municipio

logger = logging.getLogger(__name__)


def run_municipio():
    """
    Executa pipeline completo de município: Extract → Transform → Load.
    """
    logger.info("🏙️  Iniciando pipeline de MUNICÍPIO...")

    try:
        # Extract (baixa todos os datasets, mas vamos usar só município por enquanto)
        logger.info("1/3 - Extract...")
        extract.run()

        # Transform
        logger.info("2/3 - Transform...")
        df = transform_municipio.run()
        logger.info(f"   Municípios processados: {len(df)}")

        # Load
        logger.info("3/3 - Load...")
        total = load_municipio.run()
        logger.info(f"   Documentos no MongoDB: {total}")

        logger.info("✅ Pipeline de município concluído com sucesso!")

    except Exception as e:
        logger.error(f"❌ Erro no pipeline de município: {e}")
        raise


def run():
    """
    Executa o pipeline completo: Extract → Transform → Load para todas as granularidades.
    """
    logger.info("=" * 60)
    logger.info("PIPELINE IBGE CENSO 2022")
    logger.info("=" * 60)

    # Sprint 1: apenas município
    run_municipio()

    # Sprint 2: adicionar setor e bairro
    # run_setor()
    # run_bairro()

    logger.info("=" * 60)
    logger.info("✅ PIPELINE COMPLETO!")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
```

2. **Script de Validação:** Criar `scripts/validar_socioeconomico.py`

```python
"""
Script de validação do módulo socioeconômico.

Verifica:
- Arquivos no Silver e Gold
- Dados no MongoDB
- Qualidade dos indicadores
"""
import sys
from pathlib import Path

import pandas as pd
from pymongo import MongoClient


def validar_arquivos():
    """Valida existência de arquivos no Silver e Gold."""
    print("=" * 60)
    print("VALIDANDO ARQUIVOS")
    print("=" * 60)

    erros = []

    # Silver: 7 datasets × 3 granularidades = 21 arquivos
    silver_path = Path("data/silver")
    datasets = ["basico", "demografia", "cor_ou_raca", "caracteristicas_domicilio2",
                "caracteristicas_domicilio3", "alfabetizacao", "obitos"]
    granularidades = ["municipio", "setor", "bairro"]

    for gran in granularidades:
        for dataset in datasets:
            arquivo = silver_path / f"ibge_censo2022_{gran}_{dataset}_pb.parquet"
            if arquivo.exists():
                df = pd.read_parquet(arquivo)
                print(f"✅ {arquivo.name}: {len(df)} registros")
            else:
                print(f"❌ {arquivo.name}: NÃO ENCONTRADO")
                erros.append(f"Arquivo faltando: {arquivo}")

    # Gold: município
    gold_path = Path("data/gold/municipio_socioeconomico_pb.parquet")
    if gold_path.exists():
        df = pd.read_parquet(gold_path)
        print(f"✅ {gold_path.name}: {len(df)} municípios")
    else:
        print(f"❌ {gold_path.name}: NÃO ENCONTRADO")
        erros.append(f"Arquivo faltando: {gold_path}")

    return erros


def validar_mongodb():
    """Valida dados no MongoDB."""
    print("\n" + "=" * 60)
    print("VALIDANDO MONGODB")
    print("=" * 60)

    erros = []

    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        db = client["odin"]
        collection = db["municipio_socioeconomico"]

        total = collection.count_documents({})
        print(f"✅ Collection 'municipio_socioeconomico': {total} documentos")

        if total != 223:
            erros.append(f"Esperado 223 municípios, encontrado {total}")

        # Verificar João Pessoa
        jp = collection.find_one({"municipioIdIbge": 2507507})
        if jp:
            pop = jp["populacao"]["total"]
            print(f"✅ João Pessoa encontrada: {pop:,} habitantes")

            if pop < 700_000 or pop > 900_000:
                erros.append(f"População de João Pessoa fora do esperado: {pop:,}")
        else:
            print("❌ João Pessoa não encontrada")
            erros.append("João Pessoa (2507507) não encontrada no MongoDB")

        # Verificar índices
        indices = list(collection.list_indexes())
        print(f"✅ Índices criados: {len(indices)}")

        client.close()

    except Exception as e:
        print(f"❌ Erro ao conectar no MongoDB: {e}")
        erros.append(f"MongoDB: {e}")

    return erros


def validar_qualidade():
    """Valida qualidade dos indicadores."""
    print("\n" + "=" * 60)
    print("VALIDANDO QUALIDADE DOS INDICADORES")
    print("=" * 60)

    erros = []

    gold_path = Path("data/gold/municipio_socioeconomico_pb.parquet")
    if not gold_path.exists():
        erros.append("Arquivo Gold não encontrado")
        return erros

    df = pd.read_parquet(gold_path)

    # Verificar população total
    pop_total = df["total_populacao"].sum()
    print(f"População total PB: {pop_total:,.0f}")

    if pop_total < 3_500_000 or pop_total > 5_000_000:
        erros.append(f"População total fora do esperado (~4M): {pop_total:,.0f}")

    # Verificar percentuais (devem estar entre 0 e 100)
    colunas_pct = [col for col in df.columns if col.startswith('pct_')]

    for col in colunas_pct:
        valores = df[col].dropna()
        if len(valores) == 0:
            continue

        minimo = valores.min()
        maximo = valores.max()

        if minimo < 0 or maximo > 100:
            print(f"❌ {col}: fora do range [0, 100] ({minimo:.1f} - {maximo:.1f})")
            erros.append(f"{col} fora do range: {minimo:.1f} - {maximo:.1f}")
        else:
            print(f"✅ {col}: {minimo:.1f}% - {maximo:.1f}%")

    # Verificar NaN excessivos
    for col in df.columns:
        if col in ['CD_MUN', 'uf', 'ano_referencia', 'fonte']:
            continue

        pct_nan = df[col].isna().sum() / len(df) * 100
        if pct_nan > 50:
            print(f"⚠️  {col}: {pct_nan:.1f}% de valores ausentes")

    return erros


def main():
    """Executa todas as validações."""
    print("\n🔍 VALIDAÇÃO DO MÓDULO SOCIOECONÔMICO\n")

    erros_arquivos = validar_arquivos()
    erros_mongo = validar_mongodb()
    erros_qualidade = validar_qualidade()

    todos_erros = erros_arquivos + erros_mongo + erros_qualidade

    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    if todos_erros:
        print(f"❌ {len(todos_erros)} erro(s) encontrado(s):\n")
        for erro in todos_erros:
            print(f"  - {erro}")
        sys.exit(1)
    else:
        print("✅ Todas as validações passaram!")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

3. **Adicionar ao Makefile:**

```makefile
.PHONY: validar-socioeconomico
validar-socioeconomico:
	@echo "🔍 Validando módulo socioeconômico..."
	poetry run python scripts/validar_socioeconomico.py
```

**✅ Validação do Sprint 1:**

```bash
# 1. Executar pipeline completo
make run-socioeconomico

# 2. Executar validação
make validar-socioeconomico

# 3. Verificar logs
# Deve mostrar:
# - 21 arquivos no Silver
# - 1 arquivo no Gold (município)
# - 223 documentos no MongoDB
# - População total PB ~4 milhões
# - Todos os percentuais entre 0 e 100
```

**🎯 Critérios de Aceitação (Definition of Done):**

- [ ] Pipeline `make run-socioeconomico` executa sem erros
- [ ] Script de validação passa 100%
- [ ] 223 municípios no MongoDB
- [ ] População total PB entre 3.5M e 5M
- [ ] João Pessoa com ~800 mil habitantes
- [ ] Todos os percentuais entre 0 e 100
- [ ] Code review aprovado
- [ ] Documentação atualizada

**Reunião de validação (2h):**

- [ ] Rodar `make run-socioeconomico` end-to-end
- [ ] Validar dados no MongoDB: 225 municípios da PB
- [ ] Verificar se indicadores fazem sentido (comparar com dados conhecidos de João Pessoa/Campina Grande)
- [ ] Code review cruzado: Pessoa 1 revisa código da Pessoa 2, etc.
- [ ] Ajustar bugs encontrados

**Entrega Sprint 1:** Pipeline de município 100% funcional + biblioteca de indicadores pronta para reutilização

---

## Sprint 2 — Setor e Bairro (5 dias úteis)

**Objetivo:** Replicar a lógica para setor censitário e bairro (paralelização total)

### 👤 Pessoa 1 — Pipeline Setor Censitário (3 dias)

**Task 2.1 — Transform setor** (4h)

**📋 Objetivo:** Adaptar o transform de município para setor censitário. A lógica é idêntica, apenas muda a granularidade dos dados.

**📚 Referência:** Copie `municipio/transform.py` e adapte para setor.

**📁 Arquivo a Criar:** `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/setor/transform.py`

**🔑 Diferenças em relação a Município:**

- Chave geográfica: `CD_SETOR` (15 dígitos) ao invés de `CD_MUN` (7 dígitos)
- Arquivos Silver: `ibge_censo2022_setor_*` ao invés de `ibge_censo2022_municipio_*`
- Arquivo Gold: `setor_socioeconomico_pb.parquet`
- Volume: ~2.243 setores ao invés de 223 municípios

**📝 Implementação (Diferenças):**

```python
"""
Transform — Setor Censitário (IBGE Censo 2022)

Calcula indicadores socioeconômicos agregados por setor censitário da Paraíba.
"""
import logging
from pathlib import Path

import pandas as pd

from src.common.storage import StorageBackend, get_storage_backend
from src.jobs.socioeconomico_jobs.ibge_censo_pipeline import indicadores

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def run(storage: StorageBackend = None) -> pd.DataFrame:
    """
    Calcula indicadores socioeconômicos por setor censitário.

    Returns:
        DataFrame com uma linha por setor e mesmas colunas do município
    """
    storage = storage or get_storage_backend()

    logger.info("=" * 60)
    logger.info("TRANSFORM — SETOR CENSITÁRIO")
    logger.info("=" * 60)

    # 1. Carregar dados do Silver (DIFERENÇA: setor ao invés de municipio)
    logger.info("Carregando dados do Silver...")

    silver_path = Path("data/silver")

    df_basico = storage.read_parquet(str(silver_path / "ibge_censo2022_setor_basico_pb.parquet"))
    df_demografia = storage.read_parquet(str(silver_path / "ibge_censo2022_setor_demografia_pb.parquet"))
    df_cor_raca = storage.read_parquet(str(silver_path / "ibge_censo2022_setor_cor_ou_raca_pb.parquet"))
    df_domicilio2 = storage.read_parquet(str(silver_path / "ibge_censo2022_setor_caracteristicas_domicilio2_pb.parquet"))
    df_domicilio3 = storage.read_parquet(str(silver_path / "ibge_censo2022_setor_caracteristicas_domicilio3_pb.parquet"))

    logger.info(f"Setores no basico: {len(df_basico)}")

    # 2. Calcular indicadores (MESMA LÓGICA)
    logger.info("Calculando indicadores...")

    ind_populacao = indicadores.calcular_populacao(df_basico)
    ind_etaria = indicadores.calcular_estrutura_etaria(df_demografia)
    ind_raca = indicadores.calcular_raca(df_cor_raca)
    ind_agua = indicadores.calcular_saneamento_agua(df_domicilio2)
    ind_esgoto = indicadores.calcular_saneamento_esgoto(df_domicilio2)
    ind_lixo = indicadores.calcular_saneamento_lixo(df_domicilio3)

    # 3. Fazer merge (DIFERENÇA: chave é CD_SETOR)
    logger.info("Fazendo merge dos indicadores...")

    df_final = ind_populacao

    for ind_df in [ind_etaria, ind_raca, ind_agua, ind_esgoto, ind_lixo]:
        df_final = df_final.merge(ind_df, on='CD_SETOR', how='outer')

    # 4. Adicionar metadados + extrair código do município
    df_final['ano_referencia'] = 2022
    df_final['fonte'] = 'IBGE Censo 2022'
    df_final['uf'] = 'PB'

    # IMPORTANTE: Extrair CD_MUN dos primeiros 7 dígitos do CD_SETOR
    df_final['CD_MUN'] = df_final['CD_SETOR'].str[:7]

    # 5. Validar dados
    logger.info("Validando dados...")

    total_setores = len(df_final)
    setores_com_populacao = df_final['total_populacao'].notna().sum()
    populacao_total_pb = df_final['total_populacao'].sum()

    logger.info(f"Total de setores: {total_setores}")
    logger.info(f"Setores com população: {setores_com_populacao}")
    logger.info(f"População total PB: {populacao_total_pb:,.0f}")

    if total_setores < 2000 or total_setores > 3000:
        logger.warning(f"⚠️ Número de setores fora do esperado (~2.243): {total_setores}")

    if populacao_total_pb < 3_500_000 or populacao_total_pb > 5_000_000:
        logger.warning(f"⚠️ População total fora do esperado (~4 milhões): {populacao_total_pb:,.0f}")

    # 6. Salvar no Gold
    output_path = "data/gold/setor_socioeconomico_pb.parquet"
    storage.write_parquet(df_final, output_path)

    logger.info(f"✅ Dados salvos: {output_path}")
    logger.info("=" * 60)

    return df_final


if __name__ == "__main__":
    run()
```

**✅ Validação:**

```bash
# 1. Executar transform
make run-socioeconomico-transform-setor

# 2. Verificar resultado
poetry run python -c "
import pandas as pd
df = pd.read_parquet('data/gold/setor_socioeconomico_pb.parquet')

print(f'Setores: {len(df)}')
print(f'População total: {df[\"total_populacao\"].sum():,.0f}')
print(f'\nSetores com maior população:')
print(df.nlargest(5, 'total_populacao')[['CD_SETOR', 'CD_MUN', 'total_populacao']])
"
```

**🎯 Resultado Esperado:**

- ~2.243 setores no Gold
- População total PB ~4 milhões (mesma do município)
- Coluna `CD_MUN` extraída corretamente dos primeiros 7 dígitos

---

**Task 2.2 — Load setor no MongoDB** (4h)

**📋 Objetivo:** Carregar setores no MongoDB com geometria (polígono).

**📁 Arquivo a Criar:** `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/etl/setor/load.py`

**🔑 Diferenças em relação a Município:**

- Chave: `cd_setor` (string de 15 dígitos)
- Collection: `setor_socioeconomico`
- **NOVO:** Adicionar campo `geometria` (GeoJSON Polygon) fazendo merge com `setores_pb.gpkg`
- **NOVO:** Criar índice geoespacial `2dsphere` em `geometria`

**📝 Implementação Completa:**

```python
"""
Load — Setor Censitário (IBGE Censo 2022)

Carrega indicadores socioeconômicos de setor no MongoDB com geometria.
"""
import logging
from pathlib import Path
from typing import Dict, Any

import geopandas as gpd
import pandas as pd
from pymongo import MongoClient, ASCENDING, GEOSPHERE
from pymongo.errors import BulkWriteError
from shapely.geometry import mapping

from src.common.storage import StorageBackend, get_storage_backend
from src.common.utils import load_config

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)


def _carregar_geometrias_setores() -> Dict[str, dict]:
    """
    Carrega geometrias dos setores do arquivo GPKG.

    Returns:
        Dict {cd_setor: geometria_geojson}
    """
    gpkg_path = "data/silver/setores_pb.gpkg"

    if not Path(gpkg_path).exists():
        logger.warning(f"Arquivo de geometrias não encontrado: {gpkg_path}")
        return {}

    logger.info(f"Carregando geometrias de {gpkg_path}...")
    gdf = gpd.read_file(gpkg_path)

    # Identificar coluna de código do setor (pode ser CD_SETOR ou cd_setor)
    col_setor = None
    for col in ['CD_SETOR', 'cd_setor', 'CD_GEOCODI']:
        if col in gdf.columns:
            col_setor = col
            break

    if not col_setor:
        logger.error("Coluna de código do setor não encontrada no GPKG")
        return {}

    geometrias = {}
    for _, row in gdf.iterrows():
        cd_setor = str(row[col_setor])
        geom = row['geometry']

        # Converter para GeoJSON
        geometrias[cd_setor] = mapping(geom)

    logger.info(f"✅ {len(geometrias)} geometrias carregadas")
    return geometrias


def _converter_para_documento(row: pd.Series, geometrias: Dict[str, dict]) -> Dict[str, Any]:
    """
    Converte uma linha do DataFrame para documento MongoDB.

    Args:
        row: Linha do DataFrame com indicadores
        geometrias: Dict com geometrias por cd_setor

    Returns:
        Documento MongoDB estruturado por tema + geometria
    """
    def _val(x):
        if pd.isna(x):
            return None
        if isinstance(x, (int, float)):
            return float(x) if isinstance(x, float) else int(x)
        return x

    cd_setor = str(row['CD_SETOR'])

    doc = {
        "cd_setor": cd_setor,
        "cd_municipio": str(row['CD_MUN']),
        "uf": row['uf'],
        "anoReferencia": int(row['ano_referencia']),
        "fonte": row['fonte'],

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
    }

    # Adicionar geometria se disponível
    if cd_setor in geometrias:
        doc["geometria"] = geometrias[cd_setor]

    return doc


def run(storage: StorageBackend = None) -> int:
    """
    Carrega indicadores de setor no MongoDB.

    Returns:
        Número de documentos inseridos/atualizados
    """
    storage = storage or get_storage_backend()
    config = load_config()

    logger.info("=" * 60)
    logger.info("LOAD — SETOR CENSITÁRIO")
    logger.info("=" * 60)

    # 1. Carregar dados do Gold
    gold_path = "data/gold/setor_socioeconomico_pb.parquet"
    df = storage.read_parquet(gold_path)

    logger.info(f"Carregando {len(df)} setores do Gold...")

    # 2. Carregar geometrias
    geometrias = _carregar_geometrias_setores()

    # 3. Conectar no MongoDB
    mongo_uri = config.get("mongodb", {}).get("uri", "mongodb://localhost:27017/")
    db_name = config.get("mongodb", {}).get("database", "odin")
    collection_name = "setor_socioeconomico"

    logger.info(f"Conectando no MongoDB: {db_name}.{collection_name}")

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    # 4. Criar índices
    logger.info("Criando índices...")
    collection.create_index([("cd_setor", ASCENDING)], unique=True)
    collection.create_index([("cd_municipio", ASCENDING)])
    collection.create_index([("uf", ASCENDING)])

    # Índice geoespacial (se houver geometrias)
    if geometrias:
        collection.create_index([("geometria", GEOSPHERE)])
        logger.info("✅ Índice geoespacial criado")

    # 5. Converter para documentos e fazer upsert
    logger.info("Fazendo upsert dos documentos...")

    documentos = []
    setores_com_geometria = 0

    for _, row in df.iterrows():
        doc = _converter_para_documento(row, geometrias)
        documentos.append(doc)

        if "geometria" in doc:
            setores_com_geometria += 1

    logger.info(f"Setores com geometria: {setores_com_geometria}/{len(documentos)}")

    # Upsert em batch
    operacoes = []
    for doc in documentos:
        operacoes.append({
            "replaceOne": {
                "filter": {"cd_setor": doc["cd_setor"]},
                "replacement": doc,
                "upsert": True,
            }
        })

    try:
        resultado = collection.bulk_write(operacoes, ordered=False)

        inseridos = resultado.upserted_count
        atualizados = resultado.modified_count

        logger.info(f"✅ Documentos inseridos: {inseridos}")
        logger.info(f"✅ Documentos atualizados: {atualizados}")

    except BulkWriteError as e:
        logger.error(f"❌ Erro no bulk write: {e.details}")
        raise

    # 6. Validar
    total_docs = collection.count_documents({})
    logger.info(f"Total de documentos na collection: {total_docs}")

    # Testar query geoespacial
    if geometrias:
        # Buscar setores num raio de 5km de João Pessoa (lat: -7.1195, lon: -34.8450)
        ponto_jp = {
            "type": "Point",
            "coordinates": [-34.8450, -7.1195]
        }

        setores_proximos = collection.count_documents({
            "geometria": {
                "$near": {
                    "$geometry": ponto_jp,
                    "$maxDistance": 5000  # 5km em metros
                }
            }
        })

        logger.info(f"Setores num raio de 5km de João Pessoa: {setores_proximos}")

    logger.info("=" * 60)

    client.close()
    return inseridos + atualizados


if __name__ == "__main__":
    run()
```

**✅ Validação:**

```bash
# 1. Executar load
make run-socioeconomico-load-setor

# 2. Verificar no MongoDB
poetry run python -c "
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['odin']
collection = db['setor_socioeconomico']

print(f'Total de setores: {collection.count_documents({})}')

# Verificar setores com geometria
com_geom = collection.count_documents({'geometria': {'$exists': True}})
print(f'Setores com geometria: {com_geom}')

# Buscar setores próximos a João Pessoa
ponto_jp = {'type': 'Point', 'coordinates': [-34.8450, -7.1195]}
proximos = collection.count_documents({
    'geometria': {
        '\$near': {
            '\$geometry': ponto_jp,
            '\$maxDistance': 5000
        }
    }
})
print(f'Setores num raio de 5km de JP: {proximos}')
"
```

**🎯 Resultado Esperado:**

- ~2.243 documentos na collection
- Todos os setores com geometria (se GPKG estiver correto)
- Query geoespacial funciona (retorna setores próximos a um ponto)
- Índice `2dsphere` criado

**⚠️ Problemas Comuns:**

- **Geometrias não carregam:** Verifique nome da coluna no GPKG (`CD_SETOR` vs `cd_setor`)
- **Query geoespacial falha:** Índice `2dsphere` não foi criado. Delete collection e rode novamente.
- **Coordenadas invertidas:** GeoJSON usa [longitude, latitude], não [lat, lon]

---

**Task 2.3 — Enriquecimento: merge com geometria** (4h)

**📋 Objetivo:** Esta task já foi implementada na Task 2.2 (load_setor.py). Não precisa de arquivo separado.

**✅ Checklist:**

- [ ] Geometrias carregadas do GPKG
- [ ] Merge feito por `cd_setor`
- [ ] Campo `geometria` adicionado ao documento
- [ ] Índice `2dsphere` criado
- [ ] Query geoespacial testada

**Entrega:** Pipeline de setor completo (2.243 setores com indicadores + geometria)

---

### 👤 Pessoa 2 — Pipeline Bairro (3 dias)

**Task 2.4 — Transform bairro** (4h)

- [ ] Copiar `transform_municipio.py` → `transform_bairro.py`
- [ ] Adaptar para ler arquivos de bairro (`Agregados_por_bairros_*`)
- [ ] Chave de join composta: `{CD_BAIRRO, CD_MUN}`
- [ ] Reutilizar funções de `indicadores.py`
- [ ] Salvar no Gold: `bairro_socioeconomico_pb.parquet`

**Task 2.5 — Load bairro no MongoDB** (4h)

- [ ] Copiar `load_municipio.py` → `load_bairro.py`
- [ ] Adaptar documento para chave composta `{cd_bairro, cd_mun}`
- [ ] Upsert na collection `bairro_socioeconomico`
- [ ] Criar índice único composto em `{cd_bairro, cd_mun}`

**Task 2.6 — Enriquecimento: merge com geometria** (4h)

- [ ] Ler `data/silver/bairros_pb.gpkg` (já existe do módulo educação)
- [ ] Fazer merge com indicadores socioeconômicos por `{cd_bairro, cd_mun}`
- [ ] Adicionar campo `geometria` (GeoJSON Polygon) ao documento MongoDB
- [ ] Criar índice geoespacial `2dsphere` em `geometria`

**Entrega:** Pipeline de bairro completo (194 bairros com indicadores + geometria)

---

### 👤 Pessoa 3 — Integração e Documentação (5 dias)

**Task 2.7 — Orquestrador principal** (2h)

- [ ] Implementar `src/jobs/socioeconomico_jobs/main.py`:

```python
def run():
    pipelines = [
        ("extract", run_extract),
        ("transform_municipio", run_transform_municipio),
        ("load_municipio", run_load_municipio),
        ("transform_setor", run_transform_setor),
        ("load_setor", run_load_setor),
        ("transform_bairro", run_transform_bairro),
        ("load_bairro", run_load_bairro),
    ]
    # Executar em sequência com logging
```

- [ ] Adicionar ao `src/jobs/education_jobs/main.py` (orquestrador geral do ODIN)

**Task 2.8 — Testes de integração** (4h)

- [ ] Criar `tests/test_socioeconomico_pipeline.py`
- [ ] Testar cada função de `indicadores.py` com dados sintéticos
- [ ] Testar pipeline end-to-end com amostra de 3 municípios
- [ ] Validar schema dos documentos MongoDB

**Task 2.9 — Documentação técnica** (4h)

- [ ] Criar `docs/modulo-socioeconomico/PIPELINE_SOCIOECONOMICO.md`:
  - Arquitetura do pipeline
  - Fluxo de dados (Bronze → Silver → Gold → MongoDB)
  - Dicionário de indicadores (nome, fórmula, variáveis IBGE)
  - Comandos de execução
- [ ] Atualizar `README.md` do projeto com novo módulo
- [ ] Criar `docs/modulo-socioeconomico/QUERIES_EXEMPLO.md` com queries MongoDB úteis

**Task 2.10 — Validação de qualidade** (6h)

- [ ] Criar script de validação `scripts/validar_socioeconomico.py`:
  - Verificar se 225 municípios têm dados
  - Verificar se 2.243 setores têm dados
  - Verificar se 194 bairros têm dados
  - Verificar se indicadores estão no range esperado (0-100 para percentuais)
  - Comparar totais de população com dados oficiais do IBGE
- [ ] Gerar relatório de qualidade em Markdown

**Entrega:** Pipeline completo, testado, documentado e validado

---

### 🎯 Checkpoint Sprint 2 (último dia)

**Reunião de validação (3h):**

- [ ] Rodar `make run-socioeconomico` end-to-end (todas as granularidades)
- [ ] Validar dados no MongoDB:
  - 225 municípios em `municipio_socioeconomico`
  - 2.243 setores em `setor_socioeconomico`
  - 194 bairros em `bairro_socioeconomico`
- [ ] Testar queries geoespaciais (ex: buscar setores num raio de 5km de um ponto)
- [ ] Comparar indicadores entre granularidades (município vs. soma dos setores)
- [ ] Code review final
- [ ] Merge para `main`

**Entrega Sprint 2:** Módulo socioeconômico 100% funcional nas 3 granularidades

---

## Sprint 3 (Opcional) — Expansão e Refinamento

**Se houver tempo ou se Sprint 2 atrasar:**

### 👤 Pessoa 1 — Indicadores de Prioridade 2 (3 dias)

**Task 3.1 — Adicionar 8 indicadores complementares**

- [ ] `pct_dom_improvisado` (habitação precária)
- [ ] `pct_dom_superlotado` (adensamento)
- [ ] `pct_agua_inadequada` (vulnerabilidade hídrica)
- [ ] `pct_esgoto_inadequado` (vulnerabilidade sanitária)
- [ ] `pct_lixo_inadequado` (vulnerabilidade ambiental)
- [ ] `razao_dependencia` (estrutura etária)
- [ ] `total_obitos_2019_2022` (mortalidade)
- [ ] `taxa_mortalidade_infantil_proxy` (saúde infantil)

---

### 👤 Pessoa 2 — Dashboard de Monitoramento (3 dias)

**Task 3.2 — Criar notebook de análise exploratória**

- [ ] `notebooks/analise_socioeconomico_pb.ipynb`
- [ ] Gráficos de distribuição dos indicadores
- [ ] Mapas coropléticos (setor/bairro/município)
- [ ] Correlações entre indicadores socioeconômicos e educacionais
- [ ] Identificação de outliers

---

### 👤 Pessoa 3 — API e Queries Otimizadas (3 dias)

**Task 3.3 — Preparar queries para a API**

- [ ] Criar views agregadas no MongoDB (se necessário)
- [ ] Otimizar índices para queries comuns
- [ ] Documentar endpoints sugeridos para a API:
  - `GET /socioeconomico/municipio/{id}`
  - `GET /socioeconomico/setor/{id}`
  - `GET /socioeconomico/bairro/{id}`
  - `GET /socioeconomico/geo?lat=X&lon=Y&raio=5km`

---

## Resumo de Entregas por Sprint

| Sprint       | Entrega Principal                              | Granularidades           | Indicadores           |
| ------------ | ---------------------------------------------- | ------------------------ | --------------------- |
| **Sprint 1** | Pipeline município + biblioteca de indicadores | Município                | 10 (Prioridade 1)     |
| **Sprint 2** | Pipelines setor + bairro + integração          | Setor, Bairro, Município | 10 (Prioridade 1)     |
| **Sprint 3** | Expansão de indicadores + análises             | Todas                    | 18 (Prioridade 1 + 2) |

---

## Riscos e Mitigações

| Risco                                              | Probabilidade | Impacto | Mitigação                                                               |
| -------------------------------------------------- | ------------- | ------- | ----------------------------------------------------------------------- |
| **Arquivos IBGE muito grandes** (download lento)   | Média         | Baixo   | Implementar cache local; baixar apenas PB quando possível               |
| **Variáveis IBGE mudaram de nome**                 | Baixa         | Alto    | Validar com dicionário oficial; criar testes com dados reais            |
| **Geometrias não fazem merge** (chaves diferentes) | Média         | Médio   | Validar chaves no início da Sprint 2; usar fuzzy matching se necessário |
| **Indicadores não batem com dados oficiais**       | Média         | Alto    | Comparar com dados publicados do IBGE; ajustar fórmulas                 |
| **MongoDB fica lento com 2.243 setores**           | Baixa         | Médio   | Criar índices adequados; testar queries antes do load                   |

---

## Definição de Pronto (DoD)

Uma task está pronta quando:

- [ ] Código commitado e mergeado na branch `develop`
- [ ] Testes passando (se aplicável)
- [ ] Documentação atualizada
- [ ] Code review aprovado por outro membro da equipe
- [ ] Dados validados no MongoDB (contagem + amostra visual)

---

## Ferramentas de Acompanhamento

**Sugestão:** Usar GitHub Projects ou Trello com 4 colunas:

- 📋 **Backlog** (todas as tasks)
- 🏃 **In Progress** (máximo 1 task por pessoa)
- 👀 **Review** (aguardando code review)
- ✅ **Done** (merged e validado)

**Daily standup (15min):**

- O que fiz ontem?
- O que vou fazer hoje?
- Tenho algum bloqueio?

---

## Estimativa de Esforço Total

| Sprint    | Pessoa 1 | Pessoa 2 | Pessoa 3 | Total    |
| --------- | -------- | -------- | -------- | -------- |
| Sprint 1  | 16h      | 16h      | 20h      | 52h      |
| Sprint 2  | 20h      | 20h      | 24h      | 64h      |
| Sprint 3  | 24h      | 24h      | 24h      | 72h      |
| **Total** | **60h**  | **60h**  | **68h**  | **188h** |

**Cenário otimista (2 sprints):** 116h de esforço  
**Cenário realista (3 sprints):** 188h de esforço

Com 3 pessoas trabalhando em paralelo, **2 sprints são viáveis** se não houver bloqueios críticos.

---

## Próximos Passos Imediatos

1. **Criar issues no GitHub** para cada task (usar este documento como referência)
2. **Definir quem é Pessoa 1, 2 e 3** (considerar skills: Python/Pandas, MongoDB, GIS)
3. **Configurar ambiente de desenvolvimento** (todos com mesmas dependências)
4. **Kickoff da Sprint 1** (alinhar expectativas e tirar dúvidas)

Boa sorte! 🚀

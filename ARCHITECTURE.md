# ODIN-ETL — Arquitetura do Projeto

> Documento de arquitetura técnica do motor de dados do ODIN.
> Última atualização: Abril/2026

---

## Visão Geral

O ODIN-ETL é o motor de pipelines ETL do Observatório de Dados Integrados do
Nordeste (ODIN), desenvolvido pelo LEMA/UFPB. Processa dados públicos brasileiros
de múltiplas fontes e os entrega em um banco MongoDB pronto para consumo por
APIs e dashboards.

**Stack tecnológico:**

- Python 3.12 + Poetry
- Pandas + GeoPandas + Shapely
- MongoDB Atlas (banco operacional)
- Docker + Docker Compose
- Armazenamento local por dev (migração para Cloudflare R2 planejada)

---

## Arquitetura Medallion

Os dados fluem por três camadas de diretórios locais:

```
data/
├── bronze/     — arquivos brutos da fonte (ZIPs, CSVs, Shapefiles)
├── silver/     — dados filtrados, padronizados, prontos para processamento
├── gold/       — dados finais prontos para consumo
└── checkpoints/ — progresso incremental (geocodificação)
```

---

## Módulos e Pipelines

### Módulo de Educação (MVP — Paraíba)

```
FONTES EXTERNAS
    │
    ├── INEP (Censo Escolar 2024)
    │       ↓ censo_pipeline
    │   data/silver/censo_nordeste_2024.parquet
    │       ↓ geocode_pipeline/extract
    │   data/silver/escolas_pb.parquet
    │
    ├── LEMA/UFPB (dataset geocodificado)
    │   data/silver/escolas_nordeste_geocoded.parquet
    │       ↓ geocode_pipeline/transform (merge + geocode_fn)
    │   data/gold/escolas_pb_geocoded.parquet
    │       ↓ geocode_pipeline/load
    │   MongoDB: escolas
    │
    ├── Base dos Dados / BigQuery (indicadores INEP)
    │       ↓ indicadores_base_dos_dados_pipeline
    │   data/gold/indicadores_base_dos_dados.parquet
    │       (consumido pelo geocode_pipeline/transform)
    │
    ├── LEMA/UFPB (dataset CEPs PB)
    │   data/gold/cep.json
    │       ↓ bairro_pipeline/transform
    │   MongoDB: bairro_indicadores
    │       ↓ municipio_pipeline/transform
    │   MongoDB: municipio_indicadores
    │
    └── IBGE (shapefiles Censo 2022)
            ↓ geo_ingest_pipeline
        data/silver/bairros_pb.gpkg
        data/silver/setores_pb.gpkg
            ↓ bairro_pipeline (spatial join)
        MongoDB: bairro_indicadores
            ↓ setor_pipeline (spatial join)
        MongoDB: setor_indicadores
```

---

## Relação entre Pipelines

```
censo_pipeline
    └──→ geocode_pipeline/extract
              └──→ geocode_pipeline/transform ←── indicadores_base_dos_dados_pipeline
                        └──→ geocode_pipeline/load → MongoDB: escolas
                        └──→ bairro_pipeline ←── geo_ingest_pipeline (bairros)
                        └──→ setor_pipeline ←── geo_ingest_pipeline (setores)
                        └──→ municipio_pipeline ←── cep.json
```

**Dependências entre pipelines:**

| Pipeline                            | Depende de                                                     |
| ----------------------------------- | -------------------------------------------------------------- |
| geocode_pipeline                    | censo_pipeline (Silver)                                        |
| bairro_pipeline                     | geocode_pipeline (Gold) + geo_ingest_pipeline (bairros Silver) |
| municipio_pipeline                  | censo_pipeline (Silver) + cep.json                             |
| setor_pipeline                      | geocode_pipeline (Gold) + geo_ingest_pipeline (setores Silver) |
| indicadores_base_dos_dados_pipeline | independente (BigQuery)                                        |

---

## Abstração de Storage

Todas as operações de I/O passam pela interface `StorageBackend`
(`src/common/storage.py`):

```python
class StorageBackend(Protocol):
    def save_parquet(df, path) -> None
    def read_parquet(path) -> DataFrame
    def save_zip(content, path) -> None
    def read_file_from_zip(zip_path, target_filename) -> bytes
```

**Implementações:**

- `LocalBackend` — sistema de arquivos local (padrão atual)
- `R2Backend` — Cloudflare R2 (stub, implementação futura)

Para migrar para R2: setar `STORAGE_BACKEND=r2` no `.env` e implementar
`R2Backend`. Nenhum pipeline precisa mudar.

---

## Collections MongoDB

| Collection              | Chave única           | Índice geo               | Documentos |
| ----------------------- | --------------------- | ------------------------ | ---------- |
| `escolas`               | `escolaIdInep`        | `localizacao` (2dsphere) | 3.728      |
| `bairro_indicadores`    | `{bairro, municipio}` | `geometria` (2dsphere)   | 194        |
| `municipio_indicadores` | `municipioIdIbge`     | `centroide` (2dsphere)   | 225        |
| `setor_indicadores`     | `cd_setor`            | `geometria` (2dsphere)   | 2.243      |

**Relacionamentos por valor (sem foreign keys):**

```
escolas.municipioIdIbge
    == municipio_indicadores.municipioIdIbge
    == setor_indicadores.co_municipio
    == bairro_indicadores.municipioIdIbge
```

---

## Orquestração

O orquestrador principal (`src/jobs/education_jobs/main.py`) executa os pipelines
em sequência:

```python
pipelines = [
    ("censo_pipeline", run_censo),
    ("indicadores_pipeline", run_indicadores),
    ("geocode_pipeline", run_geocode),
    ("geo_ingest_pipeline", run_geo_ingest),
    ("bairro_pipeline", run_bairro),
    ("municipio_pipeline", run_municipio),
    ("setor_pipeline", run_setor),
]
```

Se qualquer pipeline falhar, a execução para imediatamente — os pipelines
subsequentes não são executados.

**Comandos disponíveis:**

```bash
poetry run python -m src.jobs.education_jobs.main          # tudo
poetry run python -m src.jobs.education_jobs.censo_pipeline.main
poetry run python -m src.jobs.education_jobs.geocode_pipeline.main
poetry run python -m src.jobs.education_jobs.geo_ingest_pipeline.main
poetry run python -m src.jobs.education_jobs.bairro_pipeline.main
poetry run python -m src.jobs.education_jobs.municipio_pipeline.main
poetry run python -m src.jobs.education_jobs.setor_pipeline.main
```

---

## Módulos Futuros (Cronograma)

| Módulo                     | Prazo         | Status       |
| -------------------------- | ------------- | ------------ |
| Educação (PB)              | Maio/2026     | Concluído    |
| Saúde (hospitais e postos) | Junho/2026    | Não iniciado |
| Empresas (CNPJ)            | Setembro/2026 | Não iniciado |
| Projeto final e demo       | Outubro/2026  | —            |

**Expansão geográfica:** após o MVP da PB, expandir para os 9 estados do Nordeste
mudando `filtro_uf` no `config_geocode.yml`.

---

## Variáveis de Ambiente Necessárias

```env
MONGO_URI=mongodb+srv://...
MONGO_DB_NAME=odin_db
GOOGLE_BILLING_ID=...     # para indicadores_base_dos_dados_pipeline
GOOGLE_API_KEY=           # opcional — para geocodificação via Google
STORAGE_BACKEND=local     # ou "r2" quando migrar
```

Ver `.env.example` na raiz do projeto para documentação completa.

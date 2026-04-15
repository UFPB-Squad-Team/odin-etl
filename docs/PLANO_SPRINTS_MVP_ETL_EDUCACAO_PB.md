# Plano de Sprints — Fechamento do MVP ETL (Educação PB)

Status: Proposto  
Data: 2026-04-03  
Escopo: Finalizar MVP ETL para Educação na Paraíba com entregáveis de dados prontos para API/dashboard.

---

## 1) Resumo executivo

O MVP ETL está avançado e com base forte no nível escola. O que falta para fechar o objetivo do documento de MVP é operacionalizar a camada geoespacial agregada (bairro e município), estabilizar fontes pendentes e padronizar critérios de qualidade/versionamento.

### Já pronto (comprovado)

- Pipeline de Censo (ingestão e filtros) funcionando.
- Geocodificação com reaproveitamento de base antiga + fallback funcionando.
- Enriquecimento com indicadores na camada escola funcionando.
- Documento de escola amigável no Mongo (`localizacao` GeoJSON Point, `infraestrutura`, `indicadores`).
- Orquestração principal existente.

### Faltando para “MVP ETL completo”

- Reativar e estabilizar Pipeline 3 (malhas PB).
- Operacionalizar Pipeline 6 (agregação por bairro).
- Operacionalizar Pipeline 7 (agregação por município).
- Fechar estratégia final da Pipeline 2 (INEP Resultados) com fonte estável.
- Garantir índices geoespaciais e checks de qualidade mínimos por execução.

---

## 2) Estratégia de priorização

Prioridade usada:

1. **Bloqueadores do wow factor (bairro/município)**
2. **Confiabilidade operacional (execução fim a fim)**
3. **Governança mínima (qualidade + contrato + índices)**

---

## 3) Sprint 1 (2 semanas) — “Liberar camada geoespacial MVP”

## Objetivo da sprint

Entregar execução automática e estável de escola + bairro + município na Paraíba, com escrita em Mongo pronta para consumo.

## Entregáveis obrigatórios

1. Pipeline 3 reativada e estável (malhas PB)
2. Pipeline 6 executando ponta a ponta (bairro)
3. Pipeline 7 executando ponta a ponta (município)
4. Índice geoespacial + índices de filtro nas coleções de serving
5. `education_jobs.main` com fluxo MVP habilitado

## Backlog técnico (prioridade alta → média)

### S1.1 — Reativar fluxo no orquestrador principal

**Arquivo principal:**

- [src/jobs/education_jobs/main.py](src/jobs/education_jobs/main.py)

**Ações:**

- Reabilitar etapas hoje comentadas:
  - `geo_ingest_pipeline`
  - `bairro_pipeline`
  - `municipio_pipeline`
- Tornar execução por flags/config (ex.: `RUN_GEO=true`, `RUN_BAIRRO=true`) para facilitar debug.
- Ajustar logging de início/fim por etapa com tempo e contagens.

**Critério de aceite:**

- `python -m src.jobs.education_jobs.main` executa sem intervenção manual (com dados/fontes válidas).

---

### S1.2 — Estabilizar Pipeline 3 (malhas geoespaciais PB)

**Arquivos alvo:**

- [src/jobs/education_jobs/geo_ingest_pipeline/main.py](src/jobs/education_jobs/geo_ingest_pipeline/main.py)
- [src/jobs/education_jobs/geo_ingest_pipeline/extract.py](src/jobs/education_jobs/geo_ingest_pipeline/extract.py)
- [config/config_geocode.yml](config/config_geocode.yml) (ou arquivo de config equivalente de geometrias)

**Ações:**

- Validar URLs/fontes de malhas (IBGE/PB).
- Adicionar fallback de source/local cache para indisponibilidade externa.
- Garantir CRS consistente e padronizado (ex.: EPSG:4326 no output para joins/API).
- Persistir saída em silver/gold com nomes estáveis.

**Critério de aceite:**

- Arquivos de malha de municípios e bairros da PB disponíveis e legíveis para spatial join.

---

### S1.3 — Fechar Pipeline 6 (agregação por bairro)

**Arquivos alvo:**

- [src/jobs/education_jobs/bairro_pipeline/main.py](src/jobs/education_jobs/bairro_pipeline/main.py)
- [src/jobs/education_jobs/bairro_pipeline/etl/extract.py](src/jobs/education_jobs/bairro_pipeline/etl/extract.py)
- [src/jobs/education_jobs/bairro_pipeline/etl/transform.py](src/jobs/education_jobs/bairro_pipeline/etl/transform.py)
- [src/jobs/education_jobs/bairro_pipeline/etl/load.py](src/jobs/education_jobs/bairro_pipeline/etl/load.py)

**Ações:**

- Validar spatial join escola ↔ bairro (cobertura e casos de borda).
- Definir conjunto mínimo de agregados para MVP:
  - `qtdEscolas`
  - métricas médias de indicadores (ex.: IDEB/INSE quando disponível)
  - métricas de infraestrutura chave
- Padronizar schema de saída e coleção de destino (`bairro_indicadores_agregados` ou nome final decidido).
- Criar índice geoespacial da geometria do bairro + índices de filtro (município).

**Critério de aceite:**

- Coleção de bairros preenchida para PB com geometria e agregados consultáveis.

---

### S1.4 — Fechar Pipeline 7 (agregação por município)

**Arquivos alvo:**

- [src/jobs/education_jobs/municipio_pipeline/main.py](src/jobs/education_jobs/municipio_pipeline/main.py)
- [src/jobs/education_jobs/municipio_pipeline/etl/extract.py](src/jobs/education_jobs/municipio_pipeline/etl/extract.py)
- [src/jobs/education_jobs/municipio_pipeline/etl/transform.py](src/jobs/education_jobs/municipio_pipeline/etl/transform.py)
- [src/jobs/education_jobs/municipio_pipeline/etl/load.py](src/jobs/education_jobs/municipio_pipeline/etl/load.py)

**Ações:**

- Definir agregados municipais mínimos (espelho simplificado da visão bairro).
- Garantir consistência de chave `municipioIdIbge` em todos os registros.
- Criar índice geoespacial e de filtros para API.

**Critério de aceite:**

- Coleção municipal pronta para heatmap e ranking.

---

### S1.5 — Índices e performance mínima para API

**Arquivos alvo:**

- [src/jobs/education_jobs/geocode_pipeline/etl/load.py](src/jobs/education_jobs/geocode_pipeline/etl/load.py)
- [src/jobs/education_jobs/bairro_pipeline/etl/load.py](src/jobs/education_jobs/bairro_pipeline/etl/load.py)
- [src/jobs/education_jobs/municipio_pipeline/etl/load.py](src/jobs/education_jobs/municipio_pipeline/etl/load.py)

**Ações:**

- Garantir índices mínimos:
  - escolas: `escolaIdInep` (unique), `localizacao` (2dsphere), `municipioIdIbge`, `dependenciaAdm`, `tipoLocalizacao`
  - bairros: geometria (2dsphere), `municipioIdIbge`
  - municípios: geometria (2dsphere), `municipioIdIbge`

**Critério de aceite:**

- Índices criados automaticamente nos loads.

---

## Riscos da sprint 1 e mitigação

- **URLs externas instáveis** → cache local + fallback + retry.
- **Erros de CRS/join geográfico** → validação de CRS e amostragem manual por município.
- **Volume/performance Mongo** → índices antes de carga final e testes de consulta representativos.

---

## 4) Sprint 2 (2 semanas) — “Confiabilidade, governança e fechamento de MVP”

## Objetivo da sprint

Consolidar qualidade, contrato e reprodutibilidade do ETL para entrega formal de MVP.

## Entregáveis obrigatórios

1. Estratégia final da Pipeline 2 (INEP resultados) definida e implementada
2. Qualidade de dados automatizada por execução
3. Versionamento de schema e contrato de saída
4. Runbook operacional de execução/reprocesso

## Backlog técnico (prioridade alta → média)

### S2.1 — Decisão e estabilização da Pipeline 2

**Arquivos alvo:**

- [src/jobs/education_jobs/main.py](src/jobs/education_jobs/main.py)
- [src/jobs/education_jobs/inep_resultados_pipeline/main.py](src/jobs/education_jobs/inep_resultados_pipeline/main.py)
- [src/jobs/education_jobs/inep_resultados_pipeline/etl/extract.py](src/jobs/education_jobs/inep_resultados_pipeline/etl/extract.py)
- [src/jobs/education_jobs/inep_resultados_pipeline/etl/transform.py](src/jobs/education_jobs/inep_resultados_pipeline/etl/transform.py)
- [src/jobs/education_jobs/inep_resultados_pipeline/etl/load.py](src/jobs/education_jobs/inep_resultados_pipeline/etl/load.py)

**Ações:**

- Definir oficialmente: usar `indicadores_base_dos_dados_pipeline` como fonte principal e `inep_resultados_pipeline` como complementar **ou** estabilizar ambos com precedência clara.
- Eliminar ambiguidade de pipeline duplicada para indicadores no fluxo principal.
- Se mantiver pipeline 2, garantir `load` ativo e integrado.

**Critério de aceite:**

- Fluxo de indicadores único e documentado, sem dupla verdade.

---

### S2.2 — Data Quality gates automáticos

**Arquivos alvo (sugestão):**

- [src/common](src/common)
- [tests](tests)
- [src/jobs/education_jobs](src/jobs/education_jobs)

**Ações:**

- Criar checks automatizados pós-run:
  - `% escolas com coordenadas`
  - `% escolas com indicadores`
  - total por município (outliers)
  - null-rate de chaves críticas
- Falha controlada quando limite mínimo não for atingido.

**Critério de aceite:**

- Execução falha com mensagem clara se qualidade mínima não passar.

---

### S2.3 — Versionamento de schema e contrato de dados

**Arquivos alvo:**

- [src/jobs/education_jobs/geocode_pipeline/etl/transform.py](src/jobs/education_jobs/geocode_pipeline/etl/transform.py)
- [docs/SDD_ARQUITETURA_DADOS_ODIN.md](docs/SDD_ARQUITETURA_DADOS_ODIN.md)
- Novo doc recomendado: `docs/CONTRATO_DADOS_EDUCACAO_V1.md`

**Ações:**

- Adicionar `schemaVersion` no documento da escola.
- Formalizar campos obrigatórios/opcionais/tipos por coleção.
- Registrar breaking changes e política de evolução.

**Critério de aceite:**

- Contrato `v1` publicado e respeitado na carga.

---

### S2.4 — Runbook operacional e empacotamento de execução

**Arquivos alvo:**

- [readme.md](readme.md)
- [WORKFLOW.md](WORKFLOW.md)
- Novo doc recomendado: `docs/RUNBOOK_ETL_EDUCACAO_MVP.md`

**Ações:**

- Documentar comandos oficiais (full run, run parcial, reprocesso por etapa).
- Documentar troubleshooting dos erros já vistos (Mongo serialization, billing BigQuery, geocode fallback).
- Definir janela e frequência de atualização.

**Critério de aceite:**

- Novo membro da equipe consegue rodar/reprocessar com documentação apenas.

---

## 5) Definição de pronto do MVP ETL

O MVP ETL está concluído quando:

1. Fluxo principal executa: escola + bairro + município sem passos manuais.
2. Coleções de serving possuem índices críticos.
3. Contrato de dados `v1` está documentado e versionado.
4. Checks mínimos de qualidade passam automaticamente.
5. Runbook operacional está publicado.

---

## 6) Checklist final (objetivo e binário)

### Coleção escolas

- [ ] `escolaIdInep` único
- [ ] `localizacao` GeoJSON válido
- [ ] `infraestrutura` e `indicadores` preenchidos quando disponíveis
- [ ] `schemaVersion` presente

### Coleção bairros

- [ ] geometria válida
- [ ] agregados mínimos presentes
- [ ] índice `2dsphere`

### Coleção municípios

- [ ] geometria válida
- [ ] agregados mínimos presentes
- [ ] índice `2dsphere`

### Operação

- [ ] `education_jobs.main` sem pipelines críticas comentadas
- [ ] logs por etapa com duração e contagens
- [ ] runbook atualizado

---

## 7) Observações de execução

- Se houver limitação de tempo e só couber **1 sprint**, execute integralmente a Sprint 1.
- A Sprint 2 dá robustez, governança e previsibilidade para produção/demo.
- Para o benchmark tipo Opportunity Atlas, o ganho visual chave vem da Sprint 1 (bairro + município).

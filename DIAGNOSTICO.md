# DIAGNÓSTICO DO PROJETO — ODIN-ETL

> Documento gerado para retomada do projeto.
> Última atualização: Abril/2026

---

## O que é o projeto

ODIN-ETL é o motor de dados do observatório ODIN (Northeast Integrated Data Observatory), desenvolvido pelo LEMA/UFPB. O objetivo é construir pipelines ETL reproduzíveis para ingestão, harmonização e entrega de dados públicos brasileiros, com foco inicial na região Nordeste.

O produto final alimenta dashboards, APIs e análises de políticas públicas.

**MVP atual:** escolas do Nordeste com localização geográfica (lat/lon), dados do Censo Escolar, e agregação por bairro como diferencial.

---

## Arquitetura pretendida

O projeto segue o padrão Medallion:

```
Bronze (raw) → Silver (intermediate) → Gold (processed)
```

- Bronze: cópia exata da fonte original, imutável
- Silver: filtrado, padronizado, enriquecido
- Gold: pronto para consumo por APIs e dashboards

**Armazenamento atual:** local por dev (cada desenvolvedor mantém os dados na sua máquina). A transição para um data lake formal (ex: Cloudflare R2, GCS) está planejada para depois do MVP. O código deve ser escrito pensando nessa migração — abstraindo o storage.

**Banco operacional:** MongoDB (sobe via Docker Compose).

---

## Estado atual do projeto

### O que está funcionando

| Componente | Status | Observação |
|---|---|---|
| `censo_pipeline` (download → subdatasets) | ✅ Funcional | Baixa Censo 2024, filtra Nordeste, gera CSVs por domínio |
| `geocode_pipeline/extract.py` | ⚠️ Quebrado | Dependia do S3, que foi removido do projeto |
| `geocode_pipeline/transform.py` | ⚠️ Quebrado | Dependia do S3 + tem bug de config key |
| `geocode_pipeline/load.py` | ❌ Não implementado | Apenas um TODO |
| `geocode_pipeline/main.py` | ❌ Não implementado | Apenas um TODO |
| `src/jobs/01_education/main.py` | ❌ Vazio | Orquestrador geral não implementado |
| Testes | ❌ Inexistentes | Pasta `tests/` vazia |

### Problemas encontrados

**1. S3 removido do projeto**
Todo o `geocode_pipeline` foi construído sobre AWS S3. Com a remoção do S3, `extract.py` e `transform.py` estão quebrados e precisam ser reescritos para trabalhar com armazenamento local (com abstração para futura migração).

**2. Dois pipelines desconexos para a mesma fonte**
O `censo_pipeline` baixa o Censo 2024 localmente e gera CSVs. O `geocode_pipeline` foi escrito para ler o Censo 2023 do S3. São abordagens diferentes para a mesma fonte, sem integração. Precisam ser unificados.

**3. `docs/` virou repositório de código**
`docs/pipelines/pipeline2/` contém scripts Python funcionais (`extract_indicadores.py`, `transform.py`) que deveriam estar em `src/` ou ser descartados. O `docs/` deve conter apenas documentação.

**4. Dependências não declaradas no `pyproject.toml`**
O projeto usa `boto3`, `pandas`, `geopy`, `pandarallel`, `pymongo`, `python-dotenv`, `pyarrow`, `unidecode`, `pyyaml`, `requests` — nada disso está declarado. Qualquer dev que clonar o repo e rodar `poetry install` terá um ambiente quebrado.

**5. Bug no Makefile**
Os 4 targets do geocode pipeline têm o mesmo nome (`run-geocode-extract`). Apenas o último é executado pelo `make`. Os outros são ignorados silenciosamente.

**6. Bug no `geocode_pipeline/transform.py`**
A linha `config["escolas_pipeline"]["transform"]` usa uma chave errada. O YAML define `geocode_pipeline`, não `escolas_pipeline`. O script quebra em runtime.

**7. Imports frágeis no `censo_pipeline`**
O `main.py` usa imports relativos sem o prefixo completo do pacote (ex: `from etl.downloader import ...`). Só funciona se executado de dentro do diretório `censo_pipeline/`, o que é frágil e não segue o padrão do restante do projeto.

**8. Decisão de geocodificação em aberto**
O projeto usava Google Maps API, mas o custo é inviável para o escopo completo (9 estados, milhares de escolas). Existe um documento de análise em `docs/pipelines/pipelinesGeocoding/comparacao_analitica_api.MD` que levanta o problema e compara alternativas. A decisão ainda não foi tomada.

---

## Estrutura atual do código

```
src/
├── common/
│   └── utils.py              # Utilitários compartilhados (load_config, S3, normalização)
└── jobs/
    └── 01_education/
        ├── main.py           # VAZIO — orquestrador geral
        ├── censo_pipeline/   # Pipeline do Censo Escolar (funcional)
        │   ├── main.py
        │   ├── config/       # settings.py + columns.py
        │   ├── etl/          # downloader, extract, transform, load, subdatasets
        │   └── utils/        # logger, file_utils, paths
        └── geocode_pipeline/ # Pipeline de geocodificação (quebrado/incompleto)
            ├── main.py       # TODO
            ├── extract.py    # Quebrado (S3)
            ├── transform.py  # Quebrado (S3 + bug config)
            └── load.py       # TODO

config/
└── config_geocode.yml        # Configuração central do geocode pipeline

docs/
└── pipelines/
    ├── pipeline1/            # Vazio
    ├── pipeline2/            # ⚠️ Contém scripts Python (não é documentação)
    └── pipelinesGeocoding/   # Documentação do geocode pipeline + análise de APIs

tests/                        # VAZIO
```

---

## Roadmap para o MVP

O MVP entrega: **escolas do Nordeste + localização (lat/lon) + dados do Censo + agregação por bairro**.

---

### Fase 1 — Limpeza e base sólida

> Objetivo: deixar o projeto em estado executável para qualquer dev.

- [ ] Declarar todas as dependências no `pyproject.toml`
- [ ] Mover ou descartar os scripts de `docs/pipelines/pipeline2/` (não pertencem ao `docs/`)
- [ ] Corrigir os 4 targets duplicados no Makefile
- [ ] Corrigir imports do `censo_pipeline/main.py` para usar paths absolutos do pacote
- [ ] Criar `.env.example` com todas as variáveis necessárias documentadas
- [ ] Remover referências ao S3 de `src/common/utils.py` ou isolá-las em um módulo de storage separado

---

### Fase 2 — Unificar e consertar o pipeline de dados

> Objetivo: ter um único fluxo funcional do Censo até o MongoDB, rodando localmente.

- [ ] Decidir a API de geocodificação (candidatos: Nominatim/OSM para gratuito, OpenCage para pago com custo previsível)
- [ ] Reescrever `geocode_pipeline/extract.py` para ler o Censo localmente (output do `censo_pipeline`)
- [ ] Corrigir o bug de config key no `geocode_pipeline/transform.py`
- [ ] Adaptar `geocode_pipeline/transform.py` para salvar checkpoint e resultado localmente
- [ ] Implementar `geocode_pipeline/load.py` — inserir dados geocodificados no MongoDB
- [ ] Implementar `geocode_pipeline/main.py` — orquestrar extract → transform → load
- [ ] Implementar `src/jobs/01_education/main.py` — orquestrar censo + geocode em sequência
- [ ] Abstrair o storage em uma interface (`StorageBackend`) para facilitar migração futura do local para cloud

---

### Fase 3 — Agregação por bairro (o diferencial)

> Objetivo: para cada escola geocodificada, saber em qual bairro ela está e agregar métricas.

> ⚠️ Atenção: bairro no Brasil não é padronizado. `NO_BAIRRO` no Censo é campo livre — a mesma rua pode ter grafias diferentes. A solução correta é via **spatial join com polígonos**, não agrupamento textual.

- [ ] Obter shapefiles de bairros/setores censitários (fonte: IBGE — Malha de Setores Censitários)
- [ ] Implementar spatial join: para cada escola com lat/lon, identificar o polígono de bairro correspondente
- [ ] Agregar métricas do Censo por bairro (ex: média de infraestrutura, total de matrículas, % de escolas com internet)
- [ ] Salvar resultado agregado no MongoDB como coleção separada

---

### Fase 4 — Qualidade mínima

> Objetivo: garantir que o pipeline não quebre silenciosamente e que qualquer dev consiga rodar.

- [ ] Escrever testes unitários para as funções críticas (filtro, montagem de endereço, spatial join)
- [ ] Escrever teste de integração para o pipeline completo com dados de amostra
- [ ] Atualizar o README com instruções reais de execução (não as genéricas atuais)
- [ ] Documentar as variáveis de ambiente necessárias
- [ ] Adicionar validação de dados na entrada de cada etapa (ex: checar se o Parquet tem as colunas esperadas)

---

## Decisões técnicas registradas

| Decisão | Escolha | Motivo |
|---|---|---|
| Storage para MVP | Local por dev | Desbloqueia desenvolvimento sem dependência de cloud |
| Storage futuro | A definir (R2, GCS ou similar) | Migração planejada pós-MVP; código deve abstrair o storage |
| Banco operacional | MongoDB | Já definido na arquitetura original |
| AWS S3 | Removido | Fora do escopo atual |
| Google Maps API | Em revisão | Custo inviável para escopo completo; ver análise em `docs/` |
| Agregação por bairro | Spatial join com shapefiles IBGE | Campo `NO_BAIRRO` não é confiável para agrupamento textual |

---

## Como rodar o que está funcionando hoje

```bash
# 1. Suba o MongoDB
docker-compose up -d db

# 2. Configure o ambiente
cp .env.example .env
# edite o .env com suas variáveis

# 3. Rode o censo pipeline (único pipeline funcional)
docker-compose run --rm etl python src/jobs/01_education/censo_pipeline/main.py
```

> O geocode pipeline está quebrado e não deve ser executado até a Fase 2 estar concluída.

---

## Referências internas

- Análise comparativa de APIs de geocodificação: `docs/pipelines/pipelinesGeocoding/comparacao_analitica_api.MD`
- Documentação do transform (geocode): `docs/pipelines/pipelinesGeocoding/etl/documentation_transform.md`
- Documentação do extract (geocode): `docs/pipelines/pipelinesGeocoding/etl/extract-documentation.md`

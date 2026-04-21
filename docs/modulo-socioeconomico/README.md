# Módulo Socioeconômico — ODIN-ETL

> Agregação de indicadores socioeconômicos do IBGE Censo 2022 para o observatório de dados do Nordeste.

---

## 📚 Documentação Disponível

### 1. Mapeamento de Indicadores

**Arquivo:** [`MAPEAMENTO_INDICADORES_IBGE_2022.md`](./MAPEAMENTO_INDICADORES_IBGE_2022.md)

Documento técnico completo que mapeia:

- Todos os datasets disponíveis no IBGE Censo 2022
- 1.418 variáveis brutas organizadas em 9 temas
- Fórmulas de cálculo para indicadores derivados
- Compatibilidade com granularidades (setor/bairro/município)
- Indicadores priorizados para o MVP

**Principais seções:**

- Fonte de dados e estrutura dos arquivos IBGE
- 10 categorias de indicadores (população, estrutura etária, raça, saneamento, etc.)
- Indicadores não disponíveis (renda, escolaridade — aguardando amostra)
- Estratégia de implementação

---

### 2. Plano de Sprints

**Arquivo:** [`PLANO_SPRINTS_SOCIOECONOMICO.md`](./PLANO_SPRINTS_SOCIOECONOMICO.md)

Planejamento executivo para implementação em 2-3 sprints:

- Divisão de trabalho para equipe de 3 pessoas
- Tasks detalhadas por sprint e por pessoa
- Estratégia de paralelização e reutilização de código
- Estimativas de esforço (116h para 2 sprints, 188h para 3)
- Riscos e mitigações

**Estrutura:**

- **Sprint 1:** Fundação + pipeline de município completo
- **Sprint 2:** Pipelines de setor e bairro (paralelização total)
- **Sprint 3 (opcional):** Expansão de indicadores e análises

---

## 🎯 Objetivo do Módulo

Agregar indicadores socioeconômicos do IBGE Censo 2022 nas mesmas granularidades geográficas do módulo de educação:

| Granularidade        | Cobertura                   | Collection MongoDB         |
| -------------------- | --------------------------- | -------------------------- |
| **Município**        | 225 municípios da PB        | `municipio_socioeconomico` |
| **Setor Censitário** | 2.243 setores da PB         | `setor_socioeconomico`     |
| **Bairro**           | 194 bairros (12 municípios) | `bairro_socioeconomico`    |

---

## 📊 Indicadores Prioritários (MVP)

### Prioridade 1 — Essenciais (10 indicadores)

| Indicador                       | Tema             | Relevância                  |
| ------------------------------- | ---------------- | --------------------------- |
| `total_populacao`               | População        | Base para todos os cálculos |
| `media_moradores_por_domicilio` | Habitação        | Proxy de adensamento        |
| `pct_idosos_60_mais`            | Estrutura etária | Políticas para idosos       |
| `pct_criancas_0_9`              | Estrutura etária | Demanda escolar             |
| `pct_preta_parda`               | Raça             | Equidade racial             |
| `pct_agua_rede_geral`           | Saneamento       | Acesso a água tratada       |
| `pct_esgoto_rede_geral`         | Saneamento       | Acesso a esgoto             |
| `pct_lixo_coletado`             | Saneamento       | Coleta de lixo              |
| `taxa_analfabetismo_15_mais`    | Educação         | Capital humano              |
| `pct_responsavel_feminino`      | Família          | Vulnerabilidade social      |

---

## 🏗️ Arquitetura do Pipeline

```
src/jobs/socioeconomico_jobs/
├── __init__.py
├── main.py                          # Orquestrador
└── ibge_censo_pipeline/
    ├── __init__.py
    ├── main.py
    ├── indicadores.py               # Biblioteca compartilhada de cálculos
    └── etl/
        ├── extract.py              # Download dos ZIPs do FTP IBGE
        ├── transform_municipio.py  # Cálculo de indicadores (município)
        ├── transform_setor.py      # Cálculo de indicadores (setor)
        ├── transform_bairro.py     # Cálculo de indicadores (bairro)
        ├── load_municipio.py       # Upsert no MongoDB
        ├── load_setor.py           # Upsert no MongoDB
        └── load_bairro.py          # Upsert no MongoDB
```

**Fluxo de dados:**

```
FTP IBGE (Bronze)
    ↓ extract.py
Silver (Parquet filtrado PB)
    ↓ transform_*.py + indicadores.py
Gold (Parquet com indicadores calculados)
    ↓ load_*.py
MongoDB (Collections com geometria)
```

---

## 🚀 Como Usar

### Executar pipeline completo

```bash
make run-socioeconomico
```

### Executar por etapa

```bash
# 1. Download dos dados do IBGE
make run-socioeconomico-extract

# 2. Calcular indicadores (município)
make run-socioeconomico-transform-municipio

# 3. Carregar no MongoDB (município)
make run-socioeconomico-load-municipio

# Repetir para setor e bairro...
```

---

## 📄 Gerar PDFs da Documentação

### Opção 1: Pandoc (recomendado)

```bash
brew install pandoc
brew install --cask basictex
make docs-to-pdf-socioeconomico
```

### Opção 2: Python

```bash
poetry add markdown weasyprint pygments
python scripts/md_to_pdf.py docs/modulo-socioeconomico/MAPEAMENTO_INDICADORES_IBGE_2022.md
python scripts/md_to_pdf.py docs/modulo-socioeconomico/PLANO_SPRINTS_SOCIOECONOMICO.md
```

**Ver guia completo:** [`GERAR_PDF_RAPIDO.md`](./GERAR_PDF_RAPIDO.md) ou [`docs/COMO_GERAR_PDF.md`](../COMO_GERAR_PDF.md)

---

## 📅 Cronograma

| Sprint       | Duração           | Entrega                                        |
| ------------ | ----------------- | ---------------------------------------------- |
| **Sprint 1** | 5 dias            | Pipeline município + biblioteca de indicadores |
| **Sprint 2** | 5 dias            | Pipelines setor + bairro + integração          |
| **Sprint 3** | 5 dias (opcional) | Expansão de indicadores + análises             |

**Prazo final:** Final de maio/2026

---

## 👥 Equipe

- **Pessoa 1:** Infraestrutura + Extract + Pipeline Setor
- **Pessoa 2:** Biblioteca de indicadores + Pipeline Bairro
- **Pessoa 3:** Transform/Load Município + Integração + Documentação

---

## 🔗 Links Úteis

- [FTP IBGE — Censo 2022](ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/)
- [Dicionário de Dados IBGE](ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/dicionario_de_dados_agregados_por_setores_censitarios_20250417.xlsx)
- [Documentação ODIN-ETL](../../README.md)
- [Módulo Educação](../modulo-educacao/MODULO_EDUCACAO.md)

---

## 📝 Status

- [x] Mapeamento de indicadores completo
- [x] Plano de sprints definido
- [ ] Sprint 1 — Em andamento
- [ ] Sprint 2 — Aguardando
- [ ] Sprint 3 — Aguardando

---

**Última atualização:** Abril/2026  
**Responsável:** Equipe LEMA-UFPB  
**Projeto:** ODIN-ETL — Observatório de Dados do Nordeste

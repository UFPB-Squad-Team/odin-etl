# Módulo de Educação — Documentação Técnica Completa

> Status: **MVP Concluído** (Abril/2026)
> Escopo geográfico: Paraíba
> Próxima expansão: Nordeste completo (pós-MVP)

---

## Objetivo

O módulo de educação é o primeiro módulo do ODIN a ser implementado. Seu objetivo
é processar, enriquecer e disponibilizar dados educacionais das escolas públicas
da Paraíba em múltiplos níveis de granularidade geográfica, permitindo análises
territoriais que vão da rua ao estado.

O diferencial do ODIN em relação a plataformas como o QEdu é a análise geoespacial
granular — o usuário pode consultar indicadores educacionais de um bairro específico
ou de qualquer ponto do mapa, não apenas por município.

---

## Pipelines Implementadas

### Pipeline 1 — censo_pipeline

**Propósito:** Ingestão dos microdados brutos do Censo Escolar INEP.

**Fluxo:**

```
Download ZIP (INEP) → Extração → Leitura em chunks → Filtro Nordeste → Parquet Silver
```

**Detalhes técnicos:**

- Download com retry strategy (5 tentativas, backoff exponencial)
- Leitura em chunks de 200.000 linhas para controle de memória
- Seleção de 80 colunas relevantes via `usecols` (de ~300 disponíveis)
- Filtro: `NO_REGIAO == "NORDESTE"` — 75.054 escolas
- Output: `data/silver/censo_nordeste_2024.parquet`
- Subdatasets temáticos: 9 arquivos por domínio (infraestrutura, matrículas, etc.)

**Idempotência:** verifica existência do ZIP antes de baixar; verifica existência
do diretório de extração antes de extrair.

---

### Pipeline 0 — geocode_pipeline

**Propósito:** Geocodificar escolas da PB (obter lat/lon) e carregar no MongoDB.

**Fluxo:**

```
Silver censo → Filtro PB → Merge com dataset pré-geocodificado → Geocode API (fallback) → Gold → MongoDB
```

**Estratégia de geocodificação em dois níveis:**

1. **Nível 1 (primário):** merge por `CO_ENTIDADE` com `escolas_nordeste_geocoded.parquet`
   (dataset gerado anteriormente com Google Maps API pelo Gustavo/LEMA)
2. **Nível 2 (fallback):** para escolas sem match, usa `geocode_fn` injetável
   (atualmente placeholder; pode ser substituída por Nominatim ou Google)

**Mecanismo de checkpoint:** salva progresso a cada 100 endereços geocodificados.
Se o processo for interrompido, retoma de onde parou.

**Enriquecimento:** o transform faz merge com o Gold dos indicadores da Base dos
Dados, adicionando indicadores educacionais por nível de ensino ao documento.

**Document builder:** converte dados brutos do Censo em documento JSON semântico
com campos como `escolaNome`, `dependenciaAdm`, `infraestrutura`, `localizacao`
(GeoJSON Point), `indicadores` (aninhado por nível de ensino).

**Resultados:**

- 3.703 escolas com coordenadas reais (99,1%)
- 3.728 documentos atualizados no MongoDB
- Collection: `escolas`

---

### Pipeline 2 — indicadores_base_dos_dados_pipeline

**Propósito:** Buscar indicadores educacionais ricos do INEP via BigQuery (Base dos Dados).

**Fluxo:**

```
BigQuery (Base dos Dados) → Silver Parquet → Transform (estrutura aninhada) → Gold Parquet
```

**Dados obtidos:** AFD, IED, ATU, HAD, DSU, TDI, taxas de aprovação/reprovação/abandono,
TNR, ICG — por nível de ensino (EI, EF anos iniciais/finais, EM).

**Cobertura:** 1.176.158 registros (Nordeste, todos os anos de 2007 a 2024).

**Tratamento de dados sentinela:**

- `horas_aula_diarias = 0` → convertido para `None` (97,3% eram zeros)
- `alunos_por_turma = 0` → convertido para `None` (91,4% eram zeros no EM)
- Campos onde `0` é válido (taxas) não são alterados

**Cache:** se o Silver já existir, pula a query BigQuery (evita custo desnecessário).

**Requisito:** `GOOGLE_BILLING_ID` no `.env`.

---

### Pipeline 3 — geo_ingest_pipeline

**Propósito:** Processar shapefiles geoespaciais do IBGE e salvar como GeoPackage no Silver.

**Fluxo:**

```
Shapefile local (Bronze) → Reprojeção WGS84 → GeoPackage (Silver)
```

**Arquivos processados:**

- `PB_bairros_CD2022.shp` → `data/silver/bairros_pb.gpkg` (257 polígonos)
- `PB_setores_CD2022.shp` → `data/silver/setores_pb.gpkg` (9.639 polígonos)

**CRS:** reprojetado de EPSG:4674 (SIRGAS 2000) para EPSG:4326 (WGS84).

**Nota técnica:** o driver GeoParquet não está disponível no GDAL do ambiente atual.
GeoPackage (`.gpkg`) é usado como alternativa — totalmente compatível com GeoPandas.

**Idempotência:** verifica existência do GeoPackage antes de processar.

---

### Pipeline 6 — bairro_pipeline

**Propósito:** Agregar indicadores educacionais por bairro oficial (IBGE).

**Fluxo:**

```
Gold geocodificado → Extração lat/lon → GeoDataFrame → Spatial join com bairros IBGE
→ Join com Silver censo → Agregação → MongoDB bairro_indicadores
```

**Método:** spatial join geométrico (`predicate="within"`) — cada escola é associada
ao polígono de bairro que a contém geometricamente.

**Cobertura:** 792 escolas (21,4%) em 194 bairros de 12 municípios.

**Métricas agregadas por bairro:**

- `total_escolas`, `total_matriculas`
- `pct_com_internet`, `pct_com_biblioteca`, `pct_com_lab_informatica`
- `pct_sem_acessibilidade`

**Geometria:** polígono GeoJSON real do IBGE (quando disponível) ou centróide
calculado como fallback.

**Índices MongoDB:** `2dsphere` em `geometria`, índice único composto em
`{bairro, municipio}`.

---

### Pipeline 7 — municipio_pipeline

**Propósito:** Agregar indicadores educacionais por município.

**Fluxo:**

```
Silver censo → Join por CEP → Agrupamento por município → MongoDB municipio_indicadores
```

**Método:** join por `CO_CEP` com dataset de CEPs do Aléssio, agrupamento por
`municipio_cep`.

**Cobertura:** 225 municípios (~100% da PB).

**Centróide:** média das coordenadas dos CEPs do município.

**Índices MongoDB:** `2dsphere` em `centroide`, índice único em `municipioIdIbge`.

---

### Pipeline de Setores — setor_pipeline

**Propósito:** Agregar indicadores por setor censitário — unidade base universal
que cobre 100% do território da PB.

**Fluxo:**

```
Gold geocodificado → Extração lat/lon → GeoDataFrame → Spatial join com setores IBGE
→ Join com Silver censo → Agregação → MongoDB setor_indicadores
```

**Método:** spatial join geométrico com 9.639 polígonos de setores censitários.

**Cobertura:** 3.687 escolas (98,7%) em 2.243 setores.

**Campo `nome_area`:** bairro oficial se disponível (`NM_BAIRRO` do IBGE),
nome do município caso contrário. Garante que todo setor tem um nome legível.

**Campo `tem_bairro_oficial`:** boolean — `true` para 603 setores (26,9%),
`false` para 1.640 setores (73,1%).

**Uso principal:** habilita busca por rua via `$geoIntersects`. Qualquer ponto
geográfico na PB pode ser associado a um setor censitário.

**Índices MongoDB:** `2dsphere` em `geometria`, índice único em `cd_setor`,
índice em `co_municipio` e `nome_area`.

---

## Collections no MongoDB

| Collection              | Documentos | Descrição                                                      |
| ----------------------- | ---------- | -------------------------------------------------------------- |
| `escolas`               | 3.728      | Uma por escola — perfil completo com coordenadas e indicadores |
| `bairro_indicadores`    | 194        | Indicadores agregados por bairro oficial IBGE                  |
| `municipio_indicadores` | 225        | Indicadores agregados por município                            |
| `setor_indicadores`     | 2.243      | Indicadores agregados por setor censitário                     |

---

## Schema dos Documentos MongoDB

### `escolas`

```json
{
  "escolaIdInep": "25033158",
  "escolaNome": "EMEIF MAE IAIA",
  "dependenciaAdm": "Municipal",
  "tipoLocalizacao": "Urbana",
  "estadoSigla": "PB",
  "municipioNome": "Água Branca",
  "municipioIdIbge": 2500106,
  "endereco": {
    "logradouro": "RUA SARGENTO FLORENTINO LEITE",
    "numero": "24",
    "bairro": "GUALTERINA ALENCAR VIDAL",
    "cep": "58748000",
    "municipio": "Água Branca",
    "uf": "PB"
  },
  "localizacao": {
    "type": "Point",
    "coordinates": [-37.641, -7.514]
  },
  "infraestrutura": { ... },
  "indicadores": {
    "anoReferencia": 2024,
    "fundamentalAnosIniciais": { "afd": 4.2, "tdi": 28.0, ... },
    "ensinoMedio": { "taxaReprovacao": 29.4, ... }
  }
}
```

### `setor_indicadores`

```json
{
  "cd_setor": "250750705000001",
  "nome_area": "Centro",
  "nm_bairro": "Centro",
  "nm_municipio": "João Pessoa",
  "co_municipio": "2507507",
  "situacao": "Urbana",
  "tipo_setor": "comum",
  "tem_bairro_oficial": true,
  "geometria": { "type": "Polygon", "coordinates": [...] },
  "total_escolas": 3,
  "total_matriculas": 890,
  "pct_com_internet": 100.0,
  "pct_com_biblioteca": 66.7,
  "pct_com_lab_informatica": 33.3,
  "pct_sem_acessibilidade": 0.0
}
```

---

## Status do Módulo

| Componente                          | Status   | Observação                              |
| ----------------------------------- | -------- | --------------------------------------- |
| censo_pipeline                      | Completo | Funcional, idempotente                  |
| geocode_pipeline                    | Completo | 99,1% das escolas geocodificadas        |
| indicadores_base_dos_dados_pipeline | Completo | Requer GOOGLE_BILLING_ID                |
| geo_ingest_pipeline                 | Completo | Bairros + setores processados           |
| bairro_pipeline                     | Completo | 21,4% de cobertura (limitação da fonte) |
| municipio_pipeline                  | Completo | ~100% de cobertura                      |
| setor_pipeline                      | Completo | 98,7% de cobertura                      |
| Testes unitários                    | Pendente | Nenhum teste implementado               |
| inep_resultados_pipeline            | Parcial  | Load comentado, URLs a verificar        |

---

## O que Falta para Expansão Pós-MVP

1. **Expandir para os 9 estados do Nordeste:** mudar `filtro_uf: ["PB"]` para
   `["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"]` no config.

2. **Malha municipal com polígonos:** instalar GDAL com suporte a GeoParquet
   ou usar GeoPackage para a malha municipal, habilitando `$geoWithin` por município.

3. **Testes automatizados:** implementar testes unitários e de integração para
   garantir que refatorações futuras não quebrem os pipelines.

4. **Pipeline INEP Resultados:** verificar URLs do INEP, descomentar o load,
   habilitar no orquestrador principal.

5. **Buffer no spatial join:** aplicar buffer de 50m para capturar as 16 escolas
   que ficam fora dos polígonos de setor por imprecisão de coordenada.

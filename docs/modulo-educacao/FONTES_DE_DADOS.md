# Fontes de Dados — Módulo de Educação

> Documento de referência para todas as fontes de dados utilizadas no módulo de educação do ODIN-ETL.
> Última atualização: Abril/2026

---

## 1. Microdados do Censo Escolar — INEP

**Pipeline:** `censo_pipeline`
**Camada de destino:** Bronze → Silver

| Atributo             | Valor                                                                                    |
| -------------------- | ---------------------------------------------------------------------------------------- |
| Fonte                | Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP)            |
| URL de download      | `https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2024.zip`           |
| Formato              | ZIP contendo CSV (separador `;`, encoding `latin-1`)                                     |
| Tamanho aproximado   | ~1.5 GB (ZIP)                                                                            |
| Ano de referência    | 2024                                                                                     |
| Granularidade        | Uma linha por escola                                                                     |
| Cobertura geográfica | Brasil completo                                                                          |
| Licença              | Dados abertos — uso livre com atribuição                                                 |
| Página oficial       | https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar |

**Colunas coletadas (80 no total):**

- Identificação: região, UF, município, código IBGE, nome da escola, código INEP, dependência administrativa, localização, situação de funcionamento, endereço completo (logradouro, número, bairro, CEP)
- Infraestrutura: água potável, energia elétrica, esgoto, coleta de lixo, biblioteca, laboratórios, quadra, cozinha, refeitório, pátio
- Acessibilidade: corrimão, elevador, pisos táteis, rampas, sinais visual/sonoro/tátil, flag de acessibilidade inexistente
- Tecnologia: internet (geral, alunos, administrativa), equipamentos (impressora, lousa digital, multimídia, computadores, tablets)
- Profissionais: quantidades por função (administrativo, bibliotecário, coordenador, etc.)
- Matrículas: por nível de ensino (infantil, fundamental, médio, EJA) e subnível
- Docentes: por nível de ensino
- Salas: utilizadas, climatizadas, acessíveis
- Transporte: público, estadual, municipal

**Filtros aplicados no pipeline:**

- Região: Nordeste (`NO_REGIAO == "NORDESTE"`) — 9 estados
- Para o MVP da PB: `SG_UF == "PB"`
- Dependência administrativa: Federal (1), Estadual (2), Municipal (3) — exclui privadas
- Situação de funcionamento: Em atividade (1) — exclui fechadas e paralisadas

---

## 2. Dataset de CEPs da Paraíba — LEMA/UFPB

**Pipeline:** `bairro_pipeline`, `municipio_pipeline`
**Camada de destino:** Gold (arquivo de referência)

| Atributo          | Valor                          |
| ----------------- | ------------------------------ |
| Fonte             | Prof. Aléssio Tony — LEMA/UFPB |
| Arquivo           | `data/gold/cep.json`           |
| Formato           | JSON (array de objetos)        |
| Tamanho           | ~213.527 linhas                |
| Cobertura         | Paraíba                        |
| Ano de referência | 2022                           |

**Campos disponíveis:**

- `cep` — CEP (8 dígitos, chave de join com `CO_CEP` do Censo)
- `bairro` — nome do bairro padronizado
- `logradouro` — nome da rua
- `municipio` — nome do município
- `id_mundv` — código IBGE do município (7 dígitos)
- `sg_uf` — sigla do estado
- `latitude` / `longitude` — centróide do logradouro
- `complemento` — complemento do logradouro (lado par/ímpar, trechos)
- `data_inclusao` — data de inclusão no dataset

**Cobertura medida:**

- 14.235 CEPs únicos
- 225 municípios cobertos
- 20,3% das escolas da PB têm bairro identificado via join por CEP
- 79,7% das escolas não têm match (principalmente interior e áreas rurais)

**Limitação:** O dataset cobre principalmente municípios maiores. CEPs rurais e de municípios pequenos do interior da PB têm cobertura reduzida.

---

## 3. Dataset de Escolas Geocodificadas — Gustavo (LEMA/UFPB)

**Pipeline:** `geocode_pipeline`
**Camada de destino:** Silver (arquivo de referência)

| Atributo      | Valor                                                       |
| ------------- | ----------------------------------------------------------- |
| Fonte         | Gustavo — LEMA/UFPB (execução anterior com Google Maps API) |
| Arquivo       | `data/silver/escolas_nordeste_geocoded.parquet`             |
| Formato       | Parquet                                                     |
| Cobertura     | 9 estados do Nordeste                                       |
| API utilizada | Google Maps Geocoding API                                   |

**Campos disponíveis:**

- `CO_ENTIDADE` — código INEP da escola (chave de join)
- `latitude` / `longitude` — coordenadas geográficas

**Cobertura medida:**

- 49.429 registros (Nordeste completo)
- 3.703 escolas da PB com coordenadas válidas (99,1% do total PB)
- 25 escolas com coordenadas placeholder (-999) — não geocodificadas
- 9 escolas sem coordenadas

**Observação:** Este dataset foi gerado em execução anterior com a Google Maps API. O custo de regeneração seria proibitivo. O pipeline atual usa este arquivo como fonte primária de coordenadas, com fallback para geocodificação via API para os registros ausentes.

---

## 4. Indicadores Educacionais INEP — Base dos Dados (BigQuery)

**Pipeline:** `indicadores_base_dos_dados_pipeline`
**Camada de destino:** Silver → Gold

| Atributo             | Valor                                                             |
| -------------------- | ----------------------------------------------------------------- |
| Fonte                | INEP via plataforma Base dos Dados                                |
| Tabela BigQuery      | `basedosdados.br_inep_indicadores_educacionais.escola`            |
| Formato              | BigQuery → Parquet                                                |
| Cobertura            | Brasil completo (filtrado para Nordeste)                          |
| Anos disponíveis     | 2007–2024                                                         |
| Ano utilizado no MVP | 2024 (mais recente)                                               |
| Requisito            | `GOOGLE_BILLING_ID` no `.env`                                     |
| Página oficial       | https://basedosdados.org/dataset/br-inep-indicadores-educacionais |

**Indicadores disponíveis por nível de ensino (EI, EF anos iniciais/finais, EM):**

- `atu_*` — Média de Alunos por Turma
- `had_*` — Média de Horas-Aula Diária
- `dsu_*` — Percentual de Docentes com Curso Superior
- `tdi_*` — Taxa de Distorção Idade-Série
- `taxa_aprovacao_*`, `taxa_reprovacao_*`, `taxa_abandono_*`
- `tnr_*` — Taxa de Não-Resposta
- `afd_*` — Adequação da Formação Docente
- `ied_*` — Irregularidade do Corpo Docente
- `icg_*` — Índice de Complexidade de Gestão da Escola

**Problema de qualidade identificado (EDA):**
O dataset usa `0` como valor sentinela para dados ausentes em campos onde zero é fisicamente impossível:

- `horas_aula_diarias`: 97,3% dos valores são `0` — range real é `[1.4, 22.2]`
- `alunos_por_turma` (ensino médio): 91,4% são `0` — range real é `[0.9, 36.6]`

**Tratamento aplicado:** valores `0` em `horas_aula_diarias` e `alunos_por_turma` são convertidos para `None` no transform. Campos onde `0` é válido (taxas de reprovação/abandono) não são alterados.

---

## 5. Malha de Bairros da Paraíba — IBGE Censo 2022

**Pipeline:** `geo_ingest_pipeline`, `bairro_pipeline`
**Camada de destino:** Bronze → Silver (GeoPackage)

| Atributo               | Valor                                                                             |
| ---------------------- | --------------------------------------------------------------------------------- |
| Fonte                  | Instituto Brasileiro de Geografia e Estatística (IBGE)                            |
| Arquivo local          | `data/bronze/PB_bairros_CD2022/PB_bairros_CD2022.shp`                             |
| Formato                | Shapefile (SHP + DBF + PRJ + SHX + CPG)                                           |
| CRS original           | EPSG:4674 (SIRGAS 2000)                                                           |
| CRS após processamento | EPSG:4326 (WGS84)                                                                 |
| Arquivo Silver         | `data/silver/bairros_pb.gpkg`                                                     |
| Referência             | Censo Demográfico 2022                                                            |
| Página oficial         | https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais |

**Cobertura medida:**

- 257 polígonos de bairros
- 12 municípios com bairros delimitados (de 223 municípios da PB)
- João Pessoa: 64 bairros
- Campina Grande: 60 bairros
- Cabedelo: 24 bairros
- Patos: 23 bairros
- Santa Rita: 18 bairros
- Itabaiana: 16 bairros
- Sumé: 16 bairros
- Bayeux: 14 bairros
- Ingá: 7 bairros
- Santa Luzia: 6 bairros
- Outros 2 municípios: restante

**Limitação crítica:** Apenas 12 dos 223 municípios da PB (5,4%) têm bairros oficialmente delimitados pelo IBGE. O interior da PB não possui essa divisão administrativa formal.

---

## 6. Malha de Setores Censitários da Paraíba — IBGE Censo 2022

**Pipeline:** `geo_ingest_pipeline`, `setor_pipeline`
**Camada de destino:** Bronze → Silver (GeoPackage)

| Atributo               | Valor                                                                             |
| ---------------------- | --------------------------------------------------------------------------------- |
| Fonte                  | Instituto Brasileiro de Geografia e Estatística (IBGE)                            |
| Arquivo local          | `data/bronze/PB_setores_CD2022/PB_setores_CD2022.shp`                             |
| Formato                | Shapefile                                                                         |
| CRS original           | EPSG:4674 (SIRGAS 2000)                                                           |
| CRS após processamento | EPSG:4326 (WGS84)                                                                 |
| Arquivo Silver         | `data/silver/setores_pb.gpkg`                                                     |
| Referência             | Censo Demográfico 2022                                                            |
| Página oficial         | https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais |

**Cobertura medida:**

- 9.639 polígonos de setores censitários
- 223 municípios cobertos (100% da PB)
- 66,7% setores urbanos (6.434)
- 33,2% setores rurais (3.200)
- 0,1% sem classificação (5)
- 36,2% dos setores têm `NM_BAIRRO` preenchido (3.494) — cidades grandes
- 63,8% sem `NM_BAIRRO` (6.145) — interior e áreas rurais

**Tipos de setor:**

- Tipo 0 (comum): 8.724 (90,5%)
- Tipo 1 (aglomerado subnormal): 572 (5,9%)
- Tipo 4 (embarcação): 110 (1,1%)
- Tipo 5 (aldeia indígena): 73 (0,8%)
- Tipo 8 (hospital/clínica): 58 (0,6%)
- Tipo 6 (penitenciária): 19 (0,2%)
- Outros tipos especiais: 83 (0,9%)

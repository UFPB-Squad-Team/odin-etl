# Análise de Granularidades — Módulo de Educação

> Documento técnico sobre as granularidades de análise disponíveis no ODIN,
> cobertura de dados por nível geográfico, e limitações identificadas via EDA.
> Última atualização: Abril/2026

---

## Visão Geral

O projeto ODIN tem como objetivo permitir análise territorial em múltiplos níveis de granularidade:

```
Rua → Bairro → Setor Censitário → Município → Estado
```

Este documento detalha o que está implementado, a cobertura real de cada nível,
as evidências obtidas via análise exploratória dos dados (EDA), e as limitações
que o time deve conhecer antes de desenvolver o frontend e a API.

---

## 1. Estado (Paraíba)

**Status: Cobertura total**

Todos os dados do módulo de educação são filtrados para a Paraíba. O estado é
o escopo do MVP conforme definido na reunião com os professores orientadores
(Abril/2026).

| Métrica                      | Valor      |
| ---------------------------- | ---------- |
| Escolas na PB (Censo 2024)   | 3.737      |
| Escolas no Nordeste (Silver) | 75.054     |
| Cobertura do MVP             | 100% da PB |

**Collection MongoDB:** não existe uma collection separada para estado — os dados
estaduais são derivados das collections de município e setor.

---

## 2. Município

**Status: Cobertura total (225 municípios)**

**Collection MongoDB:** `municipio_indicadores`

| Métrica                               | Valor |
| ------------------------------------- | ----- |
| Municípios na PB                      | 223   |
| Municípios com indicadores no MongoDB | 225   |
| Cobertura                             | ~100% |

A pequena diferença (225 vs 223) ocorre porque o dataset de CEPs do Aléssio
inclui 2 registros com municípios limítrofes ou variações de nome.

**Como funciona:** join por CEP (`CO_CEP` do Censo → `cep` do dataset do Aléssio),
agrupamento por `municipio_cep`. Centróide calculado como média das coordenadas
dos CEPs do município.

**Indicadores disponíveis por município:**

- `total_escolas` — quantidade de escolas
- `total_matriculas` — soma de matrículas (fundamental + médio + infantil)
- `pct_com_internet` — % de escolas com internet
- `pct_com_biblioteca` — % de escolas com biblioteca
- `pct_com_lab_informatica` — % de escolas com laboratório de informática
- `pct_sem_acessibilidade` — % de escolas sem nenhuma acessibilidade

**Limitação:** o centróide do município é calculado como média dos CEPs, não como
centróide geométrico do polígono municipal. Para queries `$geoNear` isso é
suficiente, mas para `$geoWithin` seria necessário o polígono completo (malha
municipal do IBGE — pendente de implementação por limitação do driver GDAL).

---

## 3. Setor Censitário

**Status: Cobertura de 98,7% das escolas geocodificadas**

**Collection MongoDB:** `setor_indicadores`

| Métrica                        | Valor                    |
| ------------------------------ | ------------------------ |
| Total de setores na PB         | 9.639                    |
| Setores com escolas            | 2.243                    |
| Escolas associadas a setores   | 3.687                    |
| Escolas fora de qualquer setor | 16 (0,4%)                |
| Cobertura geográfica           | 100% do território da PB |

**Como funciona:** spatial join geométrico — para cada escola com coordenadas
válidas, verifica em qual polígono de setor censitário ela está contida
(`predicate="within"` via GeoPandas). Usa o shapefile `PB_setores_CD2022.shp`
do IBGE Censo 2022.

**Por que 16 escolas ficam fora?** Coordenadas ligeiramente fora dos polígonos
por imprecisão de geocodificação (escola na borda de um setor) ou erro de
coordenada na fonte. São 0,4% do total — aceitável para o MVP.

**Campos semânticos no documento:**

- `cd_setor` — código único do setor (15 dígitos), chave de upsert
- `nome_area` — bairro oficial se existir, nome do município caso contrário
- `nm_bairro` — nome do bairro (vazio para 63,8% dos setores)
- `nm_municipio` — nome do município
- `situacao` — "Urbana" ou "Rural"
- `tipo_setor` — "comum", "aglomerado_subnormal", etc.
- `tem_bairro_oficial` — boolean
- `geometria` — GeoJSON Polygon (índice `2dsphere`)

**EDA — distribuição dos setores com escolas:**

| Situação | Setores com escolas | %    |
| -------- | ------------------- | ---- |
| Urbana   | ~1.490              | ~66% |
| Rural    | ~753                | ~34% |

**Uso para busca por rua:** o setor censitário é a unidade que habilita a busca
por rua. Quando o usuário digita um endereço, o backend geocodifica para obter
lat/lon e executa:

```js
db.setor_indicadores.findOne({
  geometria: {
    $geoIntersects: {
      $geometry: { type: "Point", coordinates: [lon, lat] },
    },
  },
});
```

Isso retorna os indicadores do setor que contém aquele ponto, independente de
o endereço ter ou não bairro oficial.

---

## 4. Bairro

**Status: Cobertura parcial — apenas 12 municípios (5,4% da PB)**

**Collection MongoDB:** `bairro_indicadores`

| Métrica                                      | Valor                    |
| -------------------------------------------- | ------------------------ |
| Municípios com bairros delimitados pelo IBGE | 12 de 223 (5,4%)         |
| Total de polígonos de bairros                | 257                      |
| Bairros com escolas                          | 194                      |
| Escolas associadas a bairros                 | 792                      |
| Cobertura de escolas                         | 21,4% das geocodificadas |

**Municípios cobertos:**

| Município           | Bairros delimitados |
| ------------------- | ------------------- |
| João Pessoa         | 64                  |
| Campina Grande      | 60                  |
| Cabedelo            | 24                  |
| Patos               | 23                  |
| Santa Rita          | 18                  |
| Itabaiana           | 16                  |
| Sumé                | 16                  |
| Bayeux              | 14                  |
| Ingá                | 7                   |
| Santa Luzia         | 6                   |
| Outros 2 municípios | 9                   |

**Como funciona:** spatial join geométrico com o shapefile `PB_bairros_CD2022.shp`
do IBGE. Cada escola com coordenadas válidas é associada ao polígono de bairro
que a contém.

**Por que a cobertura é baixa?** O IBGE só delimita bairros em municípios que
possuem essa divisão administrativa formal. Municípios pequenos do interior da
PB não têm bairros oficialmente delimitados — não é uma limitação do pipeline,
é uma limitação da fonte de dados.

**Implicação para o produto:** para 78,6% das escolas geocodificadas, não existe
bairro oficial. O nível de granularidade disponível para essas escolas é o
setor censitário (que cobre 98,7% das escolas).

---

## 5. Rua

**Status: Não implementado como unidade de análise**

A rua não é uma unidade de análise com dados próprios — é o ponto de entrada
da busca do usuário. O fluxo correto é:

```
Usuário digita "Rua das Flores, João Pessoa"
    ↓
Backend geocodifica → obtém lat/lon
    ↓
$geoIntersects em setor_indicadores → retorna setor
    ↓
Retorna indicadores do setor (escolas, % internet, etc.)
```

**Dataset de ruas disponível:** o dataset de CEPs do Aléssio tem 14.235 registros
com `logradouro` (nome da rua) + `lat/lon`. Isso pode ser usado como índice de
busca no backend para sugerir ruas ao usuário digitar.

**Cobertura do dataset de ruas:**

- 14.235 logradouros únicos
- 225 municípios
- Concentrado em municípios maiores

**O que falta para implementar busca por rua:**

1. Indexar o dataset de CEPs no MongoDB com índice de texto em `logradouro`
2. Endpoint de autocomplete no backend: `GET /buscar?q=Rua das Flores`
3. Ao selecionar uma rua, geocodificar e fazer `$geoIntersects`

Isso é responsabilidade do backend, não do ETL.

---

## Resumo de Cobertura por Granularidade

| Nível            | Collection MongoDB      | Escolas cobertas | % do total PB | Observação                               |
| ---------------- | ----------------------- | ---------------- | ------------- | ---------------------------------------- |
| Estado           | —                       | 3.737            | 100%          | Derivado das outras collections          |
| Município        | `municipio_indicadores` | ~3.726           | ~99,7%        | 225 municípios                           |
| Setor Censitário | `setor_indicadores`     | 3.687            | 98,7%         | 2.243 setores                            |
| Bairro           | `bairro_indicadores`    | 792              | 21,2%         | Só 12 municípios                         |
| Rua              | —                       | —                | —             | Ponto de entrada, não unidade de análise |

---

## Hierarquia Geográfica e Relacionamentos

```
Estado (PB)
    └── Município (225 no MongoDB)
            └── Setor Censitário (2.243 com escolas)
                    └── Bairro (194 com escolas — só cidades grandes)
                            └── Rua (busca via CEP do Aléssio)
```

**Relacionamentos entre collections:**

```
setor_indicadores.co_municipio == municipio_indicadores.municipioIdIbge
bairro_indicadores.municipioIdIbge == municipio_indicadores.municipioIdIbge
escolas.municipioIdIbge == municipio_indicadores.municipioIdIbge
```

O `cd_setor` do IBGE tem 15 dígitos onde os primeiros 7 são o código do município:
`CD_SETOR[0:7] == CD_MUN` — isso permite derivar o município a partir do setor
sem join adicional.

---

## Limitações Conhecidas e Recomendações

### Limitação 1 — Bairros só em cidades grandes

**Causa:** O IBGE não delimita bairros em municípios sem essa divisão administrativa.
**Impacto:** 78,6% das escolas não têm bairro oficial.
**Recomendação:** Usar setor censitário como proxy de bairro para o interior.
No frontend, exibir "Setor X — Município Y" quando não houver bairro oficial.

### Limitação 2 — 16 escolas fora de qualquer setor

**Causa:** Imprecisão de geocodificação — coordenadas na borda de polígonos.
**Impacto:** 0,4% das escolas sem setor atribuído.
**Recomendação:** Aplicar buffer de 50m no spatial join para capturar escolas
na borda. Implementação futura.

### Limitação 3 — Centróide de município calculado por média de CEPs

**Causa:** Malha municipal do IBGE não pôde ser salva como GeoParquet por
limitação do driver GDAL no ambiente atual.
**Impacto:** Queries `$geoWithin` por município não funcionam com precisão.
**Recomendação:** Instalar GDAL com suporte a Parquet ou usar GeoPackage para
a malha municipal também.

### Limitação 4 — Indicadores sentinela no dataset da Base dos Dados

**Causa:** O INEP usa `0` como valor sentinela para dados ausentes em alguns campos.
**Impacto:** Médias de `horas_aula_diarias` e `alunos_por_turma` seriam distorcidas.
**Tratamento aplicado:** Valores `0` nesses campos são convertidos para `None`
no transform. Ver `FONTES_DE_DADOS.md` para detalhes.

### Limitação 5 — Dataset de CEPs com cobertura parcial

**Causa:** O dataset do Prof. Aléssio cobre principalmente municípios maiores.
**Impacto:** 79,7% das escolas não têm bairro identificado via CEP.
**Recomendação:** Para a agregação por bairro, usar o spatial join com shapefile
IBGE (já implementado) em vez do join por CEP.

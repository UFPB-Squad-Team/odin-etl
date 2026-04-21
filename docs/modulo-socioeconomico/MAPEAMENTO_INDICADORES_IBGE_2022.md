# Mapeamento de Indicadores Socioeconômicos — IBGE Censo 2022

> Documento de planejamento do módulo socioeconômico do ODIN-ETL.
> Última atualização: Abril/2026
> Autor: Brenno Henrique / LEMA-UFPB

---

## Contexto

Os professores orientadores solicitaram que o MVP inclua, além dos indicadores
educacionais já implementados, **indicadores socioeconômicos do IBGE Censo 2022**
agregados pelas mesmas granularidades geográficas já disponíveis no projeto.

Este documento mapeia:

1. Quais datasets o IBGE disponibiliza por setor censitário, bairro e município
2. Quais indicadores derivados são possíveis de calcular
3. A granularidade de cada indicador
4. A estratégia de implementação

---

## Fonte de Dados

**IBGE — Agregados por Setores Censitários (Censo Demográfico 2022)**

O IBGE disponibiliza os mesmos datasets em **quatro granularidades**:

| Granularidade          | URL base no FTP                                    |
| ---------------------- | -------------------------------------------------- |
| Setor Censitário       | `ftp.ibge.gov.br/.../Agregados_por_Setor_csv/`     |
| Bairro                 | `ftp.ibge.gov.br/.../Agregados_por_Bairro_csv/`    |
| Município              | `ftp.ibge.gov.br/.../Agregados_por_Municipio_csv/` |
| Distrito / Subdistrito | `ftp.ibge.gov.br/.../Agregados_por_Distrito_csv/`  |

**Importante:** os arquivos de bairro do IBGE cobrem apenas os 12 municípios da
PB com bairros oficialmente delimitados — mesma limitação já documentada no
módulo de educação. Para cobertura total da PB, usar setor censitário.

**Dicionário de dados oficial:**
`ftp.ibge.gov.br/.../dicionario_de_dados_agregados_por_setores_censitarios_20250417.xlsx`

---

## Datasets Disponíveis

O IBGE organiza os dados em **9 arquivos temáticos** por granularidade:

| Arquivo                      | Tema                                        | Nº de variáveis |
| ---------------------------- | ------------------------------------------- | --------------- |
| `basico`                     | Totais gerais (população, domicílios)       | 7               |
| `demografia`                 | Estrutura etária e sexo                     | 36              |
| `cor_ou_raca`                | Distribuição por cor/raça                   | 95              |
| `caracteristicas_domicilio1` | Tipo de domicílio, moradores, espécie       | 89              |
| `caracteristicas_domicilio2` | Abastecimento de água, banheiros, esgoto    | 406             |
| `caracteristicas_domicilio3` | Esgoto (cont.), lixo, rede elétrica         | 148             |
| `alfabetizacao`              | Alfabetização por faixa etária e parentesco | 362             |
| `parentesco`                 | Estrutura familiar e unidades domésticas    | 182             |
| `obitos`                     | Óbitos domiciliares (jan/2019 a jul/2022)   | 93              |

**Total: ~1.418 variáveis brutas** — a maioria são desagregações cruzadas
(ex: abastecimento de água × cor/raça × sexo). Os indicadores úteis para o
ODIN são derivados dessas variáveis brutas.

---

## Indicadores Derivados — Mapeamento Completo

### 1. POPULAÇÃO E DOMICÍLIOS (fonte: `basico`)

| Indicador                                | Variáveis IBGE | Fórmula | Granularidade              |
| ---------------------------------------- | -------------- | ------- | -------------------------- |
| `total_populacao`                        | V0001          | direto  | Setor / Bairro / Município |
| `total_domicilios`                       | V0002          | direto  | Setor / Bairro / Município |
| `total_domicilios_particulares`          | V0003          | direto  | Setor / Bairro / Município |
| `total_domicilios_coletivos`             | V0004          | direto  | Setor / Bairro / Município |
| `media_moradores_por_domicilio`          | V0005          | direto  | Setor / Bairro / Município |
| `total_domicilios_particulares_ocupados` | V0007          | direto  | Setor / Bairro / Município |

---

### 2. ESTRUTURA ETÁRIA (fonte: `demografia`)

| Indicador            | Variáveis IBGE                         | Fórmula               | Granularidade              |
| -------------------- | -------------------------------------- | --------------------- | -------------------------- |
| `total_moradores`    | V01006                                 | direto                | Setor / Bairro / Município |
| `total_masculino`    | V01007                                 | direto                | Setor / Bairro / Município |
| `total_feminino`     | V01008                                 | direto                | Setor / Bairro / Município |
| `pct_masculino`      | V01007, V01006                         | V01007 / V01006 × 100 | Setor / Bairro / Município |
| `pop_0_4_anos`       | V01009 + V01027                        | soma masc + fem       | Setor / Bairro / Município |
| `pop_5_9_anos`       | V01010 + V01028                        | soma masc + fem       | Setor / Bairro / Município |
| `pop_10_14_anos`     | V01011 + V01029                        | soma masc + fem       | Setor / Bairro / Município |
| `pop_15_19_anos`     | V01012 + V01030                        | soma masc + fem       | Setor / Bairro / Município |
| `pop_20_24_anos`     | V01013 + V01031                        | soma masc + fem       | Setor / Bairro / Município |
| `pop_25_39_anos`     | V01014..V01016 + V01032..V01034        | soma faixas           | Setor / Bairro / Município |
| `pop_40_59_anos`     | V01017..V01020 + V01035..V01038        | soma faixas           | Setor / Bairro / Município |
| `pop_60_anos_mais`   | V01021..V01026 + V01039..V01041        | soma faixas           | Setor / Bairro / Município |
| `pct_criancas_0_9`   | pop_0_4 + pop_5_9, V01006              | / total × 100         | Setor / Bairro / Município |
| `pct_idosos_60_mais` | pop_60_mais, V01006                    | / total × 100         | Setor / Bairro / Município |
| `razao_dependencia`  | (pop_0_14 + pop_60+) / pop_15_59 × 100 | calculado             | Setor / Bairro / Município |

---

### 3. COR OU RAÇA (fonte: `cor_ou_raca`)

| Indicador         | Variáveis IBGE          | Fórmula       | Granularidade              |
| ----------------- | ----------------------- | ------------- | -------------------------- |
| `total_branca`    | V01317                  | direto        | Setor / Bairro / Município |
| `total_preta`     | V01318                  | direto        | Setor / Bairro / Município |
| `total_amarela`   | V01319                  | direto        | Setor / Bairro / Município |
| `total_parda`     | V01320                  | direto        | Setor / Bairro / Município |
| `total_indigena`  | V01321                  | direto        | Setor / Bairro / Município |
| `pct_branca`      | V01317, V01006          | / total × 100 | Setor / Bairro / Município |
| `pct_preta`       | V01318, V01006          | / total × 100 | Setor / Bairro / Município |
| `pct_parda`       | V01320, V01006          | / total × 100 | Setor / Bairro / Município |
| `pct_preta_parda` | V01318 + V01320, V01006 | / total × 100 | Setor / Bairro / Município |
| `pct_indigena`    | V01321, V01006          | / total × 100 | Setor / Bairro / Município |

---

### 4. SANEAMENTO — ABASTECIMENTO DE ÁGUA (fonte: `caracteristicas_domicilio2`)

| Indicador                   | Variáveis IBGE                                    | Fórmula           | Granularidade              |
| --------------------------- | ------------------------------------------------- | ----------------- | -------------------------- |
| `dom_agua_rede_geral`       | V00111                                            | direto            | Setor / Bairro / Município |
| `dom_agua_poco_artesiano`   | V00112                                            | direto            | Setor / Bairro / Município |
| `dom_agua_poco_raso`        | V00113                                            | direto            | Setor / Bairro / Município |
| `dom_agua_fonte_nascente`   | V00114                                            | direto            | Setor / Bairro / Município |
| `dom_agua_carro_pipa`       | V00115                                            | direto            | Setor / Bairro / Município |
| `dom_agua_chuva`            | V00116                                            | direto            | Setor / Bairro / Município |
| `dom_agua_rio_acude`        | V00117                                            | direto            | Setor / Bairro / Município |
| `dom_agua_outra`            | V00118                                            | direto            | Setor / Bairro / Município |
| `pct_agua_rede_geral`       | V00111, V00001 (dom)                              | / total dom × 100 | Setor / Bairro / Município |
| `pct_agua_inadequada`       | V00113+V00114+V00115+V00116+V00117+V00118, V00001 | / total × 100     | Setor / Bairro / Município |
| `pct_agua_encanada_interna` | V00199, V00001                                    | / total × 100     | Setor / Bairro / Município |

---

### 5. SANEAMENTO — ESGOTO (fonte: `caracteristicas_domicilio2` e `3`)

| Indicador                     | Variáveis IBGE                             | Fórmula           | Granularidade              |
| ----------------------------- | ------------------------------------------ | ----------------- | -------------------------- |
| `dom_esgoto_rede_geral`       | V00309                                     | direto            | Setor / Bairro / Município |
| `dom_esgoto_fossa_septica`    | V00310                                     | direto            | Setor / Bairro / Município |
| `dom_esgoto_fossa_rudimentar` | V00311                                     | direto            | Setor / Bairro / Município |
| `dom_esgoto_vala`             | V00313                                     | direto            | Setor / Bairro / Município |
| `dom_esgoto_rio_lago`         | V00314                                     | direto            | Setor / Bairro / Município |
| `dom_esgoto_outro`            | V00315                                     | direto            | Setor / Bairro / Município |
| `dom_sem_banheiro_sanitario`  | V00316                                     | direto            | Setor / Bairro / Município |
| `pct_esgoto_rede_geral`       | V00309, V00001                             | / total dom × 100 | Setor / Bairro / Município |
| `pct_esgoto_inadequado`       | V00311+V00313+V00314+V00315+V00316, V00001 | / total × 100     | Setor / Bairro / Município |
| `pct_sem_banheiro`            | V00238, V00001                             | / total × 100     | Setor / Bairro / Município |

---

### 6. SANEAMENTO — COLETA DE LIXO (fonte: `caracteristicas_domicilio3`)

| Indicador                   | Variáveis IBGE                      | Fórmula           | Granularidade              |
| --------------------------- | ----------------------------------- | ----------------- | -------------------------- |
| `dom_lixo_coletado_servico` | V00397                              | direto            | Setor / Bairro / Município |
| `dom_lixo_cacamba`          | V00398                              | direto            | Setor / Bairro / Município |
| `dom_lixo_queimado`         | V00399                              | direto            | Setor / Bairro / Município |
| `dom_lixo_enterrado`        | V00400                              | direto            | Setor / Bairro / Município |
| `dom_lixo_terreno_baldio`   | V00401                              | direto            | Setor / Bairro / Município |
| `dom_lixo_outro`            | V00402                              | direto            | Setor / Bairro / Município |
| `pct_lixo_coletado`         | V00397 + V00398, V00001             | / total dom × 100 | Setor / Bairro / Município |
| `pct_lixo_inadequado`       | V00399+V00400+V00401+V00402, V00001 | / total × 100     | Setor / Bairro / Município |

---

### 7. HABITAÇÃO — TIPO E CONDIÇÕES (fonte: `caracteristicas_domicilio1`)

| Indicador                 | Variáveis IBGE                            | Fórmula            | Granularidade              |
| ------------------------- | ----------------------------------------- | ------------------ | -------------------------- |
| `dom_tipo_casa`           | V00047                                    | direto             | Setor / Bairro / Município |
| `dom_tipo_apartamento`    | V00049                                    | direto             | Setor / Bairro / Município |
| `dom_tipo_cortico`        | V00050                                    | direto             | Setor / Bairro / Município |
| `dom_tipo_improvisado`    | V00002 (DPIO)                             | direto             | Setor / Bairro / Município |
| `pct_dom_casa`            | V00047, V00001                            | / total dom × 100  | Setor / Bairro / Município |
| `pct_dom_apartamento`     | V00049, V00001                            | / total dom × 100  | Setor / Bairro / Município |
| `pct_dom_improvisado`     | V00002, V00003                            | / total part × 100 | Setor / Bairro / Município |
| `dom_1_morador`           | V00017                                    | direto             | Setor / Bairro / Município |
| `dom_5_ou_mais_moradores` | V00021+V00022+V00023+V00024+V00025+V00026 | soma               | Setor / Bairro / Município |
| `pct_dom_superlotado`     | dom_5_mais, V00001                        | / total dom × 100  | Setor / Bairro / Município |

---

### 8. ALFABETIZAÇÃO (fonte: `alfabetizacao`)

> **Nota:** O Censo 2022 não coletou renda por setor censitário (apenas no
> questionário amostral, não no universo). Alfabetização é o principal proxy
> de capital humano disponível no universo.

| Indicador                         | Variáveis IBGE                   | Fórmula       | Granularidade              |
| --------------------------------- | -------------------------------- | ------------- | -------------------------- |
| `total_alfabetizados_15_mais`     | V00644..V00660 (soma faixas 15+) | soma          | Setor / Bairro / Município |
| `total_nao_alfabetizados_15_mais` | complemento das faixas 15+       | calculado     | Setor / Bairro / Município |
| `pct_alfabetizados_15_mais`       | alfabetizados_15+, pop_15+       | / total × 100 | Setor / Bairro / Município |
| `taxa_analfabetismo_15_mais`      | 100 - pct_alfabetizados          | calculado     | Setor / Bairro / Município |
| `pct_alfabetizados_10_mais`       | faixas 10+                       | calculado     | Setor / Bairro / Município |
| `taxa_analfabetismo_10_mais`      | complemento                      | calculado     | Setor / Bairro / Município |

---

### 9. ESTRUTURA FAMILIAR (fonte: `parentesco`)

| Indicador                      | Variáveis IBGE                          | Fórmula       | Granularidade              |
| ------------------------------ | --------------------------------------- | ------------- | -------------------------- |
| `total_responsaveis_domicilio` | V01042                                  | direto        | Setor / Bairro / Município |
| `responsaveis_femininos`       | V01043 (cônjuge fem) + derivados        | calculado     | Setor / Bairro / Município |
| `pct_responsavel_feminino`     | resp_fem, V01042                        | / total × 100 | Setor / Bairro / Município |
| `dom_unipessoal`               | V01042 (responsável sem cônjuge/filhos) | derivado      | Setor / Bairro / Município |
| `dom_casal_com_filhos`         | derivado de parentesco                  | calculado     | Setor / Bairro / Município |
| `dom_monoparental`             | derivado de parentesco                  | calculado     | Setor / Bairro / Município |

---

### 10. ÓBITOS (fonte: `obitos`)

| Indicador                         | Variáveis IBGE                  | Fórmula         | Granularidade              |
| --------------------------------- | ------------------------------- | --------------- | -------------------------- |
| `total_obitos_2019_2022`          | V01224 (domicílios com óbito)   | direto          | Setor / Bairro / Município |
| `total_obitos_masculinos`         | V01226                          | direto          | Setor / Bairro / Município |
| `total_obitos_femininos`          | V01227                          | direto          | Setor / Bairro / Município |
| `obitos_0_4_anos`                 | V01228 + V01246                 | soma masc + fem | Setor / Bairro / Município |
| `obitos_5_19_anos`                | V01229..V01231 + V01247..V01249 | soma faixas     | Setor / Bairro / Município |
| `obitos_60_mais`                  | V01238..V01245 + V01256..V01263 | soma faixas     | Setor / Bairro / Município |
| `taxa_mortalidade_infantil_proxy` | obitos_0_4 / pop_0_4 × 1000     | proxy           | Setor / Bairro / Município |

---

## Indicadores NÃO Disponíveis no Universo 2022

> Atenção: o Censo 2022 tem dois questionários — **universo** (aplicado a todos)
> e **amostra** (aplicado a ~10% dos domicílios). Os dados por setor censitário
> são do **universo**, que é mais limitado.

| Indicador desejado                | Situação                           | Alternativa                                           |
| --------------------------------- | ---------------------------------- | ----------------------------------------------------- |
| **Renda domiciliar**              | ❌ Não disponível no universo 2022 | Usar dados de 2010 (desatualizados) ou PNAD municipal |
| **Renda per capita**              | ❌ Não disponível no universo 2022 | Idem                                                  |
| **Escolaridade (anos de estudo)** | ❌ Não disponível no universo 2022 | Alfabetização como proxy                              |
| **Nível de instrução**            | ❌ Não disponível no universo 2022 | Alfabetização como proxy                              |
| **Ocupação / emprego**            | ❌ Não disponível no universo 2022 | RAIS/CAGED por município                              |
| **Energia elétrica**              | ❌ Não coletado no Censo 2022      | Não disponível                                        |

**Nota crítica sobre renda:** O IBGE coletou renda no Censo 2022, mas apenas
no questionário amostral. Os resultados da amostra por setor censitário ainda
**não foram publicados** (previsão: 2025-2026). Quando publicados, estarão em
`Agregados_por_Setor_Amostra_csv/`. Monitorar o FTP do IBGE.

---

## Granularidades Disponíveis no ODIN vs. IBGE

| Granularidade ODIN                        | Granularidade IBGE | Compatibilidade               | Chave de join                             |
| ----------------------------------------- | ------------------ | ----------------------------- | ----------------------------------------- |
| `setor_indicadores` (cd_setor)            | Setor Censitário   | ✅ Direta                     | `CD_SETOR` == `cd_setor`                  |
| `bairro_indicadores` (bairro + municipio) | Bairro             | ⚠️ Parcial (12 municípios PB) | `CD_BAIRRO` + `CD_MUN`                    |
| `municipio_indicadores` (municipioIdIbge) | Município          | ✅ Direta                     | `CD_MUN` == `municipioIdIbge` (7 dígitos) |

**Estratégia recomendada:**

- Para setor e município: join direto pelo código IBGE
- Para bairro: join por `CD_BAIRRO` + `CD_MUN` (cobertura limitada a 12 municípios)

---

## Indicadores Prioritários para o MVP (Seleção)

Dado o prazo (final de maio/2026), recomenda-se implementar os indicadores de
maior impacto analítico primeiro:

### Prioridade 1 — Essenciais (implementar primeiro)

| Indicador                       | Tema             | Por quê                           |
| ------------------------------- | ---------------- | --------------------------------- |
| `total_populacao`               | População        | Base para todos os outros         |
| `media_moradores_por_domicilio` | Habitação        | Proxy de adensamento              |
| `pct_idosos_60_mais`            | Estrutura etária | Relevante para políticas públicas |
| `pct_criancas_0_9`              | Estrutura etária | Correlaciona com demanda escolar  |
| `pct_preta_parda`               | Raça             | Indicador de equidade             |
| `pct_agua_rede_geral`           | Saneamento       | Acesso a serviço básico           |
| `pct_esgoto_rede_geral`         | Saneamento       | Acesso a serviço básico           |
| `pct_lixo_coletado`             | Saneamento       | Acesso a serviço básico           |
| `taxa_analfabetismo_15_mais`    | Educação         | Proxy de capital humano           |
| `pct_responsavel_feminino`      | Família          | Indicador de vulnerabilidade      |

### Prioridade 2 — Complementares

| Indicador                         | Tema                      |
| --------------------------------- | ------------------------- |
| `pct_dom_improvisado`             | Habitação precária        |
| `pct_dom_superlotado`             | Adensamento               |
| `pct_agua_inadequada`             | Vulnerabilidade hídrica   |
| `pct_esgoto_inadequado`           | Vulnerabilidade sanitária |
| `pct_lixo_inadequado`             | Vulnerabilidade ambiental |
| `razao_dependencia`               | Estrutura etária          |
| `total_obitos_2019_2022`          | Mortalidade               |
| `taxa_mortalidade_infantil_proxy` | Saúde infantil            |

### Prioridade 3 — Pós-MVP

| Indicador          | Tema           | Observação                            |
| ------------------ | -------------- | ------------------------------------- |
| Renda domiciliar   | Socioeconômico | Aguardar publicação da amostra 2022   |
| Nível de instrução | Educação       | Aguardar publicação da amostra 2022   |
| Ocupação/emprego   | Trabalho       | Fonte alternativa: RAIS por município |

---

## Estratégia de Implementação

### Novo job: `socioeconomico_pipeline`

```
src/jobs/
└── socioeconomico_jobs/
    ├── __init__.py
    ├── main.py                          # Orquestrador
    └── ibge_censo_pipeline/
        ├── __init__.py
        ├── main.py
        └── etl/
            ├── extract.py              # Download dos ZIPs do FTP IBGE
            ├── transform.py            # Cálculo dos indicadores derivados
            └── load.py                 # Upsert no MongoDB
```

### Collections MongoDB novas

| Collection                 | Chave única           | Índice geo             | Descrição                      |
| -------------------------- | --------------------- | ---------------------- | ------------------------------ |
| `setor_socioeconomico`     | `cd_setor`            | `geometria` (2dsphere) | Indicadores IBGE por setor     |
| `bairro_socioeconomico`    | `{cd_bairro, cd_mun}` | `geometria` (2dsphere) | Indicadores IBGE por bairro    |
| `municipio_socioeconomico` | `cd_mun`              | `centroide` (2dsphere) | Indicadores IBGE por município |

**Alternativa:** enriquecer as collections existentes (`setor_indicadores`,
`bairro_indicadores`, `municipio_indicadores`) com um bloco `socioeconomico`
aninhado. Isso simplifica as queries da API mas aumenta o tamanho dos documentos.

### Arquivos a baixar do FTP IBGE (PB)

Para o MVP da PB, baixar apenas os arquivos da PB (quando disponíveis) ou
filtrar o arquivo nacional pelo código de UF `CD_UF == 25`:

```
Agregados_por_setores_basico_BR_20250417.zip          (~13 MB)
Agregados_por_setores_demografia_BR.zip
Agregados_por_setores_cor_ou_raca_BR.zip
Agregados_por_setores_caracteristicas_domicilio2_BR_20250417.zip
Agregados_por_setores_caracteristicas_domicilio3_BR_20250417.zip
Agregados_por_setores_alfabetizacao_BR.zip
Agregados_por_setores_obitos_BR.zip
```

Mesmos arquivos para `Agregados_por_municipios_*` e `Agregados_por_bairros_*`.

### Chave de join com dados educacionais

```
setor_indicadores.cd_setor == setor_socioeconomico.cd_setor
municipio_indicadores.municipioIdIbge == municipio_socioeconomico.cd_mun (7 dígitos)
```

---

## Resumo Executivo

O IBGE disponibiliza dados do Censo 2022 nas mesmas granularidades que o ODIN
já usa (setor, bairro, município). Os dados cobrem **população, estrutura etária,
cor/raça, saneamento (água, esgoto, lixo), habitação, alfabetização, estrutura
familiar e óbitos**.

**O que não está disponível:** renda, escolaridade e emprego — esses dados foram
coletados apenas no questionário amostral, cujos resultados por setor ainda não
foram publicados pelo IBGE.

**Recomendação para o MVP:** implementar os 10 indicadores de Prioridade 1,
que cobrem os temas mais relevantes para análise de políticas públicas e têm
join direto com as collections educacionais existentes.

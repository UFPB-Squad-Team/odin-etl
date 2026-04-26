# EDA Integrada — Educação × Socioeconômico nos Municípios da PB

> **Módulo:** Integração Educação + Socioeconômico — ODIN-ETL  
> **Escopo:** 223 municípios da Paraíba  
> **Data:** Abril/2026  
> **Fontes:** IBGE Censo Demográfico 2022 + INEP Censo Escolar 2024  
> **Variáveis:** 10 indicadores socioeconômicos + 10 indicadores educacionais

---

## Por que esta análise importa

Os dados de educação e socioeconômicos da PB existem em fontes separadas —
INEP e IBGE — e nunca foram cruzados sistematicamente no nível municipal.
Esta EDA é a primeira vez que esses dois universos são integrados para os
223 municípios paraibanos, e os resultados justificam diretamente o projeto ODIN.

**O que descobrimos:** vulnerabilidade não é unidimensional. Um município pode
ter internet em 100% das escolas e ainda assim ter 30% de analfabetismo adulto.
Outro pode ter boa infraestrutura escolar mas zero esgoto nos domicílios.
Só a visão integrada revela esses paradoxos — e é exatamente isso que o ODIN
vai expor para gestores e pesquisadores.

---

## Dataset Integrado

| Dimensão       | Fonte                   | Variáveis                                                                                                                                                                                                    |
| -------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Socioeconômico | IBGE Censo 2022         | total_populacao, media_moradores, pct_criancas_0_9, pct_idosos_60_mais, pct_preta_parda, pct_agua_rede_geral, pct_esgoto_rede_geral, pct_lixo_coletado, taxa_analfabetismo_15_mais, pct_responsavel_feminino |
| Educacional    | INEP Censo Escolar 2024 | total_escolas, pct_escolas_rurais, total_matriculas_fund, mat_eja, pct_escola_internet, pct_escola_biblioteca, pct_escola_lab_info, pct_escola_agua, pct_escola_esgoto, pct_escola_lixo                      |

**Cobertura:** 223/223 municípios com dados completos em ambas as fontes.

---

## Parte 1 — Municípios Prioritários: como está a educação?

Os 5 municípios identificados como prioritários na validação socioeconômica
foram investigados em detalhe. A média da PB é usada como referência.

**Médias PB para referência:**

- Internet nas escolas: 93%
- Biblioteca nas escolas: 31%
- Lab. informática: 23%
- Esgoto nas escolas: 38%
- Analfabetismo adulto: 22.5%

### Algodão de Jandaíra — menor município, 0% água, 29.9% analfabetismo

| Indicador              | Valor          | vs. PB              |
| ---------------------- | -------------- | ------------------- |
| População              | 2.953          | —                   |
| Escolas                | 8 (38% rurais) | —                   |
| Internet nas escolas   | 100%           | +7pp acima da média |
| Biblioteca nas escolas | 17%            | -14pp abaixo        |
| Lab. informática       | 17%            | -6pp abaixo         |
| Esgoto nas escolas     | 17%            | -21pp abaixo        |
| Analfabetismo adulto   | 29.9%          | +7.4pp acima        |

**Insight:** Tem internet em todas as escolas, mas apenas 1 em 6 tem biblioteca.
O analfabetismo adulto alto (30%) indica que gerações anteriores não tiveram
acesso à educação — o problema não é a escola atual, é o legado histórico.

### Alcantil — 0% água encanada, 19.9% analfabetismo

| Indicador              | Valor          | vs. PB           |
| ---------------------- | -------------- | ---------------- |
| Escolas                | 8 (50% rurais) | —                |
| Internet nas escolas   | 88%            | -5pp             |
| Biblioteca nas escolas | 38%            | +7pp acima       |
| Lab. informática       | **75%**        | **+52pp acima**  |
| Esgoto nas escolas     | **0%**         | **-38pp abaixo** |
| Analfabetismo adulto   | 19.9%          | -2.6pp           |

**Insight paradoxal:** Alcantil tem 75% das escolas com laboratório de
informática — muito acima da média — mas zero esgoto nas escolas e zero
água encanada nos domicílios. Investimento em tecnologia educacional sem
infraestrutura básica. Esse tipo de desequilíbrio só aparece com dados integrados.

### Bom Sucesso — 24.5% idosos, forte êxodo rural

| Indicador              | Valor          | vs. PB          |
| ---------------------- | -------------- | --------------- |
| Escolas                | 6 (17% rurais) | —               |
| Internet nas escolas   | 100%           | +7pp            |
| Biblioteca nas escolas | **67%**        | **+36pp acima** |
| Lab. informática       | 33%            | +10pp           |
| Esgoto nas escolas     | 50%            | +12pp           |
| Analfabetismo adulto   | 25.2%          | +2.7pp          |

**Insight:** Apesar do alto analfabetismo adulto e população envelhecida,
as escolas de Bom Sucesso têm infraestrutura acima da média. O problema
educacional aqui é geracional — adultos que não tiveram acesso à escola,
não a qualidade das escolas atuais.

### São Sebastião de Lagoa de Roça — maior % de escolas rurais (70%)

| Indicador              | Valor           | vs. PB           |
| ---------------------- | --------------- | ---------------- |
| Escolas                | 20 (70% rurais) | —                |
| Internet nas escolas   | 85%             | -8pp             |
| Biblioteca nas escolas | 15%             | -16pp            |
| Lab. informática       | **5%**          | **-18pp abaixo** |
| Esgoto nas escolas     | 30%             | -8pp             |
| Analfabetismo adulto   | 18.6%           | -3.9pp           |

**Insight:** 70% de escolas rurais e apenas 5% com laboratório de informática.
Escolas rurais têm sistematicamente menos recursos — esse padrão se repete
em toda a PB e é confirmado pelas correlações da Parte 2.

---

## Parte 2 — Correlações Cruzadas: Educação × Socioeconômico

**Método:** Correlação de Pearson com teste de significância.  
`***` p<0.001 | `**` p<0.01 | `*` p<0.05 | `n.s.` não significativo

### Resultados

| Par de indicadores                   | r          | Sig.     | Interpretação                            |
| ------------------------------------ | ---------- | -------- | ---------------------------------------- |
| Esgoto escolar × esgoto domiciliar   | +0.753     | \*\*\*   | Fortíssima — mesma infraestrutura        |
| Lixo escolar × lixo domiciliar       | +0.484     | \*\*\*   | Forte — coleta de lixo é sistêmica       |
| % escolas rurais × analfabetismo     | +0.333     | \*\*\*   | Mais escolas rurais = mais analfabetismo |
| EJA × analfabetismo adulto           | -0.294     | \*\*\*   | Mais EJA onde há mais analfabetismo      |
| % escolas rurais × água domiciliar   | -0.279     | \*\*\*   | Mais rural = menos água encanada         |
| Biblioteca × analfabetismo           | -0.247     | \*\*\*   | Mais biblioteca = menos analfabetismo    |
| Lab. informática × analfabetismo     | -0.184     | \*\*     | Mais lab = menos analfabetismo           |
| **Internet escolar × analfabetismo** | **-0.024** | **n.s.** | **Sem relação — ver paradoxo**           |
| Água escolar × água domiciliar       | -0.070     | n.s.     | Sem relação — ver explicação             |

### Interpretações detalhadas

**Esgoto escolar × esgoto domiciliar (r = +0.753) — a correlação mais forte**

Municípios com bom esgoto nos domicílios também têm bom esgoto nas escolas,
e vice-versa. Isso confirma que saneamento é uma questão de infraestrutura
municipal — ou o município tem rede de esgoto ou não tem, e isso afeta
domicílios e escolas igualmente.

_Valor de negócio:_ Investir em rede de esgoto municipal beneficia
simultaneamente a saúde pública e as condições das escolas. Políticas
setoriais isoladas (só escola ou só domicílio) são menos eficientes.

**% escolas rurais × analfabetismo adulto (r = +0.333, p<0.001)**

Municípios com mais escolas rurais têm mais analfabetismo adulto. Isso não
significa que escolas rurais causam analfabetismo — significa que municípios
mais rurais têm historicamente menos acesso à educação. As gerações atuais
de adultos analfabetos cresceram sem escolas acessíveis.

_Valor de negócio:_ Municípios com alta proporção de escolas rurais são
candidatos prioritários para programas de EJA (Educação de Jovens e Adultos)
e alfabetização de adultos.

**EJA × analfabetismo adulto (r = -0.294, p<0.001)**

Municípios com mais matrículas em EJA têm menos analfabetismo. A relação
negativa pode parecer contraintuitiva, mas faz sentido: municípios que
investem em EJA conseguem reduzir o analfabetismo ao longo do tempo.

_Valor de negócio:_ EJA é uma política eficaz. Municípios com alto
analfabetismo e baixa oferta de EJA são os que mais precisam de expansão
desse programa.

**O Paradoxo da Internet (r = -0.024, n.s.)**

Internet nas escolas não tem nenhuma relação com analfabetismo adulto.
Municípios com 30% de analfabetismo têm a mesma taxa de internet escolar
(93-94%) que municípios com 6% de analfabetismo.

Isso revela uma política pública bem-sucedida de universalização de
conectividade escolar — mas também mostra que conectividade sozinha não
resolve o analfabetismo adulto, que é um problema de gerações anteriores.

_Valor de negócio:_ Não use internet escolar como proxy de qualidade
educacional. É um indicador de infraestrutura, não de resultado. O ODIN
deve apresentar os dois separadamente para evitar conclusões equivocadas.

**Água escolar × água domiciliar (r = -0.070, n.s.)**

Diferente do esgoto, a água nas escolas não correlaciona com a água nos
domicílios. Isso provavelmente reflete que escolas têm acesso a cisternas
e outras fontes alternativas independentemente da rede municipal.

_Valor de negócio:_ Água potável nas escolas é um indicador mais robusto
que água nos domicílios para avaliar condições de saúde escolar — as escolas
conseguem garantir água mesmo onde a rede domiciliar é precária.

---

## Parte 3 — Grupos de Vulnerabilidade por Quartil de Analfabetismo

**Método:** Kruskal-Wallis comparando Q1 (menor analfabetismo, <17%) vs.
Q4 (maior analfabetismo, >27%) em todos os indicadores.

**Grupos:**

- Q1 baixo (<17%): 59 municípios
- Q2 médio-baixo (17-23%): 53 municípios
- Q3 médio-alto (23-27%): 55 municípios
- Q4 alto (>27%): 56 municípios

| Indicador            | Q1 (baixo) | Q4 (alto) | Diferença   | Sig.     |
| -------------------- | ---------- | --------- | ----------- | -------- |
| Esgoto nas escolas   | 49.4%      | 26.8%     | **-22.6pp** | \*\*\*   |
| Esgoto domiciliar    | 31.7%      | 14.5%     | **-17.2pp** | \*\*\*   |
| Água domiciliar      | 48.3%      | 34.7%     | -13.5pp     | \*\*     |
| % escolas rurais     | 42.6%      | 55.9%     | **+13.3pp** | \*\*     |
| Lab. informática     | 26.6%      | 18.0%     | -8.6pp      | \*       |
| Biblioteca           | 33.3%      | 27.5%     | -5.9pp      | n.s.     |
| **Internet escolar** | **93.8%**  | **93.7%** | **-0.0pp**  | **n.s.** |
| Responsável feminino | 51.4%      | 50.2%     | -1.2pp      | n.s.     |

### Achados principais

**Esgoto é o indicador que mais separa os grupos** — 22.6 pontos percentuais
de diferença entre municípios com baixo e alto analfabetismo. Municípios
vulneráveis têm menos esgoto nas escolas E menos esgoto nos domicílios.

**Escolas rurais aumentam 13pp no grupo mais vulnerável** — confirma que
ruralidade e vulnerabilidade educacional andam juntas.

**Internet é completamente uniforme** — 93.8% vs. 93.7%. A universalização
da conectividade escolar foi bem-sucedida e não discrimina por nível de
vulnerabilidade. Isso é uma conquista de política pública.

**Responsável feminino não varia** — chefia feminina está distribuída
uniformemente entre municípios vulneráveis e não-vulneráveis. Não é um
marcador de vulnerabilidade educacional.

_Valor de negócio:_ Para identificar municípios que precisam de intervenção
educacional, esgoto nas escolas e % de escolas rurais são melhores preditores
que internet ou biblioteca. Gestores devem priorizar saneamento escolar nos
municípios do Q4.

---

## Parte 4 — Score de Vulnerabilidade Composta

**Método:** Normalização min-max de 4 indicadores (0-1) e média simples.
Indicadores usados: analfabetismo adulto, água domiciliar (invertido),
esgoto domiciliar (invertido), esgoto escolar (invertido).
Score 0 = menos vulnerável, 100 = mais vulnerável.

### Top 10 municípios mais vulneráveis

| Município           | Score | Pop    | Analfab. | Água dom. | Esgoto dom. | Esgoto esc. |
| ------------------- | ----- | ------ | -------- | --------- | ----------- | ----------- |
| Riachão do Poço     | 93.4  | 4.738  | 29.3%    | 7.3%      | 0.0%        | 0.0%        |
| Vieirópolis         | 92.4  | 4.864  | 33.0%    | 20.8%     | 0.3%        | 0.0%        |
| Gado Bravo          | 90.8  | 8.179  | 25.4%    | 0.3%      | 1.5%        | 2.9%        |
| Santa Cecília       | 90.2  | 7.670  | 26.0%    | 0.0%      | 2.6%        | 5.9%        |
| Damião              | 89.0  | 4.982  | 33.3%    | 1.0%      | 6.5%        | 30.0%       |
| Tenório             | 88.3  | 2.966  | 21.1%    | 0.0%      | 0.0%        | 0.0%        |
| Algodão de Jandaíra | 88.1  | 2.953  | 29.9%    | 0.0%      | 10.5%       | 16.7%       |
| Dona Inês           | 87.3  | 10.380 | 28.3%    | 0.3%      | 8.6%        | 16.7%       |
| Poço Dantas         | 87.3  | 3.830  | 29.7%    | 8.7%      | 11.3%       | 7.7%        |
| Alcantil            | 86.3  | 5.578  | 19.9%    | 0.0%      | 2.5%        | 0.0%        |

**População total nos 10 mais vulneráveis:** 56.140 pessoas (1.4% da PB)

Esses 10 municípios representam 4.5% do total de municípios mas concentram
as piores condições simultâneas de analfabetismo, saneamento domiciliar e
infraestrutura escolar.

_Valor de negócio:_ O score de vulnerabilidade composta é uma ferramenta
direta para priorização de políticas públicas. Com um único número, gestores
podem identificar onde a intervenção simultânea em educação e saneamento
teria maior impacto. Esse score pode ser exposto pela API do ODIN como
campo calculado nos documentos MongoDB.

---

## Parte 5 — Síntese dos Achados

### O que os dados integrados revelam que os dados isolados não mostram

| Achado                                           | Dado isolado                   | Dado integrado                                                       |
| ------------------------------------------------ | ------------------------------ | -------------------------------------------------------------------- |
| Alcantil tem 75% de lab. informática             | Parece bem servido             | Mas tem 0% de esgoto escolar e 0% de água domiciliar                 |
| Internet escolar é universal (93%)               | Parece indicador de qualidade  | Não correlaciona com analfabetismo — é infraestrutura, não resultado |
| Bom Sucesso tem 24.5% de idosos                  | Parece problema de saúde       | Escolas têm 67% de biblioteca — o problema é geracional, não atual   |
| EJA correlaciona negativamente com analfabetismo | Parece paradoxo                | É política eficaz: onde há EJA, o analfabetismo cai                  |
| Esgoto escolar e domiciliar correlacionam r=0.75 | Não visível em dados separados | Saneamento é sistêmico — escola e domicílio são afetados juntos      |

### Implicações para o ODIN

1. **O cruzamento educação × socioeconômico é o diferencial do projeto.**
   Nenhuma plataforma pública atual faz isso no nível municipal para a PB.

2. **Score de vulnerabilidade composta** deve ser um campo calculado na API,
   não apenas dados brutos. Gestores precisam de síntese, não de 20 variáveis.

3. **Internet escolar não deve ser usada como proxy de qualidade educacional.**
   O ODIN deve apresentar claramente a distinção entre infraestrutura (internet)
   e resultado (analfabetismo, EJA).

4. **Saneamento escolar é o indicador mais discriminante** entre municípios
   vulneráveis e não-vulneráveis — mais que biblioteca ou laboratório.

5. **Os 10 municípios do score composto** são os candidatos naturais para
   estudos de caso e para demonstração do valor do ODIN para professores
   e gestores públicos.

---

## Correlações Significativas — Resumo Visual

```
EDUCAÇÃO                          SOCIOECONÔMICO
─────────────────────────────────────────────────────────────
pct_escola_esgoto    ←──── r=+0.75 ────→  pct_esgoto_rede_geral
pct_escola_lixo      ←──── r=+0.48 ────→  pct_lixo_coletado
pct_escolas_rurais   ←──── r=+0.33 ────→  taxa_analfabetismo
mat_eja              ←──── r=-0.29 ────→  taxa_analfabetismo
pct_escola_biblioteca ←─── r=-0.25 ────→  taxa_analfabetismo
pct_escola_lab_info  ←──── r=-0.18 ────→  taxa_analfabetismo
pct_escola_internet  ←──── r=~0.00 ────→  taxa_analfabetismo  (sem relação)
```

---

_Documento gerado durante EDA integrada do módulo socioeconômico do ODIN-ETL._  
_Código de reprodução: `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/indicadores.py`_  
_Dados educacionais: `data/silver/subdatasets/_.parquet`*  
*Dados socioeconômicos: `data/silver/ibge*censo2022_municipio*_\_pb.parquet`_

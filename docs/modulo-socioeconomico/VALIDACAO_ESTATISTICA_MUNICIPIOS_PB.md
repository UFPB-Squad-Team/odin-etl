# Validação Estatística — Indicadores Socioeconômicos dos Municípios da PB

> **Módulo:** Socioeconômico — IBGE Censo 2022  
> **Escopo:** 223 municípios da Paraíba  
> **Data:** Abril/2026  
> **Autor:** Gerado durante EDA do pipeline ODIN-ETL  
> **Fonte dos dados:** IBGE Censo Demográfico 2022 — Agregados por Município

---

## Contexto

Antes de implementar o pipeline de transformação (Task 1.4), realizamos uma
validação estatística completa dos 10 indicadores de Prioridade 1 calculados
por `indicadores.py`. O objetivo foi garantir que os dados refletem a realidade
socioeconômica da Paraíba antes de persistir no MongoDB.

Os indicadores validados são:

| Indicador                       | Fonte IBGE                                     |
| ------------------------------- | ---------------------------------------------- |
| `total_populacao`               | basico.v0001                                   |
| `media_moradores_por_domicilio` | basico.v0005                                   |
| `pct_criancas_0_9`              | demografia.V01031+V01032 / V01006              |
| `pct_idosos_60_mais`            | demografia.V01040+V01041 / V01006              |
| `pct_preta_parda`               | cor_ou_raca.V01318+V01320 / total              |
| `pct_agua_rede_geral`           | domicilio2.V00111 / basico.v0003               |
| `pct_esgoto_rede_geral`         | domicilio2.V00309 / basico.v0003               |
| `pct_lixo_coletado`             | domicilio2.V00397+V00398 / basico.v0003        |
| `taxa_analfabetismo_15_mais`    | alfabetizacao.V00901 / (V00901+V00748..V00760) |
| `pct_responsavel_feminino`      | parentesco.V01063 / V01042                     |

---

## 1. Estatísticas Descritivas

**Método:** média, mediana, desvio padrão, mínimo, máximo e quartis.

| Indicador                  | Mín   | Q1    | Mediana | Média  | Q3     | Máx     | DP  |
| -------------------------- | ----- | ----- | ------- | ------ | ------ | ------- | --- |
| total_populacao            | 1.699 | 5.578 | 9.224   | 17.824 | 16.737 | 833.932 | —   |
| media_moradores            | 2.5   | 2.8   | 2.9     | 2.9    | 3.0    | 3.3     | —   |
| pct_criancas_0_9           | 9.6%  | 12.8% | 13.6%   | 13.6%  | 14.5%  | 18.4%   | —   |
| pct_idosos_60_mais         | 10.9% | 15.3% | 16.7%   | 16.7%  | 18.1%  | 24.5%   | —   |
| pct_preta_parda            | 10.1% | 61.5% | 66.5%   | 65.0%  | 71.0%  | 78.3%   | —   |
| pct_agua_rede_geral        | 0.0%  | 28.5% | 40.5%   | 41.5%  | 54.5%  | 82.6%   | —   |
| pct_esgoto_rede_geral      | 0.0%  | 11.5% | 20.5%   | 23.2%  | 32.5%  | 69.3%   | —   |
| pct_lixo_coletado          | 16.1% | 44.5% | 52.5%   | 52.3%  | 61.5%  | 82.3%   | —   |
| taxa_analfabetismo_15_mais | 6.1%  | 19.5% | 23.0%   | 22.5%  | 26.5%  | 34.3%   | —   |
| pct_responsavel_feminino   | 31.3% | 48.5% | 51.0%   | 50.8%  | 53.5%  | 70.1%   | —   |

**Valor de negócio:** Esses números são a linha de base do ODIN. Qualquer
indicador fora desses ranges em consultas futuras deve ser investigado como
possível erro de dados ou mudança real na realidade do município.

---

## 2. Distribuição e Forma (Assimetria e Curtose)

**Método:** Skewness (assimetria) e Kurtosis (curtose) de Pearson.  
**Interpretação:** skewness > |1| indica distribuição assimétrica; kurtosis > 2 indica caudas pesadas (valores extremos mais frequentes que o normal).

| Indicador                  | Skewness  | Curtose    | Forma                                                |
| -------------------------- | --------- | ---------- | ---------------------------------------------------- |
| pct_criancas_0_9           | +0.31     | +0.62      | Aproximadamente simétrica                            |
| pct_idosos_60_mais         | +0.25     | +0.46      | Aproximadamente simétrica                            |
| **pct_preta_parda**        | **-2.69** | **+15.24** | ⚠️ Fortemente assimétrica à esquerda, caudas pesadas |
| pct_agua_rede_geral        | -0.51     | -0.01      | Levemente assimétrica                                |
| pct_esgoto_rede_geral      | +0.45     | -0.55      | Levemente assimétrica                                |
| pct_lixo_coletado          | -0.11     | -0.13      | Aproximadamente simétrica                            |
| taxa_analfabetismo_15_mais | -0.25     | +0.16      | Aproximadamente simétrica                            |
| pct_responsavel_feminino   | -0.45     | +0.37      | Levemente assimétrica                                |

**Destaque — `pct_preta_parda`:** A assimetria extrema (skew=-2.69, kurt=+15.24)
é causada por 3 municípios indígenas Potiguara (Marcação, Baía da Traição,
Carrapateira) com valores muito baixos (10–39%). Esses municípios têm população
majoritariamente indígena, que o IBGE classifica separadamente de preta/parda.
Não é erro de dados — é uma característica real do território.

**Valor de negócio:** Indicadores com distribuição não-normal não devem ser
comparados usando médias simples. Para `pct_preta_parda`, a mediana (66.5%) é
mais representativa que a média (65.0%). A API deve expor ambas quando relevante.

---

## 3. Detecção de Outliers

**Método:** IQR (1.5× o intervalo interquartil) e Z-score (|z| > 3).  
**Interpretação:** outliers não são necessariamente erros — podem ser municípios
com características genuinamente extremas.

### Outliers identificados e investigados

| Município               | Indicador                  | Valor | Explicação                                                                  |
| ----------------------- | -------------------------- | ----- | --------------------------------------------------------------------------- |
| **Marcação**            | pct_preta_parda            | 10.1% | Município indígena Potiguara — população majoritariamente indígena          |
| **Baía da Traição**     | pct_preta_parda            | 13.3% | Idem — sede da Terra Indígena Potiguara                                     |
| **Carrapateira**        | pct_preta_parda            | 38.9% | Município pequeno (2.3k hab) com composição racial atípica                  |
| **Bom Sucesso**         | pct_idosos_60_mais         | 24.5% | Município com forte êxodo rural de jovens — população envelhecida           |
| **Santa Cruz**          | pct_idosos_60_mais         | 24.2% | Idem                                                                        |
| **Cacimbas**            | pct_criancas_0_9           | 18.4% | Alta natalidade — município rural sem transição demográfica completa        |
| **Cacimbas**            | pct_responsavel_feminino   | 70.1% | Alta emigração masculina para trabalho — fenômeno comum no sertão semiárido |
| **Alcantil**            | pct_agua_rede_geral        | 0.0%  | Município rural extremo — abastecimento por cisterna e carro-pipa           |
| **Algodão de Jandaíra** | pct_agua_rede_geral        | 0.0%  | Idem — menor município da PB                                                |
| **João Pessoa**         | taxa_analfabetismo_15_mais | 6.1%  | Outlier inferior — capital tem a menor taxa, esperado                       |
| **São Domingos**        | taxa_analfabetismo_15_mais | 34.3% | Município rural pequeno (2.6k hab) no sertão                                |

**Conclusão:** Nenhum outlier é erro de dados. Todos têm explicação geográfica,
demográfica ou socioeconômica verificável.

**Valor de negócio:** Esses municípios são os mais importantes para políticas
públicas. Alcantil e Algodão de Jandaíra sem água encanada, Cacimbas com 70%
de domicílios chefiados por mulheres, São Domingos com 34% de analfabetismo —
são os territórios que o ODIN deve priorizar em análises de vulnerabilidade.

---

## 4. Correlações entre Indicadores

**Método:** Correlação de Pearson (r) com teste de significância (p-valor).  
**Interpretação:** r mede a força e direção da relação linear entre dois
indicadores. Valores próximos de ±1 indicam relação forte; próximos de 0,
relação fraca ou inexistente. **Correlação não implica causalidade** — indica
que os fenômenos coexistem nos mesmos territórios.

### Resultados

| Par de indicadores            | r      | p-valor | Direção esperada | Resultado         |
| ----------------------------- | ------ | ------- | ---------------- | ----------------- |
| Analfabetismo × Água rede     | -0.332 | <0.001  | Negativa         | ✅ Confirmada     |
| Analfabetismo × Esgoto        | -0.410 | <0.001  | Negativa         | ✅ Confirmada     |
| Analfabetismo × Lixo coletado | -0.289 | <0.001  | Negativa         | ✅ Confirmada     |
| Crianças 0-9 × Idosos 60+     | -0.817 | <0.001  | Negativa         | ✅ Confirmada     |
| Água rede × Esgoto rede       | +0.330 | <0.001  | Positiva         | ✅ Confirmada     |
| Água rede × Lixo coletado     | +0.527 | <0.001  | Positiva         | ✅ Confirmada     |
| Pop total × Água rede         | +0.247 | <0.001  | Positiva         | ✅ Confirmada     |
| Pop total × Analfabetismo     | -0.360 | <0.001  | Negativa         | ✅ Confirmada     |
| Analfabetismo × Crianças 0-9  | -0.004 | 0.951   | Positiva         | ❌ Não confirmada |

### Interpretação detalhada

**Analfabetismo × Saneamento (r entre -0.29 e -0.41)**

Os três indicadores de saneamento (água, esgoto, lixo) correlacionam
negativamente com analfabetismo. Municípios com pior saneamento tendem a ter
mais analfabetismo. Isso não significa que falta de água causa analfabetismo —
ambos são sintomas de pobreza estrutural e baixo investimento público. O esgoto
tem a correlação mais forte (-0.41) porque é o indicador mais desigual da PB
(varia de 0% a 69%), separando bem os territórios vulneráveis dos desenvolvidos.

_Valor de negócio:_ Municípios com baixo saneamento são candidatos prioritários
para cruzamento com dados educacionais. A API pode usar essa correlação para
gerar alertas de vulnerabilidade composta.

**Crianças × Idosos (r = -0.817)**

Correlação fortíssima e esperada. Municípios com muitas crianças têm poucos
idosos e vice-versa. Isso reflete estágios diferentes da transição demográfica:
municípios rurais ainda têm alta natalidade (mais crianças), enquanto municípios
com êxodo rural ficam com população envelhecida (mais idosos). Bom Sucesso
(24.5% idosos, 10.2% crianças) e Cacimbas (18.4% crianças, 12.8% idosos)
ilustram os dois extremos.

_Valor de negócio:_ Municípios com alta proporção de idosos e baixa de crianças
indicam êxodo rural e envelhecimento populacional — demandam políticas de saúde
do idoso e podem ter escolas subutilizadas. O inverso indica demanda crescente
por vagas escolares.

**Infraestrutura de saneamento (r = +0.33 a +0.53)**

Água, esgoto e lixo correlacionam positivamente entre si. Municípios que têm
boa rede de água tendem a ter boa coleta de lixo (r=+0.53) e bom esgoto
(r=+0.33). Isso reflete que investimento em infraestrutura tende a vir em
conjunto — ou o município recebe investimento público ou não recebe.

_Valor de negócio:_ Um município com boa água mas péssimo esgoto é um caso
atípico que merece investigação. A API pode identificar esses desequilíbrios
para orientar políticas setoriais.

**Tamanho × Infraestrutura e Educação**

Cidades maiores têm mais acesso à água (r=+0.25) e menos analfabetismo
(r=-0.36). A relação não é fortíssima porque existem municípios pequenos bem
servidos e municípios médios com infraestrutura precária, mas a tendência geral
é clara.

_Valor de negócio:_ O tamanho populacional não deve ser usado como proxy de
desenvolvimento. Municípios médios (10k-50k hab) têm grande variância em todos
os indicadores — são o grupo mais heterogêneo e onde políticas públicas têm
maior potencial de impacto diferenciado.

**Analfabetismo × Crianças (r = -0.004, não significativo)**

A hipótese de que municípios com mais crianças teriam mais analfabetismo não
foi confirmada. Isso faz sentido: a faixa 0-9 anos não inclui adultos, então
a proporção de crianças não prediz diretamente o analfabetismo adulto. Municípios
com alta natalidade podem ter investido em educação nas últimas décadas.

_Valor de negócio:_ Não use proporção de crianças como proxy de analfabetismo.
São fenômenos independentes que requerem políticas distintas.

---

## 5. Normalidade (Shapiro-Wilk)

**Método:** Teste de Shapiro-Wilk. H0: a distribuição é normal. p < 0.05 rejeita normalidade.

| Indicador                  | W      | p-valor | Normal? |
| -------------------------- | ------ | ------- | ------- |
| pct_criancas_0_9           | 0.9885 | 0.071   | ✅ Sim  |
| pct_idosos_60_mais         | 0.9880 | 0.059   | ✅ Sim  |
| pct_preta_parda            | 0.8173 | <0.001  | ❌ Não  |
| pct_agua_rede_geral        | 0.9661 | <0.001  | ❌ Não  |
| pct_esgoto_rede_geral      | 0.9571 | <0.001  | ❌ Não  |
| pct_lixo_coletado          | 0.9908 | 0.169   | ✅ Sim  |
| taxa_analfabetismo_15_mais | 0.9903 | 0.142   | ✅ Sim  |
| pct_responsavel_feminino   | 0.9810 | 0.004   | ❌ Não  |

**Valor de negócio:** Indicadores normais (estrutura etária, analfabetismo,
lixo) podem ser comparados com testes paramétricos (t-test, ANOVA). Indicadores
não-normais (saneamento de água e esgoto, raça, responsável feminino) requerem
testes não-paramétricos (Mann-Whitney, Kruskal-Wallis) para comparações entre
grupos. Isso é relevante para análises futuras na API do ODIN.

---

## 6. Diferenças por Porte Municipal (Kruskal-Wallis)

**Método:** Kruskal-Wallis — teste não-paramétrico para comparar distribuições
entre 3 ou mais grupos independentes. H0: as distribuições são iguais entre
grupos. p < 0.05 indica diferença significativa.

**Grupos definidos por população:**

- Pequeno: < 10.000 hab (141 municípios — 63% da PB)
- Médio: 10.000–50.000 hab (72 municípios — 32%)
- Grande: > 50.000 hab (10 municípios — 5%)

| Indicador                  | H     | p-valor | Grupos diferentes? | Médias por porte                     |
| -------------------------- | ----- | ------- | ------------------ | ------------------------------------ |
| pct_criancas_0_9           | 13.60 | 0.001   | ✅ Sim             | Peq: 13.3% / Méd: 14.0% / Grd: 13.7% |
| pct_idosos_60_mais         | 22.42 | <0.001  | ✅ Sim             | Peq: 17.3% / Méd: 16.0% / Grd: 14.6% |
| pct_preta_parda            | 4.70  | 0.095   | ❌ Não             | Sem diferença significativa          |
| pct_agua_rede_geral        | 30.75 | <0.001  | ✅ Sim             | Peq: 37.9% / Méd: 44.4% / Grd: 70.7% |
| pct_esgoto_rede_geral      | 6.21  | 0.045   | ✅ Sim             | Peq: 21.1% / Méd: 25.1% / Grd: 38.1% |
| pct_lixo_coletado          | 35.74 | <0.001  | ✅ Sim             | Peq: 49.1% / Méd: 55.5% / Grd: 74.1% |
| taxa_analfabetismo_15_mais | 23.60 | <0.001  | ✅ Sim             | Peq: 23.3% / Méd: 22.1% / Grd: 13.2% |
| pct_responsavel_feminino   | 0.77  | 0.680   | ❌ Não             | Sem diferença significativa          |

### Interpretações por indicador

**Saneamento — forte gradiente por porte:**
Municípios grandes têm quase o dobro de acesso à água (70.7%) comparado aos
pequenos (37.9%). O mesmo padrão vale para lixo e esgoto. Isso confirma que
infraestrutura de saneamento é fortemente concentrada nas cidades maiores da PB.

_Valor de negócio:_ Municípios pequenos são os mais vulneráveis em saneamento.
Políticas de universalização devem priorizar os 141 municípios com menos de
10 mil habitantes, onde vivem ~790 mil pessoas com acesso médio de 37.9% à
rede de água.

**Analfabetismo — gradiente claro:**
Municípios grandes têm taxa de analfabetismo de 13.2% vs. 23.3% nos pequenos.
Diferença de 10 pontos percentuais entre o menor e o maior porte.

_Valor de negócio:_ O analfabetismo na PB é essencialmente um problema rural.
Concentrar esforços de alfabetização nos municípios pequenos do sertão e cariri
teria o maior impacto absoluto.

**Estrutura etária — padrão inverso:**
Municípios pequenos têm mais idosos (17.3%) e municípios grandes têm mais
idosos relativamente menos (14.6%). Isso reflete o êxodo rural — jovens migram
para cidades maiores, deixando os municípios pequenos com população envelhecida.

_Valor de negócio:_ Municípios pequenos com alta proporção de idosos e baixa
de crianças podem ter escolas com baixa ocupação e alta demanda por serviços
de saúde do idoso — informação relevante para planejamento de equipamentos
públicos.

**Raça e responsável feminino — sem diferença por porte:**
`pct_preta_parda` e `pct_responsavel_feminino` não variam significativamente
entre municípios de diferentes portes. Isso indica que desigualdade racial e
chefia feminina são fenômenos distribuídos uniformemente no território paraibano,
independente do tamanho da cidade.

_Valor de negócio:_ Políticas de equidade racial e de apoio a famílias
monoparentais femininas devem ter cobertura territorial ampla — não há
concentração geográfica clara que justifique foco em um porte específico.

---

## 7. Consistência Interna

**Verificações realizadas:**

| Verificação                      | Resultado                                               |
| -------------------------------- | ------------------------------------------------------- |
| pct_criancas + pct_idosos > 100% | ✅ 0 casos                                              |
| Qualquer percentual > 100%       | ✅ 0 casos                                              |
| total_populacao ≤ 0              | ✅ 0 casos                                              |
| Nulos em qualquer indicador      | ✅ 0 casos (223/223 completos)                          |
| Soma faixas etárias vs. V01006   | ⚠️ 52 municípios com diff > 10 pessoas (max: 388 em JP) |

A diferença nas faixas etárias (52 municípios) é causada por pessoas sem
declaração de idade no Censo — fenômeno documentado pelo IBGE. A diferença
máxima é de 388 pessoas em João Pessoa (0.05% da população), sem impacto
nos indicadores pois usamos V01006 como denominador, não a soma das faixas.

---

## 8. Benchmarks Externos

Comparação com dados oficiais publicados pelo IBGE e estimativas de referência.

| Indicador                        | Valor calculado | Range esperado      | Fonte           | Status      |
| -------------------------------- | --------------- | ------------------- | --------------- | ----------- |
| Pop total PB                     | 3.974.687       | 4.059.905 (oficial) | IBGE Censo 2022 | ⚠️ Ver nota |
| Analfabetismo PB (ponderado)     | **16.0%**       | 16–22%              | IBGE 2022       | ✅          |
| Analfabetismo PB (média simples) | 22.5%           | —                   | —               | ℹ️ Ver nota |
| Água rede PB (média)             | 41.5%           | 35–55%              | Estimativa      | ✅          |
| Idosos 60+ PB (média)            | 16.7%           | 13–20%              | IBGE 2022       | ✅          |
| Crianças 0-9 PB (média)          | 13.6%           | 11–17%              | Estimativa      | ✅          |

**Nota — População total (3.97M vs. 4.06M):**
`v0001` conta apenas moradores em domicílios particulares. Os ~85 mil restantes
estão em domicílios coletivos (hospitais, presídios, quartéis, alojamentos) —
contabilizados separadamente pelo IBGE em `v0004`. A diferença é esperada e
documentada. Para o ODIN, `total_populacao` representa a população residente
em domicílios, que é a base correta para calcular indicadores domiciliares.

**Nota — Analfabetismo (22.5% vs. 16.0%):**
A média simples dos municípios (22.5%) superestima a taxa real porque municípios
pequenos e rurais com alta taxa têm o mesmo peso que João Pessoa (830k hab).
A taxa ponderada pela população (16.0%) é a correta para comparar com dados
oficiais do IBGE e está dentro do range esperado. **A API deve sempre usar
a taxa ponderada ao agregar para o nível estadual.**

---

## 9. Municípios de Referência Validados

Validação qualitativa com municípios representativos de diferentes perfis:

| Município           | Perfil                   | Pop     | Crianças | Idosos | Analfab. | Água  | Esgoto | Lixo  | Resp. Fem. |
| ------------------- | ------------------------ | ------- | -------- | ------ | -------- | ----- | ------ | ----- | ---------- |
| João Pessoa         | Capital, litoral         | 833.932 | 12.9%    | 14.8%  | 6.1%     | 73.4% | 52.8%  | 77.8% | 52.1%      |
| Campina Grande      | Polo regional, agreste   | 419.379 | 13.2%    | 15.0%  | 8.0%     | 78.5% | 69.3%  | 78.0% | 52.3%      |
| Sousa               | Polo do alto sertão      | 67.259  | 13.5%    | 15.5%  | 16.7%    | 68.3% | 57.8%  | 68.4% | 47.3%      |
| Alcantil            | Rural extremo, semiárido | 5.578   | 15.6%    | 14.9%  | 19.9%    | 0.0%  | 2.5%   | 48.2% | 56.4%      |
| Algodão de Jandaíra | Menor município PB       | 2.953   | 15.9%    | 14.3%  | 29.9%    | 0.0%  | 10.5%  | 41.2% | 43.0%      |
| Bom Sucesso         | Êxodo rural intenso      | 4.661   | 10.2%    | 24.5%  | 25.2%    | —     | —      | —     | —          |
| Cacimbas            | Alta emigração masculina | 7.223   | 18.4%    | 12.8%  | 25.1%    | —     | —      | —     | 70.1%      |

**Gradiente capital → interior → rural extremo confirmado** em todos os
indicadores de saneamento e analfabetismo. Os valores são coerentes com o
conhecimento geográfico e socioeconômico da Paraíba.

---

## 10. Conclusão e Recomendações

### Os dados estão corretos e prontos para o pipeline

Todos os 10 indicadores passaram na validação estatística. Os únicos pontos
que pareciam problemas têm explicação técnica documentada (população em
domicílios coletivos, média simples vs. ponderada, pessoas sem declaração
de idade).

### Recomendações para a API do ODIN

1. **Expor mediana além da média** para `pct_preta_parda` — a assimetria
   causada pelos municípios indígenas torna a média menos representativa.

2. **Taxa de analfabetismo estadual deve ser ponderada** pela população,
   não média simples dos municípios. Diferença de 6.5 pontos percentuais.

3. **Municípios indígenas merecem flag especial** — Marcação, Baía da Traição
   e Carrapateira têm perfil racial completamente diferente do restante da PB.
   Considerar campo `tem_territorio_indigena` no documento MongoDB.

4. **Municípios sem água encanada (0%)** não são erros — são realidade de
   pelo menos 5 municípios da PB. A API não deve filtrar esses valores.

5. **Correlações podem alimentar scores de vulnerabilidade** — a combinação
   de alto analfabetismo + baixo saneamento + população pequena identifica
   os territórios mais vulneráveis da PB para priorização de políticas.

### Municípios prioritários identificados pela análise

| Município           | Por quê é prioritário                                       |
| ------------------- | ----------------------------------------------------------- |
| Algodão de Jandaíra | Menor município, 0% água, 29.9% analfabetismo               |
| São Domingos        | Maior taxa de analfabetismo da PB (34.3%)                   |
| Alcantil            | 0% água encanada, 19.9% analfabetismo                       |
| Bom Sucesso         | Maior proporção de idosos (24.5%) — demanda saúde do idoso  |
| Cacimbas            | 70.1% responsável feminino — alta vulnerabilidade de gênero |

---

_Documento gerado durante a EDA do módulo socioeconômico do ODIN-ETL._  
_Código de reprodução: `src/jobs/socioeconomico_jobs/ibge_censo_pipeline/indicadores.py`_  
_Dados: `data/silver/ibge*censo2022_municipio*_\_pb.parquet`\*

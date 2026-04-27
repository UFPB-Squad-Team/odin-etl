# Pipeline Socioeconômico — IBGE Censo 2022

Documentação técnica do módulo socioeconômico do ODIN-ETL.

---

## Visão Geral

O módulo socioeconômico processa os **Agregados por Setores Censitários** do IBGE Censo Demográfico 2022, calculando 10 indicadores socioeconômicos nas granularidades município, setor censitário e bairro da Paraíba.

Os indicadores são carregados na mesma collection do módulo de educação, sob o campo `socioeconomico`, coexistindo com o campo `educacao` sem conflito.

---

## Arquitetura

```
FTP IBGE
    │
    ▼ extract.py (Bronze → Silver)
data/bronze/*.zip
    │
    ▼ filtro UF=25 (PB)
data/silver/ibge_censo2022_{granularidade}_{dataset}_pb.parquet
    │
    ▼ indicadores.py + transform.py (Silver → Gold)
data/gold/{granularidade}_socioeconomico_pb.parquet
    │
    ▼ load.py (Gold → MongoDB)
municipio_indicadores.socioeconomico
setor_indicadores.socioeconomico
bairro_indicadores.socioeconomico
```

---

## Granularidades

| Granularidade | Registros PB | Collection MongoDB      | Chave             |
| ------------- | ------------ | ----------------------- | ----------------- |
| Município     | 223          | `municipio_indicadores` | `municipioIdIbge` |
| Setor         | 9.639        | `setor_indicadores`     | `cd_setor`        |
| Bairro        | 257          | `bairro_indicadores`    | `cd_bairro`       |

> **Nota sobre bairros:** O IBGE delimita bairros oficialmente apenas em municípios com essa divisão administrativa formalizada. Na PB, isso cobre principalmente João Pessoa, Campina Grande, Bayeux, Santa Rita e outras cidades maiores. O interior usa setor censitário como granularidade menor.

---

## Datasets IBGE

Cada granularidade baixa 8 datasets temáticos do FTP do IBGE:

| Dataset                      | Variáveis usadas                       | Indicadores calculados                 |
| ---------------------------- | -------------------------------------- | -------------------------------------- |
| `basico`                     | v0001, v0003, v0005                    | população, domicílios, média moradores |
| `demografia`                 | V01006, V01031, V01032, V01040, V01041 | % crianças 0-9, % idosos 60+           |
| `cor_ou_raca`                | V01317–V01321                          | % preta+parda                          |
| `caracteristicas_domicilio2` | V00111, V00309, V00397, V00398         | % água, esgoto, lixo coletado          |
| `alfabetizacao`              | V00748–V00760, V00901                  | taxa analfabetismo 15+                 |
| `parentesco`                 | V01042, V01063                         | % responsável feminino                 |
| `caracteristicas_domicilio3` | —                                      | não usado (baixado para uso futuro)    |
| `obitos`                     | —                                      | não usado (baixado para uso futuro)    |

---

## Dicionário de Indicadores

### Prioridade 1 — Essenciais

| Indicador                       | Fórmula                                    | Fonte IBGE    |
| ------------------------------- | ------------------------------------------ | ------------- |
| `total_populacao`               | v0001                                      | basico        |
| `total_domicilios_particulares` | v0003                                      | basico        |
| `media_moradores_por_domicilio` | v0005                                      | basico        |
| `pct_criancas_0_9`              | (V01031 + V01032) / V01006 × 100           | demografia    |
| `pct_idosos_60_mais`            | (V01040 + V01041) / V01006 × 100           | demografia    |
| `pct_preta_parda`               | (V01318 + V01320) / Σ(V01317–V01321) × 100 | cor_ou_raca   |
| `pct_agua_rede_geral`           | V00111 / v0003 × 100                       | dom2 + basico |
| `pct_esgoto_rede_geral`         | V00309 / v0003 × 100                       | dom2 + basico |
| `pct_lixo_coletado`             | (V00397 + V00398) / v0003 × 100            | dom2 + basico |
| `taxa_analfabetismo_15_mais`    | V00901 / (V00901 + Σ(V00748–V00760)) × 100 | alfabetizacao |
| `pct_responsavel_feminino`      | V01063 / V01042 × 100                      | parentesco    |

### Prioridade 2 — Complementares

| Indicador                    | Fórmula                                         | Fonte IBGE    |
| ---------------------------- | ----------------------------------------------- | ------------- |
| `razao_dependencia`          | (pop_0_14 + pop_60+) / pop_15_59 × 100          | demografia    |
| `pct_agua_inadequada`        | Σ(V00113–V00118) / v0003 × 100                  | dom2 + basico |
| `pct_esgoto_inadequado`      | Σ(V00311,V00313–V00316) / v0003 × 100           | dom2 + basico |
| `pct_lixo_inadequado`        | Σ(V00399–V00402) / v0003 × 100                  | dom2 + basico |
| `total_obitos_domicilios`    | V01224 (domicílios com óbito jan/2019–jul/2022) | obitos        |
| `obitos_infantis_0_4`        | V01228 + V01239                                 | obitos        |
| `pct_dom_improvisado`        | V00002 / V00001 × 100                           | dom1          |
| `pct_dom_superlotado`        | Σ(V00021–V00026) / V00001 × 100                 | dom1          |

---

## Estrutura do Documento MongoDB

```json
{
  "municipioIdIbge": 2507507,
  "municipio": "João Pessoa",
  "sg_uf": "PB",
  "centroide": { "type": "Point", "coordinates": [-34.845, -7.119] },
  "geometria": { "type": "Polygon", "coordinates": [...] },

  "educacao": {
    "totalEscolas": 300,
    "totalMatriculas": 100395,
    "pctComInternet": 99.3,
    "pctComBiblioteca": 53.7,
    "pctComLabInformatica": 43.0,
    "pctSemAcessibilidade": 21.7
  },

  "socioeconomico": {
    "anoReferencia": 2022,
    "fonte": "IBGE Censo Demográfico 2022",
    "populacao": {
      "total": 833932,
      "totalDomiciliosParticulares": null,
      "mediaMoradoresPorDomicilio": 2.8
    },
    "estruturaEtaria": {
      "pctCriancas0a9": 12.9,
      "pctIdosos60Mais": 14.8,
      "razaoDependencia": 52.1
    },
    "raca": {
      "pctPretaParda": 59.8
    },
    "saneamento": {
      "pctAguaRedeGeral": 73.4,
      "pctAguaInadequada": 3.2,
      "pctEsgotoRedeGeral": 52.8,
      "pctEsgotoInadequado": 12.1,
      "pctLixoColetado": 77.8,
      "pctLixoInadequado": 4.5
    },
    "educacaoPopulacao": {
      "taxaAnalfabetismo15Mais": 6.1
    },
    "familia": {
      "pctResponsavelFeminino": 52.1
    },
    "mortalidade": {
      "totalObitosDomicilios": 15267,
      "obitosInfantis0a4": 42
    },
    "habitacao": {
      "pctDomImprovisado": 0.1,
      "pctDomSuperlotado": 8.3
    }
  }
}
```

> `educacaoPopulacao` (não `educacao`) evita colisão com o namespace do módulo de educação.

---

## Comandos

```bash
# Pipeline completo (extract + transform + load para as 3 granularidades)
uv run python -m src.jobs.socioeconomico_jobs.ibge_censo_pipeline.main

# Ou via Makefile
make run-socioeconomico

# Etapas individuais
make run-socioeconomico-extract
make run-socioeconomico-transform-municipio
make run-socioeconomico-load-municipio
make run-socioeconomico-transform-setor
make run-socioeconomico-load-setor
make run-socioeconomico-transform-bairro
make run-socioeconomico-load-bairro

# Validação
uv run python scripts/validar_socioeconomico.py

# Testes
uv run pytest tests/test_socioeconomico_indicadores.py tests/test_socioeconomico_load_municipio.py -v
```

---

## Queries MongoDB Úteis

```js
// Municípios com menor acesso à água encanada
db.municipio_indicadores
  .find(
    { "socioeconomico.saneamento.pctAguaRedeGeral": { $lt: 20 } },
    { municipio: 1, "socioeconomico.saneamento.pctAguaRedeGeral": 1 },
  )
  .sort({ "socioeconomico.saneamento.pctAguaRedeGeral": 1 });

// Setores próximos a um ponto (ex: centro de João Pessoa)
db.setor_indicadores.find({
  geometria: {
    $geoIntersects: {
      $geometry: { type: "Point", coordinates: [-34.863, -7.115] },
    },
  },
});

// Bairros com alto analfabetismo e baixo saneamento
db.bairro_indicadores.find({
  "socioeconomico.educacaoPopulacao.taxaAnalfabetismo15Mais": { $gt: 15 },
  "socioeconomico.saneamento.pctEsgotoRedeGeral": { $lt: 30 },
});

// Comparar indicadores de educação e socioeconômico de um município
db.municipio_indicadores.findOne(
  { municipioIdIbge: 2507507 },
  {
    educacao: 1,
    "socioeconomico.populacao": 1,
    "socioeconomico.saneamento": 1,
  },
);
```

---

## Decisões de Design

**$set cirúrgico:** O load usa `$set` apenas no campo `socioeconomico`, nunca sobrescrevendo `educacao` ou campos geo. Isso permite que os dois módulos rodem independentemente em qualquer ordem.

**Normalização de chave:** O IBGE usa nomes de coluna inconsistentes entre datasets (ex: `CD_setor`, `setor`, `CD_SETOR`). A função `_normalizar_chave()` em `indicadores.py` padroniza para o nome canônico antes de qualquer cálculo.

**Denominador de saneamento:** O IBGE não inclui `V00001` (total de domicílios) nos datasets de domicílio. O denominador correto é `v0003` (domicílios particulares) do dataset `basico`.

**Lixo coletado:** As variáveis `V00397` (serviço de limpeza) e `V00398` (caçamba) estão em `caracteristicas_domicilio2`, não em `domicilio3` como documentado originalmente.

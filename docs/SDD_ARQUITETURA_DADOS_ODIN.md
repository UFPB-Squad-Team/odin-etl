# SDD — Arquitetura de Dados do ODIN (MVP Paraíba / Educação)

Status: Proposto e parcialmente implementado  
Última atualização: 2026-04-03  
Escopo atual: Educação (PB)  
Escopo futuro: Saúde, Profissões, Economia e outros domínios

---

## 1) Objetivo do documento

Este documento define a estratégia de modelagem de dados do ODIN para equilibrar:

- entrega rápida do produto (MVP);
- qualidade e governança de dados (longo prazo);
- escalabilidade para múltiplos domínios;
- consumo eficiente por API (FastAPI) e frontend.

A decisão central é **adotar duas camadas complementares**:

1. **Modelo canônico analítico (dimensional)** para curadoria, histórico e integração entre domínios;
2. **Read model orientado à aplicação** para respostas rápidas e simples no frontend/API.

---

## 2) Contexto do problema

Atualmente, a coleção de escolas no MongoDB já está em formato amigável para aplicação (campos de domínio, `localizacao` GeoJSON, blocos como `infraestrutura` e `indicadores`).

A dúvida estratégica é: **devemos modelar dimensionalmente ou manter modelagem para aplicação?**

Resposta arquitetural recomendada para o ODIN:

- Não é “ou”; é **“e”**.
- O ODIN, como repositório de dados institucional, precisa de modelo canônico robusto.
- A aplicação (benchmark Opportunity Atlas, UX centrada em mapa/insights) precisa de modelo de leitura otimizado.

---

## 3) Princípios arquiteturais

1. **Single Source of Truth**: dados padronizados e auditáveis no canônico.
2. **Read models derivados**: payloads para aplicação são materializações do canônico.
3. **Contratos versionados**: mudanças de schema com versionamento explícito.
4. **Desacoplamento de linguagem**: contrato de API não depende de Python, JS etc.
5. **Idempotência e reprocessamento**: pipelines podem rodar múltiplas vezes sem inconsistência.
6. **Observabilidade**: qualidade, frescor, linhagem e cobertura monitoráveis.

---

## 4) Escopo do MVP (PB + Educação)

### Inclui

- ingestão e filtragem de escolas da Paraíba;
- geocodificação com reaproveitamento de base existente + fallback;
- enriquecimento com indicadores educacionais;
- carga em MongoDB para consumo da API.

### Não inclui (ainda)

- motor unificado de indicadores cross-domain;
- modelo de risco consolidado multimodal;
- padronização total de score entre domínios;
- catálogo de dados com UI.

---

## 5) Modelo de dados alvo (visão macro)

## 5.1 Camada A — Canônico analítico (dimensional)

Finalidade: governança, análise histórica, comparabilidade interdomínio.

Exemplo de entidades lógicas:

- `dim_tempo` (ano, mês, trimestre, referência)
- `dim_localidade` (região, UF, município IBGE, setor censitário quando aplicável)
- `dim_escola` (id INEP, atributos estáveis)
- `fato_educacao_indicadores` (métricas por escola/ano)
- `fato_educacao_infraestrutura` (infra por escola/ano)

Características:

- granularidade explícita (`grão`);
- chaves de negócio e técnicas;
- histórico por vigência (quando necessário);
- suporte a análises e auditoria.

## 5.2 Camada B — Read model da aplicação (Mongo)

Finalidade: latência baixa, payload pronto para frontend e API.

Exemplo de estrutura orientada ao produto:

- identificadores e localização no topo;
- `localizacao` em GeoJSON Point;
- blocos aninhados por contexto (`infraestrutura`, `indicadores`);
- nomes estáveis e amigáveis para cliente.

Características:

- denormalização controlada;
- índice geoespacial e por filtros comuns;
- atualização por materialização incremental.

---

## 6) Padrão de nomenclatura e contrato

### Código Python (interno)

- seguir PEP 8 (`snake_case`).

### Contrato externo (Mongo/API)

- manter padrão único do produto (recomendado: `camelCase`);
- usar aliases no FastAPI/Pydantic quando necessário.

Exemplo de estratégia no backend:

- modelos internos em `snake_case`;
- serialização externa com aliases `camelCase`;
- `response_model` versionado por endpoint (`v1`, `v2`...).

---

## 7) Estratégia de materialização

Fluxo recomendado:

1. Bronze/Silver/Gold (ETL atual);
2. Gold canônico validado;
3. Job de materialização para read model (`gold -> mongo_read`);
4. API lê somente read model.

Benefícios:

- mudanças de frontend não quebram o pipeline canônico;
- reprocessamento histórico sem acoplamento à API;
- governança e produto evoluem em ritmos diferentes.

---

## 8) Regras de qualidade de dados (mínimas para MVP)

Obrigatórias por registro de escola no read model:

- `escolaIdInep` válido;
- `municipioIdIbge` válido;
- `localizacao.type == "Point"`;
- `localizacao.coordinates = [longitude, latitude]`;
- sem tipos não serializáveis para BSON (ex.: `numpy.ndarray`).

Checks sugeridos por execução:

- `% escolas com coordenadas`;
- `% escolas com indicadores`;
- total de documentos atualizados/inseridos;
- distribuição por município para detectar outliers.

---

## 9) Índices recomendados no Mongo (coleção `escolas`)

1. Único: `escolaIdInep`
2. Geoespacial: `localizacao` (`2dsphere`)
3. Filtro: `municipioIdIbge`
4. Filtro: `dependenciaAdm`
5. Filtro: `tipoLocalizacao`
6. Opcional composto para buscas frequentes:
   - `(municipioIdIbge, dependenciaAdm, tipoLocalizacao)`

---

## 10) Contrato da API (FastAPI) — diretriz

### Endpoints de leitura para MVP

- `GET /v1/escolas` (filtros por município, rede, tipo de localização)
- `GET /v1/escolas/{escolaIdInep}`
- `GET /v1/escolas/geo` (bbox/raio para mapa)
- `GET /v1/escolas/metrics/summary` (agregações básicas)

### Boas práticas

- paginação obrigatória;
- filtros com limites e validação;
- seleção de campos (`fields`) para reduzir payload;
- cache para consultas de mapa e agregações;
- versionamento explícito (`/v1`).

---

## 11) Roadmap de modularização (multi-domínio)

## Fase 1 — MVP robusto (agora)

- consolidar educação PB (schema estável + índices + métricas de qualidade);
- documentar contrato `v1`.

## Fase 2 — Convergência canônica

- introduzir dimensões conformadas (`tempo`, `localidade`, `instituição`);
- alinhar chaves comuns para educação/saúde/economia.

## Fase 3 — Novos domínios

- adicionar fatos de saúde/profissões/economia;
- criar read models específicos por produto/tela.

## Fase 4 — Camada de inteligência

- score composto de risco/oportunidade;
- benchmarks territoriais;
- trilhas de explicabilidade dos indicadores.

---

## 12) Decisão arquitetural formal (ADR resumido)

**Decisão:** adotar arquitetura em duas camadas: canônico dimensional + read model de aplicação.  
**Status:** aprovado para o MVP.  
**Motivo:** atender velocidade de produto sem perder governança e escalabilidade institucional.  
**Trade-off:** maior complexidade operacional (mais uma etapa de materialização), compensada por maior resiliência e evolução controlada.

---

## 13) Riscos e mitigação

1. **Divergência entre canônico e read model**  
   Mitigação: job idempotente + testes de contrato + reconciliação por contagem/hash.

2. **Quebra de frontend por mudança de campos**  
   Mitigação: versionamento de API e de schema (`schemaVersion`).

3. **Custos de processamento crescentes**  
   Mitigação: incremental por partição e atualização por delta.

4. **Inconsistência geográfica**  
   Mitigação: validação de coordenadas, fallback de geocode, auditoria por município.

---

## 14) Definição de pronto (DoD) para dados do MVP

Um ciclo de dados é considerado pronto quando:

- pipeline executa sem erro;
- qualidade mínima passa (regras da seção 8);
- índices críticos existem;
- contrato API `v1` está documentado;
- documento de escola está no schema oficial;
- variação de volume está explicada no changelog de dados.

---

## 15) Próximas ações recomendadas (curto prazo)

1. Adicionar `schemaVersion` em cada documento da coleção `escolas`.
2. Criar teste de contrato do documento de escola (shape + tipos).
3. Criar índices geoespaciais e de filtro caso não estejam criados.
4. Publicar mini catálogo de campos (descrição, tipo, origem).
5. Definir política de versionamento de contratos da API (`v1`, `v1.1`, `v2`).

---

## 16) Resumo executivo

Para o ODIN, a melhor estratégia não é escolher entre dimensional ou modelagem para aplicação.  
A estratégia correta é:

- **Canônico dimensional** para memória institucional, qualidade e expansão;
- **Read model amigável** para velocidade de produto e UX.

Essa arquitetura permite entregar o MVP de Educação na Paraíba agora, sem comprometer o crescimento para Saúde, Profissões, Economia e demais módulos.

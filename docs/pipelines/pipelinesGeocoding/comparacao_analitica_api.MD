Relatório Técnico - Ferramentas de Geocodificação

Este relatório apresenta um levantamento e análise comparativa de APIs e bibliotecas de geocodificação, considerando opções open-source, pagas e gratuitas. O objetivo é identificar as soluções mais adequadas para projetos que envolvem localização geográfica e integração com dados espaciais, como o caso da geocodificação de escolas no estado da Paraíba.

# Levantamento de Ferramentas e APIs de Geocodificação

Para atender à necessidade de uma solução sustentável, foram identificadas diversas ferramentas geocódigos, divididas entre soluções Open-Source e Auto-Hospedáveis e soluções Comerciais e Fremium. Dentre as opções open-source estão: o **Nominatim (OpenStreetMap)**, um software e serviço público amplamente utilizado e ideal para grande volume de requisições sem custos de licença; o **Pelias**, um geocoder open-source baseado em Elasticsearch, excelente para implementação de _self-hosting_ e controle total dos dados; e o **Photon**, mantido pela Komoot e baseado em dados do OpenStreetMap, conhecido por sua alta velocidade de pesquisa. Já as opções comerciais incluem o **Google Maps Geocoding API** (referência de alta precisão, mas com modelo _pay-as-you-go_), o **Mapbox Geocoding API** (alternativa comercial robusta e concorrente direto do Google, com planos gratuitos limitados), o **OpenCage API** (serviço comercial baseado em dados abertos, com planos pagos e um _free tier_ previsível), e o **LocationIQ e MapQuest** (alternativas comerciais de baixo custo e fácil integração, baseadas no OpenStreetMap, representando uma solução híbrida de baixo custo).

# Matriz Comparativa das Ferramentas

| **Provedor** | **Tipo** | **Custo** | **Precisão/Cobertura** | **Limites/Quota** | **Complexidade** |     |
| --- | --- | --- | --- | --- | --- | --- |
| Nominatim (OSM) | Open-source | Grátis (restrições públicas) | Boa, depende de OSM | Uso público limitado | Baixa |     |
| Pelias | Open-source | Grátis (infra custo) | Depende dos dados importados | Sem limites (self-host) | Alta |     |
| Photon | Open-source | Grátis (infra custo) | Boa para busca e typeahead | Sem limites (self-host) | Média |     |
| Google Maps | Comercial | Pago por uso | Excelente precisão global | Altos limites pagos | Baixa |     |
| Mapbox | Comercial | Freemium | Muito boa | Batch e limites razoáveis | Baixa-média |     |
| OpenCage | Comercial | Planos mensais | Boa, combina várias fontes | Limites brandos | Baixa |     |
| nIQ / MapQuest | Comercial | Free tier + planos pagos | Boa | Limites generosos | Baixa |     |

O

# Pontos negativos ao adotar cada uma das API's

O **Nominatim (OSM)** apresenta como principal dificuldade suas severas restrições de uso em servidores públicos, limitando o número de requisições e tornando o desempenho instável em cenários de alta demanda. O **Pelias**, embora seja open-source e escalável, exige infraestrutura própria e configuração complexa com Elasticsearch, além de manutenção contínua dos dados locais, o que eleva o custo técnico de implantação. O **Photon**, também baseado em dados do OpenStreetMap, requer hospedagem e atualizações regulares da base de dados para manter a precisão, o que implica esforço operacional constante. Já o **Google Maps Geocoding API** é a solução mais precisa e simples de usar, porém enfrenta o maior obstáculo no custo elevado por requisição e no risco jurídico de violar os Termos de Uso ao tentar contornar o limite gratuito com múltiplas contas. O **Mapbox** oferece boa precisão e interface moderna, mas seu plano gratuito é restrito e os custos crescem rapidamente conforme o volume de uso aumenta. O **OpenCage** combina diversas fontes abertas e é fácil de integrar, contudo apresenta menor precisão em áreas rurais e custos fixos mensais, o que pode inviabilizar projetos de baixo orçamento. Por fim, o **LocationIQ / MapQuest** representa uma opção comercial de baixo custo e limites generosos, mas depende de conectividade estável e sofre limitações de desempenho durante picos de uso, o que pode comprometer sua confiabilidade em ambientes de alta carga.

**O Dilema da API Google Geocoding**

A preferência pela API do Google é tecnicamente justificada por sua **eficácia, simplicidade de uso** e pelos avanços introdutórios já conquistados pela equipe. A inviabilidade técnica de uma mudança de API é evidente, dado o custo de reengenharia e a curva de aprendizado de uma alternativa.

No entanto, a dependência dessa solução se choca com uma **barreira de custo crítica**: o limite de uso gratuito de **\$200 (crédito fixo único)** foi rapidamente esgotado, apenas considerando a demanda das escolas públicas, o que sinaliza a inviabilidade do modelo atual para o escopo regional completo.

**Risco de Compliance e Sustentabilidade**

Para contornar o limite, a estratégia proposta de criar múltiplas contas de usuário para pulverizar o custo gratuito implica um **sério risco de compliance**. Essa tática viola os **Termos de Uso (ToS) da Google**, gerando complexidade de gerenciamento de múltiplas chaves de API e, mais gravemente, expondo o projeto a uma vulnerabilidade jurídica.

O principal ponto de conflito neste debate hipotético é que a eficiência técnica atual ameaça a **sustentabilidade e o futuro comercial** do ODIN. A potencial violação dos ToS pode inviabilizar a celebração de contratos e a venda da aplicação a organizações interessadas, transformando uma decisão técnica viável em um obstáculo estratégico e legal intransponível para a escalabilidade e o sucesso de longo prazo do projeto.

O debate, portanto, se concentra em priorizar: **(A) a manutenção da API do Google**, aceitando o risco de compliance e a inviabilidade comercial futura, ou **(B) a busca urgente por uma alternativa geocódigo** com custos previsíveis e termos de uso claros, garantindo a longevidade e a capacidade de contratação do ODIN.

**Palavras-chave:** Projeto ODIN, Geocoding, Google API, Risco de Compliance, Sustentabilidade, Políticas Públicas.
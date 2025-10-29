
## **Documentação: Pipeline de Escolas \- Transform (Transformação e Geocodificação)**

### **Objetivo Principal**

O script (transform.py) é a segunda etapa do nosso pipeline de dados de escolas. O objetivo é usar a lista de escolas (previamente filtrada pela etapa extract) e **descobrir a latitude e a longitude exatas de cada uma**, usando os endereços.

Em termos simples: ele transforma um endereço (como "Rua da Escola, 123, Recife, PE") em coordenadas de mapa (como \-16.059°, \-45.156°).

### **Como Funciona: O Processo Passo a Passo**

O script é desenhado para ser eficiente e, acima de tudo, **robusto**. Ele tem mecanismos para não perder o progesso atual se falhar no meio do processo.

Aqui está o fluxo de execução:

## **1\. Pré-requisitos para Execução**

Antes de rodar este script, garanta que seu ambiente atende aos seguintes requisitos:

1. **Arquivo .env**: Na raiz do projeto, deve existir um arquivo .env contendo a chave da API do Google:  
   Ini, TOML  
   GOOGLE\_API\_KEY\="sua\_chave\_secreta\_aqui"

2. **Credenciais AWS**: O ambiente de execução deve ter permissão de leitura e escrita no bucket S3 configurado. Isso geralmente é feito configurando variáveis de ambiente (como AWS\_ACCESS\_KEY\_ID, AWS\_SECRET\_ACCESS\_KEY, etc.) ou através de uma Role (ex: em uma instância EC2 ou pod Kubernetes). A função get\_s3\_storage\_options() gerencia isso.  
3. **Dados de Entrada**: O arquivo da etapa de "Extract" (ex: intermediate\_escolas\_nordeste.parquet) deve existir na camada intermediate do S3.  
4. **Bibliotecas Python**: Todas as bibliotecas listadas nos import devem estar instaladas (ex: pandas, pandarallel, python-dotenv, geopy, s3fs/fsspec)

#### **2\.  Leitura dos Dados**

*Logo após, o script vai ao S3 (na camada intermediaria) e lê o aqruivo escolas\_nordeste.parquet, que foi o resultado da etapa de extração (extract). Este arquivo contém todas as escolas que queremos processar.

#### **3\.  Preparação dos Endereços**

* Não podemos simplesmente enviar o endereço de qualquer forma para o Google. Esta etapa faz uma "limpeza":  
  1. visita as várias colunas dos endereços(Rua, Número, Bairro, Município, UF, CEP).  
  2. Junta tudo em uma única string de texto, limpa e formatada (ex: DS\_ENDERECO, NU\_ENDERECO, NO\_BAIRRO, NO\_MUNICIPIO, SG\_UF, CO\_CEP).  
  3. **Otimização crucial:** nessa etapa de limpeza, remove-se endereços duplicados. Se 10 escolas diferentes estiverem registadas exatamente no mesmo endereço (por exemplo, no mesmo complexo educacional), só precisamos requisitar ao Google esse endereço apeans *uma vez*. Isto poupa muito tempo e dinheiro (custos de API).

#### **4\.  O Mecanismo de "Checkpoint"**

* Antes de começar o trabalho pesado, o script verifica se existe um arquivo local chamado geocoding\_checkpoint.parquet.  
* **Se o documento existir:** O script lê-o e vê todas os endereços que *já foram processadas* com sucesso num momento anterior. Ele compara essa lista com a lista total de endereços e processa *apenas* as que são novas.  
* **Se não existir:** Tudo bem, ele assume que é a primeira vez que está rodadndo e processa a lista completa.

Porquê isso é tão importante?  
A geocodificação pode demorar horas. Se o script rodar durante 3 horas, processar 50.000 endereços e depois falhar (por exemplo, a internet cair), não queremos começar do zero. Com esse mecanismo, da próxima vez que rodarmos o script, ele vai se "lembrar" das 50.000 que já fez e começar a partir daí.

#### **5\.  A Geocodificação Paralela**

* Agora que ele tem a lista de endereços *novos* para processar, ele começa o trabalho.  
* Ele usa a biblioteca pandarallel, o que significa que, em vez de processar um endereço de cada vez (em série), ele processa várias ao mesmo tempo (em paralelo), usando todos os núcleos do processador do computador.  
* Para cada endereço, ele:  
  1. Chama a função geocode\_google\_process.  
  2. Envia o endereço para a API do Google.  
  3. Espera uma pequena pausa (0.05s) para não sobrecarregar a API.  
  4. Recebe de volta a latitude e longitude.  
  5. Se o Google não encontrar o endereço, ele simplesmente retorna None (vazio) e segue em frente.

#### **6\.  Salvar o Progresso (Checkpoint)**

* Assim que os novos endereços são processados, o script junta os novos resultados com os resultados antigos (que ele leu do checkpoint no passo 4).  
* Depois, ele **reescreve o ficheiro geocoding\_checkpoint.parquet** localmente com a lista completa e atualizada.

#### **7\. Envio Final para o S3**

* Com o trabalho de geocodificação terminado , o script pega no DataFrame final e completo.  
* Ele salva este resultado na camada processed do S3, com o nome escolas\_nordeste\_geocoded.parquet.  
* Este é o "produto final": uma tabela com todas as escolas e as suas coordenadas geográficas.

### **Resumo das Funções Auxiliares**

* \_get\_api\_key(): Apenas carrega e valida a chave da API do Google.  
* geocode\_google\_process(endereço, chave): A função "operária". É ela que, para *um* endereço, fala com o Google e devolve a lat/lon. É chamada milhares de vezes em paralelo.  
* create\_address\_dataframe(df): A função de "limpeza". Pega no DataFrame gigante e devolve uma lista de endereços únicos.  
* manage\_progress(df\_total, caminho\_checkpoint): A função "cérebro". Decide quais os endereços que precisam ser processadas e quais já estão prontos.

## **8\. Como Executar**

1. Certifique-se de que os **Pré-requisitos** (passo 1\) estão atendidos.  
2. Navegue até o diretório raiz do projeto.  
3. Execute o script Python (assumindo que este arquivo se chame transform\_geocode.py e esteja dentro de src/pipelines/):  
   ```Bash
   python \-m src.pipelines.transform\_geocode

4. Acompanhe o progresso pelo log no console e pela barra de progresso do pandarallel.
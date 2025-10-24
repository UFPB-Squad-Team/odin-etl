Com certeza\! Aqui está uma documentação detalhada do processo de transformação (transform) implementado no seu script. Este documento é perfeito para ser incluído na sua Pull Request (PR) ou na Wiki interna do projeto.

---

# **Documentação: Job de Transformação (Geocodificação)**

## **1\. Visão Geral e Propósito**

Este script representa a etapa de **Transformação** do pipeline de dados das escolas. Seu principal objetivo é enriquecer os dados brutos (extraídos na etapa anterior) com informações de geolocalização (latitude e longitude).

Para fazer isso, o script:

1. Lê os dados consolidados da camada intermediate do S3.  
2. Constrói um endereço completo e padronizado para cada escola.  
3. Otimiza o processo **removendo endereços duplicados** para evitar chamadas desnecessárias e reduzir custos com a API.  
4. Utiliza a API **GoogleV3 (Geocoding)** para obter as coordenadas de cada endereço único.  
5. Executa a geocodificação em **paralelo** usando pandarallel para acelerar massivamente o processamento.  
6. Implementa um sistema de **checkpoint local** para que o job possa ser interrompido e retomado sem perder progresso.  
7. Salva o resultado final (dados das escolas \+ latitude/longitude) na camada processed do S3.

## **2\. Pré-requisitos para Execução**

Antes de rodar este script, garanta que seu ambiente atende aos seguintes requisitos:

1. **Arquivo .env**: Na raiz do projeto, deve existir um arquivo .env contendo a chave da API do Google:  
   Ini, TOML  
   GOOGLE\_API\_KEY\="sua\_chave\_secreta\_aqui"

2. **Credenciais AWS**: O ambiente de execução deve ter permissão de leitura e escrita no bucket S3 configurado. Isso geralmente é feito configurando variáveis de ambiente (como AWS\_ACCESS\_KEY\_ID, AWS\_SECRET\_ACCESS\_KEY, etc.) ou através de uma Role (ex: em uma instância EC2 ou pod Kubernetes). A função get\_s3\_storage\_options() gerencia isso.  
3. **Dados de Entrada**: O arquivo da etapa de "Extract" (ex: intermediate\_escolas\_nordeste.parquet) deve existir na camada intermediate do S3.  
4. **Bibliotecas Python**: Todas as bibliotecas listadas nos import devem estar instaladas (ex: pandas, pandarallel, python-dotenv, geopy, s3fs/fsspec).

## **3\. Fluxo de Execução (Função run())**

O script é orquestrado pela função run(), que segue estes passos:

### **Passo 1: Configuração e Leitura**

* Carrega as configurações do projeto (load\_config()).  
* Obtém a chave da API do Google de forma segura (\_get\_api\_key()).  
* Lê o arquivo Parquet da camada intermediate do S3 para um DataFrame pandas (df\_full).

### **Passo 2: Preparação dos Endereços**

* Chama a função create\_address\_dataframe() para:  
  1. Selecionar apenas as colunas de endereço necessárias.  
  2. Concatenar as partes (Rua, Número, Bairro, Município, UF, CEP) em uma única string de endereço (coluna\_endereco\_final).  
  3. **Otimização-Chave:** Remover todas as linhas com endereços duplicados. Isso garante que só geocodificamos cada endereço *uma única vez*.

### **Passo 3: Gerenciamento de Progresso (Checkpoint)**

* Chama a função manage\_progress() para verificar se um arquivo de checkpoint local (ex: data/checkpoints/geocoding\_progress.parquet) já existe.  
* **Se o checkpoint existe**:  
  * Ele é lido (df\_ja\_processado).  
  * O script identifica quais endereços *já foram* geocodificados.  
  * O DataFrame de entrada é filtrado, deixando apenas os endereços *ainda não processados* (df\_para\_processar).  
* **Se o checkpoint não existe**:  
  * O script começa do zero. df\_ja\_processado fica vazio e df\_para\_processar contém todos os endereços únicos.

### **Passo 4: Geocodificação Paralela**

* Se o df\_para\_processar não estiver vazio, o script inicia a geocodificação:  
  1. **functools.partial**: É usada para criar uma "nova" função (geocode\_with\_key) que "congela" o argumento api\_key. Isso é necessário para passar a chave para a função que será executada em paralelo.  
  2. **parallel\_apply**: A pandarallel aplica a função geocode\_with\_key em múltiplos processos/CPUs, acelerando drasticamente o job.  
  3. A função geocode\_google\_process (o "worker" paralelo) retorna uma pd.Series com \[latitude, longitude\], que é desempacotada em novas colunas no DataFrame df\_para\_processar.

### **Passo 5: Atualização do Checkpoint**

* Os resultados novos (df\_para\_processar) são concatenados com os resultados antigos (df\_ja\_processado).  
* O DataFrame completo e atualizado (df\_final) é salvo localmente no arquivo de checkpoint. Se o script falhar ou for interrompido agora, ele recomeçará deste ponto na próxima execução.

### **Passo 6: Carregamento Final (Load)**

* O DataFrame final, contendo todos os endereços únicos geocodificados, é salvo em formato Parquet na camada processed do S3 (ex: s3://bucket/processed/escolas\_nordeste\_geocoded.parquet).

## **4\. Análise das Funções Auxiliares**

* \_get\_api\_key()  
  * **O que faz**: Carrega o .env e busca a variável GOOGLE\_API\_KEY.  
  * **Por que existe**: Isola a lógica de gerenciamento de segredos e falha rapidamente (raise ValueError) se a chave não for encontrada.  
* geocode\_google\_process(endereco, api\_key)  
  * **O que faz**: Função "worker" que executa em cada processo paralelo. Recebe *um* endereço e a chave.  
  * **Design**:  
    * Importa GoogleV3 e time *dentro* da função. Isso é uma prática recomendada pela pandarallel para evitar problemas de serialização de objetos complexos entre os processos.  
    * Usa geopy.geocoders.GoogleV3 para consultar a API.  
    * time.sleep(0.05): Adiciona uma pequena pausa. (Nota: O cliente GoogleV3 do geopy já gerencia o rate limiting (QPS) automaticamente, mas isso pode ser uma segurança extra).  
    * Retorna pd.Series(\[lat, lon\]) em caso de sucesso ou pd.Series(\[None, None\]) em caso de falha, permitindo que o .apply funcione corretamente.  
* create\_address\_dataframe(df, columns, final\_col\_name)  
  * **O que faz**: Limpa e prepara os dados de endereço.  
  * **Por que existe**: Centraliza a lógica de criação da "chave" de geocodificação (o endereço completo) e, o mais importante, **deduplica** os dados antes de gastar dinheiro com a API.  
* manage\_progress(df\_input, checkpoint\_path, address\_col\_name)  
  * **O que faz**: Implementa a lógica de "resumo" (resume).  
  * **Por que existe**: Geocodificação de dezenas de milhares de endereços pode levar horas e é cara. Se o script falhar na metade, esta função garante que não vamos reprocessar (e pagar por) endereços que já temos a resposta.

## **5\. Como Executar**

1. Certifique-se de que os **Pré-requisitos** (passo 2\) estão atendidos.  
2. Navegue até o diretório raiz do projeto.  
3. Execute o script Python (assumindo que este arquivo se chame transform\_geocode.py e esteja dentro de src/pipelines/):  
   Bash  
   python \-m src.pipelines.transform\_geocode

4. Acompanhe o progresso pelo log no console e pela barra de progresso do pandarallel.
## **Documentação do Módulo de Extração e Filtragem de Dados do Censo Escolar**

## 

## **(Documentação em estágio beta que serve mais para o aprendizado do uso do github)**

---

## **⚙️ Configuração Inicial**

O módulo configura o *logging* e carrega variáveis de ambiente e configurações do projeto.

### **📝 Dependências**

| Pacote/Módulo | Descrição |
| :---- | :---- |
| logging | Utilizado para registrar mensagens de avisos e erros durante a execução. |
| pandas (pd) | Biblioteca essencial para manipulação e análise de dados (DataFrames). |
| dotenv (load\_dotenv) | Carrega variáveis de ambiente (como chaves de acesso do S3) de um arquivo chamado .env |
| src.common.utils | Importa funções auxiliares de outro arquivo no projeto(utils). |
| \- get\_s3\_storage\_options | Obtém as credenciais ou opções de armazenamento para acesso ao S3. |
| \- load\_config | Carrega as configurações do projeto (e.g., de um arquivo YAML). |
| \- read\_zipped\_file\_from\_s3 | Função para ler um arquivo compactado (ZIP) diretamente do S3. |

### **🪵 Configuração de Logging**

O *logging* é configurado para registrar mensagens informativas.

logging.basicConfig(  
    level=logging.INFO,  
    format\="%(asctime)s \- \[%(levelname)s\] \- %(message)s",  
)

---

## **🛠️ Funções**

### **\_filter\_data**

Esta função recebe um DataFrame e um dicionário de configurações de filtro (filter\_config) e retorna o DataFrame filtrado.

def \_filter\_data(df: pd.DataFrame, filter\_config: dict) \-\> pd.DataFrame:

| Parâmetro | Tipo | Descrição |
| :---- | :---- | :---- |
| df | pd.DataFrame | O DataFrame com os dados brutos a serem filtrados. |
| filter\_config | dict | Dicionário contendo os critérios de filtragem. Espera-se as chaves: filtro\_uf, filtro\_dependencia\_adm e filtro\_situacao\_funcionamento.  |

| Retorno | Tipo | Descrição |
| :---- | :---- | :---- |
| df\_filtered | pd.DataFrame | O DataFrame resultante após a aplicação dos filtros. |

#### **🎯 Filtros Aplicados**

1. **Unidade Federativa (UF):** SG\_UF deve estar contido na lista de filter\_config\["filtro\_uf"\].  
2. **Dependência Administrativa:** TP\_DEPENDENCIA deve estar contido na lista de filter\_config\["filtro\_dependencia\_adm"\].  
3. **Situação de Funcionamento:** TP\_SITUACAO\_FUNCIONAMENTO deve ser **igual** a filter\_config\["filtro\_situacao\_funcionamento"\].

A função registra o número de registros selecionados após a filtragem.

---

### 

### 

### 

### 

### 

### 

### 

### 

### 

### **run**

Orquestra a extração do Censo Escolar do S3, aplica filtros  e salva o resultado na camada 'intermediate' do S3.

#### **🔄 Fluxo de Execução**

1. **Início do Job:** Registra o início do processo.  
2. **Carregamento de Configurações:**  
   * Chama load\_dotenv() para carregar variáveis de ambiente.  
   * Carrega a configuração completa do projeto via load\_config(), extraindo as seções relevantes (s3\_config, source\_config, geocode\_config).  
3. **Extração do S3:**  
   * Tenta ler o arquivo compactado do S3 usando read\_zipped\_file\_from\_s3.  
   * O caminho do arquivo de origem é construído usando o bucket\_name, a raw\_folder e o output\_filename da configuração.  
   * Parâmetros de leitura do CSV (delimiter, encoding, on\_bad\_lines, low\_memory) são passados via read\_params.  
4. **Filtragem de Dados:**  
   * Chama a função \_filter\_data para aplicar os filtros ao DataFrame bruto (df\_raw), usando as configurações de filtro (geocode\_config).  
5. **Salvamento no S3 (Camada Intermediate):**  
   * Define o output\_s3\_path para a camada intermediate do *bucket*. O arquivo é nomeado como escolas\_nordeste.parquet.  
   * Obtém as opções de armazenamento do S3 via get\_s3\_storage\_options().  
   * Salva o DataFrame filtrado (df\_filtered) no S3 no formato **Parquet**, usando o método df\_filtered.to\_parquet().  
6. **Fim do Job:** Registra o sucesso da operação.  
7. **Tratamento de Erros:** Qualquer exceção durante o processo é capturada, registrada com nível ERROR e, em seguida, relançada (raise) para interromper a execução.

---

## **🚀 Execução**

O bloco if \_\_name\_\_ \== "\_\_main\_\_": garante que a função run() seja executada quando o script for chamado diretamente.

Python

if \_\_name\_\_ \== "\_\_main\_\_":  
    run()  

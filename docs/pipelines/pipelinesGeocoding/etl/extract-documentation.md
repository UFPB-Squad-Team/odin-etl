## **Documentação do Módulo de Extração e Filtragem de Dados do Censo Escolar**

##

## **(Documentação em estágio beta que serve mais para o aprendizado do uso do github)**

---

## **⚙️ Configuração Inicial**

O módulo configura o _logging_ e carrega variáveis de ambiente e configurações do projeto.

### **📝 Dependências**

| Pacote/Módulo               | Descrição                                                                              |
| :-------------------------- | :------------------------------------------------------------------------------------- |
| logging                     | Utilizado para registrar mensagens de avisos e erros durante a execução.               |
| pandas (pd)                 | Biblioteca essencial para manipulação e análise de dados (DataFrames).                 |
| dotenv (load_dotenv)        | Carrega variáveis de ambiente (como chaves de acesso do S3) de um arquivo chamado .env |
| src.common.utils            | Importa funções auxiliares de outro arquivo no projeto(utils).                         |
| \- get_s3_storage_options   | Obtém as credenciais ou opções de armazenamento para acesso ao S3.                     |
| \- load_config              | Carrega as configurações do projeto (e.g., de um arquivo YAML).                        |
| \- read_zipped_file_from_s3 | Função para ler um arquivo compactado (ZIP) diretamente do S3.                         |

### **🪵 Configuração de Logging**

O _logging_ é configurado para registrar mensagens informativas.

logging.basicConfig(  
 level=logging.INFO,  
 format\="%(asctime)s \- \[%(levelname)s\] \- %(message)s",  
)

---

## **🛠️ Funções**

### **\_filter_data**

Esta função recebe um DataFrame e um dicionário de configurações de filtro (filter_config) e retorna o DataFrame filtrado.

def \_filter_data(df: pd.DataFrame, filter_config: dict) \-\> pd.DataFrame:

| Parâmetro     | Tipo         | Descrição                                                                                                                              |
| :------------ | :----------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| df            | pd.DataFrame | O DataFrame com os dados brutos a serem filtrados.                                                                                     |
| filter_config | dict         | Dicionário contendo os critérios de filtragem. Espera-se as chaves: filtro_uf, filtro_dependencia_adm e filtro_situacao_funcionamento. |

| Retorno     | Tipo         | Descrição                                            |
| :---------- | :----------- | :--------------------------------------------------- |
| df_filtered | pd.DataFrame | O DataFrame resultante após a aplicação dos filtros. |

#### **🎯 Filtros Aplicados**

1. **Unidade Federativa (UF):** SG_UF deve estar contido na lista de filter_config\["filtro_uf"\].
2. **Dependência Administrativa:** TP_DEPENDENCIA deve estar contido na lista de filter_config\["filtro_dependencia_adm"\].
3. **Situação de Funcionamento:** TP_SITUACAO_FUNCIONAMENTO deve ser **igual** a filter_config\["filtro_situacao_funcionamento"\].

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

Orquestra a extração do Censo Escolar do S3, aplica filtros e salva o resultado na camada 'intermediate' do S3.

#### **🔄 Fluxo de Execução**

1. **Início do Job:** Registra o início do processo.
2. **Carregamento de Configurações:**
   - Chama load_dotenv() para carregar variáveis de ambiente.
   - Carrega a configuração completa do projeto via load_config(), extraindo as seções relevantes (s3_config, source_config, geocode_config).
3. **Extração do S3:**
   - Tenta ler o arquivo compactado do S3 usando read_zipped_file_from_s3.
   - O caminho do arquivo de origem é construído usando o bucket_name, a raw_folder e o output_filename da configuração.
   - Parâmetros de leitura do CSV (delimiter, encoding, on_bad_lines, low_memory) são passados via read_params.
4. **Filtragem de Dados:**
   - Chama a função \_filter_data para aplicar os filtros ao DataFrame bruto (df_raw), usando as configurações de filtro (geocode_config).
5. **Salvamento no S3 (Camada Intermediate):**
   - Define o output_s3_path para a camada intermediate do _bucket_. O arquivo é nomeado como escolas_nordeste.parquet.
   - Obtém as opções de armazenamento do S3 via get_s3_storage_options().
   - Salva o DataFrame filtrado (df_filtered) no S3 no formato **Parquet**, usando o método df_filtered.to_parquet().
6. **Fim do Job:** Registra o sucesso da operação.
7. **Tratamento de Erros:** Qualquer exceção durante o processo é capturada, registrada com nível ERROR e, em seguida, relançada (raise) para interromper a execução.

---

## **🚀 Execução**

O bloco if \_\_name\_\_ \== "\_\_main\_\_": garante que a função run() seja executada quando o script for chamado diretamente.

Python

if \_\_name\_\_ \== "\_\_main\_\_":  
 run()

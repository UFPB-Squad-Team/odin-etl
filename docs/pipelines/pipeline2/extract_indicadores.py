# =============================================================
# BAIXAR INDICADORES EDUCACIONAIS DO INEP – ESCOLAS DO NORDESTE
# Versão com DOTENV para segurança das credenciais
# =============================================================

import os
import pandas as pd
import basedosdados as bd
from dotenv import load_dotenv


# =============================================================
# 0. Carregar Billing ID do arquivo .env
# =============================================================

load_dotenv()  # carrega variáveis do arquivo .env

billing_id = os.getenv("GOOGLE_BILLING_ID")

if not billing_id:
    raise ValueError(
        "❌ Billing ID não encontrado.\n"
        "Crie um arquivo .env com a linha:\n"
        "GOOGLE_BILLING_ID=seu_billing_id_aqui"
    )

print("Billing ID carregado com sucesso via .env.")


# =============================================================
# 1. Consulta SQL ao BigQuery via Base dos Dados
# =============================================================

query = """
SELECT 
    * 
FROM `basedosdados.br_inep_indicadores_educacionais.escola` AS dados
LEFT JOIN (
    SELECT DISTINCT id_municipio, nome
    FROM `basedosdados.br_bd_diretorios_brasil.municipio`
) AS diretorio_id_municipio
    ON dados.id_municipio = diretorio_id_municipio.id_municipio
LEFT JOIN (
    SELECT DISTINCT id_escola, nome, latitude, longitude
    FROM `basedosdados.br_bd_diretorios_brasil.escola`
) AS diretorio_id_escola
    ON dados.id_escola = diretorio_id_escola.id_escola
WHERE CAST(dados.id_municipio AS STRING) LIKE '2%'
"""

print("Iniciando consulta SQL...")
df = bd.read_sql(query=query, billing_project_id=billing_id)
print(f"Consulta concluída. Linhas retornadas: {df.shape[0]}")


# =============================================================
# 2. Salvar em arquivo Parquet
# =============================================================

saida = "indicadores_educacionais_escolas_NE.parquet"
df.to_parquet(saida)

print(f"Arquivo salvo com sucesso em: {saida}")

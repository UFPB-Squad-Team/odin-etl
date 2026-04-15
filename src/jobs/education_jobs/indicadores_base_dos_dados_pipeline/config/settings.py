"""Local constants for the indicadores Base dos Dados pipeline."""

INDICADORES_SILVER_FILENAME = "indicadores_base_dos_dados.parquet"
INDICADORES_GOLD_FILENAME = "indicadores_base_dos_dados.parquet"

INDICADORES_QUERY_NORDESTE = """
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

# =============================================================
# PROCESSAMENTO DE INDICADORES INEP – ESCOLAS DO NORDESTE
# Versão transformada de Jupyter Notebook → Script Python
# =============================================================

import pandas as pd
import json


# =============================================================
# 1. Carregar dados
# =============================================================

df = pd.read_parquet("inep_indicadores_escolas_NE.parquet")
dicionario = pd.read_excel("dicionario_variaveis_inep.xlsx")

print("Dados carregados com sucesso.")
print(df.shape)


# =============================================================
# 2. Definir blocos de variáveis por nível de ensino
# =============================================================

niveis = {
    "ei": {
        "base": ["atu", "had", "dsu"],
        "afd_grupos": [f"afd_ei_grupo_{i}" for i in range(1, 6)],
        "ied": []
    },
    "ef_anos_iniciais": {
        "base": ["atu", "had", "dsu", "tdi",
                 "taxa_aprovacao", "taxa_reprovacao", "taxa_abandono", "tnr"],
        "afd_grupos": [f"afd_ef_anos_iniciais_grupo_{i}" for i in range(1, 6)],
        "ied": [f"ied_ef_anos_iniciais_nivel_{i}" for i in range(1, 7)]
    },
    "ef_anos_finais": {
        "base": ["atu", "had", "dsu", "tdi",
                 "taxa_aprovacao", "taxa_reprovacao", "taxa_abandono", "tnr"],
        "afd_grupos": [f"afd_ef_anos_finais_grupo_{i}" for i in range(1, 6)],
        "ied": [f"ied_ef_anos_finais_nivel_{i}" for i in range(1, 7)]
    },
    "em": {
        "base": ["atu", "had", "dsu", "tdi",
                 "taxa_aprovacao", "taxa_reprovacao", "taxa_abandono", "tnr"],
        "afd_grupos": [f"afd_em_grupo_{i}" for i in range(1, 6)],
        "ied": [f"ied_em_nivel_{i}" for i in range(1, 7)]
    }
}

cols_iniciais = [
    "ano", "id_municipio", "id_escola",
    "localizacao", "rede",
    "icg_nivel_complexidade_gestao_escola"
]

cols_dinamicas = []

for nivel, grupos in niveis.items():
    cols_dinamicas += [f"{col}_{nivel}" for col in grupos["base"]]
    cols_dinamicas += grupos["afd_grupos"]
    cols_dinamicas += grupos["ied"]

cols_geo = ["latitude", "longitude"]

cols = cols_iniciais + cols_dinamicas + cols_geo

df_test = df[cols].copy()
print(f"Total de colunas selecionadas: {len(cols)}")


# =============================================================
# 3. Criar variáveis finais agregadas (AFD e IED)
# =============================================================

# Educação Infantil
df_test["afd_ei"] = df_test["afd_ei_grupo_1"] + df_test["afd_ei_grupo_2"]

# EF anos iniciais
df_test["afd_ef_anos_iniciais"] = df_test["afd_ef_anos_iniciais_grupo_1"] + df_test["afd_ef_anos_iniciais_grupo_2"]
df_test["ied_ef_anos_iniciais"] = (
    df_test["ied_ef_anos_iniciais_nivel_1"] +
    df_test["ied_ef_anos_iniciais_nivel_2"] +
    df_test["ied_ef_anos_iniciais_nivel_3"]
)

# EF anos finais
df_test["afd_ef_anos_finais"] = df_test["afd_ef_anos_finais_grupo_1"] + df_test["afd_ef_anos_finais_grupo_2"]
df_test["ied_ef_anos_finais"] = (
    df_test["ied_ef_anos_finais_nivel_1"] +
    df_test["ied_ef_anos_finais_nivel_2"] +
    df_test["ied_ef_anos_finais_nivel_3"]
)

# Ensino médio
df_test["afd_em"] = df_test["afd_em_grupo_1"] + df_test["afd_em_grupo_2"]
df_test["ied_em"] = (
    df_test["ied_em_nivel_1"] +
    df_test["ied_em_nivel_2"] +
    df_test["ied_em_nivel_3"]
)


# =============================================================
# 4. Remover colunas *_grupo_* e *_nivel_*
# =============================================================

afd_cols_to_drop = [col for col in df_test.columns if "afd_" in col and "grupo" in col]
ied_cols_to_drop = [col for col in df_test.columns if "ied_" in col and "nivel" in col]

df_test.drop(columns=afd_cols_to_drop + ied_cols_to_drop, inplace=True, errors="ignore")

print("Colunas de grupos e níveis removidas.")


# =============================================================
# 5. Funções auxiliares e conversão para JSON
# =============================================================

def to_float(v):
    return None if pd.isna(v) else float(v)


def montar_json(linha):
    return {
        "ano": int(linha["ano"]),
        "id_municipio": int(linha["id_municipio"]),
        "id_escola": str(linha["id_escola"]),
        "localizacao": linha["localizacao"],
        "rede": linha["rede"],
        "icg_nivel_complexidade_gestao_escola": linha["icg_nivel_complexidade_gestao_escola"],

        "educacao_infantil": {
            "alunos_por_turma": to_float(linha["atu_ei"]),
            "horas_aula_diarias": to_float(linha["had_ei"]),
            "docentes_superior": to_float(linha["dsu_ei"]),
            "afd": to_float(linha["afd_ei"])
        },

        "fundamental_anos_iniciais": {
            "alunos_por_turma": to_float(linha["atu_ef_anos_iniciais"]),
            "horas_aula_diarias": to_float(linha["had_ef_anos_iniciais"]),
            "docentes_superior": to_float(linha["dsu_ef_anos_iniciais"]),
            "tdi": to_float(linha["tdi_ef_anos_iniciais"]),
            "taxa_aprovacao": to_float(linha["taxa_aprovacao_ef_anos_iniciais"]),
            "taxa_reprovacao": to_float(linha["taxa_reprovacao_ef_anos_iniciais"]),
            "taxa_abandono": to_float(linha["taxa_abandono_ef_anos_iniciais"]),
            "tnr": to_float(linha["tnr_ef_anos_iniciais"]),
            "afd": to_float(linha["afd_ef_anos_iniciais"]),
            "ied": to_float(linha["ied_ef_anos_iniciais"])
        },

        "fundamental_anos_finais": {
            "alunos_por_turma": to_float(linha["atu_ef_anos_finais"]),
            "horas_aula_diarias": to_float(linha["had_ef_anos_finais"]),
            "docentes_superior": to_float(linha["dsu_ef_anos_finais"]),
            "tdi": to_float(linha["tdi_ef_anos_finais"]),
            "taxa_aprovacao": to_float(linha["taxa_aprovacao_ef_anos_finais"]),
            "taxa_reprovacao": to_float(linha["taxa_reprovacao_ef_anos_finais"]),
            "taxa_abandono": to_float(linha["taxa_abandono_ef_anos_finais"]),
            "tnr": to_float(linha["tnr_ef_anos_finais"]),
            "afd": to_float(linha["afd_ef_anos_finais"]),
            "ied": to_float(linha["ied_ef_anos_finais"])
        },

        "ensino_medio": {
            "alunos_por_turma": to_float(linha["atu_em"]),
            "horas_aula_diarias": to_float(linha["had_em"]),
            "docentes_superior": to_float(linha["dsu_em"]),
            "tdi": to_float(linha["tdi_em"]),
            "taxa_aprovacao": to_float(linha["taxa_aprovacao_em"]),
            "taxa_reprovacao": to_float(linha["taxa_reprovacao_em"]),
            "taxa_abandono": to_float(linha["taxa_abandono_em"]),
            "tnr": to_float(linha["tnr_em"]),
            "afd": to_float(linha["afd_em"]),
            "ied": to_float(linha["ied_em"])
        },

        "geo": {
            "type": "Point",
            "coordinates": [
                to_float(linha["longitude"]),
                to_float(linha["latitude"])
            ]
        }
    }

print("Convertendo para JSON (pode levar alguns segundos)...")
docs = df_test.apply(montar_json, axis=1).tolist()

with open("escolas_todos_niveis.json", "w", encoding="utf-8") as f:
    json.dump(docs, f, ensure_ascii=False, indent=2)

print(f"Arquivo JSON gerado com {len(docs)} registros.")

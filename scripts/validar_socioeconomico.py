
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Constantes — Nordeste (9 UFs)
# ---------------------------------------------------------------------------

SILVER_DIR = Path("data/silver")
GOLD_PATH   = Path("data/gold/municipio_socioeconomico_nordeste.parquet")
GOLD_SETOR  = Path("data/gold/setor_socioeconomico_nordeste.parquet")
GOLD_BAIRRO = Path("data/gold/bairro_socioeconomico_nordeste.parquet")

DATASETS = [
    "basico",
    "demografia",
    "cor_ou_raca",
    "caracteristicas_domicilio1",
    "caracteristicas_domicilio2",
    "caracteristicas_domicilio3",
    "alfabetizacao",
    "parentesco",
    "obitos",
]

GRANULARIDADES = ["municipio", "setor", "bairro"]

# Benchmarks por UF (municípios e pop mínima esperada)
BENCHMARKS_UF = {
    "MA": {"municipios": 217, "pop_min": 6_500_000},
    "PI": {"municipios": 224, "pop_min": 3_200_000},
    "CE": {"municipios": 184, "pop_min": 8_700_000},
    "RN": {"municipios": 167, "pop_min": 3_300_000},
    "PB": {"municipios": 223, "pop_min": 3_800_000},
    "PE": {"municipios": 185, "pop_min": 9_000_000},
    "AL": {"municipios": 102, "pop_min": 3_100_000},
    "SE": {"municipios": 75,  "pop_min": 2_200_000},
    "BA": {"municipios": 417, "pop_min": 14_000_000},
}

MUNICIPIOS_ESPERADOS = 1794
POP_TOTAL_MIN = 53_000_000
POP_TOTAL_MAX = 60_000_000

# Sanity checks em capitais
CAPITAIS = {
    2507507: {"nome": "João Pessoa",  "pop_min": 700_000,   "pop_max": 900_000},
    2927408: {"nome": "Salvador",     "pop_min": 2_500_000, "pop_max": 3_000_000},
    2611606: {"nome": "Recife",       "pop_min": 1_400_000, "pop_max": 1_800_000},
    2304400: {"nome": "Fortaleza",    "pop_min": 2_400_000, "pop_max": 2_800_000},
}

COLUNAS_PCT = [
    "pct_criancas_0_9",
    "pct_idosos_60_mais",
    "pct_preta_parda",
    "pct_agua_rede_geral",
    "pct_esgoto_rede_geral",
    "pct_lixo_coletado",
    "taxa_analfabetismo_15_mais",
    "pct_responsavel_feminino",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(msg: str) -> None:
    print(f"  ✅  {msg}")

def _warn(msg: str) -> None:
    print(f"  ⚠️   {msg}")

def _err(msg: str, erros: list) -> None:
    print(f"  ❌  {msg}")
    erros.append(msg)

def _secao(titulo: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {titulo}")
    print(f"{'=' * 60}")

# ---------------------------------------------------------------------------
# 1. Silver
# ---------------------------------------------------------------------------

def validar_silver(erros: list) -> None:
    _secao("1 / 3 — ARQUIVOS SILVER")

    for gran in GRANULARIDADES:
        print(f"\n  [{gran}]")
        for dataset in DATASETS:
            arquivo = SILVER_DIR / f"ibge_censo2022_{gran}_{dataset}_nordeste.parquet"
            if arquivo.exists():
                df = pd.read_parquet(arquivo)
                _ok(f"{arquivo.name}  ({len(df)} registros)")
            else:
                _warn(f"Arquivo não encontrado: {arquivo.name}")


# ---------------------------------------------------------------------------
# 2. Gold
# ---------------------------------------------------------------------------

def validar_gold(erros: list) -> None:
    _secao("2 / 3 — ARQUIVOS GOLD")

    # --- Município ---
    print("\n  [município]")
    if not GOLD_PATH.exists():
        _err(f"Arquivo não encontrado: {GOLD_PATH}", erros)
    else:
        df = pd.read_parquet(GOLD_PATH)

        if len(df) >= MUNICIPIOS_ESPERADOS:
            _ok(f"Municípios: {len(df)} (esperado >= {MUNICIPIOS_ESPERADOS})")
        else:
            _err(f"Municípios: {len(df)} (esperado >= {MUNICIPIOS_ESPERADOS})", erros)

        pop_total = df["total_populacao"].sum()
        if POP_TOTAL_MIN <= pop_total <= POP_TOTAL_MAX:
            _ok(f"População total NE: {pop_total:,.0f}")
        else:
            _err(f"Pop total fora do range ({POP_TOTAL_MIN:,.0f}–{POP_TOTAL_MAX:,.0f}): {pop_total:,.0f}", erros)

        # Verificar capitais
        for id_ibge, info in CAPITAIS.items():
            capital = df[df["CD_MUN"].astype(str) == str(id_ibge)]
            if capital.empty:
                _warn(f"{info['nome']} ({id_ibge}) não encontrada no Gold")
            else:
                pop = int(capital["total_populacao"].iloc[0])
                if info["pop_min"] <= pop <= info["pop_max"]:
                    _ok(f"{info['nome']} — população: {pop:,}")
                else:
                    _err(f"{info['nome']} — população fora do esperado ({info['pop_min']:,}–{info['pop_max']:,}): {pop:,}", erros)

        # Verificar distribuição por UF
        if "uf" in df.columns:
            print("\n  [distribuição por UF]")
            for uf, bench in BENCHMARKS_UF.items():
                df_uf = df[df["uf"] == uf]
                if len(df_uf) == 0:
                    _err(f"  Nenhum município para UF={uf}", erros)
                elif len(df_uf) >= bench["municipios"] * 0.95:
                    _ok(f"  {uf}: {len(df_uf)} municípios (esperado ~{bench['municipios']})")
                else:
                    _warn(f"  {uf}: {len(df_uf)} municípios (esperado ~{bench['municipios']})")

        # Validar ranges percentuais
        for col in COLUNAS_PCT:
            if col not in df.columns:
                _warn(f"Coluna ausente: {col}")
                continue
            valores = df[col].dropna()
            if valores.empty:
                _warn(f"{col}: sem valores")
                continue
            fora = ((valores < 0) | (valores > 100)).sum()
            if fora == 0:
                _ok(f"{col}: {valores.min():.1f}% – {valores.max():.1f}%")
            else:
                _err(f"{col}: {fora} valor(es) fora de [0, 100]", erros)

    # --- Setor e Bairro ---
    for label, path in [("setor", GOLD_SETOR), ("bairro", GOLD_BAIRRO)]:
        print(f"\n  [{label}]")
        if path.exists():
            df = pd.read_parquet(path)
            _ok(f"{path.name}  ({len(df)} registros | pop: {df['total_populacao'].sum():,.0f})")
        else:
            _warn(f"{path.name} — ainda não gerado")


# ---------------------------------------------------------------------------
# 3. MongoDB
# ---------------------------------------------------------------------------

def validar_mongodb(erros: list) -> None:
    _secao("3 / 3 — MONGODB")

    mongo_uri = os.getenv("MONGO_URI")
    db_name   = os.getenv("MONGO_DB_NAME")

    if not mongo_uri or not db_name:
        _warn("MONGO_URI ou MONGO_DB_NAME não definidos no .env — pulando validação MongoDB")
        return

    try:
        from pymongo import MongoClient
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5_000)
        db = client[db_name]

        # --- municipio_indicadores ---
        print("\n  [municipio_indicadores]")
        col = db["municipio_indicadores"]
        total = col.count_documents({})
        _ok(f"Total de documentos: {total}")

        com_socio = col.count_documents({"socioeconomico": {"$exists": True}})
        if com_socio >= MUNICIPIOS_ESPERADOS:
            _ok(f"Documentos com 'socioeconomico': {com_socio}")
        elif com_socio > 0:
            _warn(f"Documentos com 'socioeconomico': {com_socio} (esperado >= {MUNICIPIOS_ESPERADOS})")
        else:
            _err(f"Nenhum documento com 'socioeconomico'", erros)

        # Verificar capitais no MongoDB
        for id_ibge, info in CAPITAIS.items():
            doc = col.find_one({"municipioIdIbge": id_ibge})
            if not doc:
                _warn(f"{info['nome']} ({id_ibge}) não encontrada no MongoDB")
            else:
                socio = doc.get("socioeconomico", {})
                pop = socio.get("populacao", {}).get("total")
                if pop and info["pop_min"] <= pop <= info["pop_max"]:
                    _ok(f"{info['nome']} — população: {pop:,}")
                elif pop:
                    _warn(f"{info['nome']} — população: {pop:,} (fora do esperado)")

        # --- setor_indicadores ---
        print("\n  [setor_indicadores]")
        col_setor = db["setor_indicadores"]
        total_setor = col_setor.count_documents({})
        com_socio_setor = col_setor.count_documents({"socioeconomico": {"$exists": True}})
        if total_setor == 0:
            _warn("Sem dados ainda")
        else:
            _ok(f"Total de documentos: {total_setor}")
            _ok(f"Documentos com 'socioeconomico': {com_socio_setor}")

        # --- bairro_indicadores ---
        print("\n  [bairro_indicadores]")
        col_bairro = db["bairro_indicadores"]
        total_bairro = col_bairro.count_documents({})
        com_socio_bairro = col_bairro.count_documents({"socioeconomico": {"$exists": True}})
        if total_bairro == 0:
            _warn("Sem dados ainda")
        else:
            _ok(f"Total de documentos: {total_bairro}")
            _ok(f"Documentos com 'socioeconomico': {com_socio_bairro}")

        client.close()

    except Exception as exc:
        _err(f"Erro ao conectar no MongoDB: {exc}", erros)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n🔍  VALIDAÇÃO — MÓDULO SOCIOECONÔMICO (Nordeste — 9 UFs)\n")

    erros: list = []

    validar_silver(erros)
    validar_gold(erros)
    validar_mongodb(erros)

    print(f"\n{'=' * 60}")
    if erros:
        print(f"  ❌  {len(erros)} erro(s) encontrado(s):\n")
        for e in erros:
            print(f"     • {e}")
        print()
        sys.exit(1)
    else:
        print("  ✅  Todas as validações passaram — Nordeste completo!")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()

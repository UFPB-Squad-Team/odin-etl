import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SILVER_DIR = Path("data/silver")
GOLD_PATH  = Path("data/gold/municipio_socioeconomico_pb.parquet")
GOLD_SETOR  = Path("data/gold/setor_socioeconomico_pb.parquet")
GOLD_BAIRRO = Path("data/gold/bairro_socioeconomico_pb.parquet")

DATASETS = [
    "basico",
    "demografia",
    "cor_ou_raca",
    "caracteristicas_domicilio2",
    "caracteristicas_domicilio3",
    "alfabetizacao",
    "parentesco",
]

GRANULARIDADES_SPRINT1 = ["municipio"]
GRANULARIDADES_SPRINT2 = ["setor", "bairro"]

MUNICIPIOS_ESPERADOS = 223
POP_TOTAL_MIN = 3_800_000
POP_TOTAL_MAX = 4_200_000

JP_ID   = 2507507
JP_POP_MIN = 700_000
JP_POP_MAX = 900_000

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
    print(f"\n{'=' * 55}")
    print(f"  {titulo}")
    print(f"{'=' * 55}")

# ---------------------------------------------------------------------------
# 1. Silver
# ---------------------------------------------------------------------------

def validar_silver(erros: list) -> None:
    _secao("1 / 3 — ARQUIVOS SILVER")

    for gran in ["municipio", "setor", "bairro"]:
        sprint = "Sprint 1" if gran == "municipio" else "Sprint 2"
        print(f"\n  [{sprint} — {gran}]")
        for dataset in DATASETS:
            arquivo = SILVER_DIR / f"ibge_censo2022_{gran}_{dataset}_pb.parquet"
            if arquivo.exists():
                df = pd.read_parquet(arquivo)
                _ok(f"{arquivo.name}  ({len(df)} registros)")
            elif gran == "municipio":
                _err(f"Arquivo não encontrado: {arquivo.name}", erros)
            else:
                print(f"  ⏳  {arquivo.name}  (pendente)")


# ---------------------------------------------------------------------------
# 2. Gold
# ---------------------------------------------------------------------------

def validar_gold(erros: list) -> None:
    _secao("2 / 3 — ARQUIVOS GOLD")

    # Município (Sprint 1 — obrigatório)
    print("\n  [município]")
    if not GOLD_PATH.exists():
        _err(f"Arquivo não encontrado: {GOLD_PATH}", erros)
    else:
        df = pd.read_parquet(GOLD_PATH)
        if len(df) == MUNICIPIOS_ESPERADOS:
            _ok(f"Municípios: {len(df)}")
        else:
            _err(f"Municípios: {len(df)} (esperado {MUNICIPIOS_ESPERADOS})", erros)

        pop_total = df["total_populacao"].sum()
        if POP_TOTAL_MIN <= pop_total <= POP_TOTAL_MAX:
            _ok(f"População total PB: {pop_total:,.0f}")
        else:
            _err(f"Pop total fora do range ({POP_TOTAL_MIN:,.0f}–{POP_TOTAL_MAX:,.0f}): {pop_total:,.0f}", erros)

        jp = df[df["CD_MUN"].astype(str) == str(JP_ID)]
        if jp.empty:
            _err(f"João Pessoa ({JP_ID}) não encontrada no Gold", erros)
        else:
            pop_jp = int(jp["total_populacao"].iloc[0])
            if JP_POP_MIN <= pop_jp <= JP_POP_MAX:
                _ok(f"João Pessoa — população: {pop_jp:,}")
            else:
                _err(f"João Pessoa — população fora do esperado: {pop_jp:,}", erros)

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

    # Setor e Bairro (Sprint 2 — informativo)
    for label, path in [("setor", GOLD_SETOR), ("bairro", GOLD_BAIRRO)]:
        print(f"\n  [{label}]")
        if path.exists():
            df = pd.read_parquet(path)
            _ok(f"{path.name}  ({len(df)} registros | pop: {df['total_populacao'].sum():,.0f})")
        else:
            print(f"  ⏳  {path.name}  (pendente)")


# ---------------------------------------------------------------------------
# 3. MongoDB
# ---------------------------------------------------------------------------

def validar_mongodb(erros: list) -> None:
    _secao("3 / 3 — MONGODB")

    mongo_uri = os.getenv("MONGO_URI")
    db_name   = os.getenv("MONGO_DB_NAME")

    if not mongo_uri or not db_name:
        _err("MONGO_URI ou MONGO_DB_NAME não definidos no .env — pulando validação MongoDB", erros)
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
        else:
            _err(f"Documentos com 'socioeconomico': {com_socio} (esperado ≥ {MUNICIPIOS_ESPERADOS})", erros)

        jp = col.find_one({"municipioIdIbge": JP_ID})
        if not jp:
            _err(f"João Pessoa ({JP_ID}) não encontrada", erros)
        else:
            socio = jp.get("socioeconomico", {})
            pop   = socio.get("populacao", {}).get("total")
            agua  = socio.get("saneamento", {}).get("pctAguaRedeGeral")
            alfa  = socio.get("educacaoPopulacao", {}).get("taxaAnalfabetismo15Mais")
            if pop and JP_POP_MIN <= pop <= JP_POP_MAX:
                _ok(f"João Pessoa — população: {pop:,}")
            else:
                _err(f"João Pessoa — população fora do esperado: {pop}", erros)
            if agua is not None:
                _ok(f"João Pessoa — água rede geral: {agua}%")
            if alfa is not None:
                _ok(f"João Pessoa — analfabetismo 15+: {alfa}%")

        # --- setor_indicadores ---
        print("\n  [setor_indicadores]")
        col_setor = db["setor_indicadores"]
        total_setor = col_setor.count_documents({})
        com_socio_setor = col_setor.count_documents({"socioeconomico": {"$exists": True}})
        if total_setor == 0:
            print("  ⏳  Sem dados ainda (Sprint 2 pendente)")
        else:
            _ok(f"Total de documentos: {total_setor}")
            _ok(f"Documentos com 'socioeconomico': {com_socio_setor}")

        # --- bairro_indicadores ---
        print("\n  [bairro_indicadores]")
        col_bairro = db["bairro_indicadores"]
        total_bairro = col_bairro.count_documents({})
        com_socio_bairro = col_bairro.count_documents({"socioeconomico": {"$exists": True}})
        if total_bairro == 0:
            print("  ⏳  Sem dados ainda (Sprint 2 pendente)")
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
    print("\n🔍  VALIDAÇÃO — MÓDULO SOCIOECONÔMICO (Sprint 1)\n")

    erros: list = []

    validar_silver(erros)
    validar_gold(erros)
    validar_mongodb(erros)

    print(f"\n{'=' * 55}")
    if erros:
        print(f"  ❌  {len(erros)} erro(s) encontrado(s):\n")
        for e in erros:
            print(f"     • {e}")
        print()
        sys.exit(1)
    else:
        print("  ✅  Todas as validações passaram — Sprint 1 concluída!")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    main()

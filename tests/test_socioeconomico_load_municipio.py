"""
Testes de integração — load municipio (socioeconomico)

Usa mongomock para simular o MongoDB sem precisar de conexão real.
Testa:
- Estrutura do documento gerado
- Upsert idempotente
- $set cirúrgico (não sobrescreve campos de educação)
- Tratamento de NaN
"""
import os
from unittest.mock import patch

import pandas as pd
import pytest

# Pula se mongomock não estiver instalado
mongomock = pytest.importorskip("mongomock")


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017/")
    monkeypatch.setenv("MONGO_DB_NAME", "test_odin")


@pytest.fixture
def df_gold():
    """DataFrame mínimo simulando o Gold do transform de município."""
    return pd.DataFrame({
        "CD_MUN":  ["2507507", "2500205"],
        "NM_MUN":  ["João Pessoa", "Aguiar"],
        "uf":      ["PB", "PB"],
        "ano_referencia": [2022, 2022],
        "fonte":   ["IBGE Censo Demográfico 2022", "IBGE Censo Demográfico 2022"],
        "total_populacao":               [833932, 5003],
        "total_domicilios_particulares": [None, None],
        "media_moradores_por_domicilio": [2.8, 2.7],
        "pct_criancas_0_9":              [12.9, 11.3],
        "pct_idosos_60_mais":            [14.8, 19.9],
        "pct_preta_parda":               [59.8, 65.6],
        "pct_agua_rede_geral":           [73.4, 37.0],
        "pct_esgoto_rede_geral":         [52.8, 17.3],
        "pct_lixo_coletado":             [77.8, 39.4],
        "taxa_analfabetismo_15_mais":    [6.1, 30.7],
        "pct_responsavel_feminino":      [52.1, 37.6],
    })


def _run_load(df, mock_client):
    """Executa o load usando mongomock, simulando bulk_write via update_one."""
    from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio.load import run

    # mongomock não suporta o parâmetro 'sort' do pymongo 4.x no bulk_write.
    # Simulamos o bulk_write executando update_one diretamente.
    def fake_bulk_write(operacoes, ordered=False):
        col = mock_client["test_odin"]["municipio_indicadores"]
        upserted = 0
        modified = 0
        for op in operacoes:
            filt = op._filter
            update = op._doc
            result = col.update_one(filt, update, upsert=op._upsert)
            if result.upserted_id:
                upserted += 1
            elif result.modified_count:
                modified += 1

        class FakeResult:
            upserted_count = upserted
            modified_count = modified
        return FakeResult()

    col = mock_client["test_odin"]["municipio_indicadores"]
    col.bulk_write = fake_bulk_write

    with patch(
        "src.jobs.socioeconomico_jobs.ibge_censo_pipeline.etl.municipio.load.MongoClient",
        return_value=mock_client,
    ):
        return run(df=df)


class TestLoadMunicipioSocioeconomico:
    def test_insere_documentos(self, mock_env, df_gold):
        client = mongomock.MongoClient()
        total = _run_load(df_gold, client)
        assert total == 2
        assert client["test_odin"]["municipio_indicadores"].count_documents({}) == 2

    def test_estrutura_socioeconomico(self, mock_env, df_gold):
        client = mongomock.MongoClient()
        _run_load(df_gold, client)

        doc = client["test_odin"]["municipio_indicadores"].find_one(
            {"municipioIdIbge": 2507507}
        )
        assert doc is not None
        socio = doc["socioeconomico"]

        assert socio["anoReferencia"] == 2022
        assert socio["populacao"]["total"] == 833932
        assert socio["populacao"]["mediaMoradoresPorDomicilio"] == 2.8
        assert socio["estruturaEtaria"]["pctCriancas0a9"] == 12.9
        assert socio["raca"]["pctPretaParda"] == 59.8
        assert socio["saneamento"]["pctAguaRedeGeral"] == 73.4
        assert socio["educacaoPopulacao"]["taxaAnalfabetismo15Mais"] == 6.1
        assert socio["familia"]["pctResponsavelFeminino"] == 52.1

    def test_nan_vira_none(self, mock_env, df_gold):
        """total_domicilios_particulares é None no fixture — não deve aparecer como NaN."""
        client = mongomock.MongoClient()
        _run_load(df_gold, client)

        doc = client["test_odin"]["municipio_indicadores"].find_one(
            {"municipioIdIbge": 2507507}
        )
        val = doc["socioeconomico"]["populacao"]["totalDomiciliosParticulares"]
        assert val is None

    def test_upsert_idempotente(self, mock_env, df_gold):
        """Rodar duas vezes não duplica documentos."""
        client = mongomock.MongoClient()
        _run_load(df_gold, client)
        _run_load(df_gold, client)
        assert client["test_odin"]["municipio_indicadores"].count_documents({}) == 2

    def test_set_cirurgico_nao_sobrescreve_educacao(self, mock_env, df_gold):
        """$setOnInsert não deve sobrescrever campo 'educacao' já existente."""
        client = mongomock.MongoClient()
        col = client["test_odin"]["municipio_indicadores"]

        # Inserir documento com campo educacao pré-existente
        col.insert_one({
            "municipioIdIbge": 2507507,
            "educacao": {"totalEscolas": 300, "totalMatriculas": 100000},
        })

        _run_load(df_gold, client)

        doc = col.find_one({"municipioIdIbge": 2507507})
        # educacao deve continuar intacto
        assert doc["educacao"]["totalEscolas"] == 300
        # socioeconomico deve ter sido adicionado
        assert "socioeconomico" in doc

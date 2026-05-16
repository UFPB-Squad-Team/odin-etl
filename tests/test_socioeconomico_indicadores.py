import numpy as np
import pandas as pd
import pytest

from src.jobs.socioeconomico_jobs.ibge_censo_pipeline.indicadores import (
    _chave_geografica,
    _normalizar_chave,
    _pct,
    calcular_alfabetizacao,
    calcular_estrutura_etaria,
    calcular_familia,
    calcular_populacao,
    calcular_raca,
    calcular_saneamento,
    calcular_agua_inadequada,
    calcular_esgoto_inadequado,
    calcular_lixo_inadequado,
    calcular_razao_dependencia,
    calcular_obitos,
    calcular_habitacao,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _df_municipio(**kwargs) -> pd.DataFrame:
    """DataFrame mínimo com chave CD_MUN e variáveis fornecidas."""
    n = len(next(iter(kwargs.values()))) if kwargs else 1
    base = {"CD_MUN": ["2507507"] * n}
    base.update(kwargs)
    return pd.DataFrame(base)


def _df_setor(**kwargs) -> pd.DataFrame:
    """DataFrame mínimo com chave CD_SETOR."""
    n = len(next(iter(kwargs.values()))) if kwargs else 1
    base = {"CD_SETOR": ["250750701000001"] * n}
    base.update(kwargs)
    return pd.DataFrame(base)


def _df_setor_alias(**kwargs) -> pd.DataFrame:
    """DataFrame com chave 'setor' (alias do IBGE para CD_SETOR)."""
    n = len(next(iter(kwargs.values()))) if kwargs else 1
    base = {"setor": ["250750701000001"] * n}
    base.update(kwargs)
    return pd.DataFrame(base)


# ---------------------------------------------------------------------------
# _chave_geografica e _normalizar_chave
# ---------------------------------------------------------------------------

class TestChaveGeografica:
    def test_detecta_cd_mun(self):
        df = pd.DataFrame({"CD_MUN": ["2507507"], "v0001": ["100"]})
        assert _chave_geografica(df) == "CD_MUN"

    def test_detecta_cd_setor(self):
        df = pd.DataFrame({"CD_SETOR": ["250750701000001"], "v0001": ["100"]})
        assert _chave_geografica(df) == "CD_SETOR"

    def test_detecta_cd_setor_minusculo(self):
        df = pd.DataFrame({"CD_setor": ["250750701000001"], "v0001": ["100"]})
        chave = _chave_geografica(df)
        assert chave == "CD_setor"

    def test_detecta_alias_setor(self):
        df = pd.DataFrame({"setor": ["250750701000001"], "v0001": ["100"]})
        chave = _chave_geografica(df)
        assert chave == "setor"

    def test_prioridade_setor_sobre_mun(self):
        df = pd.DataFrame({"CD_SETOR": ["250750701000001"], "CD_MUN": ["2507507"]})
        assert _chave_geografica(df) == "CD_SETOR"

    def test_levanta_erro_sem_chave(self):
        df = pd.DataFrame({"v0001": ["100"], "v0003": ["50"]})
        with pytest.raises(ValueError, match="Nenhuma chave geográfica"):
            _chave_geografica(df)

    def test_normalizar_alias_setor(self):
        df = pd.DataFrame({"setor": ["250750701000001"], "v0001": ["100"]})
        df_norm = _normalizar_chave(df)
        assert "CD_SETOR" in df_norm.columns
        assert "setor" not in df_norm.columns

    def test_normalizar_nao_altera_canonico(self):
        df = pd.DataFrame({"CD_MUN": ["2507507"], "v0001": ["100"]})
        df_norm = _normalizar_chave(df)
        assert "CD_MUN" in df_norm.columns


# ---------------------------------------------------------------------------
# _pct
# ---------------------------------------------------------------------------

class TestPct:
    def test_calculo_basico(self):
        num = pd.Series([50.0, 25.0])
        den = pd.Series([100.0, 100.0])
        resultado = _pct(num, den)
        assert resultado.tolist() == [50.0, 25.0]

    def test_divisao_por_zero_retorna_none(self):
        num = pd.Series([10.0, 0.0])
        den = pd.Series([0.0, 0.0])
        resultado = _pct(num, den)
        assert pd.isna(resultado.iloc[0])
        assert pd.isna(resultado.iloc[1])

    def test_arredondamento_uma_casa(self):
        num = pd.Series([1.0])
        den = pd.Series([3.0])
        resultado = _pct(num, den)
        assert resultado.iloc[0] == 33.3


# ---------------------------------------------------------------------------
# calcular_populacao
# ---------------------------------------------------------------------------

class TestCalcularPopulacao:
    def test_valores_corretos(self):
        df = _df_municipio(v0001=["1000", "500"], v0003=["300", "150"], v0005=["3,3", "3,0"])
        resultado = calcular_populacao(df)
        assert resultado["total_populacao"].tolist() == [1000, 500]
        assert resultado["total_domicilios_particulares"].tolist() == [300, 150]
        assert resultado["media_moradores_por_domicilio"].tolist() == [3.3, 3.0]

    def test_virgula_decimal_ibge(self):
        """O IBGE usa vírgula como separador decimal em v0005."""
        df = _df_municipio(v0001=["100"], v0003=["40"], v0005=["2,5"])
        resultado = calcular_populacao(df)
        assert resultado["media_moradores_por_domicilio"].iloc[0] == 2.5

    def test_chave_preservada(self):
        df = _df_municipio(v0001=["100"], v0003=["40"], v0005=["2,5"])
        resultado = calcular_populacao(df)
        assert "CD_MUN" in resultado.columns

    def test_funciona_com_setor(self):
        df = _df_setor(v0001=["200"], v0003=["80"], v0005=["2,5"])
        resultado = calcular_populacao(df)
        assert "CD_SETOR" in resultado.columns
        assert resultado["total_populacao"].iloc[0] == 200

    def test_funciona_com_alias_setor(self):
        df = _df_setor_alias(v0001=["200"], v0003=["80"], v0005=["2,5"])
        resultado = calcular_populacao(df)
        assert "CD_SETOR" in resultado.columns


# ---------------------------------------------------------------------------
# calcular_estrutura_etaria
# ---------------------------------------------------------------------------

class TestCalcularEstruturaEtaria:
    def _df(self, v01006, v01031, v01032, v01040, v01041):
        return _df_municipio(
            V01006=[str(v01006), str(v01006)],
            V01031=[str(v01031), str(v01031)],
            V01032=[str(v01032), str(v01032)],
            V01040=[str(v01040), str(v01040)],
            V01041=[str(v01041), str(v01041)],
        )

    def test_criancas_correto(self):
        # 200 crianças 0-4, 150 crianças 5-9, total 1000 → 35%
        df = self._df(1000, 200, 150, 50, 30)
        resultado = calcular_estrutura_etaria(df)
        assert resultado["pct_criancas_0_9"].iloc[0] == 35.0

    def test_idosos_correto(self):
        # 50 idosos 60-69, 30 idosos 70+, total 1000 → 8%
        df = self._df(1000, 0, 0, 50, 30)
        resultado = calcular_estrutura_etaria(df)
        assert resultado["pct_idosos_60_mais"].iloc[0] == 8.0

    def test_populacao_zero_retorna_none(self):
        df = self._df(0, 0, 0, 0, 0)
        resultado = calcular_estrutura_etaria(df)
        assert pd.isna(resultado["pct_criancas_0_9"].iloc[0])


# ---------------------------------------------------------------------------
# calcular_raca
# ---------------------------------------------------------------------------

class TestCalcularRaca:
    def test_preta_parda_correto(self):
        # 300 preta + 400 parda de 1000 total → 70%
        df = _df_municipio(
            V01317=["200"], V01318=["300"], V01319=["50"],
            V01320=["400"], V01321=["50"],
        )
        resultado = calcular_raca(df)
        assert resultado["pct_preta_parda"].iloc[0] == 70.0

    def test_total_zero_retorna_none(self):
        df = _df_municipio(
            V01317=["0"], V01318=["0"], V01319=["0"],
            V01320=["0"], V01321=["0"],
        )
        resultado = calcular_raca(df)
        assert pd.isna(resultado["pct_preta_parda"].iloc[0])


# ---------------------------------------------------------------------------
# calcular_saneamento
# ---------------------------------------------------------------------------

class TestCalcularSaneamento:
    def _dfs(self, v00111, v00309, v00397, v00398, v0003):
        df_dom2 = _df_municipio(
            V00111=[str(v00111)], V00309=[str(v00309)],
            V00397=[str(v00397)], V00398=[str(v00398)],
        )
        df_basico = _df_municipio(v0003=[str(v0003)], v0001=["1000"], v0005=["3,0"])
        return df_dom2, df_basico

    def test_agua_correto(self):
        df_dom2, df_basico = self._dfs(80, 50, 60, 10, 100)
        resultado = calcular_saneamento(df_dom2, df_basico)
        assert resultado["pct_agua_rede_geral"].iloc[0] == 80.0

    def test_esgoto_correto(self):
        df_dom2, df_basico = self._dfs(80, 50, 60, 10, 100)
        resultado = calcular_saneamento(df_dom2, df_basico)
        assert resultado["pct_esgoto_rede_geral"].iloc[0] == 50.0

    def test_lixo_soma_dois_campos(self):
        # 60 serviço + 10 caçamba = 70 de 100 → 70%
        df_dom2, df_basico = self._dfs(80, 50, 60, 10, 100)
        resultado = calcular_saneamento(df_dom2, df_basico)
        assert resultado["pct_lixo_coletado"].iloc[0] == 70.0

    def test_denominador_zero_retorna_none(self):
        df_dom2, df_basico = self._dfs(80, 50, 60, 10, 0)
        resultado = calcular_saneamento(df_dom2, df_basico)
        assert pd.isna(resultado["pct_agua_rede_geral"].iloc[0])

    def test_chaves_diferentes_municipio_vs_setor(self):
        """Merge funciona mesmo quando dom2 usa 'setor' e basico usa 'CD_SETOR'."""
        df_dom2 = pd.DataFrame({
            "setor": ["250750701000001"],
            "V00111": ["80"], "V00309": ["50"],
            "V00397": ["60"], "V00398": ["10"],
        })
        df_basico = pd.DataFrame({
            "CD_SETOR": ["250750701000001"],
            "v0001": ["1000"], "v0003": ["100"], "v0005": ["3,0"],
        })
        resultado = calcular_saneamento(df_dom2, df_basico)
        assert resultado["pct_agua_rede_geral"].iloc[0] == 80.0


# ---------------------------------------------------------------------------
# calcular_alfabetizacao
# ---------------------------------------------------------------------------

class TestCalcularAlfabetizacao:
    def test_taxa_correta(self):
        # 200 não-alfabetizados, 800 alfabetizados 15+ → 20%
        cols_alfa = {f"V00{i}": ["800"] for i in range(748, 761)}
        # Dividir 800 entre 13 faixas — simplificado: só primeira faixa com 800
        cols_alfa = {f"V00{i}": ["0"] for i in range(748, 761)}
        cols_alfa["V00748"] = ["800"]
        df = _df_municipio(V00901=["200"], **cols_alfa)
        resultado = calcular_alfabetizacao(df)
        assert resultado["taxa_analfabetismo_15_mais"].iloc[0] == 20.0

    def test_zero_analfabetos(self):
        cols_alfa = {f"V00{i}": ["0"] for i in range(748, 761)}
        cols_alfa["V00748"] = ["1000"]
        df = _df_municipio(V00901=["0"], **cols_alfa)
        resultado = calcular_alfabetizacao(df)
        assert resultado["taxa_analfabetismo_15_mais"].iloc[0] == 0.0


# ---------------------------------------------------------------------------
# calcular_familia
# ---------------------------------------------------------------------------

class TestCalcularFamilia:
    def test_responsavel_feminino_correto(self):
        # 600 responsáveis femininos de 1000 total → 60%
        df = _df_municipio(V01042=["1000"], V01063=["600"])
        resultado = calcular_familia(df)
        assert resultado["pct_responsavel_feminino"].iloc[0] == 60.0

    def test_total_zero_retorna_none(self):
        df = _df_municipio(V01042=["0"], V01063=["0"])
        resultado = calcular_familia(df)
        assert pd.isna(resultado["pct_responsavel_feminino"].iloc[0])


# ---------------------------------------------------------------------------
# calcular_agua_inadequada
# ---------------------------------------------------------------------------

class TestCalcularAguaInadequada:
    def _dfs(self, v00113, v00114, v00115, v00116, v00117, v00118, v0003):
        df_dom2 = _df_municipio(
            V00113=[str(v00113)], V00114=[str(v00114)], V00115=[str(v00115)],
            V00116=[str(v00116)], V00117=[str(v00117)], V00118=[str(v00118)],
        )
        df_bas = _df_municipio(v0001=["1000"], v0003=[str(v0003)], v0005=["3,0"])
        return df_dom2, df_bas

    def test_soma_todas_fontes_inadequadas(self):
        # 10+5+5+5+5+5 = 35 de 100 → 35%
        df2, dfb = self._dfs(10, 5, 5, 5, 5, 5, 100)
        r = calcular_agua_inadequada(df2, dfb)
        assert r["pct_agua_inadequada"].iloc[0] == 35.0

    def test_zero_inadequada(self):
        df2, dfb = self._dfs(0, 0, 0, 0, 0, 0, 100)
        r = calcular_agua_inadequada(df2, dfb)
        assert r["pct_agua_inadequada"].iloc[0] == 0.0

    def test_denominador_zero_retorna_none(self):
        df2, dfb = self._dfs(10, 0, 0, 0, 0, 0, 0)
        r = calcular_agua_inadequada(df2, dfb)
        assert pd.isna(r["pct_agua_inadequada"].iloc[0])


# ---------------------------------------------------------------------------
# calcular_esgoto_inadequado
# ---------------------------------------------------------------------------

class TestCalcularEsgotoInadequado:
    def _dfs(self, v00311, v00313, v00314, v00315, v00316, v0003):
        df_dom2 = _df_municipio(
            V00311=[str(v00311)], V00313=[str(v00313)], V00314=[str(v00314)],
            V00315=[str(v00315)], V00316=[str(v00316)],
        )
        df_bas = _df_municipio(v0001=["1000"], v0003=[str(v0003)], v0005=["3,0"])
        return df_dom2, df_bas

    def test_soma_esgoto_inadequado(self):
        # 20+10+5+5+10 = 50 de 100 → 50%
        df2, dfb = self._dfs(20, 10, 5, 5, 10, 100)
        r = calcular_esgoto_inadequado(df2, dfb)
        assert r["pct_esgoto_inadequado"].iloc[0] == 50.0

    def test_denominador_zero_retorna_none(self):
        df2, dfb = self._dfs(10, 0, 0, 0, 0, 0)
        r = calcular_esgoto_inadequado(df2, dfb)
        assert pd.isna(r["pct_esgoto_inadequado"].iloc[0])


# ---------------------------------------------------------------------------
# calcular_lixo_inadequado
# ---------------------------------------------------------------------------

class TestCalcularLixoInadequado:
    def _dfs(self, v00399, v00400, v00401, v00402, v0003):
        df_dom2 = _df_municipio(
            V00399=[str(v00399)], V00400=[str(v00400)],
            V00401=[str(v00401)], V00402=[str(v00402)],
        )
        df_bas = _df_municipio(v0001=["1000"], v0003=[str(v0003)], v0005=["3,0"])
        return df_dom2, df_bas

    def test_soma_lixo_inadequado(self):
        # 15+10+10+5 = 40 de 100 → 40%
        df2, dfb = self._dfs(15, 10, 10, 5, 100)
        r = calcular_lixo_inadequado(df2, dfb)
        assert r["pct_lixo_inadequado"].iloc[0] == 40.0

    def test_zero_inadequado(self):
        df2, dfb = self._dfs(0, 0, 0, 0, 100)
        r = calcular_lixo_inadequado(df2, dfb)
        assert r["pct_lixo_inadequado"].iloc[0] == 0.0


# ---------------------------------------------------------------------------
# calcular_razao_dependencia
# ---------------------------------------------------------------------------

class TestCalcularRazaoDependencia:
    def _df(self, pop_0_4, pop_5_9, pop_10_14, pop_15_19, pop_20_24,
            pop_25_29, pop_30_39, pop_40_49, pop_50_59, pop_60_69, pop_70p):
        return _df_municipio(
            V01031=[str(pop_0_4)], V01032=[str(pop_5_9)], V01033=[str(pop_10_14)],
            V01034=[str(pop_15_19)], V01035=[str(pop_20_24)], V01036=[str(pop_25_29)],
            V01037=[str(pop_30_39)], V01038=[str(pop_40_49)], V01039=[str(pop_50_59)],
            V01040=[str(pop_60_69)], V01041=[str(pop_70p)],
        )

    def test_razao_correta(self):
        # dependentes: 0-14 = 300 (100+100+100), 60+ = 100 (50+50) → 400
        # ativos: 15-59 = 600 (100×6 faixas)
        # razão = 400/600 × 100 = 66.7
        df = self._df(100, 100, 100, 100, 100, 100, 100, 100, 100, 50, 50)
        r = calcular_razao_dependencia(df)
        assert r["razao_dependencia"].iloc[0] == 66.7

    def test_sem_ativos_retorna_none(self):
        df = self._df(100, 100, 100, 0, 0, 0, 0, 0, 0, 50, 50)
        r = calcular_razao_dependencia(df)
        assert pd.isna(r["razao_dependencia"].iloc[0])


# ---------------------------------------------------------------------------
# calcular_obitos
# ---------------------------------------------------------------------------

class TestCalcularObitos:
    def test_total_e_infantis(self):
        df = _df_municipio(V01224=["50"], V01228=["3"], V01239=["2"])
        r = calcular_obitos(df)
        assert r["total_obitos_domicilios"].iloc[0] == 50
        assert r["obitos_infantis_0_4"].iloc[0] == 5  # 3 + 2

    def test_zero_obitos(self):
        df = _df_municipio(V01224=["0"], V01228=["0"], V01239=["0"])
        r = calcular_obitos(df)
        assert r["total_obitos_domicilios"].iloc[0] == 0
        assert r["obitos_infantis_0_4"].iloc[0] == 0


# ---------------------------------------------------------------------------
# calcular_habitacao
# ---------------------------------------------------------------------------

class TestCalcularHabitacao:
    def _df(self, v00001, v00002, v00021, v00022, v00023, v00024, v00025, v00026):
        return _df_municipio(
            V00001=[str(v00001)], V00002=[str(v00002)],
            V00021=[str(v00021)], V00022=[str(v00022)], V00023=[str(v00023)],
            V00024=[str(v00024)], V00025=[str(v00025)], V00026=[str(v00026)],
        )

    def test_improvisado_correto(self):
        # 5 improvisados de 100 → 5%
        df = self._df(100, 5, 0, 0, 0, 0, 0, 0)
        r = calcular_habitacao(df)
        assert r["pct_dom_improvisado"].iloc[0] == 5.0

    def test_superlotado_soma_5_mais(self):
        # 5+3+2+1+1+1 = 13 de 100 → 13%
        df = self._df(100, 0, 5, 3, 2, 1, 1, 1)
        r = calcular_habitacao(df)
        assert r["pct_dom_superlotado"].iloc[0] == 13.0

    def test_denominador_zero_retorna_none(self):
        df = self._df(0, 5, 3, 0, 0, 0, 0, 0)
        r = calcular_habitacao(df)
        assert pd.isna(r["pct_dom_improvisado"].iloc[0])
        assert pd.isna(r["pct_dom_superlotado"].iloc[0])

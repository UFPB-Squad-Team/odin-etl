"""
Helpers to build and normalize the school read-model document.

These functions are intentionally pure so they can be reused and tested
without side effects.
"""

import numpy as np
import pandas as pd


DEPENDENCIA_ADM_MAP = {
    1: "Federal",
    2: "Estadual",
    3: "Municipal",
    4: "Privada",
}

LOCALIZACAO_MAP = {
    1: "Urbana",
    2: "Rural",
}


def _is_missing(value) -> bool:
    if value is None:
        return True

    if isinstance(value, (dict, list, tuple, np.ndarray)):
        return False

    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def _clean_value(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, nested_value in value.items():
            nested_cleaned = _clean_value(nested_value)
            if not _is_missing(nested_cleaned):
                cleaned[key] = nested_cleaned
        return cleaned

    if isinstance(value, list):
        cleaned_list = [_clean_value(item) for item in value]
        return [item for item in cleaned_list if not _is_missing(item)]

    if isinstance(value, tuple):
        cleaned_list = [_clean_value(item) for item in value]
        return [item for item in cleaned_list if not _is_missing(item)]

    if isinstance(value, np.ndarray):
        cleaned_list = [_clean_value(item) for item in value.tolist()]
        return [item for item in cleaned_list if not _is_missing(item)]

    if _is_missing(value):
        return None

    return value


def _to_text(value):
    if _is_missing(value):
        return None
    return str(value).strip()


def _to_int(value):
    if _is_missing(value):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _to_bool(value):
    if _is_missing(value):
        return None
    try:
        return bool(int(float(value)))
    except Exception:
        return bool(value)


def _map_dependencia(value):
    normalized = _to_int(value)
    return DEPENDENCIA_ADM_MAP.get(normalized, _to_text(value))


def _map_localizacao(value):
    normalized = _to_int(value)
    return LOCALIZACAO_MAP.get(normalized, _to_text(value))


def _build_localizacao(latitude, longitude):
    if pd.isna(latitude) or pd.isna(longitude):
        return None
    return {
        "type": "Point",
        "coordinates": [float(longitude), float(latitude)],
    }


def _build_endereco(row: pd.Series) -> dict:
    return _clean_value(
        {
            "logradouro": _to_text(row.get("DS_ENDERECO")),
            "numero": _to_text(row.get("NU_ENDERECO")),
            "bairro": _to_text(row.get("NO_BAIRRO")),
            "cep": _to_text(row.get("CO_CEP")),
            "municipio": _to_text(row.get("NO_MUNICIPIO")),
            "uf": _to_text(row.get("SG_UF")),
            "completo": _to_text(row.get("endereco_completo")),
        }
    )


def _build_infraestrutura(row: pd.Series) -> dict:
    return _clean_value(
        {
            "possuiAguaPotavel": _to_bool(row.get("IN_AGUA_POTAVEL")),
            "possuiEnergiaPublica": _to_bool(row.get("IN_ENERGIA_REDE_PUBLICA")),
            "possuiEsgotoRedePublica": _to_bool(row.get("IN_ESGOTO_REDE_PUBLICA")),
            "possuiColetaLixo": _to_bool(row.get("IN_LIXO_SERVICO_COLETA")),
            "possuiBiblioteca": _to_bool(row.get("IN_BIBLIOTECA")),
            "possuiLaboratorioInformatica": _to_bool(row.get("IN_LABORATORIO_INFORMATICA")),
            "possuiLaboratorioCiencias": _to_bool(row.get("IN_LABORATORIO_CIENCIAS")),
            "possuiQuadraEsportes": _to_bool(row.get("IN_QUADRA_ESPORTES")) or _to_bool(row.get("IN_QUADRA_ESPORTES_COBERTA")),
            "possuiCozinha": _to_bool(row.get("IN_COZINHA")),
            "possuiPiscina": _to_bool(row.get("IN_PISCINA")),
            "possuiRefeitorio": _to_bool(row.get("IN_REFEITORIO")),
            "possuiPatioCoberto": _to_bool(row.get("IN_PATIO_COBERTO")),
            "possuiPatioDescoberto": _to_bool(row.get("IN_PATIO_DESCOBERTO")),
            "possuiAcessibilidadePcd": bool(
                any(
                    _to_bool(row.get(column))
                    for column in [
                        "IN_ACESSIBILIDADE_CORRIMAO",
                        "IN_ACESSIBILIDADE_ELEVADOR",
                        "IN_ACESSIBILIDADE_PISOS_TATEIS",
                        "IN_ACESSIBILIDADE_RAMPAS",
                        "IN_ACESSIBILIDADE_SINAL_VISUAL",
                        "IN_ACESSIBILIDADE_SINAL_SONORO",
                        "IN_ACESSIBILIDADE_SINAL_TATIL",
                    ]
                )
            ),
            "internet": {
                "possuiInternet": _to_bool(row.get("IN_INTERNET")),
                "internetAdministrativa": _to_bool(row.get("IN_INTERNET_ADMINISTRATIVO")),
                "internetParaAlunos": _to_bool(row.get("IN_INTERNET_ALUNOS")),
            },
            "equipamentos": {
                "impressora": _to_bool(row.get("IN_EQUIP_IMPRESSORA")),
                "lousaDigital": _to_bool(row.get("IN_EQUIP_LOUSA_DIGITAL")),
                "multimidia": _to_bool(row.get("IN_EQUIP_MULTIMIDIA")),
                "desktopAluno": _to_bool(row.get("IN_DESKTOP_ALUNO")),
                "computadorPortatilAluno": _to_bool(row.get("IN_COMP_PORTATIL_ALUNO")),
                "tabletAluno": _to_bool(row.get("IN_TABLET_ALUNO")),
            },
            "salas": {
                "utilizadas": _to_int(row.get("QT_SALAS_UTILIZADAS")),
                "climatizadas": _to_int(row.get("QT_SALAS_UTILIZA_CLIMATIZADAS")),
                "acessiveis": _to_int(row.get("QT_SALAS_UTILIZADAS_ACESSIVEIS")),
            },
        }
    )


def _build_indicadores(row: pd.Series) -> dict:
    raw = row.get("indicadores_base_dados")
    if not isinstance(raw, dict):
        return None

    rede = _to_text(raw.get("rede"))
    if rede:
        rede = rede.capitalize()

    zona = _to_text(raw.get("localizacao"))
    if zona:
        zona = zona.capitalize()

    return _clean_value(
        {
            "anoReferencia": _to_int(raw.get("ano")),
            "municipioIdIbge": _to_int(raw.get("id_municipio")),
            "zonaLocalizacao": zona,
            "redeAdministrativa": rede,
            "complexidadeGestao": raw.get("icg_nivel_complexidade_gestao_escola"),
            "educacaoInfantil": raw.get("educacao_infantil"),
            "fundamentalAnosIniciais": raw.get("fundamental_anos_iniciais"),
            "fundamentalAnosFinais": raw.get("fundamental_anos_finais"),
            "ensinoMedio": raw.get("ensino_medio"),
        }
    )


def _build_school_document(row: pd.Series) -> dict:
    return _clean_value(
        {
            "escolaIdInep": _to_text(row.get("CO_ENTIDADE")),
            "escolaNome": _to_text(row.get("NO_ENTIDADE")),
            "estadoSigla": _to_text(row.get("SG_UF")),
            "municipioIdIbge": _to_int(row.get("CO_MUNICIPIO")),
            "municipioNome": _to_text(row.get("NO_MUNICIPIO")),
            "regiaoNome": _to_text(row.get("NO_REGIAO")),
            "dependenciaAdm": _map_dependencia(row.get("TP_DEPENDENCIA")),
            "tipoLocalizacao": _map_localizacao(row.get("TP_LOCALIZACAO")),
            "situacaoFuncionamento": _to_text(row.get("TP_SITUACAO_FUNCIONAMENTO")),
            "endereco": _build_endereco(row),
            "localizacao": _build_localizacao(row.get("latitude"), row.get("longitude")),
            "infraestrutura": _build_infraestrutura(row),
            "indicadores": _build_indicadores(row),
        }
    )

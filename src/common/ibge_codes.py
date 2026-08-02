# Códigos territoriais oficiais utilizados nos datasets do IBGE.

from typing import Final


CODIGO_UF_PARA_SIGLA: Final[dict[str, str]] = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


def sigla_uf_por_codigo_municipio(codigo_municipio: object) -> str:
    """Retorna a sigla da UF identificada pelos dois primeiros dígitos de CD_MUN."""
    codigo_uf = str(codigo_municipio)[:2]
    try:
        return CODIGO_UF_PARA_SIGLA[codigo_uf]
    except KeyError as exc:
        raise ValueError(
            f"Código de UF desconhecido em CD_MUN: {codigo_municipio!r}"
        ) from exc

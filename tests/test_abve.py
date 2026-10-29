import base64
import json

import pandas as pd
import pytest

from eletromobilidade import abve


def _resposta(registros, dicionarios=None):
    return {"results": [{"result": {"data": {"dsr": {"DS": [
        {"PH": [{"DM0": registros}], "ValueDicts": dicionarios or {}}]}}}}]}


def test_decodificar_dsr_repeticao_nulos_e_dicionario():
    registros = [
        {"S": [{"N": "G0", "DN": "D0"}, {"N": "G1"}, {"N": "M0"}], "C": [0, "BEV", 10]},
        {"C": ["PHEV", 5], "R": 1},          # repete a coluna 0
        {"C": [1, 7], "Ø": 2},               # coluna 1 nula
    ]
    linhas = abve.decodificar_dsr(_resposta(registros, {"D0": ["BYD", "GWM"]}), 3)
    assert linhas == [["BYD", "BEV", 10], ["BYD", "PHEV", 5], ["GWM", None, 7]]


def test_chave_do_painel():
    r = base64.b64encode(json.dumps({"k": "abc-123", "t": "x"}).encode()).decode().rstrip("=")
    html = f'<iframe src="https://app.powerbi.com/view?r={r}&pageName=x"></iframe>'
    assert abve.chave_do_painel(html) == "abc-123"
    assert abve.chave_do_painel("<html></html>") is None


def test_periodos_anuais_corta_o_ultimo_ano_no_mes():
    periodos = abve.periodos_anuais((2024, 9), desde=2022)
    assert periodos == [
        (pd.Timestamp(2022, 1, 1), pd.Timestamp(2023, 1, 1)),
        (pd.Timestamp(2023, 1, 1), pd.Timestamp(2024, 1, 1)),
        (pd.Timestamp(2024, 1, 1), pd.Timestamp(2024, 10, 1)),
    ]


class _ClienteFalso:
    """Responde às consultas de baixar_vendas com totais escolhidos pelo teste."""

    def __init__(self, total_nacional, por_uf):
        self.total_nacional, self.por_uf = total_nacional, por_uf

    def consultar(self, entidade, colunas, medida, filtros=None):
        if colunas == ["Estado"]:
            return pd.DataFrame({"Estado": list(self.por_uf), medida: 0})
        if colunas == ["Tipo_Tecnologia"]:
            return pd.DataFrame({"Tipo_Tecnologia": ["BEV"], medida: [self.total_nacional]})
        uf = filtros[1]["Condition"]["In"]["Values"][0][0]["Literal"]["Value"].strip("'")
        return pd.DataFrame({"Fabricante": ["BYD"], "Modelo": ["BYD DOLPHIN"], "Tipo_Tecnologia": ["BEV"],
                             "Segmento": ["Auto"], medida: [self.por_uf[uf]]})


def test_baixar_vendas_confere_as_ufs_contra_o_total():
    vendas = abve.baixar_vendas(_ClienteFalso(30, {"SP": 20, "RJ": 10, "": 0}), (2022, 3))
    assert vendas["qtd_vendas"].sum() == 30
    assert vendas["uf_sigla"].isna().sum() == 1          # UF vazia da ABVE vira nula
    assert vendas["fim"].iloc[0] == pd.Timestamp(2022, 3, 1)
    with pytest.raises(ValueError, match="cortada"):
        abve.baixar_vendas(_ClienteFalso(31, {"SP": 20, "RJ": 10}), (2022, 3))

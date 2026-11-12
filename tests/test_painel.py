import json
import re
from pathlib import Path

import pandas as pd
import pytest

from eletromobilidade import coleta
from eletromobilidade.coleta import Link
from eletromobilidade.painel import (CLASSES, MODELO, SEM_UF, SIGLAS, TIPOS, dados_painel, listar_fontes,
                                     montar_html)

RESULTADOS = Path(__file__).resolve().parent.parent / "resultados"


@pytest.fixture(scope="module")
def dados():
    return dados_painel(RESULTADOS)


def _serie(dados) -> pd.DataFrame:
    s = dados["serie"]
    return pd.DataFrame({"mes": [dados["meta"]["meses"][i] for i in s["m"]], "uf": [SIGLAS[i] for i in s["u"]],
                         "tipo": [TIPOS[i] for i in s["t"]], "classe": [CLASSES[i] for i in s["c"]], "v": s["v"]})


def test_serie_fecha_com_o_painel_por_tipo_do_brasil(dados):
    """Somadas as UFs e o grupo sem UF, a série do painel é a de modelo_tipo_brasil."""
    serie = _serie(dados)
    brasil = pd.read_csv(RESULTADOS / "modelo_tipo_brasil.csv", sep=";", decimal=",", encoding="utf-8-sig")
    brasil["mes"] = [f"{a}-{m:02d}" for a, m in zip(brasil["ano"], brasil["mes"])]
    esperado = brasil.melt(id_vars=["mes"], value_vars=[f"frota_{c}" for c in CLASSES], var_name="classe")
    esperado = esperado.assign(classe=esperado["classe"].str[len("frota_"):]).groupby(["mes", "classe"])["value"].sum()
    obtido = serie.groupby(["mes", "classe"])["v"].sum().reindex(esperado.index, fill_value=0)
    assert (obtido == esperado).all()


def test_serie_sem_o_grupo_sem_uf_e_a_tabela_das_ufs_validas(dados):
    serie = _serie(dados)
    validas = pd.read_csv(RESULTADOS / "modelo_tipo_classe_ufs_validas.csv", sep=";", decimal=",", encoding="utf-8-sig")
    validas["mes"] = [f"{a}-{m:02d}" for a, m in zip(validas["ano"], validas["mes"])]
    validas["tipo"] = validas["tipo"].fillna("sem_tipo")
    esperado = validas.groupby(["mes", "tipo", "classe"])["frota"].sum()
    esperado = esperado[esperado > 0]
    obtido = serie[serie["uf"] != SEM_UF].groupby(["mes", "tipo", "classe"])["v"].sum()
    assert obtido.sort_index().equals(esperado.sort_index())


def test_municipios_e_modelos_sao_do_ultimo_mes(dados):
    serie = _serie(dados)
    ultimo = serie[(serie["mes"] == dados["meta"]["meses"][-1]) & (serie["uf"] != SEM_UF)]["v"].sum()
    assert sum(dados["municipios"]["v"]) == ultimo
    modelos = sum(v for v, u in zip(dados["modelos"]["v"], dados["modelos"]["u"]) if SIGLAS[u] != SEM_UF)
    assert modelos == ultimo
    assert len(dados["municipios"]["cod"]) == len(set(dados["municipios"]["cod"]))
    assert "?" not in dados["modelos"]["marca"]


def test_frota_total_do_grupo_sem_uf_fecha_o_brasil(dados):
    u = dados["uf_mes"]
    brasil = pd.read_csv(RESULTADOS / "modelo_brasil.csv", sep=";", decimal=",", encoding="utf-8-sig")
    soma = pd.Series(u["total"]).groupby(u["m"]).sum()
    assert soma.tolist() == brasil["frota_total"].tolist()


def test_html_embute_tudo_e_nao_fecha_o_script_antes_da_hora():
    dados = {"meta": {"texto": "</script><b>"}, "serie": {}}
    html = montar_html(dados)
    assert "/*__" not in html
    corpo = re.search(r"window\.DEMOB = (.*?);</script>", html, re.S).group(1)
    assert json.loads(corpo.replace("<\\/", "</")) == dados
    assert "<script src" not in html and "<link" not in html  # nada carregado de fora: abre sem rede


def test_listar_fontes_casa_o_arquivo_lido_com_o_link(monkeypatch, tmp_path):
    for nome, arquivo in (("qualidade_modelo", "i_frota_marca_modelo_ano_setembro_2026.zip"),
                          ("qualidade_combustivel", "d_frota_combustivel_setembro_2026.xlsx")):
        pd.DataFrame({"ano": [2026, 2026], "mes": [8, 9], "arquivo": ["", arquivo], "ajuste": ["", ""],
                      "incluido": [False, True]}).to_csv(tmp_path / f"{nome}.csv", sep=";", index=False)
    links = [Link("https://d/I_Frota_Marca_Modelo_Ano_Setembro_2026.zip", "", "marca_modelo", (2026, 9), "ckan"),
             Link("https://g/outro_nome.xlsx", "", "combustivel", (2026, 9), "portal")]
    monkeypatch.setattr(coleta, "listar", lambda anos, **_: links)
    fontes = listar_fontes(tmp_path)
    assert [f["mes"] for f in fontes] == ["2026-09"]  # mês sem arquivo fica de fora
    assert fontes[0]["modelo"]["url"] == links[0].url and fontes[0]["modelo"]["origem"] == "dados abertos"
    assert fontes[0]["combustivel"]["url"] == links[1].url_arquivo  # sem nome igual, vale o mesmo mês


def test_malha_cobre_os_municipios_da_base(dados):
    malha = json.loads((MODELO / "malha_municipios.json").read_text(encoding="utf-8"))
    codigos = {int(g["properties"]["codarea"]) for g in next(iter(malha["objects"].values()))["geometries"]}
    fora = set(dados["municipios"]["cod"]) - codigos
    # só Boa Esperança do Norte (MT), criado em 2023 e ainda fora da malha de qualidade mínima
    assert fora <= {5101837}
    assert {str(u[3])[:2] for u in dados["meta"]["ufs"][:-1]} == {str(c)[:2] for c in codigos}

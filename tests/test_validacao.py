import pandas as pd
import pytest

from eletromobilidade.validacao import casar_modelos_abve, chave_abve, modelo_sem_uf, validar, validar_pbe


@pytest.mark.parametrize("texto, chave", [
    ("I/BYD DOLPHIN GS 180EV", "BYD DOLPHIN GS 180EV"),
    ("TOYOTA/CCROSS XRX HYBRID", "TOYOTA CCROSS XRX HYBRID"),
    ("IMP/M.BENZ C 300E", "M.BENZ C 300E"),
    ("I/CAOACHERY TIGGO8 PHEV", "CAOACHERY TIGGO8 PHEV"),
])
def test_chave_abve(texto, chave):
    assert chave_abve(texto) == chave


def test_casar_modelos_abve_tira_sufixo_de_tecnologia_e_repeticao():
    conhecidas = {"TOYOTA RAV4H SXAWD CNT", "VOLVO XC60 T8 R-DESIGN", "CAOACHERY TIGGO8 PHEV"}
    textos = pd.Series(["TOYOTA RAV4H SXAWD CNT HEV", "VOLVO XC60 T8 R-DESIGN PHEV I/VOLVO XC60 T8 R-DESIGN PHEV",
                        "CAOACHERY TIGGO8 PHEV", "MARCA NOVA X"])
    assert casar_modelos_abve(textos, conhecidas).tolist() == [
        "TOYOTA RAV4H SXAWD CNT", "VOLVO XC60 T8 R-DESIGN", "CAOACHERY TIGGO8 PHEV", "MARCA NOVA X"]


def _mes(ano, mes):
    return dict(ano=ano, mes=mes, data_referencia=pd.Timestamp(ano, mes, 1))


def _tabelas():
    """Frota em dez/2021, dez/2022 e mar/2023: um BEV, um plug-in que a regra perde e um carro em SP sem UF."""
    eletrificados, classificados = [], []
    frota = {  # (ano, mes): (dolphin SP, dolphin sem UF, outlander SP)
        (2021, 12): (10, 0, 5),
        (2022, 12): (40, 7, 20),
        (2023, 3): (60, 9, 30),
    }
    for (ano, mes), (sp, sem_uf, outlander) in frota.items():
        eletrificados += [
            {**_mes(ano, mes), "marca_modelo": "I/BYD DOLPHIN", "classe": "eletrico", "tipo": "leve",
             "uf_sigla": "SP", "qtd_veiculos": sp},
            {**_mes(ano, mes), "marca_modelo": "I/BYD DOLPHIN", "classe": "eletrico", "tipo": "leve",
             "uf_sigla": None, "qtd_veiculos": sem_uf},
        ]
        classificados += [
            {**_mes(ano, mes), "marca_modelo_norm": "I/BYD DOLPHIN", "marca": "BYD", "classe": "eletrico",
             "tipo": "leve", "pbe_classes": "eletrico", "pbe_aviso": None,
             "qtd_veiculos": sp + sem_uf, "qtd_sem_uf": sem_uf},
            {**_mes(ano, mes), "marca_modelo_norm": "I/MMC OUTLANDER X E", "marca": "MITSUBISHI",
             "classe": "combustao", "tipo": None, "pbe_classes": "hibrido_plug_in",
             "pbe_aviso": "pbe_so_eletrificado", "qtd_veiculos": outlander, "qtd_sem_uf": 0},
        ]
    eletrificados = pd.DataFrame(eletrificados)
    return {
        "modelo_eletrificados": eletrificados,
        "modelos_classificados": pd.DataFrame(classificados),
        "modelos_dimensao": pd.DataFrame({"marca_modelo": ["I/BYD DOLPHIN"], "marca": ["BYD"]}),
    }


def _abve():
    def venda(inicio, fim, uf, fabricante, modelo, tecnologia, qtd):
        return dict(inicio=pd.Timestamp(inicio), fim=pd.Timestamp(fim), uf_sigla=uf, fabricante=fabricante,
                    modelo=modelo, tecnologia=tecnologia, segmento="Auto", qtd_vendas=qtd)
    vendas = pd.DataFrame([
        venda("2022-01-01", "2022-12-01", "SP", "BYD", "BYD DOLPHIN", "BEV", 32),
        venda("2022-01-01", "2022-12-01", "SP", "MITSUBISHI", "MMC OUTLANDER X E", "PHEV", 15),
        venda("2023-01-01", "2023-03-01", "SP", "BYD", "BYD DOLPHIN", "BEV", 20),
        venda("2023-01-01", "2023-03-01", "SP", "MITSUBISHI", "MMC OUTLANDER X E", "PHEV", 10),
    ])
    serie = pd.DataFrame({"data": pd.to_datetime(["2021-06-01"]), "tecnologia": ["BEV"], "qtd_vendas": [9]})
    return {"vendas": vendas, "serie": serie}


def test_tecnologia_compara_crescimento_nas_ufs_validas_com_vendas():
    t = validar(_tabelas(), _abve())["validacao_abve_tecnologia"]
    bev_2022 = t.query("periodo == '01/2022 a 12/2022' and classe == 'eletrico'").iloc[0]
    # 40 - 10 em SP; os 7 sem UF ficam fora
    assert (bev_2022["vendas_abve"], bev_2022["crescimento_frota"], bev_2022["diferenca"]) == (32, 30, -2)
    phev_2022 = t.query("periodo == '01/2022 a 12/2022' and classe == 'hibrido_plug_in'").iloc[0]
    assert (phev_2022["vendas_abve"], phev_2022["crescimento_frota"]) == (15, 0)   # a regra perde o Outlander
    acumulado = t.query("fonte_vendas == 'acumulado' and classe == 'eletrico'").iloc[0]
    assert (acumulado["vendas_abve"], acumulado["crescimento_frota"]) == (52, 50)
    assert set(t["classe"]) >= {"eletrificada"}


def test_2021_vem_da_serie_so_com_instantaneo_de_dez_2020():
    sem_2020 = validar(_tabelas(), _abve())["validacao_abve_tecnologia"]
    assert "serie" not in set(sem_2020["fonte_vendas"])
    tabelas = _tabelas()
    dez_2020 = tabelas["modelo_eletrificados"].query("ano == 2021").assign(ano=2020, qtd_veiculos=1)
    tabelas["modelo_eletrificados"] = pd.concat([dez_2020, tabelas["modelo_eletrificados"]], ignore_index=True)
    com_2020 = validar(tabelas, _abve())["validacao_abve_tecnologia"]
    bev_2021 = com_2020.query("fonte_vendas == 'serie' and classe == 'eletrico'").iloc[0]
    assert (bev_2021["vendas_abve"], bev_2021["crescimento_frota"]) == (9, 9)   # 10 - 1 em SP
    acumulado = com_2020.query("fonte_vendas == 'acumulado' and classe == 'eletrico'").iloc[0]
    assert acumulado["vendas_abve"] == 9 + 52


def test_modelo_aponta_a_classe_divergente_e_usa_so_ufs_validas():
    m = validar(_tabelas(), _abve())["validacao_abve_modelo"]
    m = m[m["fonte_vendas"] == "acumulado"].set_index("modelo_abve")
    outlander = m.loc["MMC OUTLANDER X E"]
    assert (outlander["classe_abve"], outlander["classe_db"], bool(outlander["mesma_classe"])) == \
        ("hibrido_plug_in", "combustao", False)
    assert outlander["pbe_classes"] == "hibrido_plug_in"
    dolphin = m.loc["BYD DOLPHIN"]
    assert bool(dolphin["mesma_classe"]) and dolphin["crescimento_frota"] == 50


def test_uf_e_marca():
    resultado = validar(_tabelas(), _abve())
    uf = resultado["validacao_abve_uf"].query("fonte_vendas == 'acumulado' and classe == 'eletrico'")
    assert uf.set_index("uf_sigla").loc["SP", "vendas_abve"] == 52
    marca = resultado["validacao_abve_marca"].query("fonte_vendas == 'acumulado'").set_index(["marca", "classe"])
    assert marca.loc[("MITSUBISHI", "hibrido_plug_in"), "crescimento_frota"] == 0


def test_sem_abve_so_pbe_e_sem_uf():
    resultado = validar(_tabelas(), None)
    assert set(resultado) == {"validacao_pbe", "modelo_sem_uf"}
    sem_uf = modelo_sem_uf(_tabelas()["modelos_classificados"]).query("ano == 2022 and classe == 'eletrico'")
    assert sem_uf.iloc[0]["frota_sem_uf"] == 7 and sem_uf.iloc[0]["frota_brasil"] == 47
    pbe = validar_pbe(_tabelas()["modelos_classificados"]).query("ano == 2023 and classe == 'combustao'").iloc[0]
    assert pbe["frota_pbe_so_eletrificado"] == 30 and pbe["cobertura_pbe"] == 1

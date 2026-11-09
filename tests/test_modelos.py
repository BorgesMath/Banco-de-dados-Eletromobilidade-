import pandas as pd
import pytest

from eletromobilidade.modelos import (ClassificadorModelos, a_revisar, carregar_marcas, carregar_regras,
                                      classificar_modelos, dimensao_modelo, marca, marca_renavam,
                                      marcas_suspeitas)

# Textos reais do campo "Marca Modelo" (amostra do arquivo de abril/2026).
CASOS = [
    ("I/BYD DOLPHIN MINI GS5EV", "eletrico"),
    ("I/BYD DOLPHIN GS 180EV", "eletrico"),
    ("I/BYD SONG PRO GS DM", "hibrido_plug_in"),
    ("I/BYD SHARK GS DM", "hibrido_plug_in"),
    ("I/TESLA MODEL Y LONG R", "eletrico"),
    ("I/TAILG VOLTZ EVS", "eletrico"),
    ("I/GWM ORA 03 SKIN BEV48", "eletrico"),
    ("I/GWM HAVAL H6 GT", "hibrido_plug_in"),
    ("I/GWM HAVAL H6 PHEV19", "hibrido_plug_in"),
    ("I/GWM HAVAL H6 HEV2", "hibrido"),
    ("I/VOLVO EX30 E60 ULTRA", "eletrico"),
    ("I/VOLVO XC40 RECHARGE PE", "eletrico"),
    ("I/VOLVO XC40 T5H INSCRIP", "hibrido_plug_in"),
    ("I/VOLVO XC60 T8 POLESTAR", "hibrido_plug_in"),
    ("I/BMW I3 BEV 120AH", "eletrico"),
    ("I/BMW 330E", "hibrido_plug_in"),
    ("I/BMW X5 XDRIVE45E", "hibrido_plug_in"),
    ("I/LEXUS ES300H", "hibrido"),
    ("I/LEXUS NX450H PLUG-IN", "hibrido_plug_in"),
    ("TOYOTA/COROLLA ALTIS HV", "hibrido"),
    ("TOYOTA/CCROSS XRX HYBRID", "hibrido"),
    ("TOYOTA/YCROSS XRE-HYBRID", "hibrido"),
    ("I/TOYOTA PRIUS NGA TOP", "hibrido"),
    ("I/PORSCHE PANAMERA 4EHYB", "hibrido_plug_in"),
    ("I/PORSCHE CAYENNE SCPHEV", "hibrido_plug_in"),
    ("I/AUDI Q5 P-HIBRIDO", "hibrido_plug_in"),
    ("I/JEEP COMPASS S 4XE", "hibrido_plug_in"),
    ("I/RENAULT E-KWID INTENS", "eletrico"),
    ("I/PEUGEOT E EXPERT CARGO", "eletrico"),
    ("FIAT/PULSE AUDACE HYB", "hibrido_leve"),
    ("I/KIA SPORTAGE TMHEV EXP", "hibrido_leve"),
    ("I/CHEV BOLT EUV PREMIER", "eletrico"),
    ("SR/RANDON SR BA 03E", "nao_motorizado"),
    # encontrados na calibração com o arquivo de setembro/2026
    ("I/GEELY EX2 MAX", "eletrico"),
    ("I/GEELY EX5 EM-I ULTRA", "hibrido_plug_in"),
    ("I/AUDI Q8 E TRON 55", "eletrico"),
    ("I/M.BENZ EQC400 4M", "eletrico"),
    ("I/JAC E JS1", "eletrico"),
    ("I/JAC E-J7", "eletrico"),
    ("I/VOLVO XC40 6 PLUS", "eletrico"),
    ("I/PORSCHE MACAN E4", "eletrico"),
    ("I/PORSCHE CAYENNE CP PHE", "hibrido_plug_in"),
    ("I/DENZA B5 GS DM", "hibrido_plug_in"),
    ("I/JETOUR T2 I-DM PREMIUM", "hibrido_plug_in"),
    ("I/LPM C10 REEV E27", "hibrido_plug_in"),
    ("I/LPM B10 LIFE", "eletrico"),
    ("I/HYD IONIQ5 SIG", "eletrico"),
    ("I/HYD KONA H 16GDI SIG", "hibrido"),
    ("TOYOTA/COROLLA APREMIUMH", "hibrido"),
    ("I/TOYOTA RAV4H SXAWD CNT", "hibrido"),
    ("I/CAOACHERY TIGGO8 PHEV", "hibrido_plug_in"),
    ("CAOACHERY/TIGGO7 PRO HA", "hibrido_leve"),
    ("CAOACHERY/TIGGO5X H", "hibrido_leve"),
    ("I/GCX X11 3KW", "eletrico"),
    ("MOTOCHEFE/X11 3.000W", "eletrico"),
    ("VAMMO/VMOTO COMFORT 4KW", "eletrico"),
    ("I/MG MG4 64 KWH COM", "eletrico"),
    ("SHINERAY/SE1", "eletrico"),
    ("SHINERAY/PT3", "eletrico"),
    ("I/GAC GS4 ELITE", "hibrido"),
    ("I/GAC GS3 ELITE", "combustao"),
    ("I/GWM HAVAL H9 EXC", "combustao"),
    ("I/GWM POER P30 EXC", "combustao"),
    ("MOTTU/MOTTU-E", "eletrico"),
    # plug-ins que a comparação com a ABVE mostrou faltando
    ("I/MMC OUTLANDER SIGNTR E", "hibrido_plug_in"),
    ("I/MMC OUTLANDER HPES E", "hibrido_plug_in"),
    ("I/MMC OUTLANDER HYBRID", "hibrido_plug_in"),
    ("I/M.BENZ AMG C63S EP F1", "hibrido_plug_in"),
    ("I/M.BENZ SL63S EP", "hibrido_plug_in"),
    ("I/PORSCHE PANAMERA 4EHST", "hibrido_plug_in"),
    ("I/PORSCHE PANAMERA 4EHEX", "hibrido_plug_in"),
    ("I/PORSCHE PANAMERA TSE-H", "hibrido_plug_in"),
    ("I/PORSCHE PANAMERA TSEHS", "hibrido_plug_in"),
    ("I/PORSCHE CAYENNE CPH BE", "hibrido_plug_in"),
    ("I/PORSCHE CAYENNE S HYBR", "hibrido"),
    ("I/VOLVO XC60 INSC EXPRES", "hibrido_plug_in"),
    ("I/VOLVO XC90 INSC EXPRES", "hibrido_plug_in"),
    ("I/VOLVO XC40 INSC EXPRES", "hibrido_plug_in"),
    # Audi: o plug-in é o Q5 "P-HIBRIDO"; "HIBRIDO" e "HIB" sem o P são híbrido leve 48 V
    ("I/AUDI Q5 SB P-HIBRIDO", "hibrido_plug_in"),
    ("I/AUDI Q7 HIBRIDO", "hibrido_leve"),
    ("I/AUDI Q8 SB HIBRIDO", "hibrido_leve"),
    ("I/AUDI RS6 AV HIBRIDO", "hibrido_leve"),
    ("I/AUDI RS6 AV PERF HIB", "hibrido_leve"),
    ("I/AUDI RS6 AV GT HIB", "hibrido_leve"),
    ("I/AUDI RSQ8 SB HIBRIDO", "hibrido_leve"),
    ("I/AUDI A3 SD HIBRIDO", "hibrido_leve"),
    ("I/AUDI A3 SB HIBRIDO", "hibrido_leve"),
    # o que faltava pela comparação com o rótulo atual da ABVE: elétricos
    ("I/RENAULT KANGOO MAX ZE", "eletrico"),
    ("I/RENAULT TWIZY INTENSE", "eletrico"),
    ("I/PORSCHE MACAN ETURBO", "eletrico"),
    ("I/PORSCHE CAYENNE ES", "eletrico"),
    ("I/PORSCHE CAYENNE ET OF", "eletrico"),
    ("I/NEXTEM ORCA FEVER FN1C", "eletrico"),
    ("I/TANGJUN RD6 LUXURY PRO", "eletrico"),
    ("I/FARIZON V6E", "eletrico"),
    ("ARROW/ONE WORK", "eletrico"),
    ("HITECH/NEWDELIVERY URBAN", "eletrico"),
    ("I/SUZUKI EVITARA 4STY4WD", "eletrico"),
    ("I/FOTON EVIEWCONNECT 50S", "eletrico"),
    ("I/PEUGEOT 208 E-GT", "eletrico"),
    ("I/CADILLAC LYRIQ LUXURY", "eletrico"),
    ("I/DONGFENG SERES 3 ELEG", "eletrico"),
    ("I/M.BENZ 320 VIPK AMB", "eletrico"),
    # plug-ins e híbridos
    ("I/FERRARI 296 GTB", "hibrido_plug_in"),
    ("I/FERRARI SF90 STRADALE", "hibrido_plug_in"),
    ("I/MCLAREN ARTURA", "hibrido_plug_in"),
    ("I/LAMBORGHINI URUS SE", "hibrido_plug_in"),
    ("I/GAC GS9 ULTRA", "hibrido_plug_in"),
    ("I/PORSCHE CAYENNE CP TSP", "hibrido_plug_in"),
    ("I/BMW 745LE", "hibrido_plug_in"),
    ("I/CHRYSLER PACIFICA HYBR", "hibrido_plug_in"),
    ("I/FCA PACIFICAH PINNACLE", "hibrido_plug_in"),
    ("I/BYD SONG PLUS GS 450DM", "hibrido_plug_in"),
    ("I/BYD SONG PRO GS DMFLEX", "hibrido_plug_in"),
    ("I/CHERY T2 I-DM", "hibrido_plug_in"),
    ("I/TOYOTA RAV4 XSE PHV", "hibrido_plug_in"),
    ("I/RENAULT KOLEOS E-TECH", "hibrido"),
    ("I/TOYOTA SIENNA XSE", "hibrido"),
    ("I/BENTLEY BENTAYGA HYBRI", "hibrido"),
    ("I/LEXUS RX450H L LUXURY", "hibrido"),
    ("I/GAC GS4 PREMIUM", "hibrido"),   # BEV para a ABVE; o PBE registra híbrido
    # híbridos leves
    ("FIAT/FASTBACK IMPETUS HY", "hibrido_leve"),
    ("I/M.BENZ C200 AMG LINE", "hibrido_leve"),
    ("I/M.BENZ GLC300 4M CO", "hibrido_leve"),
    ("I/M.BENZ GLE450 D 4M", "hibrido_leve"),
    ("I/M.BENZ AMG GLE53 4M", "hibrido_leve"),
    ("I/BMW X6 XDRIVE40I MSP", "hibrido_leve"),
    ("I/BMW X3 30 XDRIVE", "hibrido_leve"),
    ("I/LR DEF110D350 HSEXD 7L", "hibrido_leve"),
    ("LR/DISC SPT D200 SE RD", "hibrido_leve"),
    ("I/LR RRS D350 HSED", "hibrido_leve"),
    ("I/JAG FPACE P340 RDYN SE", "hibrido_leve"),
    ("I/PORSCHE 911 CARRERAGTS", "hibrido_leve"),
    ("I/FOTON TUNLAND V9", "hibrido_leve"),
    ("I/CHERY TIGGO7 48V", "hibrido_leve"),
    # armadilhas: "E", "EV" e "HEV" que não indicam eletrificação
    ("VW/8.150E DELIVERY", "combustao"),
    ("VW/POLO 1.6 E-FLEX", "combustao"),
    ("HYUNDAI/HB20 10M EVOLUTI", "combustao"),
    ("CHEV/ONIX JOY", "combustao"),
    ("FIAT/UNO ELECTRONIC", "combustao"),
    ("I/PEUGEOT EXPERT CARGO", "combustao"),
    ("I/LR EVOQUE SE", "combustao"),
    ("YAMAHA/YBR 125E", "combustao"),
    ("I/CHANGAN CHANA SC1026W", "combustao"),
    ("I/M.BENZ C 300W", "combustao"),
    ("TOYOTA/YARIS HA XS15", "combustao"),
    ("CAOACHERY/TIGGO7 PRO16TA", "combustao"),
    ("MOTTU/SPORT 110I", "combustao"),
    ("I/GEELY EC-7 1.8 GS", "combustao"),
    ("I/PORSCHE MACAN T", "combustao"),
    ("I/MMC OUTLANDER 2.2 HPES", "combustao"),
    ("M.BENZ/AX0R 1933S EPG CA", "combustao"),
    ("I/AUDI Q5 2.0 TFSI", "combustao"),
    ("I/AUDI A3 SD 1.4 TFSI", "combustao"),
    # o mesmo texto cobre geração a combustão: rótulo da ABVE não coerente, ou frota antiga
    ("I/M.BENZ CLA200", "combustao"),
    ("I/M.BENZ GLA200 AMG LINE", "combustao"),
    ("I/LR R.R SPT 3.0 TD HSE", "combustao"),
    ("I/BMW X6 M COMPETITION", "combustao"),
    ("CAOACHERY/TIGGO7 SPORT", "combustao"),
    ("I/NISSAN FRONTIER S MTX4", "combustao"),
    # "HY" e "PACIFICA" sem mais nada não são híbrido
    ("I/CITROEN HY INV VAN", "combustao"),
    ("I/CHRYSLER PACIFICA", "combustao"),
    # "EV" de código de motor ou de edição, e BYD a combustão de antes da linha elétrica
    ("I/BMW 320I EV11", "combustao"),
    ("I/BMW 330I EV51 SECURITY", "combustao"),
    ("I/BMW 325I PRO EV39", "combustao"),
    ("I/BMW 325 IX", "combustao"),
    ("I/MGUZZI BR CALIFORNIA EV", "combustao"),
    ("I/LMABORGHINI HURACAN EV", "combustao"),
    ("I/BYD F0 GLX-I", "combustao"),
    ("I/BYD G3 GLX-I 1.5L", "combustao"),
    ("I/BYD F6 GS-I 2.0L", "combustao"),
    # e o que essas regras não podem levar junto
    ("I/BMW IX XDRIVE50", "eletrico"),
    ("I/BMW I4 EDRIVE35", "eletrico"),
    ("I/HYUNDAI KONA EV39", "eletrico"),
]


@pytest.mark.parametrize("texto, classe", CASOS)
def test_classificacao_de_modelos_reais(texto, classe):
    assert classificar_modelos(pd.Series([texto]))["classe"].iloc[0] == classe


def test_regra_registrada_e_alinhamento():
    s = pd.Series(["VW/GOL 1.0", None, "I/BYD KING GS DM"], index=[3, 1, 2])
    r = classificar_modelos(s)
    assert list(r.index) == [3, 1, 2]
    assert list(r["classe"]) == ["combustao", "sem_informacao", "hibrido_plug_in"]
    assert r["regra"].iloc[0] == 0 and r["regra"].iloc[2] > 0
    assert list(r["eletrificado"]) == [False, False, True]


def test_hibrido_leve_nao_conta_como_eletrificado():
    assert not classificar_modelos(pd.Series(["FIAT/PULSE AUDACE HYB"]))["eletrificado"].iloc[0]


def test_a_revisar_marca_eletrificada_sem_regra():
    r = classificar_modelos(pd.Series(["I/GAC E8 2.0 ATK GMC MAX", "VW/GOL 1.0", "I/BYD DOLPHIN GS 180EV"]))
    assert list(a_revisar(r)) == [True, False, False]


def test_classificador_com_cache_igual_ao_direto():
    s1 = pd.Series([t for t, _ in CASOS[:20]])
    s2 = pd.Series([t for t, _ in CASOS[10:]])
    clf = ClassificadorModelos()
    clf(s1)
    assert list(clf(s2)["classe"]) == list(classificar_modelos(s2)["classe"])
    assert len(clf.classificados) == len(CASOS)


def test_regras_invalidas(tmp_path):
    arq = tmp_path / "r.csv"
    arq.write_text("classe;padrao;nota\nfossil;GOL;\n", encoding="utf-8")
    with pytest.raises(ValueError, match="fossil"):
        carregar_regras(arq)
    arq.write_text("classe;padrao;nota\neletrico;(BYD;\n", encoding="utf-8")
    with pytest.raises(ValueError, match="regex inválida"):
        carregar_regras(arq)


def test_regras_com_ponto_e_virgula_na_nota(tmp_path):
    arq = tmp_path / "r.csv"
    arq.write_text("classe;padrao;nota\neletrico;BYD;nota; com ponto e vírgula\n", encoding="utf-8")
    with pytest.raises(ValueError, match="linha 2"):
        carregar_regras(arq)


# --- marca -------------------------------------------------------------------------------

def test_marca_renavam_ignora_prefixo_de_montadora_e_de_tipo():
    s = pd.Series(["I/BYD DOLPHIN GS 180EV", "IMP/ASIA TOWNER COACH", "JTA/SUZUKI EN125 YES",
                   "SR/RANDON SR CA", "REB/KRONE", "M.A./MASSEY-FERGUSON", "MR/CAT 416"])
    assert list(marca_renavam(s)) == ["BYD", "ASIA", "SUZUKI", "RANDON", "KRONE",
                                      "MASSEY-FERGUSON", "CAT"]


def test_marca_renavam_le_tudo_antes_da_barra():
    # Marca com espaço só é recuperável quando a barra a delimita; sem barra, vale a
    # primeira palavra (limitação conhecida: I/MOTO GUZZI V7 -> MOTO).
    s = pd.Series(["HARLEY DAVIDSON/XL883N", "MOTO TRAXX/JL50Q-8", "I/MOTO GUZZI V7"])
    assert list(marca_renavam(s)) == ["HARLEY DAVIDSON", "MOTO TRAXX", "MOTO"]


def test_marca_renavam_nula_sem_marca():
    assert marca_renavam(pd.Series(["SEM INFORMACAO", ""])).isna().all()


def test_marca_une_grafias_da_mesma_empresa():
    s = pd.Series(["GM/CORSA WIND", "CHEVROLET/ONIX 1.0MT LT", "CHEV/ONIX 10MT LT2",
                   "VW/GOL 1.0", "VOLKS/COMIL SVELTO U", "I/CAOACHERY TIGGO8 PHEV",
                   "I/LPM C10 REEV E27", "M.BENZ313CDI/SPRINTERM"])
    assert list(marca(s)) == ["CHEVROLET", "CHEVROLET", "CHEVROLET", "VOLKSWAGEN", "VOLKSWAGEN",
                              "CHERY", "LEAPMOTOR", "MERCEDES-BENZ"]


def test_marca_fora_da_tabela_segue_como_esta():
    assert list(marca(pd.Series(["I/BYD DOLPHIN GS 180EV", "TOYOTA/COROLLA ALTIS HV"]))) == ["BYD", "TOYOTA"]


def test_a_revisar_casa_pela_marca_canonica():
    # MARCAS_A_REVISAR lista as marcas pela forma canônica (LEAPMOTOR), e o RENAVAM
    # grafa LPM. Hoje todo LPM casa com uma regra e não chega aqui; o que o teste
    # protege é a fila continuar enxergando a marca se a regra sair ou a grafia mudar.
    classificados = pd.DataFrame({"marca_modelo_norm": ["I/LPM T03 COMFORT", "VW/GOL 1.0"],
                                  "regra": [0, 0]})
    assert list(a_revisar(classificados)) == [True, False]


def test_marcas_suspeitas_aponta_da_variante_para_a_grafia_mais_frequente():
    classificados = pd.DataFrame({
        "marca_modelo_norm": ["I/BYD DOLPHIN GS 180EV", "SR/RANDON SR CA", "SR/RANDONSP RT",
                              "SR/FACCHINI SRF CF", "SR/FACCHINI-IR CF",
                              "I/TAILG VOLTZ EVS", "I/TAIL-G VOLTZ"],
        "qtd_veiculos": [900, 500, 30, 240, 10, 500, 20],
    })
    s = marcas_suspeitas(classificados).set_index("marca_renavam")
    # BYD não parece variante de nada e fica fora, por mais frota que tenha.
    assert "BYD" not in s.index
    # A suspeita é a grafia com menos frota, e aponta para a mais frequente: modelo
    # colado na marca (RANDONSP, FACCHINI-IR) e pontuação a mais (TAIL-G).
    assert s.loc["RANDONSP", "parecida_com"] == "RANDON"
    assert s.loc["FACCHINI-IR", "parecida_com"] == "FACCHINI"
    assert s.loc["TAIL-G", "parecida_com"] == "TAILG"
    assert "RANDON" not in s.index and "FACCHINI" not in s.index


def test_dimensao_modelo():
    d = dimensao_modelo(pd.Series(["I/CAOACHERY TIGGO8 PHEV", "CHEV/ONIX 10MT LT2",
                                   "I/CAOACHERY TIGGO8 PHEV"]))
    assert len(d) == 2
    assert dict(zip(d["marca_renavam"], d["marca"])) == {"CAOACHERY": "CHERY", "CHEV": "CHEVROLET"}
    assert dict(zip(d["marca_renavam"], d["origem"])) == {"CAOACHERY": "Importado", "CHEV": "Nacional"}


def test_marcas_invalidas(tmp_path):
    arq = tmp_path / "m.csv"
    arq.write_text("marca_renavam;marca;nota\nCHEV;CHEVROLET;\nCHEV;GM;\n", encoding="utf-8")
    with pytest.raises(ValueError, match="repetidas"):
        carregar_marcas(arq)
    # GM -> CHEVROLET e CHEVROLET -> CHEV deixaria o resultado dependente da ordem.
    arq.write_text("marca_renavam;marca;nota\nGM;CHEVROLET;\nCHEVROLET;CHEV;\n", encoding="utf-8")
    with pytest.raises(ValueError, match="também são grafias"):
        carregar_marcas(arq)
    arq.write_text("marca_renavam;marca;nota\nCHEV;CHEVROLET;nota; com ponto e vírgula\n", encoding="utf-8")
    with pytest.raises(ValueError, match="linha 2"):
        carregar_marcas(arq)


def test_marcas_padrao_sao_canonicas():
    # Nenhuma forma canônica da tabela pode ser, ela mesma, uma grafia a normalizar.
    carregar_marcas()

"""Validação da base por modelo: contra as vendas da ABVE, contra o PBE do Inmetro e o grupo sem UF.

A comparação com a ABVE confronta fluxo com estoque: vendas de um período contra o
crescimento da frota entre dois instantâneos da base por modelo (dez/2021 a
dez/2022 contra as vendas de 2022, e assim por diante). Vale porque a baixa de
eletrificados quase não aparece no RENAVAM. Sempre nos veículos leves (a ABVE só
conta leves) e só nas UFs válidas: o grupo "Sem Informação" tem, nos
eletrificados, perfil de estoque ainda não emplacado, que a ABVE só conta quando
é emplacado.

Produtos:

* ``validacao_abve_tecnologia``: período x classe, Brasil (UFs válidas); 2021 vem
  da série histórica da ABVE, de 2022 em diante da base de vendas;
* ``validacao_abve_uf``: período x UF x classe;
* ``validacao_abve_marca``: período x marca x classe;
* ``validacao_abve_modelo``: período x modelo, com a classe dada pela ABVE, a dada
  aqui e o que o PBE registra; é o teste externo da classificação modelo a modelo;
* ``validacao_pbe``: mês x classe, cobertura e divergências do PBE Veicular;
* ``modelo_sem_uf``: mês x classe, o grupo sem UF que o painel do Brasil inclui.

Cada período aparece também acumulado (do primeiro ao último instantâneo). A conta
sai de duas formas: com as vendas como a ABVE as rotulou em cada ano
(``vendas_abve``) e com todo o histórico no rótulo mais recente de cada modelo
(``vendas_abve_rotulo_atual``), porque a ABVE muda o rótulo de alguns modelos com o
tempo e a base dá uma classe só a cada texto.
"""

from __future__ import annotations

import re

import pandas as pd

from .abve import CLASSE_POR_TECNOLOGIA
from .modelos import CLASSES_ELETRIFICADAS_MODELO
from .texto import normalizar

CLASSES_ABVE = ("eletrico", "hibrido_plug_in", "hibrido", "hibrido_leve")
_PREFIXO = re.compile(r"^(I|IMP)/")
_ESPACOS = re.compile(r"\s+")


def chave_abve(marca_modelo: str) -> str:
    """Texto do modelo como a ABVE grafa: sem ``I/``/``IMP/`` e com espaço no lugar da barra."""
    texto = _PREFIXO.sub("", normalizar(marca_modelo))
    return _ESPACOS.sub(" ", texto.replace("/", " ")).strip()


_SUFIXO_TECNOLOGIA = re.compile(r"\s*-?\s*\b(PHEV|HEV|MHEV|BEV)$")


def casar_modelos_abve(modelos: pd.Series, conhecidas: set[str]) -> pd.Series:
    """Chave da base para cada texto de modelo da ABVE.

    Primeiro o texto como está. Se não casar, duas grafias que a ABVE acrescenta:
    a tecnologia no fim (``TOYOTA RAV4H SXAWD CNT HEV``) e o texto repetido com o
    prefixo de importado (``VOLVO XC60 T8 R-DESIGN PHEV I/VOLVO XC60 T8 R-DESIGN PHEV``);
    a barra que às vezes fica (``GEELY/EX5 MAX``); e o espaço que às vezes falta
    (``BMW X5XDRIVE45E PHEV``), este só se o texto sem espaços for de um modelo só.
    Sem casamento, fica o texto normalizado.
    """
    sem_espacos: dict[str, list[str]] = {}
    for conhecida in conhecidas:
        sem_espacos.setdefault(conhecida.replace(" ", ""), []).append(conhecida)

    def casar(texto: str) -> str:
        chave = normalizar(texto)
        if chave in conhecidas:
            return chave
        candidata = chave.rsplit(" I/", 1)[-1] if " I/" in chave else chave
        candidata = _ESPACOS.sub(" ", candidata.replace("/", " "))
        tentativas = (candidata, _SUFIXO_TECNOLOGIA.sub("", candidata))
        for tentativa in tentativas:
            if tentativa in conhecidas:
                return tentativa
        for tentativa in tentativas:
            iguais = sem_espacos.get(tentativa.replace(" ", ""), [])
            if len(iguais) == 1:
                return iguais[0]
        return chave
    unicos = {texto: casar(texto) for texto in modelos.dropna().unique()}
    return modelos.map(unicos)


def rotulo_atual(vendas: pd.DataFrame) -> pd.Series:
    """Classe de cada modelo pelo rótulo mais recente da ABVE: a de mais vendas no último período em que vendeu.

    A ABVE muda o rótulo de alguns textos com o tempo e não reescreve o histórico: o
    ``CAOACHERY TIGGO7 PRO HA`` é HEV Flex até 2024 e MHEV 48V desde 2025.
    """
    por_periodo = vendas.groupby(["chave", "inicio", "classe"], observed=True)["qtd_vendas"].sum().reset_index()
    return (por_periodo.sort_values(["chave", "inicio", "qtd_vendas"], ascending=[True, False, False])
            .drop_duplicates("chave").set_index("chave")["classe"])


def _mes(data: pd.Timestamp) -> tuple[int, int]:
    return data.year, data.month


def _rotulo(inicio: pd.Timestamp, fim: pd.Timestamp) -> str:
    return f"{inicio:%m/%Y} a {fim:%m/%Y}"


def periodos(vendas: pd.DataFrame, serie: pd.DataFrame | None,
             instantaneos: list[tuple[int, int]]) -> pd.DataFrame:
    """Períodos de vendas que casam com dois instantâneos da frota, mais o acumulado.

    ``inicio`` e ``fim`` são o primeiro e o último mês de vendas; a frota se compara
    entre o mês anterior a ``inicio`` e ``fim``. 2021 entra pela série se houver
    instantâneo de dez/2020 e de dez/2021.
    """
    linhas = []
    for inicio, fim in vendas[["inicio", "fim"]].drop_duplicates().itertuples(index=False):
        linhas.append((inicio, fim, "vendas"))
    if serie is not None and not vendas.empty:
        primeiro = vendas["inicio"].min()
        if primeiro.month == 1:
            linhas.append((pd.Timestamp(primeiro.year - 1, 1, 1), pd.Timestamp(primeiro.year - 1, 12, 1), "serie"))
    tabela = pd.DataFrame(linhas, columns=["inicio", "fim", "fonte_vendas"])
    validos = set(instantaneos)
    tabela = tabela[[(_mes(i - pd.offsets.MonthBegin()) in validos) and (_mes(f) in validos)
                     for i, f in zip(tabela["inicio"], tabela["fim"])]]
    return tabela.sort_values("inicio").reset_index(drop=True)


def _crescimento(frota: pd.DataFrame, inicio: pd.Timestamp, fim: pd.Timestamp, chave: list[str]) -> pd.DataFrame:
    """Frota em ``fim`` menos frota no mês anterior a ``inicio``, por ``chave``."""
    antes = _mes(inicio - pd.offsets.MonthBegin())
    depois = _mes(fim)

    def no_mes(ano_mes):
        sel = frota[(frota["ano"] == ano_mes[0]) & (frota["mes"] == ano_mes[1])]
        return sel.groupby(chave, dropna=False, observed=True)["qtd_veiculos"].sum()

    return no_mes(depois).sub(no_mes(antes), fill_value=0).rename("crescimento_frota").reset_index()


def _comparar(tabela: pd.DataFrame) -> pd.DataFrame:
    tabela["vendas_abve"] = tabela["vendas_abve"].fillna(0).astype("int64")
    tabela["crescimento_frota"] = tabela["crescimento_frota"].fillna(0).astype("int64")
    tabela["diferenca"] = tabela["crescimento_frota"] - tabela["vendas_abve"]
    tabela["razao"] = tabela["crescimento_frota"] / tabela["vendas_abve"].where(tabela["vendas_abve"] > 0)
    return tabela


def _com_eletrificada(tabela: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    """Acrescenta a classe 'eletrificada' (elétrico + plug-in + híbrido), o recorte da manchete."""
    eletrificadas = tabela[tabela["classe"].isin(CLASSES_ELETRIFICADAS_MODELO)][["vendas_abve", "crescimento_frota"]
                                                                                + chave]
    if chave:
        soma = eletrificadas.groupby(chave, dropna=False, observed=True).sum().reset_index()
    else:
        soma = eletrificadas.sum().to_frame().T
    soma = soma.assign(classe="eletrificada")
    return pd.concat([tabela, soma], ignore_index=True)


def _por_periodo(pers: pd.DataFrame, vendas_fn, frota: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    """Vendas e crescimento da frota por ``chave`` (que inclui ``classe``) em cada período e no acumulado."""
    pers = pd.concat([pers, pers.agg({"inicio": "min", "fim": "max"}).to_frame().T.assign(fonte_vendas="acumulado")],
                     ignore_index=True) if len(pers) > 1 else pers
    partes = []
    for inicio, fim, fonte in pers.itertuples(index=False):
        vendidas = vendas_fn(inicio, fim, fonte)
        if vendidas is None:
            continue
        tabela = vendidas.merge(_crescimento(frota, inicio, fim, chave), on=chave, how="outer")
        tabela = _com_eletrificada(_comparar(tabela), [c for c in chave if c != "classe"])
        partes.append(tabela.assign(periodo=_rotulo(inicio, fim), inicio=inicio, fim=fim, fonte_vendas=fonte))
    if not partes:
        return pd.DataFrame()
    resultado = _comparar(pd.concat(partes, ignore_index=True))
    colunas = ["periodo", "inicio", "fim", "fonte_vendas"] + chave
    return resultado[colunas + ["vendas_abve", "crescimento_frota", "diferenca", "razao"]].sort_values(
        colunas, na_position="last").reset_index(drop=True)


def _com_rotulo_atual(publicada: pd.DataFrame, reescrita: pd.DataFrame, chave: list[str]) -> pd.DataFrame:
    """Junta à comparação a mesma conta com o histórico da ABVE no rótulo atual de cada modelo."""
    if publicada.empty:
        return publicada
    colunas = ["periodo", "inicio", "fim", "fonte_vendas"] + chave
    tabela = publicada.merge(reescrita[colunas + ["vendas_abve", "crescimento_frota"]], on=colunas, how="outer",
                             suffixes=("", "_atual"))
    tabela["crescimento_frota"] = tabela["crescimento_frota"].fillna(tabela["crescimento_frota_atual"])
    tabela = _comparar(tabela)
    atual = tabela["vendas_abve_atual"].fillna(0).astype("int64")
    tabela = tabela.drop(columns=["vendas_abve_atual", "crescimento_frota_atual"]).assign(
        vendas_abve_rotulo_atual=atual,
        diferenca_rotulo_atual=tabela["crescimento_frota"] - atual,
        razao_rotulo_atual=tabela["crescimento_frota"] / atual.where(atual > 0))
    return tabela.sort_values(colunas, na_position="last").reset_index(drop=True)


def _vendas_classificadas(vendas: pd.DataFrame) -> pd.DataFrame:
    return vendas.assign(classe=vendas["tecnologia"].map(CLASSE_POR_TECNOLOGIA))


def _filtro_vendas(vendas: pd.DataFrame, serie: pd.DataFrame | None, chave: list[str]):
    """Função (início, fim, fonte) -> vendas por ``chave``. A série só tem Brasil e tecnologia."""
    def vendas_fn(inicio, fim, fonte):
        if fonte == "serie" or (fonte == "acumulado" and inicio < vendas["inicio"].min()):
            if chave != ["classe"] or serie is None:
                return None
            s = serie[(serie["data"] >= inicio) & (serie["data"] <= fim)]
            base = s.assign(classe=s["tecnologia"].map(CLASSE_POR_TECNOLOGIA))
            if fonte == "acumulado":
                v = vendas[(vendas["inicio"] >= inicio) & (vendas["fim"] <= fim)]
                base = base[base["data"] < vendas["inicio"].min()]
                base = pd.concat([base, v], ignore_index=True)
        else:
            base = vendas[(vendas["inicio"] >= inicio) & (vendas["fim"] <= fim)]
            if chave != ["classe"]:
                base = base[base["uf_sigla"].notna()] if "uf_sigla" in chave else base
        return (base.groupby(chave, dropna=False, observed=True)["qtd_vendas"].sum()
                .rename("vendas_abve").reset_index())
    return vendas_fn


def _frota_leve(eletrificados: pd.DataFrame, dimensao: pd.DataFrame) -> pd.DataFrame:
    leve = eletrificados[(eletrificados["tipo"] == "leve") & eletrificados["uf_sigla"].notna()]
    marca = dimensao.drop_duplicates("marca_modelo").set_index("marca_modelo")["marca"]
    return leve.assign(marca=leve["marca_modelo"].map(marca))


def validar_abve(tabelas: dict[str, pd.DataFrame], abve: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Tabelas de comparação com a ABVE por tecnologia, UF, marca e modelo."""
    vendas = _vendas_classificadas(abve["vendas"])
    serie = abve.get("serie")
    eletrificados = tabelas["modelo_eletrificados"]
    classificados = tabelas["modelos_classificados"]
    instantaneos = sorted(set(zip(eletrificados["ano"], eletrificados["mes"])))
    pers = periodos(vendas, serie, instantaneos)
    if pers.empty:
        return {}
    frota = _frota_leve(eletrificados, tabelas["modelos_dimensao"])

    # marca da ABVE pelo modelo, quando o texto casa com a base; senão, o fabricante dela
    chaves = classificados.drop_duplicates("marca_modelo_norm")[["marca_modelo_norm", "marca"]]
    chaves = chaves.assign(chave=chaves["marca_modelo_norm"].map(chave_abve))
    marca_por_chave = chaves.drop_duplicates("chave").set_index("chave")["marca"]
    vendas = vendas.assign(chave=casar_modelos_abve(vendas["modelo"], set(marca_por_chave.index)))
    vendas["marca"] = vendas["chave"].map(marca_por_chave).fillna(vendas["fabricante"].map(normalizar))
    atual = vendas.assign(classe=vendas["chave"].map(rotulo_atual(vendas)))

    def comparar(periodos_: pd.DataFrame, chave: list[str], serie_: pd.DataFrame | None) -> pd.DataFrame:
        return _com_rotulo_atual(_por_periodo(periodos_, _filtro_vendas(vendas, serie_, chave), frota, chave),
                                 _por_periodo(periodos_, _filtro_vendas(atual, serie_, chave), frota, chave), chave)

    so_vendas = pers[pers["fonte_vendas"] == "vendas"]
    resultado = {
        "validacao_abve_tecnologia": comparar(pers, ["classe"], serie),
        "validacao_abve_uf": comparar(so_vendas, ["uf_sigla", "classe"], None),
        "validacao_abve_marca": comparar(so_vendas, ["marca", "classe"], None),
        "validacao_abve_modelo": validar_modelos(so_vendas, vendas, classificados),
    }
    return {nome: tabela for nome, tabela in resultado.items() if not tabela.empty}


def validar_modelos(pers: pd.DataFrame, vendas: pd.DataFrame, classificados: pd.DataFrame) -> pd.DataFrame:
    """Modelo a modelo: classe da ABVE x classe daqui x PBE, e vendas x crescimento nas UFs válidas.

    Entram os modelos que a ABVE vendeu e os leves que a base classifica como
    eletrificados ou híbridos leves, vendidos ou não pela ABVE.
    """
    cls = classificados.assign(chave=classificados["marca_modelo_norm"].map(chave_abve),
                               qtd_veiculos=classificados["qtd_veiculos"] - classificados["qtd_sem_uf"])
    # um texto da ABVE pode corresponder a mais de uma grafia aqui (importado e nacional)
    atributos = (cls.sort_values(["ano", "mes", "qtd_veiculos"], ascending=[False, False, False])
                 .groupby("chave").agg(marca_modelo_norm=("marca_modelo_norm", lambda s: " | ".join(sorted(set(s)))),
                                       marca=("marca", "first"), classe_db=("classe", "first"),
                                       tipo=("tipo", "first"), pbe_classes=("pbe_classes", "first"))
                 .reset_index())
    rotulos = rotulo_atual(vendas)
    relevantes = set(vendas["chave"]) | set(atributos.loc[atributos["classe_db"].isin(CLASSES_ABVE)
                                                         & (atributos["tipo"] == "leve"), "chave"])
    cls = cls[cls["chave"].isin(relevantes)]
    vendas = vendas[vendas["chave"].isin(relevantes)]
    if len(pers) > 1:
        pers = pd.concat([pers, pers.agg({"inicio": "min", "fim": "max"}).to_frame().T.assign(
            fonte_vendas="acumulado")], ignore_index=True)

    partes = []
    for inicio, fim, fonte in pers.itertuples(index=False):
        v = vendas[(vendas["inicio"] >= inicio) & (vendas["fim"] <= fim)]
        por_classe = v.groupby(["chave", "classe"])["qtd_vendas"].sum().unstack(fill_value=0)
        tabela = pd.DataFrame({
            "vendas_abve": por_classe.sum(axis=1),
            "classe_abve": por_classe.idxmax(axis=1),
            "classes_abve": por_classe.apply(lambda r: " | ".join(c for c in CLASSES_ABVE if r.get(c, 0) > 0), axis=1),
        }).reset_index()
        tabela = tabela.merge(_crescimento(cls, inicio, fim, ["chave"]), on="chave", how="outer")
        partes.append(_comparar(tabela).assign(periodo=_rotulo(inicio, fim), inicio=inicio, fim=fim,
                                               fonte_vendas=fonte))
    tabela = pd.concat(partes, ignore_index=True).merge(atributos, on="chave", how="left")
    tabela = tabela[(tabela["vendas_abve"] > 0) | (tabela["crescimento_frota"] != 0)]
    tabela["casou"] = tabela["classe_db"].notna()
    comparavel = tabela["classe_abve"].notna() & tabela["casou"]
    tabela["mesma_classe"] = pd.array([a == b if c else pd.NA for a, b, c in
                                       zip(tabela["classe_abve"], tabela["classe_db"], comparavel)], dtype="boolean")
    tabela["classe_abve_atual"] = tabela["chave"].map(rotulos)
    comparavel = tabela["classe_abve_atual"].notna() & tabela["casou"]
    tabela["mesma_classe_atual"] = pd.array([a == b if c else pd.NA for a, b, c in zip(
        tabela["classe_abve_atual"], tabela["classe_db"], comparavel)], dtype="boolean")
    colunas = ["periodo", "inicio", "fim", "fonte_vendas", "modelo_abve", "marca_modelo_norm", "marca",
               "classe_abve", "classes_abve", "classe_abve_atual", "classe_db", "mesma_classe", "mesma_classe_atual",
               "pbe_classes", "casou", "vendas_abve", "crescimento_frota", "diferenca", "razao"]
    return (tabela.rename(columns={"chave": "modelo_abve"})[colunas]
            .sort_values(["inicio", "fim", "vendas_abve"], ascending=[True, True, False]).reset_index(drop=True))


def validar_pbe(classificados: pd.DataFrame) -> pd.DataFrame:
    """Cobertura e divergências do PBE Veicular por mês e classe."""
    qtd = classificados["qtd_veiculos"]
    casou = (classificados["pbe_classes"].fillna("") != "").astype("int64")
    sem_versao = (classificados["pbe_aviso"] == "sem_versao_no_pbe").fillna(False).astype("int64")
    so_eletrificado = (classificados["pbe_aviso"] == "pbe_so_eletrificado").fillna(False).astype("int64")
    c = classificados.assign(
        modelos=1, frota=qtd, frota_casada_pbe=qtd * casou,
        modelos_sem_versao_no_pbe=sem_versao, frota_sem_versao_no_pbe=qtd * sem_versao,
        modelos_pbe_so_eletrificado=so_eletrificado, frota_pbe_so_eletrificado=qtd * so_eletrificado)
    chave = ["ano", "mes", "data_referencia", "classe"]
    medidas = ["modelos", "frota", "frota_casada_pbe", "modelos_sem_versao_no_pbe", "frota_sem_versao_no_pbe",
               "modelos_pbe_so_eletrificado", "frota_pbe_so_eletrificado"]
    tabela = c.groupby(chave, observed=True)[medidas].sum().reset_index()
    tabela["cobertura_pbe"] = tabela["frota_casada_pbe"] / tabela["frota"].where(tabela["frota"] > 0)
    return tabela


def modelo_sem_uf(classificados: pd.DataFrame) -> pd.DataFrame:
    """O grupo sem UF por mês e classe, com a parte dele na frota do Brasil."""
    chave = ["ano", "mes", "data_referencia", "classe"]
    tabela = (classificados.groupby(chave, observed=True)[["qtd_sem_uf", "qtd_veiculos"]].sum().reset_index()
              .rename(columns={"qtd_sem_uf": "frota_sem_uf", "qtd_veiculos": "frota_brasil"}))
    tabela["parte_sem_uf"] = tabela["frota_sem_uf"] / tabela["frota_brasil"].where(tabela["frota_brasil"] > 0)
    return tabela


def validar(tabelas: dict[str, pd.DataFrame], abve: dict[str, pd.DataFrame] | None) -> dict[str, pd.DataFrame]:
    """Todas as tabelas de validação que as entradas permitem."""
    if "modelos_classificados" not in tabelas:
        return {}
    resultado = {"validacao_pbe": validar_pbe(tabelas["modelos_classificados"])}
    if "qtd_sem_uf" in tabelas["modelos_classificados"]:
        resultado["modelo_sem_uf"] = modelo_sem_uf(tabelas["modelos_classificados"])
    if abve is not None and "modelo_eletrificados" in tabelas:
        resultado |= validar_abve(tabelas, abve)
    return resultado

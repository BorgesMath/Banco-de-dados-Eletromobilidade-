"""Painel web da base: um HTML único, com dados embutidos, gerado a partir de ``resultados/``.

O painel lê só o que está publicado em ``resultados/`` (nunca ``data/``), então
qualquer pessoa com o repositório regenera a página. Saída: ``painel/index.html``,
publicado no GitHub Pages pelo workflow ``.github/workflows/painel.yml``.

Recortes embutidos (a página tem de abrir rápido):

* série mensal por UF (com o grupo sem UF à parte), tipo de veículo e classe;
* frota total e população por UF e mês, para participação e taxa por habitante;
* município e modelo só no último mês;
* a validação contra a ABVE e a lista dos arquivos da SENATRAN usados em cada mês.

Os links dos arquivos originais vêm do portal de dados abertos e do gov.br
(``coleta.listar``) e ficam guardados em ``painel/fontes.json``, para que gerar
a página não dependa da rede; ``--atualizar-fontes`` refaz a lista.

Os mapas usam a malha municipal do IBGE em qualidade mínima, em TopoJSON
(``painel_web/malha_municipios.json``, 5.570 municípios); os estados saem da
união dos municípios, na própria página. ``--atualizar-malha`` baixa de novo.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import coleta
from .publicacao import PUBLICADAS

log = logging.getLogger(__name__)

MODELO = Path(__file__).with_name("painel_web")
REPOSITORIO = "https://github.com/BorgesMath/Banco-de-dados-Eletromobilidade-"
BRUTO = f"{REPOSITORIO}/raw/main/resultados"
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR"
             "?formato=application/json&qualidade=minima&intrarregiao=municipio")

CLASSES = ["eletrico", "hibrido_plug_in", "hibrido", "hibrido_leve", "celula_combustivel"]
TIPOS = ["leve", "moto", "onibus", "caminhao", "outros", "sem_tipo"]
SEM_UF = "SU"
UFS = {  # sigla: (nome, região), na ordem do código IBGE
    "RO": ("Rondônia", "Norte"), "AC": ("Acre", "Norte"), "AM": ("Amazonas", "Norte"),
    "RR": ("Roraima", "Norte"), "PA": ("Pará", "Norte"), "AP": ("Amapá", "Norte"),
    "TO": ("Tocantins", "Norte"), "MA": ("Maranhão", "Nordeste"), "PI": ("Piauí", "Nordeste"),
    "CE": ("Ceará", "Nordeste"), "RN": ("Rio Grande do Norte", "Nordeste"), "PB": ("Paraíba", "Nordeste"),
    "PE": ("Pernambuco", "Nordeste"), "AL": ("Alagoas", "Nordeste"), "SE": ("Sergipe", "Nordeste"),
    "BA": ("Bahia", "Nordeste"), "MG": ("Minas Gerais", "Sudeste"), "ES": ("Espírito Santo", "Sudeste"),
    "RJ": ("Rio de Janeiro", "Sudeste"), "SP": ("São Paulo", "Sudeste"), "PR": ("Paraná", "Sul"),
    "SC": ("Santa Catarina", "Sul"), "RS": ("Rio Grande do Sul", "Sul"),
    "MS": ("Mato Grosso do Sul", "Centro-Oeste"), "MT": ("Mato Grosso", "Centro-Oeste"),
    "GO": ("Goiás", "Centro-Oeste"), "DF": ("Distrito Federal", "Centro-Oeste"),
}
SIGLAS = list(UFS) + [SEM_UF]
COD_UF = {"RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17, "MA": 21, "PI": 22, "CE": 23,
          "RN": 24, "PB": 25, "PE": 26, "AL": 27, "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35,
          "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53}


def _ler(resultados: Path, nome: str, colunas: list[str] | None = None) -> pd.DataFrame:
    if (resultados / f"{nome}.parquet").exists():
        return pd.read_parquet(resultados / f"{nome}.parquet", columns=colunas)
    tabela = pd.read_csv(resultados / f"{nome}.csv", sep=";", decimal=",", encoding="utf-8-sig")
    return tabela[colunas] if colunas else tabela


def _indice(valores: pd.Series, dominio: list) -> list[int]:
    posicao = {v: i for i, v in enumerate(dominio)}
    return [posicao[v] for v in valores]


def _mes(ano, mes) -> str:
    return f"{int(ano)}-{int(mes):02d}"


def dados_painel(resultados: str | Path, fontes: list[dict] | None = None) -> dict:
    """Tudo o que a página precisa, em colunas (listas paralelas) para ocupar pouco."""
    resultados = Path(resultados)
    detalhe = _ler(resultados, "modelo_eletrificados", ["ano", "mes", "uf_sigla", "cod_municipio_ibge",
                                                        "marca_modelo", "tipo", "classe", "qtd_veiculos"])
    detalhe["uf_sigla"] = detalhe["uf_sigla"].fillna(SEM_UF).astype(str)
    detalhe["tipo"] = detalhe["tipo"].fillna("sem_tipo").astype(str)
    detalhe["classe"] = detalhe["classe"].astype(str)
    detalhe["m"] = [_mes(a, m) for a, m in zip(detalhe["ano"], detalhe["mes"])]
    meses = sorted(detalhe["m"].unique())
    ultimo = meses[-1]

    serie = detalhe.groupby(["m", "uf_sigla", "tipo", "classe"], observed=True)["qtd_veiculos"].sum().reset_index()
    serie = serie[serie["qtd_veiculos"] > 0]

    # frota total (todas as classes e tipos) e população, por UF e mês; o grupo sem UF é Brasil − UFs
    por_uf = _ler(resultados, "modelo_uf", ["ano", "mes", "uf_sigla", "frota_total"])
    brasil = _ler(resultados, "modelo_brasil", ["ano", "mes", "frota_total"])
    populacao = _ler(resultados, "combustivel_uf", ["ano", "mes", "uf_sigla", "populacao"])
    por_uf = por_uf.dropna(subset=["uf_sigla"]).merge(populacao, on=["ano", "mes", "uf_sigla"], how="left")
    sem_uf = brasil.set_index(["ano", "mes"])["frota_total"] - por_uf.groupby(["ano", "mes"])["frota_total"].sum()
    por_uf = pd.concat([por_uf, sem_uf.rename("frota_total").reset_index().assign(uf_sigla=SEM_UF)],
                       ignore_index=True)
    por_uf["m"] = [_mes(a, m) for a, m in zip(por_uf["ano"], por_uf["mes"])]
    por_uf = por_uf[por_uf["m"].isin(meses)].sort_values(["m", "uf_sigla"])

    recente = detalhe[detalhe["m"] == ultimo]
    municipios = (recente[recente["uf_sigla"] != SEM_UF]
                  .groupby(["cod_municipio_ibge", "tipo", "classe"], observed=True)["qtd_veiculos"].sum()
                  .reset_index())
    municipios["cod_municipio_ibge"] = municipios["cod_municipio_ibge"].astype("int64")
    ano, mes = map(int, ultimo.split("-"))
    frota_mun = _ler(resultados, "modelo_municipio", ["ano", "mes", "cod_municipio_ibge", "frota_total"])
    frota_mun = frota_mun[(frota_mun["ano"] == ano) & (frota_mun["mes"] == mes)].dropna(subset=["cod_municipio_ibge"])
    frota_mun = frota_mun.groupby("cod_municipio_ibge")["frota_total"].sum()
    pop_mun = _ler(resultados, "combustivel_municipio", ["ano", "mes", "cod_municipio_ibge", "populacao"])
    pop_mun = pop_mun[(pop_mun["ano"] == ano) & (pop_mun["mes"] == mes)].dropna(subset=["cod_municipio_ibge"])
    pop_mun = pop_mun.groupby("cod_municipio_ibge")["populacao"].sum()
    dimensao = _ler(resultados, "municipios_dimensao", ["cod_municipio_ibge", "municipio_ibge", "uf_sigla"])
    dimensao = dimensao.dropna(subset=["cod_municipio_ibge"]).astype({"cod_municipio_ibge": "int64"})
    dimensao = dimensao.sort_values("cod_municipio_ibge").reset_index(drop=True)
    dimensao["frota_total"] = dimensao["cod_municipio_ibge"].map(frota_mun).fillna(0).astype("int64")
    dimensao["populacao"] = dimensao["cod_municipio_ibge"].map(pop_mun)

    modelos = recente.groupby(["marca_modelo", "uf_sigla", "tipo", "classe"], observed=True)["qtd_veiculos"].sum()
    modelos = modelos[modelos > 0].reset_index()
    marcas = _ler(resultados, "modelos_dimensao", ["marca_modelo", "marca"]).drop_duplicates("marca_modelo")
    nomes_modelo = sorted(modelos["marca_modelo"].unique())
    marca = marcas.set_index("marca_modelo")["marca"].reindex(nomes_modelo).fillna("?")

    return {
        "meta": {
            "gerado": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "meses": meses,
            "ufs": [[s, *UFS[s], COD_UF[s]] for s in UFS] + [[SEM_UF, "Sem UF informada", "—", None]],
            "tipos": TIPOS,
            "classes": CLASSES,
            "repositorio": REPOSITORIO,
        },
        "serie": {
            "m": _indice(serie["m"], meses), "u": _indice(serie["uf_sigla"], SIGLAS),
            "t": _indice(serie["tipo"], TIPOS), "c": _indice(serie["classe"], CLASSES),
            "v": serie["qtd_veiculos"].astype("int64").tolist(),
        },
        "uf_mes": {
            "m": _indice(por_uf["m"], meses), "u": _indice(por_uf["uf_sigla"], SIGLAS),
            "total": por_uf["frota_total"].astype("int64").tolist(),
            "pop": [None if pd.isna(p) else int(p) for p in por_uf["populacao"]],
        },
        "municipios": {
            "cod": dimensao["cod_municipio_ibge"].tolist(), "nome": dimensao["municipio_ibge"].tolist(),
            "u": _indice(dimensao["uf_sigla"], SIGLAS), "total": dimensao["frota_total"].tolist(),
            "pop": [None if pd.isna(p) else int(p) for p in dimensao["populacao"]],
            "i": _indice(municipios["cod_municipio_ibge"], dimensao["cod_municipio_ibge"].tolist()),
            "t": _indice(municipios["tipo"], TIPOS), "c": _indice(municipios["classe"], CLASSES),
            "v": municipios["qtd_veiculos"].astype("int64").tolist(),
        },
        "modelos": {
            "nome": nomes_modelo, "marca": marca.tolist(),
            "i": _indice(modelos["marca_modelo"], nomes_modelo), "u": _indice(modelos["uf_sigla"], SIGLAS),
            "t": _indice(modelos["tipo"], TIPOS), "c": _indice(modelos["classe"], CLASSES),
            "v": modelos["qtd_veiculos"].astype("int64").tolist(),
        },
        "abve": validacao_abve(resultados),
        "fontes": fontes or [],
        "arquivos": arquivos_publicados(resultados),
    }


def validacao_abve(resultados: Path) -> dict:
    """Vendas da ABVE x crescimento da frota (leves, UFs válidas): por ano, por UF e por marca."""
    colunas = ["vendas_abve", "crescimento_frota", "vendas_abve_rotulo_atual"]

    def linhas(tabela: pd.DataFrame, chave: list[str]) -> list[list]:
        return tabela[chave + colunas].astype({c: "int64" for c in colunas}).values.tolist()

    if not (resultados / "validacao_abve_tecnologia.csv").exists():
        return {}
    tecnologia = _ler(resultados, "validacao_abve_tecnologia")
    uf = _ler(resultados, "validacao_abve_uf")
    marca = _ler(resultados, "validacao_abve_marca")
    acumulado = tecnologia[tecnologia["fonte_vendas"] == "acumulado"]
    return {
        "colunas": colunas,
        "periodo": acumulado["periodo"].iloc[0] if len(acumulado) else "",
        "tecnologia": linhas(tecnologia, ["periodo", "fonte_vendas", "classe"]),
        "uf": linhas(uf[uf["fonte_vendas"] == "acumulado"], ["uf_sigla", "classe"]),
        "uf_periodo": uf.loc[uf["fonte_vendas"] == "acumulado", "periodo"].iloc[0] if len(uf) else "",
        "marca": linhas(marca[marca["fonte_vendas"] == "acumulado"], ["marca", "classe"]),
    }


def arquivos_publicados(resultados: Path) -> list[dict]:
    lista = []
    for nome, (formato, descricao) in PUBLICADAS.items():
        caminho = resultados / f"{nome}.{formato}"
        if caminho.exists():
            lista.append({"arquivo": caminho.name, "descricao": descricao, "bytes": caminho.stat().st_size,
                          "url": f"{BRUTO}/{caminho.name}"})
    for extra in ("LEIAME.md", "DICIONARIO.md"):
        if (resultados / extra).exists():
            lista.append({"arquivo": extra, "descricao": "Documentação dos resultados.",
                          "bytes": (resultados / extra).stat().st_size,
                          "url": f"{REPOSITORIO}/blob/main/resultados/{extra}"})
    return lista


def listar_fontes(resultados: str | Path, sessao=None, cache_ckan: Path | None = None) -> list[dict]:
    """Para cada mês da série, o arquivo da SENATRAN de cada base e o link para baixá-lo.

    O arquivo é o que a qualidade registra como lido; o link é o da fonte que o
    publica com o mesmo nome (sem diferenciar caixa) ou, sem nome igual, o do mesmo mês.
    """
    resultados = Path(resultados)
    qualidade = {"modelo": _ler(resultados, "qualidade_modelo"), "combustivel": _ler(resultados, "qualidade_combustivel")}
    anos = sorted({int(a) for q in qualidade.values() for a in q["ano"]})
    links = coleta.listar(anos, sessao=sessao, cache_ckan=cache_ckan)
    fontes: dict[str, dict] = {}
    for base, tabela in (("modelo", "marca_modelo"), ("combustivel", "combustivel")):
        candidatos = [l for l in links if l.tabela == tabela]
        por_nome = {l.nome_arquivo.lower(): l for l in candidatos}
        por_periodo = {l.periodo: l for l in coleta.selecionar(candidatos, tabela) if l.periodo}
        for linha in qualidade[base].itertuples():
            if not isinstance(linha.arquivo, str) or not linha.arquivo:
                continue
            link = por_nome.get(linha.arquivo.lower()) or por_periodo.get((int(linha.ano), int(linha.mes)))
            fontes.setdefault(_mes(linha.ano, linha.mes), {})[base] = {
                "arquivo": linha.arquivo, "url": link.url_arquivo if link else None,
                "origem": ("dados abertos" if link.fonte == "ckan" else "gov.br") if link else None,
                "incluido": bool(linha.incluido) if not isinstance(linha.incluido, str) else linha.incluido == "True",
                "ajuste": linha.ajuste if isinstance(linha.ajuste, str) else "",
            }
    return [{"mes": mes, **bases} for mes, bases in sorted(fontes.items())]


def _json_seguro(dados: dict) -> str:
    # dentro de <script>, "</" encerraria o bloco
    return json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def montar_html(dados: dict, modelo: Path = MODELO) -> str:
    pagina = (modelo / "painel.html").read_text(encoding="utf-8")
    trocas = {
        "/*__ESTILO__*/": (modelo / "painel.css").read_text(encoding="utf-8"),
        "/*__D3__*/": (modelo / "d3.min.js").read_text(encoding="utf-8"),
        "/*__TOPOJSON__*/": (modelo / "topojson-client.min.js").read_text(encoding="utf-8"),
        "/*__MALHA__*/": f"window.DEMOB_MALHA = {(modelo / 'malha_municipios.json').read_text(encoding='utf-8')};",
        "/*__DADOS__*/": f"window.DEMOB = {_json_seguro(dados)};",
        "/*__APP__*/": (modelo / "painel.js").read_text(encoding="utf-8"),
    }
    for marcador, conteudo in trocas.items():
        assert pagina.count(marcador) == 1, marcador
        pagina = pagina.replace(marcador, conteudo)
    return pagina


def baixar_malha(destino: Path = MODELO / "malha_municipios.json", sessao=None) -> Path:
    """Malha municipal do IBGE (TopoJSON, qualidade mínima), conferida antes de gravar."""
    resposta = (sessao or coleta.criar_sessao()).get(URL_MALHA, timeout=120)
    resposta.raise_for_status()
    malha = resposta.json()
    geometrias = next(iter(malha["objects"].values()))["geometries"]
    if malha.get("type") != "Topology" or len(geometrias) < 5500:
        raise ValueError(f"Malha do IBGE inesperada: {len(geometrias)} geometrias")
    destino.write_text(json.dumps(malha, separators=(",", ":")), encoding="utf-8")
    return destino


def gerar_painel(resultados: str | Path, saida: str | Path, atualizar_fontes: bool = False,
                 cache_ckan: Path | None = None, atualizar_malha: bool = False) -> Path:
    """Escreve o HTML do painel; a lista de fontes fica ao lado, em ``fontes.json``."""
    saida = Path(saida)
    if atualizar_malha:
        baixar_malha()
    saida.parent.mkdir(parents=True, exist_ok=True)
    arquivo_fontes = saida.with_name("fontes.json")
    if atualizar_fontes or not arquivo_fontes.exists():
        fontes = listar_fontes(resultados, cache_ckan=cache_ckan)
        arquivo_fontes.write_text(json.dumps(fontes, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        fontes = json.loads(arquivo_fontes.read_text(encoding="utf-8"))
    saida.write_text(montar_html(dados_painel(resultados, fontes)), encoding="utf-8")
    log.info("Painel: %s (%.1f MB)", saida, saida.stat().st_size / 1e6)
    return saida

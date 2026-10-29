"""Vendas de eletrificados da ABVE, para validar a base por modelo.

A fonte é o painel público BI Frotas da ABVE (abve.org.br/bi-frotas/), um
relatório do Power BI publicado na web. Não há arquivo para baixar: os dados se
consultam pela mesma API que o navegador usa (``querydata``), com a chave pública
que está no endereço do painel. Duas tabelas do modelo deles interessam:

* ``BaseVendas_ABVE``: emplacamentos por data, UF, fabricante, modelo (o texto
  "Marca Modelo" do RENAVAM, sem o prefixo ``I/`` e com espaço no lugar da barra)
  e tecnologia (BEV, PHEV, HEV, HEV FLEX, MHEV, MHEV 12V, MHEV 48V), de jan/2022
  em diante;
* ``BaseSerieHistoricaTecnologia``: emplacamentos por mês e tecnologia, Brasil,
  desde 2012. É o que cobre 2021.

A API devolve cada consulta no formato compactado do Power BI (DSR), com
dicionários de valores e máscaras de repetição, e corta respostas grandes. Por
isso as vendas são consultadas por período e UF, e cada período é conferido
contra o total nacional: fatia que não fecha é erro, não aviso.

Os dados brutos ficam em ``data/raw/abve/`` e não vão para o repositório: são de
terceiro. O que se publica é a comparação (``validacao.py``).
"""

from __future__ import annotations

import base64
import json
import logging
import re
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .coleta import CABECALHOS

log = logging.getLogger(__name__)

URL_PAINEL = "https://abve.org.br/bi-frotas/"
# o "r=" do endereço do painel, em base64: {"k": chave do relatório, "t": inquilino}
CHAVE_PADRAO = "bc748218-53e3-462f-bf8c-7a4347ae9149"
API = "https://wabi-brazil-south-b-primary-api.analysis.windows.net/public/reports"

ARQUIVO_VENDAS = "vendas_abve.parquet"
ARQUIVO_SERIE = "serie_abve.parquet"

# tecnologia da ABVE -> classe da base por modelo
CLASSE_POR_TECNOLOGIA = {
    "BEV": "eletrico",
    "PHEV": "hibrido_plug_in",
    "HEV": "hibrido",
    "HEV FLEX": "hibrido",
    "MHEV": "hibrido_leve",
    "MHEV 12V": "hibrido_leve",
    "MHEV 48V": "hibrido_leve",
}


def chave_do_painel(html: str) -> str | None:
    """Chave pública do relatório, lida do ``view?r=`` embutido na página do painel."""
    achado = re.search(r"app\.powerbi\.com/view\?r=([A-Za-z0-9_=-]+)", html)
    if not achado:
        return None
    codigo = achado.group(1)
    return json.loads(base64.b64decode(codigo + "=" * (-len(codigo) % 4)))["k"]


def criar_sessao(tentativas: int = 5, espera: float = 2.0) -> requests.Session:
    """Sessão com novas tentativas também no POST, que é como a API consulta."""
    sessao = requests.Session()
    retry = Retry(total=tentativas, backoff_factor=espera, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET", "POST"), raise_on_status=False)
    sessao.mount("https://", HTTPAdapter(max_retries=retry))
    sessao.headers.update(CABECALHOS)
    return sessao


class ClienteABVE:
    """Consultas ao relatório público. ``chave`` é a do painel; o modelo é descoberto por ela."""

    def __init__(self, chave: str = CHAVE_PADRAO, sessao: requests.Session | None = None):
        self.chave = chave
        self.sessao = sessao or criar_sessao()
        self.sessao.headers["X-PowerBI-ResourceKey"] = chave
        self._modelo: int | None = None

    @property
    def modelo(self) -> int:
        if self._modelo is None:
            r = self.sessao.get(f"{API}/{self.chave}/modelsAndExploration?preferReadOnlySession=true", timeout=60)
            r.raise_for_status()
            self._modelo = r.json()["models"][0]["id"]
        return self._modelo

    def consultar(self, entidade: str, colunas: list[str], medida: str,
                  filtros: list[dict] | None = None) -> pd.DataFrame:
        """Soma de ``medida`` por ``colunas`` da ``entidade``; uma linha por combinação."""
        corpo = corpo_consulta(entidade, colunas, medida, filtros, self.modelo)
        r = self.sessao.post(f"{API}/querydata?synchronous=true", json=corpo, timeout=180)
        r.raise_for_status()
        linhas = decodificar_dsr(r.json(), len(colunas) + 1)
        return pd.DataFrame(linhas, columns=colunas + [medida])


def _coluna(propriedade: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Source": "b"}}, "Property": propriedade}}


def filtro_igual(propriedade: str, valor: str) -> dict:
    texto = valor.replace("'", "''")
    return {"Condition": {"In": {"Expressions": [_coluna(propriedade)],
                                 "Values": [[{"Literal": {"Value": f"'{texto}'"}}]]}}}


def filtro_datas(propriedade: str, inicio: pd.Timestamp, fim: pd.Timestamp) -> dict:
    """``inicio <= propriedade < fim``."""
    def comparar(tipo: int, data: pd.Timestamp) -> dict:
        return {"Comparison": {"ComparisonKind": tipo, "Left": _coluna(propriedade),
                               "Right": {"Literal": {"Value": f"datetime'{data:%Y-%m-%dT00:00:00}'"}}}}
    return {"Condition": {"And": {"Left": comparar(2, inicio), "Right": comparar(3, fim)}}}


def corpo_consulta(entidade: str, colunas: list[str], medida: str, filtros: list[dict] | None,
                   modelo: int) -> dict:
    selecao = [{**_coluna(c), "Name": f"b.{c}"} for c in colunas]
    selecao.append({"Aggregation": {"Expression": _coluna(medida), "Function": 0}, "Name": f"Sum(b.{medida})"})
    consulta = {"Version": 2, "From": [{"Name": "b", "Entity": entidade, "Type": 0}], "Select": selecao}
    if filtros:
        consulta["Where"] = filtros
    comando = {"SemanticQueryDataShapeCommand": {
        "Query": consulta,
        "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(selecao)))}]},
                    "DataReduction": {"DataVolume": 4, "Primary": {"Window": {"Count": 30000}}},
                    "Version": 1}}}
    return {"version": "1.0.0", "queries": [{"Query": {"Commands": [comando]}, "QueryId": ""}],
            "cancelQueries": [], "modelId": modelo}


def decodificar_dsr(resposta: dict, n_colunas: int) -> list[list]:
    """Linhas de uma resposta DSR do Power BI.

    Cada linha traz em ``C`` só os valores que mudaram. ``R`` é a máscara de bits
    das colunas que repetem a linha anterior, ``Ø`` a das nulas, e o valor de uma
    coluna com dicionário (``DN`` no esquema ``S``) é o índice em ``ValueDicts``.
    """
    ds = resposta["results"][0]["result"]["data"]["dsr"]["DS"][0]
    dicionarios = ds.get("ValueDicts", {})
    esquema, anterior, linhas = None, [None] * n_colunas, []
    for registro in ds["PH"][0].get("DM0", []):
        esquema = registro.get("S", esquema)
        valores = iter(registro.get("C", []))
        repete, nulas = registro.get("R", 0), registro.get("Ø", 0)
        atual = []
        for i in range(n_colunas):
            if repete >> i & 1:
                valor = anterior[i]
            elif nulas >> i & 1:
                valor = None
            else:
                valor = next(valores)
                dicionario = esquema[i].get("DN") if esquema and i < len(esquema) else None
                if dicionario and isinstance(valor, int):
                    valor = dicionarios[dicionario][valor]
            atual.append(valor)
        linhas.append(atual)
        anterior = atual
    return linhas


def periodos_anuais(ate: tuple[int, int], desde: int = 2022) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Anos civis de ``desde`` até o ano de ``ate``, o último cortado no mês de ``ate``.

    Cada período é ``[início, fim)``: é o intervalo de vendas que corresponde ao
    crescimento da frota entre dois instantâneos (dezembro a dezembro, e dezembro
    ao último mês).
    """
    ano_final, mes_final = ate
    periodos = [(pd.Timestamp(a, 1, 1), pd.Timestamp(a + 1, 1, 1)) for a in range(desde, ano_final)]
    periodos.append((pd.Timestamp(ano_final, 1, 1), pd.Timestamp(ano_final, mes_final, 1) + pd.offsets.MonthBegin()))
    return periodos


def baixar_vendas(cliente: ClienteABVE, ate: tuple[int, int], desde: int = 2022) -> pd.DataFrame:
    """Vendas por período anual, UF, fabricante, modelo, tecnologia e segmento.

    Cada período é consultado UF a UF e conferido contra o total nacional do período.
    """
    ufs = cliente.consultar("BaseVendas_ABVE", ["Estado"], "QTD")["Estado"].tolist()
    colunas = ["Fabricante", "Modelo", "Tipo_Tecnologia", "Segmento"]
    partes = []
    for inicio, fim in periodos_anuais(ate, desde):
        datas = filtro_datas("Data_Emplacamento", inicio, fim)
        total = int(cliente.consultar("BaseVendas_ABVE", ["Tipo_Tecnologia"], "QTD", [datas])["QTD"].sum())
        fatias = []
        for uf in ufs:
            fatia = cliente.consultar("BaseVendas_ABVE", colunas, "QTD", [datas, filtro_igual("Estado", uf)])
            fatias.append(fatia.assign(uf_sigla=uf or None))
        periodo = pd.concat(fatias, ignore_index=True)
        if int(periodo["QTD"].sum()) != total:
            raise ValueError(f"ABVE, {inicio:%Y-%m} a {fim:%Y-%m}: as UFs somam {int(periodo['QTD'].sum())}, "
                             f"o total nacional é {total}. Resposta cortada pela API?")
        log.info("ABVE, %s a %s: %d vendas em %d linhas", f"{inicio:%m/%Y}", f"{fim - pd.Timedelta(days=1):%m/%Y}",
                 total, len(periodo))
        partes.append(periodo.assign(inicio=inicio, fim=fim - pd.offsets.MonthBegin()))
    vendas = pd.concat(partes, ignore_index=True).rename(columns={
        "Fabricante": "fabricante", "Modelo": "modelo", "Tipo_Tecnologia": "tecnologia",
        "Segmento": "segmento", "QTD": "qtd_vendas"})
    vendas["qtd_vendas"] = vendas["qtd_vendas"].astype("int64")
    return vendas[["inicio", "fim", "uf_sigla", "fabricante", "modelo", "tecnologia", "segmento", "qtd_vendas"]]


def baixar_serie(cliente: ClienteABVE) -> pd.DataFrame:
    """Vendas por mês e tecnologia, Brasil (``BaseSerieHistoricaTecnologia``)."""
    serie = cliente.consultar("BaseSerieHistoricaTecnologia", ["Data", "Tipo de Tecnologia "], "Qtd")
    serie.columns = ["data", "tecnologia", "qtd_vendas"]
    serie["data"] = pd.to_datetime(serie["data"], unit="ms").dt.to_period("M").dt.to_timestamp()
    serie["tecnologia"] = serie["tecnologia"].str.strip()
    serie["qtd_vendas"] = serie["qtd_vendas"].astype("int64")
    return serie.groupby(["data", "tecnologia"], as_index=False)["qtd_vendas"].sum()


def chave_atual(sessao: requests.Session | None = None) -> str:
    """Chave lida da página do painel; a conhecida, se a página não responder ou mudar de formato."""
    try:
        r = (sessao or criar_sessao()).get(URL_PAINEL, timeout=60)
        return chave_do_painel(r.text) or CHAVE_PADRAO
    except requests.RequestException:
        return CHAVE_PADRAO


def baixar(destino: str | Path, ate: tuple[int, int], cliente: ClienteABVE | None = None) -> list[Path]:
    """Baixa as vendas e a série para ``destino`` (``data/raw/abve``)."""
    cliente = cliente or ClienteABVE(chave_atual())
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    gravados = []
    for nome, tabela in ((ARQUIVO_VENDAS, baixar_vendas(cliente, ate)), (ARQUIVO_SERIE, baixar_serie(cliente))):
        caminho = destino / nome
        tabela.to_parquet(caminho, index=False)
        gravados.append(caminho)
    return gravados


def carregar(pasta: str | Path) -> dict[str, pd.DataFrame] | None:
    """Vendas e série já baixadas, ou ``None`` se não houver."""
    pasta = Path(pasta)
    if not (pasta / ARQUIVO_VENDAS).exists():
        return None
    tabelas = {"vendas": pd.read_parquet(pasta / ARQUIVO_VENDAS)}
    if (pasta / ARQUIVO_SERIE).exists():
        tabelas["serie"] = pd.read_parquet(pasta / ARQUIVO_SERIE)
    return tabelas

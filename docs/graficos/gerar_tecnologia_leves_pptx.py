"""Versão editável de tecnologia_leves.png: gráficos nativos do PowerPoint, em % (slide 1) e em veículos (slide 2).

Mesmos dados do PNG (resultados/modelo_tipo_classe_ufs_validas.csv, tipo "leve", só UFs
válidas, sem híbrido leve). Os dados se editam no PowerPoint em "Editar dados"; no
slide 2, as barras estreitas demais ficam sem rótulo. Rodar da raiz do repositório:

    uv run --no-project --with python-pptx --with pandas python docs/graficos/gerar_tecnologia_leves_pptx.py
"""
from pathlib import Path

import pandas as pd
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.text import MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = Path(__file__).with_name("tecnologia_leves.pptx")
INSTANTES = [(2020, 12, "dez/2020"), (2023, 12, "dez/2023"), (2026, 9, "set/2026")]  # de baixo para cima no gráfico
CLASSES = [("eletrico", "Elétrico (BEV)", "2A78D6", "FFFFFF"),
           ("hibrido_plug_in", "Híbrido plug-in (PHEV)", "EB6834", "FFFFFF"),
           ("hibrido", "Híbrido (HEV)", "1BAF7A", "1F1F1E")]
TINTA, TINTA_2, GRADE = RGBColor.from_string("1F1F1E"), RGBColor.from_string("5F5E58"), RGBColor.from_string("E4E3DD")
FONTE = "Arial"


def br(n):
    return f"{n:,.0f}".replace(",", ".")


def texto(slide, x, y, w, h, conteudo, tamanho, cor, negrito=False):
    caixa = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    quadro = caixa.text_frame
    quadro.word_wrap = True
    quadro.margin_left = quadro.margin_right = quadro.margin_top = quadro.margin_bottom = 0
    for i, linha in enumerate(conteudo.split("\n")):
        p = quadro.paragraphs[0] if i == 0 else quadro.add_paragraph()
        run = p.add_run()
        run.text = linha
        run.font.size, run.font.bold, run.font.name = Pt(tamanho), negrito, FONTE
        run.font.color.rgb = cor
    return caixa


t = pd.read_csv(RAIZ / "resultados" / "modelo_tipo_classe_ufs_validas.csv", sep=";", decimal=",",
                encoding="utf-8-sig")
leves = t[t["tipo"] == "leve"].pivot_table(index=["ano", "mes"], columns="classe", values="frota", aggfunc="sum")

linhas = [leves.loc[(ano, mes)] for ano, mes, _ in INSTANTES]
totais = [sum(linha[c] for c, *_ in CLASSES) for linha in linhas]
CATEGORIAS = [f"{rotulo}\n{br(total)} veículos" for (_, _, rotulo), total in zip(INSTANTES, totais)]
RODAPE = ("Fonte: SENATRAN, frota por UF, município, marca/modelo e ano de fabricação, tratada no db-demob "
          "(tecnologia inferida do modelo).\nExclui híbridos leves (MHEV) e a frota sem UF ('Sem Informação', "
          "estoque ainda não emplacado).")


def slide_grafico(apresentacao, subtitulo, series, eixo_max, eixo_passo, formato_eixo, formato_rotulo,
                  rotulo_minimo=0.0):
    """Um slide com o gráfico de barras empilhadas; rótulos abaixo de rotulo_minimo x eixo_max ficam ocultos."""
    slide = apresentacao.slides.add_slide(apresentacao.slide_layouts[6])
    texto(slide, 0.6, 0.45, 12.1, 0.6, "Frota de carros eletrificados por tecnologia", 28, TINTA, negrito=True)
    texto(slide, 0.6, 1.05, 12.1, 0.4, subtitulo, 16, TINTA_2)

    dados = CategoryChartData()
    dados.categories = CATEGORIAS
    for (_, nome, *_), valores_serie in zip(CLASSES, series):
        dados.add_series(nome, valores_serie)
    grafico = slide.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, Inches(0.6), Inches(1.65), Inches(12.1),
                                     Inches(4.9), dados).chart
    grafico.font.name, grafico.font.size, grafico.font.color.rgb = FONTE, Pt(12), TINTA
    grafico.has_legend = True
    grafico.legend.position, grafico.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
    grafico.legend.font.size = Pt(13)
    grafico.plots[0].gap_width, grafico.plots[0].overlap = 55, 100

    categorias = grafico.category_axis
    categorias.format.line.fill.background()
    categorias.tick_labels.font.size = Pt(14)
    valores = grafico.value_axis
    valores.minimum_scale, valores.maximum_scale, valores.major_unit = 0, eixo_max, eixo_passo
    valores.has_major_gridlines = True
    valores.major_gridlines.format.line.color.rgb = GRADE
    valores.format.line.fill.background()
    valores.tick_labels.number_format, valores.tick_labels.number_format_is_linked = formato_eixo, False
    valores.tick_labels.font.size, valores.tick_labels.font.color.rgb = Pt(11), TINTA_2

    for serie, valores_serie, (_, _, cor, tinta) in zip(grafico.series, series, CLASSES):
        serie.format.fill.solid()
        serie.format.fill.fore_color.rgb = RGBColor.from_string(cor)
        serie.format.line.color.rgb = RGBColor.from_string("FFFFFF")
        serie.format.line.width = Pt(1.5)
        rotulos = serie.data_labels
        rotulos.show_value, rotulos.position = True, XL_LABEL_POSITION.CENTER
        rotulos.number_format, rotulos.number_format_is_linked = formato_rotulo, False
        rotulos.font.size, rotulos.font.bold = Pt(14), True
        rotulos.font.color.rgb = RGBColor.from_string(tinta)
        for i, valor in enumerate(valores_serie):
            if valor < rotulo_minimo * eixo_max:  # barra estreita demais para o rótulo
                rotulo = serie.points[i].data_label._get_or_add_dLbl()
                for filho in list(rotulo)[1:]:
                    rotulo.remove(filho)
                rotulo.append(rotulo.makeelement(qn("c:delete"), {"val": "1"}))

    rodape = texto(slide, 0.6, 6.7, 12.1, 0.5, RODAPE, 10, TINTA_2)
    rodape.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM


apresentacao = Presentation()
apresentacao.slide_width, apresentacao.slide_height = Inches(13.333), Inches(7.5)
slide_grafico(apresentacao, "Participação de cada tecnologia na frota de veículos leves BEV + PHEV + HEV, "
              "Brasil (UFs válidas)",
              [[round(linha[c] / total * 100, 1) for linha, total in zip(linhas, totais)] for c, *_ in CLASSES],
              100, 25, '0"%"', '0.0"%"')
slide_grafico(apresentacao, "Frota de veículos leves BEV + PHEV + HEV por tecnologia, em veículos, Brasil "
              "(UFs válidas)",
              [[int(linha[c]) for linha in linhas] for c, *_ in CLASSES],
              1_000_000, 250_000, '#,##0," mil"', '#,##0.0," mil"', rotulo_minimo=0.08)

apresentacao.save(SAIDA)
print(SAIDA)

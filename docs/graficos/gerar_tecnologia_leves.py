"""Gráfico: frota de carros eletrificados por tecnologia (BEV, PHEV, HEV), dez/2020, dez/2023 e set/2026.

Fonte: resultados/modelo_tipo_classe_ufs_validas.csv (base por modelo, tipo "leve", só UFs válidas: o grupo
"Sem Informação", estoque ainda não emplacado, fica de fora). Híbrido leve (MHEV) também fica de fora.
Rodar da raiz do repositório:

    uv run --no-project --with matplotlib --with pandas python docs/graficos/gerar_tecnologia_leves.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = Path(__file__).with_name("tecnologia_leves.png")
INSTANTES = [(2026, 9, "set/2026"), (2023, 12, "dez/2023"), (2020, 12, "dez/2020")]  # de cima para baixo
CLASSES = [("eletrico", "Elétrico (BEV)", "#2a78d6", "white"),
           ("hibrido_plug_in", "Híbrido plug-in (PHEV)", "#eb6834", "white"),
           ("hibrido", "Híbrido (HEV)", "#1baf7a", "#1f1f1e")]
TINTA, TINTA_2, FUNDO = "#1f1f1e", "#5f5e58", "#fcfcfb"


def br(n, casas=0):
    return f"{n:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


t = pd.read_csv(RAIZ / "resultados" / "modelo_tipo_classe_ufs_validas.csv", sep=";", decimal=",",
                encoding="utf-8-sig")
leves = t[t["tipo"] == "leve"].pivot_table(index=["ano", "mes"], columns="classe", values="frota", aggfunc="sum")

fig, ax = plt.subplots(figsize=(11, 4.6), dpi=200)
fig.patch.set_facecolor(FUNDO)
ax.set_facecolor(FUNDO)
for y, (ano, mes, rotulo) in enumerate(INSTANTES):
    linha = leves.loc[(ano, mes)]
    total = sum(linha[c] for c, *_ in CLASSES)
    esquerda = 0.0
    for coluna, _, cor, tinta in CLASSES:
        parte = linha[coluna] / total * 100
        ax.barh(y, parte, left=esquerda, height=0.56, color=cor, edgecolor=FUNDO, linewidth=2)
        if parte >= 4:
            ax.text(esquerda + parte / 2, y - 0.07, f"{br(parte, 1)}%", ha="center", va="center",
                    fontsize=12 if parte >= 8 else 9.5, fontweight="bold", color=tinta)
            ax.text(esquerda + parte / 2, y + 0.15, f"{br(linha[coluna] / 1000, 1)} mil", ha="center",
                    va="center", fontsize=8.5 if parte >= 8 else 7, color=tinta)
        esquerda += parte
    ax.text(101.5, y, f"{br(total)}\nveículos", ha="left", va="center", fontsize=9.5, color=TINTA_2)

ax.set_yticks(range(len(INSTANTES)), [r for *_, r in INSTANTES], fontsize=12, color=TINTA)
ax.set_xlim(0, 100)
ax.invert_yaxis()
ax.set_xticks(range(0, 101, 25), [f"{v}%" for v in range(0, 101, 25)], fontsize=9, color=TINTA_2)
ax.tick_params(length=0)
for lado in ax.spines.values():
    lado.set_visible(False)
ax.grid(axis="x", color="#e4e3dd", linewidth=0.8)
ax.set_axisbelow(True)

fig.text(0.02, 0.95, "Frota de carros eletrificados por tecnologia", fontsize=15, fontweight="bold", color=TINTA)
fig.text(0.02, 0.89, "Participação de cada tecnologia na frota de veículos leves BEV + PHEV + HEV, Brasil (UFs válidas)",
         fontsize=10, color=TINTA_2)
manuseio = [plt.Rectangle((0, 0), 1, 1, color=c) for _, _, c, _ in CLASSES]
fig.legend(manuseio, [n for _, n, _, _ in CLASSES], loc="lower center", ncol=3, frameon=False,
           fontsize=10, bbox_to_anchor=(0.5, 0.085), labelcolor=TINTA)
fig.text(0.02, 0.015, "Fonte: SENATRAN, frota por UF, município, marca/modelo e ano de fabricação, tratada no "
         "db-demob (tecnologia inferida do modelo).\nExclui híbridos leves (MHEV) e a frota sem UF "
         "('Sem Informação', estoque ainda não emplacado).", fontsize=7.5, color=TINTA_2)
fig.subplots_adjust(left=0.09, right=0.89, top=0.83, bottom=0.25)
fig.savefig(SAIDA, facecolor=FUNDO)
print(SAIDA)

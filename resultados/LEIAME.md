# Resultados

Gerado por `eletromobilidade publicar` a partir de `data/processed` em 2026-10-29 21:45 UTC (código no commit `b67ae94`). Não edite à mão: rode `processar` e `publicar` de novo.

## Cobertura

- **Base por combustível:** jun/2020 a set/2026, 75 meses; faltam jan/2022.
- **Base por modelo:** dez/2020 a set/2026, 7 meses; faltam 63 meses no intervalo.
- **Conciliação:** dez/2020 a set/2026, 7 meses; faltam 63 meses no intervalo.
- **Municípios:** 5.571 com código IBGE, 7 deles publicados pela SENATRAN com mais de uma grafia na série; sem código: NAO IDENTIFICADO, NAO SE APLICA, SEM INFORMACAO.
- **População:** estimativas do IBGE de 2020, 2021, 2024, 2025 e 2026; 2022 e 2023, sem estimativa, usam a de 2024.
- **Tipo de veículo, dez/2020:** leve 90,7%, moto 8,9%, onibus 0,2%, caminhao 0,2% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2021:** leve 91,2%, moto 8,1%, caminhao 0,6%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2022:** leve 84,2%, moto 14,9%, caminhao 0,8%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2023:** leve 85,2%, moto 14,1%, caminhao 0,6%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2024:** leve 88,1%, moto 11,4%, caminhao 0,5%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2025:** leve 90,4%, moto 9,2%, caminhao 0,3%, onibus 0,1%, outros 0,0% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, set/2026:** leve 92,8%, moto 6,8%, caminhao 0,2%, onibus 0,1%, outros 0,0% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- Ajuste em d_frota_por_uf_municipio_combustivel_novembro_2021.xlsx (nov/2021): contagens divididas por 10 (todas eram múltiplas de 10 no arquivo publicado).
- Ajuste em d_frota_por_uf_municipio_combustivel_janeiro_2022.xlsx (jan/2022): idêntico a 2021-12; excluído da série.
- Ajuste em d_frota_por_uf_municipio_combustivel_abril_2022.xlsx (abr/2022): frota_hibrido_plug_in: classe sem registro até 2022-04; antes disso os veículos dela estão em outra classe.
- Ajuste em d_frota_por_uf_municipio_combustivel_novembro_2022.xlsx (nov/2022): frota_celula_combustivel: classe sem registro até 2022-11; antes disso os veículos dela estão em outra classe.

## Qual base usar

- **Totais, série mensal, UF e município:** `combustivel_*`, contagem do campo combustível do RENAVAM.
- **Plug-in x híbrido convencional, marca, modelo, ano de fabricação e tipo de veículo:** `modelo_*`, tecnologia inferida do nome do modelo e validada abaixo. O rótulo HIBRIDO PLUG-IN do campo combustível registra só uma parte dos plug-ins; o resto está como híbrido.
- **Comparar com vendas:** só UFs válidas. O grupo sem UF (`modelo_sem_uf`) entra no Brasil e, nos eletrificados, é estoque ainda não emplacado.

## Validação

Contra as vendas da ABVE (crescimento da frota de leves nas UFs válidas x emplacamentos; ver `validacao_abve_*`):

| Período | Eletrificados | Elétricos | Plug-in | Híbridos | Híbridos leves (fora da frota eletrificada) |
|---|---:|---:|---:|---:|---:|
| 01/2021 a 12/2021 | 33.492 / 34.990 (−4,3%) | 2.707 / 2.851 (−5,1%) | 10.541 / 11.461 (−8,0%) | 20.244 / 20.678 (−2,1%) | — |
| 01/2022 a 12/2022 | 39.610 / 43.005 (−7,9%) | 8.021 / 8.457 (−5,2%) | 9.434 / 11.503 (−18,0%) | 22.154 / 23.045 (−3,9%) | 6.128 / 6.239 (−1,8%) |
| 01/2023 a 12/2023 | 80.734 / 82.742 (−2,4%) | 19.244 / 19.310 (−0,3%) | 31.986 / 33.049 (−3,2%) | 29.503 / 30.383 (−2,9%) | 9.281 / 11.185 (−17,0%) |
| 01/2024 a 12/2024 | 157.698 / 161.321 (−2,2%) | 61.387 / 61.615 (−0,4%) | 62.184 / 64.010 (−2,9%) | 34.126 / 35.696 (−4,4%) | 9.691 / 16.036 (−39,6%) |
| 01/2025 a 12/2025 | 222.048 / 223.896 (−0,8%) | 79.349 / 80.184 (−1,0%) | 98.207 / 99.996 (−1,8%) | 44.491 / 43.716 (+1,8%) | 42.776 / 61.356 (−30,3%) |
| 01/2026 a 09/2026 | 380.279 / 381.609 (−0,3%) | 164.843 / 165.820 (−0,6%) | 137.338 / 137.637 (−0,2%) | 78.098 / 78.152 (−0,1%) | 37.862 / 51.692 (−26,8%) |
| 01/2021 a 09/2026 (acumulado) | 913.861 / 927.563 (−1,5%) | 335.551 / 338.237 (−0,8%) | 349.690 / 357.656 (−2,2%) | 228.616 / 231.670 (−1,3%) | 105.822 / 146.508 (−27,8%) |

Cada célula: crescimento da frota / vendas da ABVE (diferença).

Modelo a modelo (01/2022 a 09/2026): 848 de 857 textos de modelo da ABVE casam com a base, 99,9% das vendas; nos eletrificados, 98,6% das vendas têm a mesma classe nas duas fontes.

Contra o PBE Veicular do Inmetro (set/2026): 78,8% da frota eletrificada casa com o PBE; 19 modelos e 6.879 veículos com classe que o PBE não registra (ver `validacao_pbe`).

## Arquivos

| Arquivo | Linhas | Conteúdo |
|---|---:|---|
| `combustivel_brasil.csv` | 75 | Base por combustível: frota por classe, total, eletrificada e participação, Brasil, por mês. |
| `combustivel_uf.csv` | 2.025 | Idem, por UF. |
| `combustivel_municipio.parquet` | 417.997 | Idem, por município. |
| `combustivel_eletrificados.parquet` | 725.874 | Base por combustível: rótulos eletrificados por município e mês. |
| `combustiveis_classificados.csv` | 30 | Auditoria: rótulos de combustível, classe atribuída e total de veículos. |
| `modelo_brasil.csv` | 7 | Base por modelo: frota por classe (inclui plug-in x convencional e híbrido leve), Brasil, por mês. |
| `modelo_uf.csv` | 189 | Idem, por UF. |
| `modelo_municipio.parquet` | 39.014 | Idem, por município. |
| `modelo_eletrificados.parquet` | 502.471 | Base por modelo: eletrificados e híbridos leves por município, modelo e ano de fabricação. |
| `modelo_tipo_brasil.csv` | 37 | Base por modelo: eletrificados e híbridos leves por tipo de veículo (leve, moto, ônibus, caminhão, outros), Brasil, por mês. Use participacao_tipo; a contagem absoluta herda a diferença para a base por combustível. |
| `modelo_tipo_uf.csv` | 556 | Idem, por UF. |
| `modelos_classificados.parquet` | 248.086 | Auditoria: cada modelo, classe, regra aplicada, total, marca, marcação 'revisar' e confronto com a tabela PBE Veicular do Inmetro. |
| `modelos_dimensao.parquet` | 943 | Dimensão de marca e modelo: grafia do RENAVAM, marca canônica e origem, por modelo distinto. |
| `municipios_dimensao.parquet` | 5.574 | Dimensão de município: código IBGE, nome oficial, UF e as grafias com que a SENATRAN publicou o município na série. |
| `conciliacao_brasil.csv` | 7 | Comparação combustível x modelo, Brasil, nos meses presentes nas duas bases. |
| `conciliacao_uf.csv` | 189 | Idem, por UF. |
| `conciliacao_municipio.parquet` | 39.014 | Idem, por município. |
| `modelo_sem_uf.csv` | 54 | Base por modelo: o grupo sem UF ('Sem Informação') por mês e classe, que o painel do Brasil inclui e o de UF não. Nos eletrificados, tem perfil de estoque ainda não emplacado. |
| `validacao_abve_tecnologia.csv` | 41 | Validação externa: vendas da ABVE x crescimento da frota da base por modelo, por período e classe (leves, UFs válidas). 2021 vem da série histórica da ABVE; de 2022 em diante, da base de vendas. A classe 'eletrificada' soma elétrico, plug-in e híbrido. |
| `validacao_abve_uf.csv` | 811 | Idem, por UF (de 2022 em diante). |
| `validacao_abve_marca.csv` | 1.050 | Idem, por marca. |
| `validacao_abve_modelo.parquet` | 2.991 | Idem, modelo a modelo: classe pela ABVE, classe pela base, classes do PBE Veicular e vendas x crescimento. É o teste externo da classificação. |
| `validacao_pbe.csv` | 54 | Validação contra o PBE Veicular do Inmetro, por mês e classe: modelos e frota que casam com o PBE e as duas divergências. |
| `qualidade_combustivel.csv` | 76 | Arquivos mensais da base por combustível: linhas, total, ajustes e inclusão na série. |
| `qualidade_modelo.csv` | 7 | Idem para a base por modelo. |

CSV: separador `;`, decimal `,`, UTF-8 com BOM (abre direto no Excel pt-BR). Parquet: ler com `pandas.read_parquet` ou no Power BI/R/DuckDB.
Colunas, tipos, fontes e classes: [DICIONARIO.md](DICIONARIO.md). Limitações: README do repositório. Método de conciliação: [src/eletromobilidade/README.md](../src/eletromobilidade/README.md#conciliação).

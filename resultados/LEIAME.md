# Resultados

Gerado por `eletromobilidade publicar` a partir de `data/processed` em 2026-11-09 22:56 UTC (código no commit `6e3759f`). Não edite à mão: rode `processar` e `publicar` de novo.

## Cobertura

- **Base por combustível:** jun/2020 a set/2026, 75 meses; faltam dez/2021.
- **Base por modelo:** dez/2020 a set/2026, 7 meses; faltam 63 meses no intervalo.
- **Conciliação:** 6 meses (dez/2020, dez/2022, dez/2023, dez/2024, dez/2025, set/2026).
- **Municípios:** 5.571 com código IBGE, 7 deles publicados pela SENATRAN com mais de uma grafia na série; sem código: NAO IDENTIFICADO, NAO SE APLICA, SEM INFORMACAO.
- **População:** estimativas do IBGE de 2020, 2021, 2024, 2025 e 2026; 2022 e 2023, sem estimativa, usam a de 2024.
- **Tipo de veículo, dez/2020:** leve 90,8%, moto 8,8%, onibus 0,2%, caminhao 0,2% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2021:** leve 91,3%, moto 7,9%, caminhao 0,6%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2022:** leve 84,4%, moto 14,8%, caminhao 0,8%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2023:** leve 85,2%, moto 14,1%, caminhao 0,6%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2024:** leve 88,1%, moto 11,4%, caminhao 0,5%, onibus 0,1% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, dez/2025:** leve 90,4%, moto 9,2%, caminhao 0,3%, onibus 0,1%, outros 0,0% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- **Tipo de veículo, set/2026:** leve 92,9%, moto 6,8%, caminhao 0,2%, onibus 0,1%, outros 0,0% da frota eletrificada da base por modelo; sem tipo: 0,00%.
- Ajuste em d_frota_por_uf_municipio_combustivel_novembro_2021.xlsx (nov/2021): contagens divididas por 10 (todas eram múltiplas de 10 no arquivo publicado).
- Ajuste em d_frota_por_uf_municipio_combustivel_dezembro_2021.xlsx (dez/2021): idêntico a 2022-01; excluído da série.
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
| 01/2021 a 12/2021 | 34.198 / 34.990 (−2,3%) | 2.869 / 2.851 (+0,6%) | 10.998 / 11.461 (−4,0%) | 20.331 / 20.678 (−1,7%) | — |
| 01/2022 a 12/2022 | 39.623 / 43.005 (−7,9%) | 8.467 / 8.457 (+0,1%) | 9.582 / 11.503 (−16,7%) | 21.573 / 23.045 (−6,4%) | 10.113 / 6.239 (+62,1%) |
| 01/2023 a 12/2023 | 79.636 / 82.742 (−3,8%) | 19.333 / 19.310 (+0,1%) | 32.162 / 33.049 (−2,7%) | 28.140 / 30.383 (−7,4%) | 15.622 / 11.185 (+39,7%) |
| 01/2024 a 12/2024 | 156.921 / 161.321 (−2,7%) | 61.537 / 61.615 (−0,1%) | 62.321 / 64.010 (−2,6%) | 33.062 / 35.696 (−7,4%) | 19.882 / 16.036 (+24,0%) |
| 01/2025 a 12/2025 | 222.090 / 223.896 (−0,8%) | 79.772 / 80.184 (−0,5%) | 98.319 / 99.996 (−1,7%) | 43.998 / 43.716 (+0,6%) | 61.865 / 61.356 (+0,8%) |
| 01/2026 a 09/2026 | 381.425 / 381.609 (−0,0%) | 165.540 / 165.820 (−0,2%) | 137.640 / 137.637 (+0,0%) | 78.245 / 78.152 (+0,1%) | 50.964 / 51.692 (−1,4%) |
| 01/2021 a 09/2026 (acumulado) | 913.893 / 927.563 (−1,5%) | 337.518 / 338.237 (−0,2%) | 351.022 / 357.656 (−1,9%) | 225.349 / 231.670 (−2,7%) | 160.862 / 146.508 (+9,8%) |

Cada célula: crescimento da frota / vendas da ABVE (diferença).

A ABVE muda o rótulo de alguns modelos com o tempo e não reescreve o histórico: o Tiggo 7 Pro "HA" é HEV Flex até 2024 e MHEV 48V desde 2025. A base dá uma classe só a cada texto, então a mesma conta sai também com todo o histórico no rótulo mais recente de cada modelo (2021 não muda: a série histórica não tem modelo):

| Período | Eletrificados | Elétricos | Plug-in | Híbridos | Híbridos leves (fora da frota eletrificada) |
|---|---:|---:|---:|---:|---:|
| 01/2021 a 12/2021 | 34.198 / 34.990 (−2,3%) | 2.869 / 2.851 (+0,6%) | 10.998 / 11.461 (−4,0%) | 20.331 / 20.678 (−1,7%) | — |
| 01/2022 a 12/2022 | 39.623 / 40.190 (−1,4%) | 8.467 / 8.457 (+0,1%) | 9.582 / 10.001 (−4,2%) | 21.573 / 21.732 (−0,7%) | 10.113 / 9.054 (+11,7%) |
| 01/2023 a 12/2023 | 79.636 / 79.749 (−0,1%) | 19.333 / 19.310 (+0,1%) | 32.162 / 32.282 (−0,4%) | 28.140 / 28.157 (−0,1%) | 15.622 / 14.178 (+10,2%) |
| 01/2024 a 12/2024 | 156.921 / 157.343 (−0,3%) | 61.537 / 61.618 (−0,1%) | 62.321 / 62.664 (−0,5%) | 33.062 / 33.061 (+0,0%) | 19.882 / 20.014 (−0,7%) |
| 01/2025 a 12/2025 | 222.090 / 222.212 (−0,1%) | 79.772 / 80.184 (−0,5%) | 98.319 / 98.580 (−0,3%) | 43.998 / 43.448 (+1,3%) | 61.865 / 63.040 (−1,9%) |
| 01/2026 a 09/2026 | 381.425 / 381.603 (−0,0%) | 165.540 / 165.820 (−0,2%) | 137.640 / 137.633 (+0,0%) | 78.245 / 78.150 (+0,1%) | 50.964 / 51.698 (−1,4%) |
| 01/2021 a 09/2026 (acumulado) | 913.893 / 916.087 (−0,2%) | 337.518 / 338.240 (−0,2%) | 351.022 / 352.621 (−0,5%) | 225.349 / 225.226 (+0,1%) | 160.862 / 157.984 (+1,8%) |

**Esta comparação não é validação independente da classificação.** As regras da base por modelo seguem o rótulo atual da ABVE onde as vendas e o crescimento da frota do mesmo texto batem, então a diferença pequena no rótulo atual é, em boa parte, construída. Ela segue servindo para achar regra faltando e erro de contagem. A validação independente é a do PBE Veicular do Inmetro, abaixo.

Modelo a modelo (01/2022 a 09/2026): 848 de 856 textos de modelo da ABVE casam com a base, 100,0% das vendas; nos eletrificados, 98,9% das vendas têm a mesma classe nas duas fontes. Pelo rótulo atual de cada modelo, 99,8%.

Contra o PBE Veicular do Inmetro (set/2026): 78,9% da frota eletrificada casa com o PBE; 18 modelos e 6.867 veículos com classe que o PBE não registra (ver `validacao_pbe`).

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
| `modelo_eletrificados.parquet` | 558.184 | Base por modelo: eletrificados e híbridos leves por município, modelo e ano de fabricação. |
| `modelo_tipo_brasil.csv` | 37 | Base por modelo: eletrificados e híbridos leves por tipo de veículo (leve, moto, ônibus, caminhão, outros), Brasil, por mês. Use participacao_tipo; a contagem absoluta herda a diferença para a base por combustível. |
| `modelo_tipo_uf.csv` | 556 | Idem, por UF. |
| `modelos_classificados.parquet` | 248.086 | Auditoria: cada modelo, classe, regra aplicada, total, marca, marcação 'revisar' e confronto com a tabela PBE Veicular do Inmetro. |
| `modelos_dimensao.parquet` | 1.235 | Dimensão de marca e modelo: grafia do RENAVAM, marca canônica e origem, por modelo distinto. |
| `municipios_dimensao.parquet` | 5.574 | Dimensão de município: código IBGE, nome oficial, UF e as grafias com que a SENATRAN publicou o município na série. |
| `conciliacao_brasil.csv` | 6 | Comparação combustível x modelo, Brasil, nos meses presentes nas duas bases. |
| `conciliacao_uf.csv` | 162 | Idem, por UF. |
| `conciliacao_municipio.parquet` | 33.441 | Idem, por município. |
| `modelo_sem_uf.csv` | 54 | Base por modelo: o grupo sem UF ('Sem Informação') por mês e classe, que o painel do Brasil inclui e o de UF não. Nos eletrificados, tem perfil de estoque ainda não emplacado. |
| `validacao_abve_tecnologia.csv` | 41 | Validação externa: vendas da ABVE x crescimento da frota da base por modelo, por período e classe (leves, UFs válidas). 2021 vem da série histórica da ABVE; de 2022 em diante, da base de vendas. A classe 'eletrificada' soma elétrico, plug-in e híbrido. |
| `validacao_abve_uf.csv` | 814 | Idem, por UF (de 2022 em diante). |
| `validacao_abve_marca.csv` | 1.103 | Idem, por marca. |
| `validacao_abve_modelo.parquet` | 3.019 | Idem, modelo a modelo: classe pela ABVE, classe pela base, classes do PBE Veicular e vendas x crescimento. É o teste externo da classificação. |
| `validacao_pbe.csv` | 54 | Validação contra o PBE Veicular do Inmetro, por mês e classe: modelos e frota que casam com o PBE e as duas divergências. |
| `qualidade_combustivel.csv` | 76 | Arquivos mensais da base por combustível: linhas, total, ajustes e inclusão na série. |
| `qualidade_modelo.csv` | 7 | Idem para a base por modelo. |

CSV: separador `;`, decimal `,`, UTF-8 com BOM (abre direto no Excel pt-BR). Parquet: ler com `pandas.read_parquet` ou no Power BI/R/DuckDB.
Colunas, tipos, fontes e classes: [DICIONARIO.md](DICIONARIO.md). Limitações: README do repositório. Método de conciliação: [src/eletromobilidade/README.md](../src/eletromobilidade/README.md#conciliação).

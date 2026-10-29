# Dicionário de dados

Gerado por `eletromobilidade publicar` a partir das tabelas publicadas.

## Fontes

| Base | Arquivo da SENATRAN | Onde | Colunas originais |
|---|---|---|---|
| Combustível | `D_Frota_por_UF_Municipio_COMBUSTIVEL_<Mês>_<Ano>.xlsx` (mensal) | Páginas anuais [frota-de-veiculos-{ano}](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2026) no gov.br (Ministério dos Transportes/SENATRAN) | UF, Município, Combustível Veículo, Qtd. Veículos |
| Modelo | `I_Frota_por_UF_Municipio_Marca_e_Modelo_Ano_<Mês>_<Ano>.zip` (mensal, ~22 mi de linhas) | Conjunto RENAVAM no [portal de dados abertos](https://dados.transportes.gov.br/dataset/12686da0-3d71-4499-b432-d270f785c907) (API CKAN); alguns meses de 2019–2022 também no gov.br | UF, Município, Marca Modelo, Ano Fabricação Veículo CRV, Qtd. Veículos |

Ambos são extrações do RENAVAM: frota **registrada** no mês de referência (inclui
veículos que já não circulam e não foram baixados). UF vem por extenso; sigla,
código IBGE da UF e região são acrescentados pelo pacote (tabela fixa em
`src/eletromobilidade/ufs.py`). O município vem só pelo nome, e o pacote acrescenta o
código IBGE (`cod_municipio_ibge`) casando UF e nome com a lista oficial da
[API de localidades do IBGE](https://servicodados.ibge.gov.br/api/docs/localidades)
(instantâneo em `src/eletromobilidade/dados/municipios.csv`) e, onde a grafia da
SENATRAN difere da do IBGE, com `src/eletromobilidade/dados/municipios_grafias.csv`,
conferida à mão. Alguns municípios mudam de grafia no meio da série; o código é a
identidade estável.
População (base por combustível): estimativas anuais do IBGE, tabela
[6579 do SIDRA](https://sidra.ibge.gov.br/tabela/6579) (população residente em 1º de
julho), instantâneo em `src/eletromobilidade/dados/populacao.csv`. Cada mês usa a
estimativa do próprio ano; 2022 e 2023 não têm estimativa e usam a de 2024. Até 2021
as estimativas projetam o Censo 2010 e de 2024 em diante partem do Censo 2022, então a
taxa por habitante de um município muda de base em 2022: ver `ano_populacao`.
Classificação: `src/eletromobilidade/dados/combustiveis.csv` (base por
combustível) e `src/eletromobilidade/dados/modelos.csv` (base por modelo).
Equivalência de grafias de marca: `src/eletromobilidade/dados/marcas.csv`.
Auditoria da classificação contra a tabela PBE Veicular do Inmetro
(propulsão e porte declarados por versão de veículo leve):
`src/eletromobilidade/dados/pbev.csv`, extraída do PDF do ciclo publicado em
[Veículos Automotivos (PBE veicular)](https://www.gov.br/inmetro/pt-br/assuntos/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica/veiculos-automotivos-pbe-veicular).
Validação externa (`validacao_abve_*`): emplacamentos de eletrificados leves do
[BI Frotas da ABVE](https://abve.org.br/bi-frotas/), consultados pela API pública do
painel (`eletromobilidade abve`). A base bruta da ABVE não é publicada aqui, só a
comparação.

## Classes de tecnologia

| Classe | Definição |
|---|---|
| `eletrico` | Tração 100% elétrica (a bateria). Combustível: ELETRICO/FONTE EXTERNA, ELETRICO/FONTE INTERNA, ELETRICO. |
| `hibrido_plug_in` | Híbrido recarregável na tomada (PHEV), incluindo elétricos com extensor de autonomia (REEV). |
| `hibrido` | Híbrido convencional (HEV): bateria recarregada só pelo motor a combustão e pela frenagem regenerativa. |
| `hibrido_leve` | Só na base por modelo. Híbrido leve (12/48 V): o motor elétrico não traciona sozinho. Fora da frota eletrificada. |
| `celula_combustivel` | Elétrico a célula de combustível (hidrogênio). |
| `combustao` | Somente motor a combustão (inclui flex e GNV). |
| `nao_motorizado` | Só na base por modelo. Reboques (R/) e semirreboques (SR/). |
| `sem_informacao` | Sem informação de combustível ou de modelo. |

## Tabelas

### `combustivel_brasil.csv`

Base por combustível: frota por classe, total, eletrificada e participação, Brasil, por mês.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_combustao` | inteiro | Veículos da classe combustao. |
| `frota_sem_informacao` | inteiro | Veículos da classe sem_informacao. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_eletrificada` | decimal | frota_eletrificada / frota_total (fração entre 0 e 1). |
| `ano_populacao` | inteiro | Ano da estimativa de população do IBGE usada no mês: a do próprio ano ou, sem ela, a mais próxima do mesmo lado do Censo 2022 (2022 e 2023 usam 2024). Até 2021 a base é o Censo 2010; de 2024 em diante, o Censo 2022. |
| `populacao` | inteiro | População residente estimada (IBGE, tabela 6579), em 1º de julho de ano_populacao. Na UF e no Brasil, soma dos municípios. Nula nos pseudo-municípios e na linha do distrito de Ibitiúva, cuja população já está na de Pitangueiras. |
| `eletrificada_por_mil_habitantes` | decimal | frota_eletrificada / populacao x 1000. No Brasil, o numerador inclui a frota sem UF, que não tem população. |

### `combustivel_uf.csv`

Idem, por UF.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_combustao` | inteiro | Veículos da classe combustao. |
| `frota_sem_informacao` | inteiro | Veículos da classe sem_informacao. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_eletrificada` | decimal | frota_eletrificada / frota_total (fração entre 0 e 1). |
| `ano_populacao` | inteiro | Ano da estimativa de população do IBGE usada no mês: a do próprio ano ou, sem ela, a mais próxima do mesmo lado do Censo 2022 (2022 e 2023 usam 2024). Até 2021 a base é o Censo 2010; de 2024 em diante, o Censo 2022. |
| `populacao` | inteiro | População residente estimada (IBGE, tabela 6579), em 1º de julho de ano_populacao. Na UF e no Brasil, soma dos municípios. Nula nos pseudo-municípios e na linha do distrito de Ibitiúva, cuja população já está na de Pitangueiras. |
| `eletrificada_por_mil_habitantes` | decimal | frota_eletrificada / populacao x 1000. No Brasil, o numerador inclui a frota sem UF, que não tem população. |

### `combustivel_municipio.parquet`

Idem, por município.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `municipio_norm` | texto | Município como a SENATRAN o grafa, sem acentos, em caixa alta. A grafia muda no meio da série em alguns municípios (EMBU virou EMBU DAS ARTES): para identificar o município, use cod_municipio_ibge. |
| `cod_municipio_ibge` | inteiro | Código IBGE do município (7 dígitos). Nulo só nos pseudo-municípios da SENATRAN sem UF ('Sem Informação', 'Não Identificado', 'Não se Aplica'). |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_combustao` | inteiro | Veículos da classe combustao. |
| `frota_sem_informacao` | inteiro | Veículos da classe sem_informacao. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_eletrificada` | decimal | frota_eletrificada / frota_total (fração entre 0 e 1). |
| `ano_populacao` | inteiro | Ano da estimativa de população do IBGE usada no mês: a do próprio ano ou, sem ela, a mais próxima do mesmo lado do Censo 2022 (2022 e 2023 usam 2024). Até 2021 a base é o Censo 2010; de 2024 em diante, o Censo 2022. |
| `populacao` | inteiro | População residente estimada (IBGE, tabela 6579), em 1º de julho de ano_populacao. Na UF e no Brasil, soma dos municípios. Nula nos pseudo-municípios e na linha do distrito de Ibitiúva, cuja população já está na de Pitangueiras. |
| `eletrificada_por_mil_habitantes` | decimal | frota_eletrificada / populacao x 1000. No Brasil, o numerador inclui a frota sem UF, que não tem população. |

### `combustivel_eletrificados.parquet`

Base por combustível: rótulos eletrificados por município e mês.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf` | texto | UF como publicada pela SENATRAN (por extenso; inclui 'Sem Informação'). |
| `municipio` | texto | Município como publicado pela SENATRAN. |
| `combustivel` | texto | Rótulo do campo combustível do RENAVAM, como publicado. |
| `qtd_veiculos` | inteiro | Número de veículos registrados. |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `municipio_norm` | texto | Município como a SENATRAN o grafa, sem acentos, em caixa alta. A grafia muda no meio da série em alguns municípios (EMBU virou EMBU DAS ARTES): para identificar o município, use cod_municipio_ibge. |
| `cod_municipio_ibge` | inteiro | Código IBGE do município (7 dígitos). Nulo só nos pseudo-municípios da SENATRAN sem UF ('Sem Informação', 'Não Identificado', 'Não se Aplica'). |
| `arquivo_origem` | texto | Arquivo da SENATRAN de onde o dado veio. |
| `combustivel_norm` | texto | Rótulo de combustível normalizado (sem acentos, caixa alta, grafias unificadas). |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `eletrificado` | lógico | Verdadeiro para eletrico, hibrido_plug_in, hibrido e celula_combustivel. |
| `origem_classificacao` | texto | 'tabela' (rótulo listado em combustiveis.csv) ou 'regra' (inferido; revisar). |

### `combustiveis_classificados.csv`

Auditoria: rótulos de combustível, classe atribuída e total de veículos.

| Coluna | Tipo | Descrição |
|---|---|---|
| `combustivel` | texto | Rótulo do campo combustível do RENAVAM, como publicado. |
| `combustivel_norm` | texto | Rótulo de combustível normalizado (sem acentos, caixa alta, grafias unificadas). |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `eletrificado` | lógico | Verdadeiro para eletrico, hibrido_plug_in, hibrido e celula_combustivel. |
| `origem_classificacao` | texto | 'tabela' (rótulo listado em combustiveis.csv) ou 'regra' (inferido; revisar). |
| `qtd_veiculos` | inteiro | Número de veículos registrados. |
| `primeiro_mes` | data | Primeiro mês em que o rótulo aparece na série. |
| `ultimo_mes` | data | Último mês em que o rótulo aparece na série. |

### `modelo_brasil.csv`

Base por modelo: frota por classe (inclui plug-in x convencional e híbrido leve), Brasil, por mês.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_hibrido_leve` | inteiro | Veículos da classe hibrido_leve. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_combustao` | inteiro | Veículos da classe combustao. |
| `frota_nao_motorizado` | inteiro | Veículos da classe nao_motorizado. |
| `frota_sem_informacao` | inteiro | Veículos da classe sem_informacao. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_eletrificada` | decimal | frota_eletrificada / frota_total (fração entre 0 e 1). |

### `modelo_uf.csv`

Idem, por UF.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_hibrido_leve` | inteiro | Veículos da classe hibrido_leve. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_combustao` | inteiro | Veículos da classe combustao. |
| `frota_nao_motorizado` | inteiro | Veículos da classe nao_motorizado. |
| `frota_sem_informacao` | inteiro | Veículos da classe sem_informacao. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_eletrificada` | decimal | frota_eletrificada / frota_total (fração entre 0 e 1). |

### `modelo_municipio.parquet`

Idem, por município.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `municipio_norm` | texto | Município como a SENATRAN o grafa, sem acentos, em caixa alta. A grafia muda no meio da série em alguns municípios (EMBU virou EMBU DAS ARTES): para identificar o município, use cod_municipio_ibge. |
| `cod_municipio_ibge` | inteiro | Código IBGE do município (7 dígitos). Nulo só nos pseudo-municípios da SENATRAN sem UF ('Sem Informação', 'Não Identificado', 'Não se Aplica'). |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_hibrido_leve` | inteiro | Veículos da classe hibrido_leve. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_combustao` | inteiro | Veículos da classe combustao. |
| `frota_nao_motorizado` | inteiro | Veículos da classe nao_motorizado. |
| `frota_sem_informacao` | inteiro | Veículos da classe sem_informacao. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_eletrificada` | decimal | frota_eletrificada / frota_total (fração entre 0 e 1). |

### `modelo_eletrificados.parquet`

Base por modelo: eletrificados e híbridos leves por município, modelo e ano de fabricação.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf` | texto | UF como publicada pela SENATRAN (por extenso; inclui 'Sem Informação'). |
| `municipio` | texto | Município como publicado pela SENATRAN. |
| `marca_modelo` | texto | Texto 'Marca Modelo' do RENAVAM, como publicado (prefixo I/ = importado). |
| `ano_fabricacao` | inteiro | Ano de fabricação (campo do CRV); nulo quando 'Sem Informação'. |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `tipo` | texto | Tipo de veículo do modelo: leve (automóvel, SUV, picape, van), moto (inclui motoneta, ciclomotor e triciclo), onibus, caminhao ou outros. Só para eletrificados e híbridos leves; nulo quando o modelo não tem regra em dados/tipos.csv nem está no PBE Veicular. |
| `regra` | inteiro | Número da linha de modelos.csv que definiu a classe (0 = nenhuma regra; classe padrão combustao). |
| `qtd_veiculos` | inteiro | Número de veículos registrados. |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `municipio_norm` | texto | Município como a SENATRAN o grafa, sem acentos, em caixa alta. A grafia muda no meio da série em alguns municípios (EMBU virou EMBU DAS ARTES): para identificar o município, use cod_municipio_ibge. |
| `cod_municipio_ibge` | inteiro | Código IBGE do município (7 dígitos). Nulo só nos pseudo-municípios da SENATRAN sem UF ('Sem Informação', 'Não Identificado', 'Não se Aplica'). |
| `arquivo_origem` | texto | Arquivo da SENATRAN de onde o dado veio. |

### `modelo_tipo_brasil.csv`

Base por modelo: eletrificados e híbridos leves por tipo de veículo (leve, moto, ônibus, caminhão, outros), Brasil, por mês. Use participacao_tipo; a contagem absoluta herda a diferença para a base por combustível.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `tipo` | texto | Tipo de veículo do modelo: leve (automóvel, SUV, picape, van), moto (inclui motoneta, ciclomotor e triciclo), onibus, caminhao ou outros. Só para eletrificados e híbridos leves; nulo quando o modelo não tem regra em dados/tipos.csv nem está no PBE Veicular. |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_hibrido_leve` | inteiro | Veículos da classe hibrido_leve. |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_tipo` | decimal | Parte do tipo na frota eletrificada do recorte no mês (fração entre 0 e 1). |

### `modelo_tipo_uf.csv`

Idem, por UF.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `tipo` | texto | Tipo de veículo do modelo: leve (automóvel, SUV, picape, van), moto (inclui motoneta, ciclomotor e triciclo), onibus, caminhao ou outros. Só para eletrificados e híbridos leves; nulo quando o modelo não tem regra em dados/tipos.csv nem está no PBE Veicular. |
| `frota_eletrico` | inteiro | Veículos da classe eletrico. |
| `frota_hibrido_plug_in` | inteiro | Veículos da classe hibrido_plug_in. |
| `frota_hibrido` | inteiro | Veículos da classe hibrido. |
| `frota_celula_combustivel` | inteiro | Veículos da classe celula_combustivel. |
| `frota_hibrido_leve` | inteiro | Veículos da classe hibrido_leve. |
| `frota_eletrificada` | inteiro | Soma de eletrico, hibrido_plug_in, hibrido e celula_combustivel (sem hibrido_leve). |
| `participacao_tipo` | decimal | Parte do tipo na frota eletrificada do recorte no mês (fração entre 0 e 1). |

### `modelos_classificados.parquet`

Auditoria: cada modelo, classe, regra aplicada, total, marca, marcação 'revisar' e confronto com a tabela PBE Veicular do Inmetro.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `marca_modelo_norm` | texto | Marca Modelo normalizado (sem acentos, caixa alta). |
| `marca_renavam` | texto | Marca como o RENAVAM grafa, sem o prefixo de montadora (I/, IMP/, JTA/) nem de tipo de veículo (R/, SR/, REB/, MR/, MO/, M.A./). Nula quando o texto não traz marca. |
| `marca` | texto | Marca canônica: grafias da mesma empresa unidas por dados/marcas.csv (GM, CHEVROLET e CHEV viram CHEVROLET). Grafia fora da tabela segue como está. |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `regra` | inteiro | Número da linha de modelos.csv que definiu a classe (0 = nenhuma regra; classe padrão combustao). |
| `qtd_veiculos` | inteiro | Número de veículos registrados. |
| `qtd_sem_uf` | inteiro | Parte de qtd_veiculos registrada sem UF válida ('Sem Informação'). Nos eletrificados, tem perfil de estoque ainda não emplacado. |
| `revisar` | lógico | Verdadeiro para modelo de marca com linha eletrificada que não casou com nenhuma regra. |
| `padrao` | texto | Expressão regular da regra aplicada. |
| `pbe_classes` | texto | Classes que a linha do modelo tem na tabela PBE Veicular do Inmetro, separadas por barra vertical. Vazio quando o modelo não casou com o PBE (moto, ônibus, caminhão e modelo fora de linha). |
| `pbe_categoria` | texto | Categoria de porte do PBE Veicular (Médio, Picape, Utilitário Esportivo Compacto...). Vazio quando o modelo não casou. |
| `pbe_aviso` | texto | Divergência com o PBE: 'sem_versao_no_pbe' (classe eletrificada que o PBE não registra para o modelo; falso positivo provável) ou 'pbe_so_eletrificado' (classificado combustão, mas toda versão do modelo no PBE é eletrificada; pode ser regra faltando ou geração antiga). Vazio quando não há divergência. |
| `tipo` | texto | Tipo de veículo do modelo: leve (automóvel, SUV, picape, van), moto (inclui motoneta, ciclomotor e triciclo), onibus, caminhao ou outros. Só para eletrificados e híbridos leves; nulo quando o modelo não tem regra em dados/tipos.csv nem está no PBE Veicular. |
| `origem_tipo` | texto | 'pbe' (o modelo está no PBE Veicular do Inmetro, que só tem veículo leve) ou 'regra' (regra de dados/tipos.csv). |
| `regra_tipo` | inteiro | Número da linha de dados/tipos.csv que casou (0 = nenhuma). |
| `tipo_aviso` | texto | 'pbe_diverge' quando a regra dá tipo não leve a um modelo que está no PBE Veicular. Vazio quando não há divergência. |

### `modelos_dimensao.parquet`

Dimensão de marca e modelo: grafia do RENAVAM, marca canônica e origem, por modelo distinto.

| Coluna | Tipo | Descrição |
|---|---|---|
| `marca_modelo` | texto | Texto 'Marca Modelo' do RENAVAM, como publicado (prefixo I/ = importado). |
| `marca_modelo_norm` | texto | Marca Modelo normalizado (sem acentos, caixa alta). |
| `marca_renavam` | texto | Marca como o RENAVAM grafa, sem o prefixo de montadora (I/, IMP/, JTA/) nem de tipo de veículo (R/, SR/, REB/, MR/, MO/, M.A./). Nula quando o texto não traz marca. |
| `marca` | texto | Marca canônica: grafias da mesma empresa unidas por dados/marcas.csv (GM, CHEVROLET e CHEV viram CHEVROLET). Grafia fora da tabela segue como está. |
| `importado` | lógico | Verdadeiro quando o texto traz o prefixo I/ ou IMP/ de veículo importado. |
| `origem` | texto | 'Importado' ou 'Nacional', conforme o prefixo do texto. |
| `tipo` | texto | Tipo de veículo do modelo: leve (automóvel, SUV, picape, van), moto (inclui motoneta, ciclomotor e triciclo), onibus, caminhao ou outros. Só para eletrificados e híbridos leves; nulo quando o modelo não tem regra em dados/tipos.csv nem está no PBE Veicular. |
| `origem_tipo` | texto | 'pbe' (o modelo está no PBE Veicular do Inmetro, que só tem veículo leve) ou 'regra' (regra de dados/tipos.csv). |

### `municipios_dimensao.parquet`

Dimensão de município: código IBGE, nome oficial, UF e as grafias com que a SENATRAN publicou o município na série.

| Coluna | Tipo | Descrição |
|---|---|---|
| `cod_municipio_ibge` | inteiro | Código IBGE do município (7 dígitos). Nulo só nos pseudo-municípios da SENATRAN sem UF ('Sem Informação', 'Não Identificado', 'Não se Aplica'). |
| `municipio_ibge` | texto | Nome oficial do município no IBGE, com acentos. Nulo nos pseudo-municípios. |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `municipio_norm` | texto | Grafia mais recente do município na SENATRAN, sem acentos, em caixa alta. As anteriores estão em grafias_senatran. |
| `grafias_senatran` | texto | Grafias com que a SENATRAN publicou o município na série, na ordem em que aparecem, separadas por barra vertical (EMBU, depois EMBU DAS ARTES). |

### `conciliacao_brasil.csv`

Comparação combustível x modelo, Brasil, nos meses presentes nas duas bases.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `total_combustivel` | inteiro | Frota total: pela base por combustível. |
| `total_modelo` | inteiro | Frota total: pela base por modelo. |
| `total_diferenca` | inteiro | Frota total: diferença modelo − combustível. |
| `total_razao` | decimal | Frota total: razão modelo / combustível (nula se combustível = 0). |
| `eletrico_combustivel` | inteiro | Elétricos: pela base por combustível. |
| `eletrico_modelo` | inteiro | Elétricos: pela base por modelo. |
| `eletrico_diferenca` | inteiro | Elétricos: diferença modelo − combustível. |
| `eletrico_razao` | decimal | Elétricos: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_plug_in_combustivel` | inteiro | Híbridos plug-in: pela base por combustível. |
| `hibrido_plug_in_modelo` | inteiro | Híbridos plug-in: pela base por modelo. |
| `hibrido_plug_in_diferenca` | inteiro | Híbridos plug-in: diferença modelo − combustível. |
| `hibrido_plug_in_razao` | decimal | Híbridos plug-in: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_combustivel` | inteiro | Híbridos convencionais: pela base por combustível. |
| `hibrido_modelo` | inteiro | Híbridos convencionais: pela base por modelo. |
| `hibrido_diferenca` | inteiro | Híbridos convencionais: diferença modelo − combustível. |
| `hibrido_razao` | decimal | Híbridos convencionais: razão modelo / combustível (nula se combustível = 0). |
| `hibridos_combustivel` | inteiro | Híbridos plug-in + convencionais: pela base por combustível. |
| `hibridos_modelo` | inteiro | Híbridos plug-in + convencionais: pela base por modelo. |
| `hibridos_diferenca` | inteiro | Híbridos plug-in + convencionais: diferença modelo − combustível. |
| `hibridos_razao` | decimal | Híbridos plug-in + convencionais: razão modelo / combustível (nula se combustível = 0). |
| `eletrificada_combustivel` | inteiro | Frota eletrificada: pela base por combustível. |
| `eletrificada_modelo` | inteiro | Frota eletrificada: pela base por modelo. |
| `eletrificada_diferenca` | inteiro | Frota eletrificada: diferença modelo − combustível. |
| `eletrificada_razao` | decimal | Frota eletrificada: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_leve_modelo` | inteiro | Híbridos leves na base por modelo (sem equivalente na base por combustível). |

### `conciliacao_uf.csv`

Idem, por UF.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `total_combustivel` | inteiro | Frota total: pela base por combustível. |
| `total_modelo` | inteiro | Frota total: pela base por modelo. |
| `total_diferenca` | inteiro | Frota total: diferença modelo − combustível. |
| `total_razao` | decimal | Frota total: razão modelo / combustível (nula se combustível = 0). |
| `eletrico_combustivel` | inteiro | Elétricos: pela base por combustível. |
| `eletrico_modelo` | inteiro | Elétricos: pela base por modelo. |
| `eletrico_diferenca` | inteiro | Elétricos: diferença modelo − combustível. |
| `eletrico_razao` | decimal | Elétricos: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_plug_in_combustivel` | inteiro | Híbridos plug-in: pela base por combustível. |
| `hibrido_plug_in_modelo` | inteiro | Híbridos plug-in: pela base por modelo. |
| `hibrido_plug_in_diferenca` | inteiro | Híbridos plug-in: diferença modelo − combustível. |
| `hibrido_plug_in_razao` | decimal | Híbridos plug-in: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_combustivel` | inteiro | Híbridos convencionais: pela base por combustível. |
| `hibrido_modelo` | inteiro | Híbridos convencionais: pela base por modelo. |
| `hibrido_diferenca` | inteiro | Híbridos convencionais: diferença modelo − combustível. |
| `hibrido_razao` | decimal | Híbridos convencionais: razão modelo / combustível (nula se combustível = 0). |
| `hibridos_combustivel` | inteiro | Híbridos plug-in + convencionais: pela base por combustível. |
| `hibridos_modelo` | inteiro | Híbridos plug-in + convencionais: pela base por modelo. |
| `hibridos_diferenca` | inteiro | Híbridos plug-in + convencionais: diferença modelo − combustível. |
| `hibridos_razao` | decimal | Híbridos plug-in + convencionais: razão modelo / combustível (nula se combustível = 0). |
| `eletrificada_combustivel` | inteiro | Frota eletrificada: pela base por combustível. |
| `eletrificada_modelo` | inteiro | Frota eletrificada: pela base por modelo. |
| `eletrificada_diferenca` | inteiro | Frota eletrificada: diferença modelo − combustível. |
| `eletrificada_razao` | decimal | Frota eletrificada: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_leve_modelo` | inteiro | Híbridos leves na base por modelo (sem equivalente na base por combustível). |

### `conciliacao_municipio.parquet`

Idem, por município.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `cod_uf_ibge` | inteiro | Código IBGE da UF (2 dígitos). |
| `regiao` | texto | Grande região (Norte, Nordeste, Sudeste, Sul, Centro-Oeste). |
| `municipio_norm` | texto | Município como a SENATRAN o grafa, sem acentos, em caixa alta. A grafia muda no meio da série em alguns municípios (EMBU virou EMBU DAS ARTES): para identificar o município, use cod_municipio_ibge. |
| `cod_municipio_ibge` | inteiro | Código IBGE do município (7 dígitos). Nulo só nos pseudo-municípios da SENATRAN sem UF ('Sem Informação', 'Não Identificado', 'Não se Aplica'). |
| `total_combustivel` | inteiro | Frota total: pela base por combustível. |
| `total_modelo` | inteiro | Frota total: pela base por modelo. |
| `total_diferenca` | inteiro | Frota total: diferença modelo − combustível. |
| `total_razao` | decimal | Frota total: razão modelo / combustível (nula se combustível = 0). |
| `eletrico_combustivel` | inteiro | Elétricos: pela base por combustível. |
| `eletrico_modelo` | inteiro | Elétricos: pela base por modelo. |
| `eletrico_diferenca` | inteiro | Elétricos: diferença modelo − combustível. |
| `eletrico_razao` | decimal | Elétricos: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_plug_in_combustivel` | inteiro | Híbridos plug-in: pela base por combustível. |
| `hibrido_plug_in_modelo` | inteiro | Híbridos plug-in: pela base por modelo. |
| `hibrido_plug_in_diferenca` | inteiro | Híbridos plug-in: diferença modelo − combustível. |
| `hibrido_plug_in_razao` | decimal | Híbridos plug-in: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_combustivel` | inteiro | Híbridos convencionais: pela base por combustível. |
| `hibrido_modelo` | inteiro | Híbridos convencionais: pela base por modelo. |
| `hibrido_diferenca` | inteiro | Híbridos convencionais: diferença modelo − combustível. |
| `hibrido_razao` | decimal | Híbridos convencionais: razão modelo / combustível (nula se combustível = 0). |
| `hibridos_combustivel` | inteiro | Híbridos plug-in + convencionais: pela base por combustível. |
| `hibridos_modelo` | inteiro | Híbridos plug-in + convencionais: pela base por modelo. |
| `hibridos_diferenca` | inteiro | Híbridos plug-in + convencionais: diferença modelo − combustível. |
| `hibridos_razao` | decimal | Híbridos plug-in + convencionais: razão modelo / combustível (nula se combustível = 0). |
| `eletrificada_combustivel` | inteiro | Frota eletrificada: pela base por combustível. |
| `eletrificada_modelo` | inteiro | Frota eletrificada: pela base por modelo. |
| `eletrificada_diferenca` | inteiro | Frota eletrificada: diferença modelo − combustível. |
| `eletrificada_razao` | decimal | Frota eletrificada: razão modelo / combustível (nula se combustível = 0). |
| `hibrido_leve_modelo` | inteiro | Híbridos leves na base por modelo (sem equivalente na base por combustível). |

### `modelo_sem_uf.csv`

Base por modelo: o grupo sem UF ('Sem Informação') por mês e classe, que o painel do Brasil inclui e o de UF não. Nos eletrificados, tem perfil de estoque ainda não emplacado.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `frota_sem_uf` | inteiro | Frota da classe registrada sem UF válida. |
| `frota_brasil` | inteiro | Frota da classe no Brasil, com o grupo sem UF. |
| `parte_sem_uf` | decimal | frota_sem_uf / frota_brasil (fração entre 0 e 1). |

### `validacao_abve_tecnologia.csv`

Validação externa: vendas da ABVE x crescimento da frota da base por modelo, por período e classe (leves, UFs válidas). 2021 vem da série histórica da ABVE; de 2022 em diante, da base de vendas. A classe 'eletrificada' soma elétrico, plug-in e híbrido.

| Coluna | Tipo | Descrição |
|---|---|---|
| `periodo` | texto | Período de vendas comparado, do primeiro ao último mês (MM/AAAA a MM/AAAA). |
| `inicio` | data | Primeiro mês de vendas do período. A frota se compara a partir do mês anterior. |
| `fim` | data | Último mês de vendas do período, que é também o instantâneo final da frota. |
| `fonte_vendas` | texto | 'vendas' (base de vendas da ABVE, por modelo e UF), 'serie' (série histórica da ABVE, só Brasil e tecnologia) ou 'acumulado' (todos os períodos somados). |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `vendas_abve` | inteiro | Emplacamentos contados pela ABVE no período. |
| `crescimento_frota` | inteiro | Frota da base por modelo no fim do período menos a do mês anterior ao início, nos leves e nas UFs válidas. Compara-se com vendas porque a baixa de eletrificados quase não aparece no RENAVAM. |
| `diferenca` | inteiro | crescimento_frota − vendas_abve. |
| `razao` | decimal | crescimento_frota / vendas_abve (nula sem vendas). |

### `validacao_abve_uf.csv`

Idem, por UF (de 2022 em diante).

| Coluna | Tipo | Descrição |
|---|---|---|
| `periodo` | texto | Período de vendas comparado, do primeiro ao último mês (MM/AAAA a MM/AAAA). |
| `inicio` | data | Primeiro mês de vendas do período. A frota se compara a partir do mês anterior. |
| `fim` | data | Último mês de vendas do período, que é também o instantâneo final da frota. |
| `fonte_vendas` | texto | 'vendas' (base de vendas da ABVE, por modelo e UF), 'serie' (série histórica da ABVE, só Brasil e tecnologia) ou 'acumulado' (todos os períodos somados). |
| `uf_sigla` | texto | Sigla da UF; nula quando a UF publicada não é válida ('Sem Informação' etc.). |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `vendas_abve` | inteiro | Emplacamentos contados pela ABVE no período. |
| `crescimento_frota` | inteiro | Frota da base por modelo no fim do período menos a do mês anterior ao início, nos leves e nas UFs válidas. Compara-se com vendas porque a baixa de eletrificados quase não aparece no RENAVAM. |
| `diferenca` | inteiro | crescimento_frota − vendas_abve. |
| `razao` | decimal | crescimento_frota / vendas_abve (nula sem vendas). |

### `validacao_abve_marca.csv`

Idem, por marca.

| Coluna | Tipo | Descrição |
|---|---|---|
| `periodo` | texto | Período de vendas comparado, do primeiro ao último mês (MM/AAAA a MM/AAAA). |
| `inicio` | data | Primeiro mês de vendas do período. A frota se compara a partir do mês anterior. |
| `fim` | data | Último mês de vendas do período, que é também o instantâneo final da frota. |
| `fonte_vendas` | texto | 'vendas' (base de vendas da ABVE, por modelo e UF), 'serie' (série histórica da ABVE, só Brasil e tecnologia) ou 'acumulado' (todos os períodos somados). |
| `marca` | texto | Marca canônica: grafias da mesma empresa unidas por dados/marcas.csv (GM, CHEVROLET e CHEV viram CHEVROLET). Grafia fora da tabela segue como está. |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `vendas_abve` | inteiro | Emplacamentos contados pela ABVE no período. |
| `crescimento_frota` | inteiro | Frota da base por modelo no fim do período menos a do mês anterior ao início, nos leves e nas UFs válidas. Compara-se com vendas porque a baixa de eletrificados quase não aparece no RENAVAM. |
| `diferenca` | inteiro | crescimento_frota − vendas_abve. |
| `razao` | decimal | crescimento_frota / vendas_abve (nula sem vendas). |

### `validacao_abve_modelo.parquet`

Idem, modelo a modelo: classe pela ABVE, classe pela base, classes do PBE Veicular e vendas x crescimento. É o teste externo da classificação.

| Coluna | Tipo | Descrição |
|---|---|---|
| `periodo` | texto | Período de vendas comparado, do primeiro ao último mês (MM/AAAA a MM/AAAA). |
| `inicio` | data | Primeiro mês de vendas do período. A frota se compara a partir do mês anterior. |
| `fim` | data | Último mês de vendas do período, que é também o instantâneo final da frota. |
| `fonte_vendas` | texto | 'vendas' (base de vendas da ABVE, por modelo e UF), 'serie' (série histórica da ABVE, só Brasil e tecnologia) ou 'acumulado' (todos os períodos somados). |
| `modelo_abve` | texto | Texto do modelo como a ABVE grafa: o do RENAVAM sem o prefixo I/ e com espaço no lugar da barra. É a chave da comparação. |
| `marca_modelo_norm` | texto | Marca Modelo normalizado (sem acentos, caixa alta). |
| `marca` | texto | Marca canônica: grafias da mesma empresa unidas por dados/marcas.csv (GM, CHEVROLET e CHEV viram CHEVROLET). Grafia fora da tabela segue como está. |
| `classe_abve` | texto | Classe que a tecnologia da ABVE indica (BEV elétrico, PHEV plug-in, HEV e HEV FLEX híbrido, MHEV híbrido leve); a de mais vendas, se o modelo tiver mais de uma. |
| `classes_abve` | texto | Todas as classes com que a ABVE vendeu o modelo no período, separadas por barra vertical. |
| `classe_db` | texto | Classe que a base por modelo dá ao texto (dados/modelos.csv), no último mês. |
| `mesma_classe` | lógico | Se classe_abve e classe_db coincidem. Nulo quando o modelo não casou ou não teve venda. |
| `pbe_classes` | texto | Classes que a linha do modelo tem na tabela PBE Veicular do Inmetro, separadas por barra vertical. Vazio quando o modelo não casou com o PBE (moto, ônibus, caminhão e modelo fora de linha). |
| `casou` | lógico | Se o texto da ABVE foi encontrado na base por modelo. |
| `vendas_abve` | inteiro | Emplacamentos contados pela ABVE no período. |
| `crescimento_frota` | inteiro | Frota da base por modelo no fim do período menos a do mês anterior ao início, nos leves e nas UFs válidas. Compara-se com vendas porque a baixa de eletrificados quase não aparece no RENAVAM. |
| `diferenca` | inteiro | crescimento_frota − vendas_abve. |
| `razao` | decimal | crescimento_frota / vendas_abve (nula sem vendas). |

### `validacao_pbe.csv`

Validação contra o PBE Veicular do Inmetro, por mês e classe: modelos e frota que casam com o PBE e as duas divergências.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `classe` | texto | Classe de tecnologia atribuída (ver a tabela de classes). |
| `modelos` | inteiro | Número de modelos distintos. |
| `frota` | inteiro | Frota da classe no mês. |
| `frota_casada_pbe` | inteiro | Frota de modelos que casaram com uma linha do PBE Veicular. |
| `modelos_sem_versao_no_pbe` | inteiro | Modelos com classe eletrificada que o PBE não registra para eles. |
| `frota_sem_versao_no_pbe` | inteiro | Frota desses modelos (falso positivo provável). |
| `modelos_pbe_so_eletrificado` | inteiro | Modelos classificados como combustão cujas versões no PBE são todas eletrificadas. |
| `frota_pbe_so_eletrificado` | inteiro | Frota desses modelos (regra faltando ou geração antiga). |
| `cobertura_pbe` | decimal | frota_casada_pbe / frota (fração entre 0 e 1). |

### `qualidade_combustivel.csv`

Arquivos mensais da base por combustível: linhas, total, ajustes e inclusão na série.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `arquivo` | texto | Arquivo mensal da SENATRAN; vazio quando o mês do calendário não chegou na entrada. |
| `linhas` | inteiro | Linhas lidas do arquivo. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `ajuste` | texto | Correção ou ressalva do mês: escala x10, mês idêntico ao anterior, mês ausente, ou classe que só passa a existir no cadastro a partir dali. Vazio se nenhuma. |
| `incluido` | lógico | Se o mês entrou na série (falso para mês idêntico ao anterior e para mês ausente). |
| `sem_informacao` | decimal | frota_sem_informacao / frota_total no mês (fração entre 0 e 1): parte da frota sem rótulo de combustível aproveitável, que é o piso de incerteza das participações. |

### `qualidade_modelo.csv`

Idem para a base por modelo.

| Coluna | Tipo | Descrição |
|---|---|---|
| `ano` | inteiro | Ano do mês de referência do arquivo mensal. |
| `mes` | inteiro | Mês de referência (1 a 12). |
| `data_referencia` | data | Primeiro dia do mês de referência (para eixos de tempo). |
| `arquivo` | texto | Arquivo mensal da SENATRAN; vazio quando o mês do calendário não chegou na entrada. |
| `linhas` | inteiro | Linhas lidas do arquivo. |
| `frota_total` | inteiro | Frota total do recorte (todas as classes). |
| `ajuste` | texto | Correção ou ressalva do mês: escala x10, mês idêntico ao anterior, mês ausente, ou classe que só passa a existir no cadastro a partir dali. Vazio se nenhuma. |
| `incluido` | lógico | Se o mês entrou na série (falso para mês idêntico ao anterior e para mês ausente). |

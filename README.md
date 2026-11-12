# eletromobilidade (db-demob)

Base de eletromobilidade construída a partir da frota de veículos da SENATRAN
(RENAVAM): quantos veículos elétricos, híbridos plug-in e híbridos há em cada
município, UF e no Brasil, mês a mês, tratada, conferida e documentada. O
produto são as tabelas de [`resultados/`](resultados/LEIAME.md), que o
[painel web](https://borgesmath.github.io/Banco-de-dados-Eletromobilidade-/) apresenta com filtros por UF, município, tipo de veículo
e tecnologia.

## Fontes

| Fonte | O que entra | Como é usada |
|---|---|---|
| SENATRAN, frota por UF, município e **combustível** (`D_`, mensal, [gov.br](https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-2026)) | Contagem por rótulo de combustível do RENAVAM | Base por combustível: a série mensal, jun/2020 a set/2026 |
| SENATRAN, frota por UF, município, **marca/modelo** e ano de fabricação (`I_`, [CKAN](https://dados.transportes.gov.br/dataset/12686da0-3d71-4499-b432-d270f785c907)) | Texto "Marca Modelo", sem combustível | Base por modelo: tecnologia inferida do nome; a série mensal, jun/2020 a set/2026 |
| IBGE, [API de localidades](https://servicodados.ibge.gov.br/api/docs/localidades) | Código e nome oficial dos 5.571 municípios | Identidade do município |
| IBGE, Estimativas de População ([SIDRA 6579](https://sidra.ibge.gov.br/tabela/6579)) | População de 1º de julho, por município | Eletrificados por mil habitantes |
| Inmetro, PBE Veicular (PDF do ciclo) | Propulsão declarada pelo fabricante, versão por versão | Auditoria da classificação por modelo e tipo de veículo leve |
| ABVE, [BI Frotas](https://abve.org.br/bi-frotas/) | Emplacamentos de eletrificados leves por mês, UF, modelo e tecnologia, pela API pública do painel | Validação externa da base por modelo, por ano, UF, marca e modelo. Só a comparação é publicada |

Os arquivos da SENATRAN não vão para o repositório; as tabelas do IBGE e do
Inmetro entram como instantâneos versionados em
[`src/eletromobilidade/dados/`](src/eletromobilidade/dados/README.md).

## Arquitetura

```
data/raw/         arquivos da SENATRAN e vendas da ABVE      (fora do git)
   │  eletromobilidade baixar | abve
   ▼
src/eletromobilidade/   coleta, leitura, classificação, conciliação, validação
   │  eletromobilidade processar       └─ dados/  tabelas de referência e regras
   ▼
data/processed/   todas as tabelas, Parquet e CSV            (fora do git)
   │  eletromobilidade publicar
   ▼
resultados/       painéis, auditorias, LEIAME e DICIONARIO   (versionado)
   │  eletromobilidade painel
   ▼
painel/           painel web, HTML único com os dados        (versionado; GitHub Pages)
```

| Pasta | O que tem | Leia |
|---|---|---|
| [`src/eletromobilidade/`](src/eletromobilidade/README.md) | O pacote Python: CLI, pipeline, qualidade dos arquivos, conciliação | Uso, módulos, saídas |
| [`src/eletromobilidade/dados/`](src/eletromobilidade/dados/README.md) | Regras e tabelas de referência: combustível, modelo, tipo, marca, município, população, PBE | Como cada coisa é classificada e por quê |
| [`resultados/`](resultados/LEIAME.md) | O que o projeto publica. `LEIAME.md` e `DICIONARIO.md` são gerados por `publicar` | Cobertura e colunas |
| [`painel/`](https://borgesmath.github.io/Banco-de-dados-Eletromobilidade-/) | O painel web, gerado de `resultados/` por `painel`, e a lista dos arquivos da SENATRAN usados em cada mês | Abra no navegador |
| [`tests/`](tests/README.md) | Testes do pacote e das tabelas publicadas | Como rodar |
| [`docs/`](docs/README.md) | Roteiro e apresentações | O que falta e o que a base sustenta |
| [`data/`](data/README.md) | Arquivos brutos, cache e saídas locais | Layout |

**Toda regra mora no Python.** O que decide se um veículo é eletrificado está em
`src/`, onde um teste pega a mudança. Quem consome `resultados/` apresenta e
agrega, sem reclassificar.

## Premissas

**Duas bases independentes, conciliadas e validadas.** A base por combustível
usa o campo combustível do RENAVAM: é a contagem oficial e tem série mensal. A
base por modelo infere a tecnologia do nome do modelo, porque o arquivo de
marca/modelo não traz combustível: dá marca, modelo, ano de fabricação e tipo de
veículo. A base por modelo é conferida por três lados: contra a base por
combustível (conciliação), contra o PBE Veicular do Inmetro e contra as vendas
da ABVE.

**Frota é estoque registrado, não emplacamento.** A variação mensal é saldo, não
venda. A baixa quase não aparece: os eletrificados leves fabricados até 2018 eram
12.298 em dez/2020 e 12.317 em set/2026.

**Eletrificado é elétrico, plug-in, híbrido e célula de combustível.** O híbrido
leve (12 V ou 48 V) fica fora, em coluna própria. O PBE do Inmetro, que registra
esses carros como combustão, sustenta a decisão.

**O município é o código IBGE, nunca o nome.** A SENATRAN troca a grafia de seis
municípios no meio da série (`EMBU` vira `EMBU DAS ARTES`).

**Classificação por regra explícita, sem semelhança aproximada.** Cada regra é
uma linha de CSV com nota, cada armadilha é um caso de teste, e o que não casa
vai para fila de revisão, não para palpite.

**A série começa em jan/2020.** O arquivo por combustível falta de jan a
mai/2020, então ela começa de fato em jun/2020. A base por modelo tem a mesma série
mensal, jun/2020 a set/2026 (76 meses, desde 10/11/2026). A rodada completa lê
~8,5 GB de arquivos de marca/modelo e leva ~2 h sem cache; com o cache em
`data/interim`, ~20 min. A validação contra a ABVE segue por ano, porque os
períodos de venda dela são anuais.

## Resultados

Base por combustível, set/2026, Brasil:

| | |
|---|---:|
| Frota total registrada | 136.424.856 |
| Frota eletrificada | 1.330.703 (0,98%) |
| Elétricos (BEV) | 484.407 |
| Híbridos (HEV + PHEV pelo campo combustível) | 846.283 |
| Eletrificados por mil habitantes | 6,21 |

Em jun/2020 eram 41.332 eletrificados (0,04% da frota): 32 vezes mais em seis
anos, contra 26% de aumento da frota total. São Paulo concentra 28% do total; o
Distrito Federal lidera em intensidade, com 28,9 eletrificados por mil
habitantes.

**Conciliação, set/2026, UFs válidas** (base por modelo / base por combustível):

| | Combustível | Modelo | Razão |
|---|---:|---:|---:|
| Elétrico | 395.132 | 379.518 | 0,96 |
| Híbrido plug-in | 79.245 | 358.506 | 4,52 |
| Híbrido convencional | 709.697 | 257.337 | 0,36 |
| Híbridos + híbridos leves do modelo | 788.942 | 788.833 | 1,00 |

As duas bases concordam no elétrico e no total de híbridos, porque o campo
combustível conta o híbrido leve como híbrido; divergem na divisão entre plug-in e
híbrido convencional.

**Validação contra as vendas da ABVE** (crescimento da frota de leves nas UFs
válidas, pela base por modelo, contra emplacamentos sem micro-híbridos). A ABVE
muda o rótulo de alguns modelos com o tempo sem reescrever os anos anteriores (o
Tiggo 7 Pro "HA" é HEV Flex até 2024 e MHEV 48V depois), então a conta sai também
com todo o histórico no rótulo atual de cada modelo:

| Período | Frota | ABVE | Diferença | ABVE no rótulo atual | Diferença |
|---|---:|---:|---:|---:|---:|
| 2021 | 34.198 | 34.990 | −2,3% | 34.990 | −2,3% |
| 2022 | 39.623 | 43.005 | −7,9% | 40.190 | −1,4% |
| 2023 | 79.636 | 82.742 | −3,8% | 79.749 | −0,1% |
| 2024 | 156.921 | 161.321 | −2,7% | 157.343 | −0,3% |
| 2025 | 222.090 | 223.896 | −0,8% | 222.212 | −0,05% |
| jan–set/2026 | 381.425 | 381.609 | −0,05% | 381.603 | −0,05% |
| **2021 a set/2026** | **913.893** | **927.563** | **−1,5%** | **916.087** | **−0,2%** |

No acumulado, contra a ABVE publicada, elétrico −0,2%, plug-in −1,9%, híbrido
−2,7%; no rótulo atual, −0,2%, −0,5% e +0,1%. Por marca, BYD, GWM, Toyota, Geely,
Volvo, Omoda e Jaecoo batem a ±0,2%. Modelo a modelo, 848 de 856 textos de modelo
da ABVE casam com a base (99,99% das vendas), e nos eletrificados 98,9% das vendas
têm a mesma classe nas duas fontes (99,8% pelo rótulo atual). Contra a ABVE
publicada, 6.253 dos 6.321 híbridos a menos são os Caoa Chery "H"/"HA", híbridos
leves aqui e no rótulo atual dela.

**O quanto a comparação depende da ABVE.** Desde 09/11/2026 as regras de modelo
seguem o rótulo atual da ABVE onde as vendas e o crescimento da frota do mesmo
texto batem. A contagem continua independente: o crescimento de cada texto sai do
RENAVAM e só é comparado com as vendas dela. O que se tomou dela foi a classe de
257 textos, e o peso disso muda com a classe. Em elétrico, plug-in e híbrido, os
textos que mudaram somam 3,5 mil vendas, 0,4% das vendas desses três, e a maior
parte é regra que o nome já justificava (Renault, Ferrari, Nextem, Tangjun). Em
híbrido leve, são 48,6 mil, 31% das vendas da classe: o nome não diz que o motor é
de 48 V (`M.BENZ C200 AMG LINE`, `BMW X3 30 XDRIVE`, `FIAT FASTBACK IMPETUS HY`),
e a classe veio da ABVE. Para híbrido leve, então, a diferença pequena no rótulo
atual é em boa parte construída. A validação independente da classe é a do PBE do
Inmetro, logo abaixo, e a do próprio RENAVAM: os híbridos do campo combustível, que
incluem os híbridos leves, fecham com os híbridos e híbridos leves da base por
modelo (tabela de conciliação acima).

O que isso decide: **o rótulo HIBRIDO PLUG-IN do campo combustível pega só 22%
dos plug-ins vendidos**; o resto entra como híbrido. A divisão PHEV × HEV vale
pela base por modelo, não pelo campo combustível.

**Contra o PBE Veicular do Inmetro** (set/2026): 78,9% da frota eletrificada da
base por modelo casa com uma versão do PBE, e só 18 modelos (6.867 veículos) têm
classe eletrificada que o PBE não registra.

Detalhe por ano, UF, marca e modelo: `resultados/validacao_*`, com o resumo no
[`LEIAME.md`](resultados/LEIAME.md#validação).

**Composição por tipo** (base por modelo, set/2026): 92,9% da frota eletrificada
é leve e 6,8% é moto. Entre os elétricos a bateria a moto é 16,9%, e era 64,6% em
dez/2020. Cite a parte, não a contagem: a base por modelo acha 18% menos
eletrificados que a por combustível, e a contagem por tipo herda isso.

### Limitações

1. **Sem tipo de veículo no campo combustível.** A participação eletrificada é
   sobre a frota total, não sobre veículos leves; o tipo só existe na base por
   modelo.
2. **Plug-in e célula de combustível começam tarde no RENAVAM**: o código
   plug-in em abr/2022, o de célula em nov/2022. Antes disso o zero é ausência de
   código. A separação PHEV/HEV pelo campo combustível só se compara de abr/2022
   em diante, e mesmo assim subconta o plug-in.
3. **O campo combustível conta híbrido leve como híbrido** (Fiat "Hybrid" como
   GASOLINA/ALCOOL/ELETRICO, e as motos Yamaha Ray ZR e Fluo 125 Hybrid), e a
   base por modelo não. A conciliação mede isso em `hibrido_leve_modelo`.
4. **ELETRICO/FONTE INTERNA e FONTE EXTERNA** não têm significado documentado de
   forma inequívoca; os dois contam como elétrico, e o rótulo original fica em
   `frota_combustivel`.
5. **O grupo sem UF** ("Sem Informação", 3,1 milhões de veículos) entra no total
   do Brasil e tem, nos eletrificados, perfil de estoque ainda não emplacado.
   Para comparar com vendas, use as UFs válidas.
6. **3,6% da frota não tem combustível aproveitável** no cadastro. É o piso de
   incerteza de qualquer participação sobre a frota total.
7. **Algumas regras de modelo vêm de conhecimento de mercado ou do rótulo da
   ABVE**, não do texto (Stellantis, Caoa Chery e Audi "Hybrid" como híbrido leve,
   Jaecoo 7 como plug-in, e os híbridos leves 48 V de Mercedes, BMW e Land Rover,
   em lista fechada). Cada caso está anotado na nota da regra.
8. **A base por combustível não tem dez/2021.** O arquivo publicado para esse mês
   é idêntico ao de jan/2022 e traz a frota de janeiro; o mês foi excluído.

O que pode e o que não pode ser afirmado com a base está em
[`docs/ROTEIRO.md`](docs/ROTEIRO.md#o-que-a-base-sustenta).

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

eletromobilidade baixar --tabela combustivel --anos 2025 2026
eletromobilidade baixar --tabela marca_modelo --anos 2020 2021 2022 2023 2024 2025 --meses 12
eletromobilidade baixar --tabela marca_modelo --anos 2026 --meses 9
eletromobilidade abve              # vendas da ABVE até o último mês da base por modelo
eletromobilidade -v processar      # data/raw -> data/processed, com a validação
eletromobilidade publicar          # data/processed -> resultados/
eletromobilidade painel            # resultados/ -> painel/index.html
pytest
```

Todos os comandos e opções: [`src/eletromobilidade/README.md`](src/eletromobilidade/README.md).

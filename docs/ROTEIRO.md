# Roteiro

Estado em 10/11/2026. O pipeline Python está fechado e testado (396 testes), e o
escopo do repositório vai até `resultados/`. O que falta está abaixo, em ordem de
valor. A comparação com as vendas da ABVE, feita em 23/10, está no item 8, com as
pendências que saíram dela resolvidas.

As tabelas de `resultados/` estão em dia com o código, regeradas em 10/11 com a
série completa nas duas bases: 76 meses de combustível e 76 de marca/modelo
(item 2). Os 7 meses que já existiam na base por modelo não mudaram. Na base por combustível, o mês excluído passou a ser dez/2021
(item 4). Regerá-las exige os arquivos da SENATRAN em `data/raw`, que não são
versionados: `baixar`, depois `processar` e `publicar`.

## 1. Código IBGE e população por município — feito

**Feito em 21/10/2026.** Toda tabela no grão de município traz
`cod_municipio_ibge`, e `resultados/municipios_dimensao.parquet` tem uma linha
por município, com o nome oficial do IBGE. O casamento é determinístico: 5.537
das 5.581 grafias da base casam pelo nome sem acento e sem pontuação, e as 41
que sobram estão em `src/eletromobilidade/dados/municipios_grafias.csv`,
conferidas uma a uma. Ficam sem código só os três pseudo-municípios sem UF. O
teste que este item pedia existe e roda sobre `resultados/`: falha se sobrar
município com UF e sem código. Detalhe em `src/eletromobilidade/dados/README.md`, seção Município.

**O resíduo não era só grafia.** Seis municípios trocam de nome no meio da série
— `EMBU` vira `EMBU DAS ARTES` em abr/2022, `GOUVEA` vira `GOUVEIA` em mar/2024
—, e pelo nome cada um deles era dois municípios, com a série cortada no mês da
troca. A dimensão do painel era por nome e tinha 5.581 membros; passou a ser por
código, com 5.574, e os seis têm os 75 meses contínuos.

**População, também feita em 21/10/2026.** Os painéis da base por combustível
trazem `populacao` e `eletrificada_por_mil_habitantes`, a medida que uma política
de recarga usa e o motivo de este item vir primeiro. A fonte escolhida foram as
estimativas anuais do IBGE (SIDRA 6579), não o Censo 2022, por darem série. A
junção é pelo código, sem casar nome nenhum.

**A ressalva que acompanha a taxa por habitante.** Não há estimativa para 2022 nem
2023, e a base das estimativas muda no meio: até 2021 projetam o Censo 2010, de
2024 em diante partem do Censo 2022. Entre as duas, 1.709 municípios mudam mais de
10%. 2022 e 2023 usam a estimativa de 2024, que está do mesmo lado do Censo, e a
quebra fica em 2022. A taxa de um município comparada através dela mede revisão de
população junto com frota. Detalhe em `src/eletromobilidade/dados/README.md`, seção População.

**O mapa municipal também está destravado.** A malha do IBGE identifica o
município pelo mesmo código. Ela tem
5.570 polígonos: falta Boa Esperança do Norte, mais novo que a malha.

## 2. Ampliar a série da base por modelo — feito (série mensal)

**Feito em 29/10/2026**, por decisão do usuário: dezembro de 2020 a 2025 mais
set/2026, 7 meses. Dá série anual por marca, modelo e ano de fabricação, a
conciliação com 6 pontos (dez/2021 saiu da base por combustível, item 4) e a
validação contra a ABVE ano a ano. Cada mês são ~22
milhões de linhas e ~130 MB, e cerca de 1,5 min de processamento sem cache.

**Série mensal feita em 10/11/2026**, a pedido do usuário: jun/2020 a set/2026,
76 meses, a mesma cobertura da base por combustível. A conciliação passou a ter
75 meses (falta dez/2021, excluído da base por combustível) e fecha o total em
todos eles. As razões por classe andam devagar, sem degrau de um mês para o
outro. O único salto, jul/2024 (+27,8 mil eletrificados contra ~13 mil nos meses
vizinhos), aparece igual no campo combustível (+29,5 mil): vem da fonte, e parte
dele cai no grupo sem UF. A validação contra a ABVE não muda: segue por ano.

## 3. Tipo de veículo — feito

**Feito em 21/10/2026.** Os eletrificados e híbridos leves da base por modelo
têm tipo de veículo — leve, moto, ônibus, caminhão, outros —, publicado em
`modelo_eletrificados`, `modelos_dimensao` e nos painéis `modelo_tipo_{uf,brasil}`.
Detalhe em `src/eletromobilidade/dados/README.md`, seção Tipo de veículo. A resposta à pergunta que motivou o
item, base por modelo:

| | dez/2020 | set/2026 |
|---|---:|---:|
| Leve, na frota eletrificada | 90,8% | 92,9% |
| Moto, na frota eletrificada | 8,8% | 6,8% |
| **Moto, entre os elétricos a bateria** | **64,6%** | **16,9%** |

Ônibus e caminhão somam menos de 0,5%. Plug-in e híbrido convencional são todos
leves. Leia como composição: a base por modelo acha 18% menos eletrificados que a
por combustível, e a contagem por tipo herda isso.

**Duas premissas deste item estavam erradas, e o trabalho mostrou.**

- *"Os 20,9% fora do PBE concentram moto, scooter e ônibus."* Não: dois terços do
  que fica fora do PBE ainda é carro, que não casou por geração antiga ou nome
  abreviado — o maior é o Corolla Cross, `TOYOTA/CCROSS XRX HYBRID`, com 69 mil.
  O PBE não bastava; a tabela de regras precisou cobrir carro também.
- *"`G_` como total de controle transformaria a inferência em erro medido."* Não
  transforma: `G_` não tem combustível, então só controlaria uma classificação de
  tipo da frota inteira (40 mil modelos), não a da eletrificada. Ficou como
  conferência pontual — em nenhum município os eletrificados de um grupo passam o
  total oficial do grupo em set/2026 —, que pega erro grosso e não mede erro fino.

**O que faz o número ser defensável** é outra coisa: o tipo de um modelo com nome
não é ambíguo, como a tecnologia é. O PBE dá o tipo de 78,7% da frota com fonte
externa; as 27 regras de `dados/tipos.csv` foram conferidas contra os modelos;
regra que contradiz o PBE é divergência e derruba o teste — foi o que pegou a BYD
eT3, van, que uma regra de caminhão levava. Sem tipo ficaram 3 veículos. Um caso
foi decidido por exclusão, e a regra diz isso (`FLASH/MV ING ELETRIC`, ver
`src/eletromobilidade/dados/README.md`).

**De passagem, a revisão achou falsos elétricos na classificação de tecnologia,
corrigidos em 21/10/2026** com três regras de combustão em `dados/modelos.csv`,
antes das que os pegavam. Em set/2026, na base por modelo:

- BMW com código de motor `EV` no nome: `I/BMW 320I EV11` (1.242), `330I EV51`
  (632, com a versão Security), `325I EV31` (391), `325I PRO EV39` (58) e
  `330I EV53` (2). O EV11 era o caso que o README citava como achado pela
  auditoria do PBE — achado em 2026, mas a regra não tinha mudado;
- `I/BMW 325 IX` (2), o 325ix dos anos 1980, que casava com a regra do iX;
- `MOTO GUZZI CALIFORNIA EV` (12), moto a combustão dos anos 1990, e um
  `LMABORGHINI HURACAN EV` (1), em que EV é EVO truncado;
- `BYD F0`, `G3` e `F6` (8), carros a combustão que a BYD vendeu por volta de
  2010, pegos pela regra "toda BYD é elétrica".

São 2.348 elétricos a menos em set/2026, 0,5% dos elétricos da base por modelo,
e nada mais mudou de classe. **Em dez/2020 o efeito é outro**: 2.345 dos 8.529
elétricos daquele mês eram esses falsos. O reconhecimento de elétricos nas UFs
válidas, que parecia de 99%, é de 61% (64% com as regras de 09/11/2026). A base
por modelo de 2020 reconhecia mal os elétricos, e um erro compensava o outro. O
que ela não reconhece em 2020 não foi investigado.

## 4. Fechar o furo de dez/2021 e esticar a série para trás

Dois buracos distintos:

- **dez/2021** está excluído desde 09/11/2026. Os arquivos de combustível de
  dez/2021 e de jan/2022 são idênticos, e o conteúdo é o de janeiro: a frota
  total salta 525 mil sobre novembro e fevereiro cresce só 271 mil, num mês
  normal de 300 mil; o arquivo de marca/modelo de dez/2021, que é dezembro de
  verdade, tem 197.557 veículos a menos; e, contra a série mensal da ABVE, o mês
  dava +72%. Até então o excluído era jan/2022, e dez/2021 trazia a frota de
  janeiro. É inferido dos totais, sem documento da SENATRAN, e a exceção está em
  `qualidade.CONTEUDO_DO_MES_SEGUINTE`. Vale checar se a SENATRAN republicou o
  arquivo de dezembro; se não, o furo é da fonte. A conciliação perdeu o ponto de
  dez/2021 por isso: a base por modelo tem dezembro, a por combustível não.
- **A série começa em jun/2020.** O CKAN tem mensal desde 2013, mas até 2015
  parte dos arquivos está em `.rar`, que o pacote não abre. Suportar `.rar`
  (via `rarfile` + `unrar`, ou convertendo à mão) levaria a série a 2016 ou
  2013. Para a tendência de eletrificação, 2020 em diante provavelmente basta —
  antes disso a frota eletrificada é residual. Item de baixa prioridade.

## 5. Normalizar marca — feito, com resíduo

Dois problemas, e o menor deles era o das grafias.

**O primeiro era de posição.** O primeiro elemento de "Marca Modelo" não é sempre
a marca: pode ser marcador de importação (`I/`, `IMP/`), a montadora que montou o
veículo no Brasil (`JTA/SUZUKI EN125 YES`) ou o tipo do veículo, em reboque e
máquina (`SR/RANDON SR CA`, `M.A./MASSEY-FERGUSON`, `MR/CAT 416`). Só `I/` e
`IMP/` eram tratados, então 4,58 milhões de veículos tinham como "marca" um
`R`, `SR` ou `REB`. Tratados os prefixos, aparecem os fabricantes que estavam
escondidos: RANDON com 500.746, FACCHINI 246.774, GUERRA 138.320, LIBRELATO
132.229, NOMA 90.997.

A extração também passou a ler tudo o que vem antes da barra, e não até o
primeiro espaço, que é o que o Power Query já fazia — `HARLEY DAVIDSON/XL883N`
dava "HARLEY". Python e painel divergiam.

**O segundo são as grafias**, em `src/eletromobilidade/dados/marcas.csv`
(33 equivalências conferidas à mão). As maiores:

| Marca canônica | Frota | Grafias unidas |
|---|---:|---|
| VOLKSWAGEN | 21.953.416 | VW, VOLKS, VOLKSWAGEN |
| CHEVROLET | 16.500.963 | GM, CHEVROLET, CHEV |
| MERCEDES-BENZ | 2.363.055 | M.BENZ, MBENZ, MERCEDES, M.BENZ313CDI, MERCEDES BENZ |
| MITSUBISHI | 833.802 | MMC, MITSUBISHI |
| SUZUKI | 837.461 | SUZUKI, JTA-SUZUKI |
| CHERY | 420.677 | CAOACHERY, CHERY |
| IVECO | 274.424 | IVECO, IVECOFIAT |
| ROYAL ENFIELD | 112.061 | RE, ROYAL |
| HARLEY-DAVIDSON | 91.372 | HARLEY DAVIDSON, H.DAVIDSON, HARLEY-DAVIDSON |

Na dimensão do painel, 118 marcas viraram 110. O ganho grande não está aí: está
na base completa, onde Chevrolet estava partida em três linhas e Mercedes em
cinco.

**O resíduo, que é real.** A estimativa de "uma tarde" valia para as 118 marcas
do recorte eletrificado. A base completa tem cerca de 4,7 mil grafias distintas,
e normalizar todas à mão não se paga — a cauda é marca de verdade, grafada uma
única vez. O que existe agora é fila ordenada: `processar` lista as grafias que
*parecem* variante de outra (modelo colado na marca, pontuação a mais), por frota
decrescente. São 310, e a maior é `RANDONSP` com 32.547 veículos. Duas ordens de
grandeza abaixo do que já foi resolvido, e por isso item de baixa prioridade
daqui para frente.

O que o heurístico não acha, e que só sai a olho, é abreviação sem parentesco no
texto: `GM` para Chevrolet, `MMC` para Mitsubishi, `LR` para Land Rover. Essas
entraram pelo conhecimento de mercado, uma a uma, e é assim que as próximas
entram.

**Agrupamento por fabricante não foi feito.** `marca` é marca comercial:
CHEVROLET e GMC seguem separadas, como VOLVO e GEELY, como CHERY e OMODA. Somar
por grupo econômico pede outra coluna e outra tabela, com decisão de fronteira
em cada caso — e errar isso é pior que não ter.

## 6. Publicar a tabela longa por classe

`combustivel_municipio` é larga, uma coluna por classe. Publicar
`frota_classe_municipio.parquet` no formato longo (mês × município × classe ×
frota) poupa quem consome a base de despivotar por conta própria, fora do
Python, onde não há teste. Fica para quando houver um consumidor que precise.

## 7. Outras tabelas da SENATRAN

`municipio_tipo`, `uf_tipo`, `ano_fabricacao`, `tipo_especie_eixos`, `potencia`,
`restricao`, `cor`, `cep` são reconhecidas pelo coletor e não processadas.
Nenhuma cruza com combustível, então nenhuma responde pergunta de
eletromobilidade por si. `potencia` (`E_`) é a mais promissora: potência cruzada
com município dá uma proxy de porte da frota. Só depois do resto.

## 8. Comparação com as vendas da ABVE — feita

**Feita em 23/10/2026**, na apresentação `docs/Comparação com ABVE Data v2.pptx`,
em que o projeto passa a se chamar db-demob. É a primeira validação da base contra
uma fonte independente.

**O número comparável.** Vendas são fluxo e frota é estoque, então se compara o
crescimento da frota com as vendas do mesmo período, só nos leves e só nas UFs
válidas (`modelo_tipo_uf`, tipo `leve`). De dez/2020 a set/2026 os eletrificados
leves cresceram 913.893; a ABVE vendeu 927.563 de jan/2021 a set/2026, sem os
micro-híbridos. A frota fica 1,5% abaixo: elétrico −0,2%, plug-in −1,9%, híbrido
−2,7%. Dos 6.321 híbridos a menos, 6.253 são os Caoa Chery da pendência 2. Com o
histórico da ABVE no rótulo atual de cada modelo (pendência 6), a diferença cai
para −0,2%. O deck de 23/10 traz a versão anterior às regras de plug-in da
pendência 1 (909.699, −1,9%, plug-in −3,4%).

**Três achados que mudam a leitura da base.**

- *O painel Brasil inclui um grupo que, nos eletrificados, tem perfil de
  estoque.* É a UF e o município "Sem Informação", que vem dos dois arquivos da
  fonte: combustível e marca/modelo dão o mesmo total, 3.086.939 em set/2026. Nos
  eletrificados, 99,8% não têm ano de fabricação, o grupo se concentra nos
  lançamentos mais recentes (Dolphin Mini, Geely EX2 e EX5, Jaecoo 7) e cai
  depois de jul/2026. Entre dez/2020 e set/2026 ele ganhou 62.507 leves
  eletrificados, mais que toda a folga contra a ABVE. A leitura provável é
  veículo já cadastrado pelo fabricante ou importador e ainda não emplacado; não
  há documento da SENATRAN que a confirme. Para comparar com vendas, use as UFs
  válidas.
- *Baixa quase não aparece.* Os eletrificados leves fabricados até 2018, nas UFs
  válidas, eram 12.528 em dez/2020 e 12.563 em set/2026, com as regras de
  09/11/2026 (12.298 e 12.317 com as de 23/10). Frota e vendas deveriam
  empatar; o que sobra é diferença de medição, não perda de veículos.
- *Por fabricante, a diferença está em poucos modelos.* O BI Frotas da ABVE
  (abve.org.br/bi-frotas/) tem a base de vendas por fabricante e modelo, com o
  texto do RENAVAM, de jan/2022 a set/2026. Para alinhar o período, dez/2021 da
  base por modelo foi processado à parte, fora de `resultados/`. De dez/2021 a
  set/2026 a frota de leves cresceu 876.674, contra 892.573 vendidos (−1,8%); BYD,
  GWM, Toyota, Omoda Jaecoo e Geely batem a ±0,2%. Dos 10.737 plug-ins a menos,
  cerca de 5,4 mil são modelos que a ABVE conta como plug-in e que, pela versão,
  são híbridos leves de 48 V (BMW X6 40i e M Competition; Mercedes GLE 450d, AMG
  GLE 53 e 63, GLS 450; Land Rover diesel), e cerca de 3,2 mil são plug-ins que as
  regras daqui não reconhecem. O "fabricante" da ABVE é na prática a marca: só
  Omoda e Jaecoo aparecem juntas.

**Pendências que saíram da comparação.**

1. ~~*Regras de plug-in que faltam*~~ — **feito em 29/10/2026.** Passaram a
   plug-in o Outlander com "E" no fim (`SIGNTR E`, `HPES E`) e o `OUTLANDER
   HYBRID` de 2018-19, os Mercedes-AMG "EP", os Panamera abreviados (`4EHST`,
   `4EHEX`, `4SEHS`, `TSE-H`, `TSEHS`), o `CAYENNE CPH BE` e os Volvo XC60/XC90
   `INSC EXPRES`; o `CAYENNE S HYBR` de 2011 passou a híbrido. São 4.162 plug-ins
   leves a mais no crescimento comparável, contra os ~3,2 mil estimados; o
   excedente é a Volvo. A validação modelo a modelo confirmou a inferência: a ABVE
   conta XC60 e XC90 `INSC EXPRES` como PHEV. O XC40 `INSC EXPRES`, também PHEV
   para a ABVE, entrou na regra em 09/11/2026 (381 veículos), e a Volvo fecha a
   −0,03% (era −2,6%). Os Cayenne `E CO`, `E OF`, `ET`, `ES` passaram a elétrico
   em 09/11/2026: a ABVE os vende como BEV.
2. ~~*Fronteira entre híbrido e híbrido leve*~~ — **decidido em 09/11/2026.** O
   Tiggo 7 Pro "H"/"HA" segue híbrido leve, que é o rótulo atual da ABVE: ela o
   conta como HEV Flex até 2024 e como MHEV 48V desde 2025 (6.253 vendas como HEV
   Flex desde 2022, com o Tiggo 5X). O plug-in da Audi é o Q5 TFSI
   e, grafado `P-HIBRIDO`, que já estava certo; os demais Audi "HIBRIDO" e "HIB"
   seguem a ABVE e passaram a híbrido leve (3.910 no crescimento comparável, dos
   quais 3.722 eram híbridos e 188 combustão). Três casos em que seguir a ABVE não
   dá resposta direta:
   - `Q8 SB HIBRIDO` é PHEV na ABVE em 2024-25 (280) e MHEV 48V em 2026 (81). Vale
     o rótulo mais recente, porque o RENAVAM grafa o plug-in da marca com `P-`.
   - `A3 SD`, `A3 SB`, `RS6 AV` e `RSQ8 SB HIBRIDO` (2.381 veículos) não têm venda
     na ABVE. Entram como híbrido leve por inferência, pela leitura dos demais.
   - `Q5 2.0 TFSI` e `Q5 2.0 TFSI Q` (3 vendidos como PHEV, 2.419 de crescimento)
     seguem combustão, e o `E-TRON QUATTRO` (1 vendido como PHEV) segue elétrico.
     Os rótulos da ABVE nesses textos parecem erro pontual.
3. ~~*Tabela de validação*~~ — **feito em 29/10/2026.** `eletromobilidade abve`
   baixa a base da ABVE pela API pública do painel para `data/raw/abve/` (fora do
   git, por ser dado de terceiro), e `processar` publica a comparação em
   `validacao_abve_{tecnologia,uf,marca,modelo}`, por ano e acumulada. Modelo a
   modelo, 848 de 856 textos da ABVE casam com a base (99,99% das vendas), e nos
   eletrificados 98,9% das vendas têm a mesma classe nas duas fontes (99,8% pelo
   rótulo atual). A diferença no total cai com o tempo: −7,9% em 2022, −0,8% em
   2025, −0,05% em jan–set/2026.
4. ~~*O grupo sem UF*~~ — **feito em 29/10/2026**: `modelo_sem_uf`, por mês e
   classe, e `qtd_sem_uf` em `modelos_classificados`.
5. ~~*Dizer em `resultados/` qual base vale para cada pergunta*~~ — **feito em
   29/10/2026**: seções "Qual base usar" e "Validação" do `LEIAME.md`, geradas
   por `publicar`, e `validacao_pbe` com a cobertura do Inmetro por mês e classe.
6. ~~*Chegar mais perto da ABVE*~~ — **feito em 09/11/2026.** A diferença era
   quase toda de classificação, e por quantidade quase não havia erro: de
   jan/2022 a set/2026, −11.476 eram rótulo antigo da própria ABVE, que muda o
   rótulo de alguns modelos com o tempo sem reescrever os anos anteriores, e
   −3.766 eram regras faltando aqui. As regras passaram a seguir o rótulo atual
   da ABVE onde vendas e crescimento da frota batem a ±25% (Ferrari, McLaren,
   Renault Kangoo e Koleos, Nextem, Tangjun, Cayenne e Macan elétricos e os
   híbridos leves Mercedes, BMW, Land Rover e Fastback "HY"). Onde não batem, o
   texto cobre geração a combustão e ficou de fora (`TIGGO7 SPORT`: 23 vendas e
   70 mil de crescimento). A validação sai também com o histórico no rótulo
   atual (`vendas_abve_rotulo_atual`), o texto `BMW X5XDRIVE45E` passou a casar,
   e as diferenças entre o HEV e o MHEV daqui e da ABVE, caso a caso, estão em
   `docs/internos/HEV_MHEV_aqui_x_ABVE.md`, fora do git.
7. ~~*Aviso no `LEIAME.md`*~~ — **feito em 09/11/2026.** Com as regras
   calibradas pela ABVE, a comparação com ela deixou de ser validação
   independente da classificação: o −0,2% no rótulo atual é, em boa parte,
   construído. O `LEIAME.md` (gerado por `publicacao.validacao_leiame`) e a seção
   Resultados do README dizem isso, e apontam o PBE do Inmetro como a validação
   independente.

---

# O que a base sustenta

Critério de qualidade: o que está medido, o que é indício e o que não se pode
afirmar a partir destes dados. Vale para qualquer uso — o roteiro não presume
formato nem destino de entrega.

## O que já está disponível para citar

Base por combustível, setembro de 2026, Brasil:

| | |
|---|---:|
| Frota total registrada | 136.424.856 |
| Frota eletrificada | 1.330.703 |
| Participação | 0,98% |
| Elétricos (BEV) | 484.407 |
| Híbridos plug-in (PHEV) | 83.987 |
| Híbridos convencionais (HEV) | 762.296 |
| Recarregáveis (BEV + PHEV) | 568.394 |
| Célula de combustível | 13 |
| Eletrificados por mil habitantes | 6,21 |

Série de jun/2020 a set/2026, 75 meses, por município, UF e Brasil. No primeiro
mês da série a frota eletrificada era de 41.332 veículos, 0,04% da frota — um
crescimento de **32 vezes em pouco mais de seis anos**, contra 26% de aumento da
frota total no mesmo período. Em dez/2020 eram 54.526 (0,05%), se a comparação
precisar fechar em ano cheio.

Os dois números vêm da mesma base (combustível). Não compare o início da série
pela base por modelo com o fim pela base por combustível: elas medem a
eletrificação de formas diferentes e a razão entre as duas é de 0,82.

Concentração: São Paulo tem 371.659 eletrificados (28% do total nacional), mas o
Distrito Federal lidera em intensidade, com 376 eletrificados por 10 mil
veículos contra 103 de São Paulo e 98 da média nacional. Por habitante a
distância é maior: 28,9 por mil no Distrito Federal, 8,7 em Santa Catarina, 8,0
em São Paulo e 6,2 no Brasil. A população é a estimativa de 2026 do IBGE.

Composição por tipo de veículo, pela base por modelo: 92,9% da frota
eletrificada é leve e 6,8% é moto. Entre os elétricos a bateria a moto é 16,9%
— e era quase dois terços, 64,6%, em dez/2020, com a ressalva de que naquele mês
a base por modelo só reconhece 64% dos elétricos. Cite a parte, não a contagem:
a base por modelo acha 18% menos eletrificados que a por combustível.

## Quatro ressalvas que acompanham estes números em qualquer uso

**Frota é estoque registrado, não emplacamento.** A variação mensal é saldo —
entradas menos baixas, mais correção de cadastro. Escrever "vendas" ou
"licenciamentos" a partir desses números é erro material. A base também inclui
veículos que já não circulam e nunca foram baixados; é característica do
RENAVAM. Medido: os eletrificados leves fabricados até 2018 não diminuíram entre
dez/2020 e set/2026.

**A divisão entre plug-in e híbrido convencional não vale pelo campo
combustível.** O rótulo HIBRIDO PLUG-IN pega 22% dos plug-ins que a ABVE contou
como vendidos; o resto entra como híbrido, junto com o híbrido leve e com as
motos híbridas da Yamaha (Ray ZR e Fluo 125 Hybrid, 17 mil em set/2026, quase
todas de 2026), que a ABVE não conta. A base por modelo reproduz as vendas por
tecnologia com diferença de 0,2% a 2,7% (item 8). Até
22/10/2026 este roteiro dizia o contrário: lia a razão de 4,5 entre os plug-ins
das duas bases como erro do nome do modelo, e a comparação com a ABVE mostrou que
o erro é do rótulo. Isso está em `resultados/LEIAME.md`, seções "Qual base usar" e
"Validação".

**Duas classes não existem no começo da série.** O código de combustível
plug-in só aparece no RENAVAM em **abr/2022**, e o de célula de combustível em
**nov/2022**. Antes disso a contagem é zero, e zero aqui é ausência de código,
não de veículo: `frota_hibrido` não cai quando o plug-in surge, ou seja, os
plug-in anteriores seguem contados como híbrido. Série de PHEV desde 2020 mostra
um zero falso seguido de salto artificial, e o HEV antes de abr/2022 está
inflado pelos plug-in. Para trajetória longa, use a frota eletrificada total ou
BEV; a separação PHEV/HEV só é comparável de abr/2022 em diante. Ambas as
classes estão marcadas em `resultados/qualidade_combustivel.csv`.

**3,6% da frota não tem combustível aproveitável no cadastro.** A fração sobe de
3,17% no início da série para 3,64% em set/2026 (coluna `sem_informacao` na
tabela de qualidade). É limite do RENAVAM, não erro de leitura, e é o piso de
incerteza de qualquer participação calculada sobre a frota total.

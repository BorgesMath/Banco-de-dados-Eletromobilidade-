/* Painel da base de eletromobilidade. Lê window.DEMOB (gerado por eletromobilidade/painel.py). */
(() => {
  "use strict";
  const D = window.DEMOB;

  // ---------- formatos ----------
  const L = d3.formatLocale({ decimal: ",", thousands: ".", grouping: [3], currency: ["R$ ", ""] });
  const fInt = L.format(",.0f");
  const f1 = L.format(",.1f");
  const f2 = L.format(",.2f");
  const fPct = (x) => (x == null || !isFinite(x) ? "—" : L.format(".1%")(x));
  const fVar = (x) => (x == null || !isFinite(x) ? "—" : (x > 0 ? "+" : "") + L.format(".1%")(x));
  const fCurto = (x) => (x >= 1e6 ? f1(x / 1e6) + " mi" : x >= 1e4 ? f1(x / 1e3) + " mil" : fInt(x));
  const fEixo = (x) => (x >= 1e6 ? L.format(",~r")(+(x / 1e6).toPrecision(3)) + " mi" : x >= 1e3 ? L.format(",~r")(+(x / 1e3).toPrecision(3)) + " mil" : fInt(x));
  const NOMES_MES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
  const rotMes = (s) => { const [a, m] = s.split("-"); return `${NOMES_MES[+m - 1]}/${a}`; };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---------- domínios ----------
  const MESES = D.meta.meses, N = MESES.length, ULTIMO = N - 1;
  const UFS = D.meta.ufs, SU = UFS.length - 1;            // [sigla, nome, região]; o último é o grupo sem UF
  const CL = D.meta.classes, TP = D.meta.tipos;
  const IDX_CL = Object.fromEntries(CL.map((c, i) => [c, i]));
  const ORDEM_CL = ["eletrico", "hibrido_plug_in", "hibrido", "celula_combustivel", "hibrido_leve"].map((c) => IDX_CL[c]);
  const ELETRIFICADAS = ["eletrico", "hibrido_plug_in", "hibrido", "celula_combustivel"].map((c) => IDX_CL[c]);
  const NOME_CL = { eletrico: "Elétrico (BEV)", hibrido_plug_in: "Híbrido plug-in (PHEV)", hibrido: "Híbrido (HEV)",
    celula_combustivel: "Célula de combustível", hibrido_leve: "Híbrido leve (MHEV)", eletrificada: "Eletrificada" };
  const CURTO_CL = { eletrico: "BEV", hibrido_plug_in: "PHEV", hibrido: "HEV", celula_combustivel: "Célula comb.",
    hibrido_leve: "MHEV", eletrificada: "Eletrificada" };
  const NOME_TP = { leve: "Leves", moto: "Motos", onibus: "Ônibus", caminhao: "Caminhões", outros: "Outros", sem_tipo: "Sem tipo" };
  const REGIOES = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"];
  const cor = (c) => `var(--s-${CL[c]})`;
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

  // frota total e população por mês e UF
  const TOTAL = Array.from({ length: N }, () => new Float64Array(UFS.length));
  const POP = Array.from({ length: N }, () => new Array(UFS.length).fill(null));
  D.uf_mes.m.forEach((m, i) => { TOTAL[m][D.uf_mes.u[i]] = D.uf_mes.total[i]; POP[m][D.uf_mes.u[i]] = D.uf_mes.pop[i]; });

  // ---------- estado ----------
  const PADRAO = () => ({ de: 0, ate: ULTIMO, ufs: new Set(), tipos: new Set(TP.map((_, i) => i)),
    classes: new Set(ELETRIFICADAS), semUF: false });
  const S = Object.assign(PADRAO(), { aba: "inicio", modoEvo: "abs", metricaUF: "abs", limiteMun: 50, limiteMod: 50,
    buscaMun: "", buscaMod: "", ordMun: ["v", -1], ordMod: ["v", -1], tabelaEvo: false });
  const ABAS = ["inicio", "evolucao", "estados", "municipios", "modelos", "validacao", "dados"];
  const FILTROS = { inicio: [], evolucao: ["periodo", "uf", "tipo", "classe", "semuf"], estados: ["mes", "tipo", "classe", "semuf-nota"],
    municipios: ["uf", "tipo", "classe"], modelos: ["uf", "tipo", "classe", "semuf"], validacao: [], dados: [] };

  // o grupo sem UF não pertence a UF nem a região: só entra com o Brasil inteiro
  const ufAtiva = (u) => (u === SU ? S.semUF && S.ufs.size === 0 : S.ufs.size === 0 || S.ufs.has(u));
  const todosTipos = () => S.tipos.size === TP.length;
  const classesOrdenadas = () => ORDEM_CL.filter((c) => S.classes.has(c));

  // ---------- agregações ----------
  function seriePorClasse(filtroUf = ufAtiva) {
    const out = CL.map(() => new Float64Array(N));
    const s = D.serie;
    for (let i = 0; i < s.v.length; i++) {
      if (filtroUf(s.u[i]) && S.tipos.has(s.t[i]) && S.classes.has(s.c[i])) out[s.c[i]][s.m[i]] += s.v[i];
    }
    return out;
  }
  function porUf(mes) {
    const out = UFS.map(() => new Float64Array(CL.length));
    const s = D.serie;
    for (let i = 0; i < s.v.length; i++) {
      if (s.m[i] === mes && S.tipos.has(s.t[i]) && S.classes.has(s.c[i])) out[s.u[i]][s.c[i]] += s.v[i];
    }
    return out;
  }
  function frotaEPop(mes, filtroUf = ufAtiva) {
    let total = 0, pop = 0, semPop = false;
    UFS.forEach((_, u) => {
      if (!filtroUf(u)) return;
      total += TOTAL[mes][u];
      if (u !== SU) { if (POP[mes][u] == null) semPop = true; else pop += POP[mes][u]; }
    });
    return { total, pop: semPop ? null : pop };
  }
  const soma = (arr) => arr.reduce((a, b) => a + b, 0);

  // ---------- tooltip ----------
  const dica = document.getElementById("tooltip");
  function mostrarDica(ev, html) {
    dica.innerHTML = html; dica.hidden = false;
    const r = dica.getBoundingClientRect(), pad = 14;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - pad;
    if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - pad;
    dica.style.left = Math.max(8, x) + "px"; dica.style.top = Math.max(8, y) + "px";
  }
  const esconderDica = () => { dica.hidden = true; };
  function linhasDica(partes, fmt = fInt, total = true) {
    const vivas = partes.filter((p) => p.v > 0 || partes.length <= 3);
    let html = vivas.map((p) => `<div class="l"><span class="amostra" style="background:${cor(p.c)}"></span><span>${CURTO_CL[CL[p.c]]}</span><span class="v">${fmt(p.v)}</span></div>`).join("");
    if (total && partes.length > 1) html += `<div class="tot"><span>Total</span><span>${fmt(soma(partes.map((p) => p.v)))}</span></div>`;
    return html;
  }

  // ---------- componentes ----------
  function cartoes(el, itens) {
    el.innerHTML = itens.map((c) => `<div class="cartao"><div class="rotulo">${c.rotulo}</div><div class="valor">${c.valor}</div>${c.det ? `<div class="det">${c.det}</div>` : ""}</div>`).join("");
  }
  function legenda(el, classes) {
    el.innerHTML = classes.map((c) => `<span><i class="amostra" style="background:${cor(c)}"></i>${NOME_CL[CL[c]]}</span>`).join("");
  }
  function segmentado(id, chave, aoMudar) {
    const el = document.getElementById(id);
    el.addEventListener("click", (ev) => {
      const b = ev.target.closest("button"); if (!b) return;
      S[chave] = b.dataset.v;
      el.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      aoMudar();
    });
  }

  function areaEmpilhada(el, ms, porClasse, chaves, pct) {
    el.innerHTML = "";
    const linhas = ms.map((i) => { const o = { i, tot: 0 }; chaves.forEach((c) => { o[c] = porClasse[c][i]; o.tot += o[c]; }); return o; });
    if (!chaves.length || !d3.max(linhas, (d) => d.tot)) { el.innerHTML = '<div class="vazio">Nada na seleção.</div>'; return; }
    const w = el.clientWidth, h = el.clientHeight, m = { t: 10, r: 14, b: 26, l: pct ? 44 : 62 };
    const pilha = d3.stack().keys(chaves).offset(pct ? d3.stackOffsetExpand : d3.stackOffsetNone)(linhas);
    const x = d3.scaleLinear().domain([ms[0], ms[ms.length - 1]]).range([m.l, w - m.r]);
    const y = d3.scaleLinear().domain([0, pct ? 1 : d3.max(linhas, (d) => d.tot)]).nice().range([h - m.b, m.t]);
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${w} ${h}`).attr("role", "img")
      .attr("aria-label", "Gráfico de área empilhada da frota por tecnologia");
    svg.append("g").attr("class", "eixo").attr("transform", `translate(${m.l},0)`)
      .call(d3.axisLeft(y).ticks(5).tickSize(-(w - m.l - m.r)).tickFormat(pct ? L.format(".0%") : fEixo))
      .call((g) => g.select(".domain").remove());
    const span = ms.length;
    const marcas = ms.filter((i) => (span > 30 ? MESES[i].endsWith("-01") : span > 12 ? /-(01|07)$/.test(MESES[i]) : true))
      .filter((_, k, arr) => span > 12 || k % Math.ceil(arr.length / 8) === 0);
    svg.append("g").attr("class", "eixo").attr("transform", `translate(0,${h - m.b})`)
      .call(d3.axisBottom(x).tickValues(marcas).tickSize(4).tickFormat((i) => (span > 30 ? MESES[i].slice(0, 4) : rotMes(MESES[i]))));
    const area = d3.area().x((d) => x(d.data.i)).y0((d) => y(d[0])).y1((d) => y(d[1])).curve(d3.curveMonotoneX);
    svg.append("g").selectAll("path").data(pilha).join("path").attr("d", area)
      .style("fill", (s) => cor(s.key)).style("stroke", "var(--superficie)").style("stroke-width", 1.5);
    const guia = svg.append("line").attr("y1", m.t).attr("y2", h - m.b).style("stroke", "var(--tinta-2)").style("stroke-width", 1).style("opacity", 0);
    svg.append("rect").attr("x", m.l).attr("y", m.t).attr("width", w - m.l - m.r).attr("height", h - m.t - m.b)
      .style("fill", "transparent")
      .on("pointermove", (ev) => {
        const [px] = d3.pointer(ev);
        const i = Math.round(x.invert(px)), d = linhas[Math.max(0, Math.min(linhas.length - 1, i - ms[0]))];
        guia.attr("x1", x(d.i)).attr("x2", x(d.i)).style("opacity", 1);
        const partes = chaves.slice().reverse().map((c) => ({ c, v: d[c] }));
        mostrarDica(ev, `<b>${rotMes(MESES[d.i])}</b>` + (pct
          ? linhasDica(partes.map((p) => ({ c: p.c, v: d.tot ? p.v / d.tot : 0 })), fPct, false)
          : linhasDica(partes)));
      })
      .on("pointerleave", () => { guia.style("opacity", 0); esconderDica(); });
  }

  function barras(el, linhas, classes, fmt, opcoes = {}) {
    // linhas: [{nome, partes: Float64Array por classe, sel?, alvo?}]
    const max = d3.max(linhas, (l) => soma(classes.map((c) => l.partes[c]))) || 1;
    el.innerHTML = `<div class="barras">${linhas.map((l, k) => {
      const tot = soma(classes.map((c) => l.partes[c]));
      const segs = classes.filter((c) => l.partes[c] > 0).map((c) => `<i style="width:calc(${(l.partes[c] / max) * 100}% - 2px);background:${cor(c)}"></i>`).join("");
      return `<div class="barra-linha${l.sel ? " sel" : ""}" data-k="${k}"><span class="nome" title="${esc(l.nome)}">${esc(l.nome)}</span><span class="trilho">${segs}</span><span class="num">${fmt(tot)}</span></div>`;
    }).join("")}</div>`;
    el.querySelectorAll(".barra-linha").forEach((row) => {
      const l = linhas[+row.dataset.k];
      row.addEventListener("pointermove", (ev) => mostrarDica(ev, `<b>${esc(l.titulo || l.nome)}</b>` + linhasDica(classes.slice().map((c) => ({ c, v: l.partes[c] })), fmt)));
      row.addEventListener("pointerleave", esconderDica);
      if (opcoes.clique) { row.style.cursor = "pointer"; row.addEventListener("click", () => opcoes.clique(l)); }
    });
  }

  function tabela(el, colunas, linhas, opcoes = {}) {
    const [chave, sentido] = opcoes.ordem || [null, 1];
    if (chave) {
      const col = colunas.find((c) => c.k === chave);
      linhas = linhas.slice().sort((a, b) => {
        const va = a[chave], vb = b[chave];
        if (va == null) return 1; if (vb == null) return -1;
        return (col && col.n ? va - vb : String(va).localeCompare(String(vb), "pt-BR")) * sentido;
      });
    }
    const visiveis = opcoes.limite ? linhas.slice(0, opcoes.limite) : linhas;
    const cab = colunas.map((c) => `<th class="${c.n ? "n " : ""}${c.ord !== false && opcoes.aoOrdenar ? "ord" : ""}" data-k="${c.k}"${c.k === chave ? ` aria-sort="${sentido > 0 ? "ascending" : "descending"}"` : ""}>${c.rot}</th>`).join("");
    const corpo = visiveis.map((l, i) => `<tr>${colunas.map((c) => `<td class="${c.n ? "n" : ""}">${c.html ? c.html(l, i) : c.fmt ? c.fmt(l[c.k]) : esc(l[c.k] ?? "")}</td>`).join("")}</tr>`).join("");
    el.innerHTML = `<table><thead><tr>${cab}</tr></thead><tbody>${corpo || `<tr><td colspan="${colunas.length}" class="vazio">Nada na seleção.</td></tr>`}</tbody></table>`;
    if (opcoes.aoOrdenar) el.querySelectorAll("th.ord").forEach((th) => th.addEventListener("click", () => {
      const k = th.dataset.k, col = colunas.find((c) => c.k === k);
      opcoes.aoOrdenar([k, k === chave ? -sentido : col.n ? -1 : 1]);
    }));
    return linhas.length;
  }
  const miniBarra = (partes, classes) => {
    const tot = soma(classes.map((c) => partes[c])) || 1;
    return `<span class="mini">${classes.filter((c) => partes[c] > 0).map((c) => `<i style="width:${(partes[c] / tot) * 100}%;background:${cor(c)}"></i>`).join("")}</span>`;
  };

  function baixarCSV(nome, cabecalho, linhas) {
    const celula = (v) => (typeof v === "number" ? String(v).replace(".", ",") : `"${String(v ?? "").replace(/"/g, '""')}"`);
    const texto = "﻿" + [cabecalho.join(";"), ...linhas.map((l) => l.map(celula).join(";"))].join("\r\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([texto], { type: "text/csv;charset=utf-8" }));
    a.download = nome; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---------- filtros ----------
  const barraFiltros = document.getElementById("filtros");
  function montarFiltros() {
    const opcoesMes = MESES.map((m, i) => `<option value="${i}">${rotMes(m)}</option>`).join("");
    const grupos = REGIOES.map((r) => `<div><h3><button data-regiao="${r}">${r}</button></h3>${UFS.slice(0, SU).map((u, i) => (u[2] === r ? `<label><input type="checkbox" value="${i}"> ${u[1]}</label>` : "")).join("")}</div>`).join("");
    barraFiltros.innerHTML = `
      <div class="campo" data-f="periodo"><span>Período</span><div class="periodo">
        <select id="f-de" aria-label="Mês inicial">${opcoesMes}</select><span>a</span><select id="f-ate" aria-label="Mês final">${opcoesMes}</select></div></div>
      <div class="campo" data-f="mes"><span>Mês</span><select id="f-mes" aria-label="Mês">${opcoesMes}</select></div>
      <div class="campo menu" data-f="uf"><span>UF</span><button class="menu-bt" id="f-uf-bt" aria-expanded="false" aria-haspopup="true"></button>
        <div class="menu-painel" id="f-uf-painel" hidden><div class="regioes">${grupos}</div>
        <div class="menu-rodape"><button class="limpar" id="f-uf-todas">Todas as UFs</button><button class="limpar" id="f-uf-fechar">Fechar</button></div></div></div>
      <div class="campo" data-f="tipo"><span>Tipo de veículo</span><div class="chips" id="f-tipo">${TP.map((t, i) => `<button class="chip" data-i="${i}">${NOME_TP[t]}</button>`).join("")}</div></div>
      <div class="campo" data-f="classe"><span>Tecnologia</span><div class="chips" id="f-classe">${ORDEM_CL.map((c) => `<button class="chip" data-i="${c}"><i class="amostra" style="background:${cor(c)}"></i>${CURTO_CL[CL[c]]}</button>`).join("")}</div></div>
      <div class="campo" data-f="semuf"><span>&nbsp;</span><label class="alternar" title="Só com todas as UFs: o grupo sem UF não pertence a nenhuma"><input type="checkbox" id="f-semuf"> Incluir frota sem UF</label></div>
      <div class="campo" data-f="semuf-nota"><span>&nbsp;</span><label class="alternar"><input type="checkbox" id="f-semuf2"> Mostrar grupo sem UF</label></div>
      <div class="campo" data-f="limpar"><span>&nbsp;</span><button class="limpar" id="f-limpar">Limpar filtros</button></div>`;

    const de = document.getElementById("f-de"), ate = document.getElementById("f-ate"), mes = document.getElementById("f-mes");
    de.addEventListener("change", () => { S.de = Math.min(+de.value, S.ate); atualizar(); });
    ate.addEventListener("change", () => { S.ate = Math.max(+ate.value, S.de); atualizar(); });
    mes.addEventListener("change", () => { S.ate = +mes.value; S.de = Math.min(S.de, S.ate); atualizar(); });
    const chips = (id, conjunto) => document.getElementById(id).addEventListener("click", (ev) => {
      const b = ev.target.closest(".chip"); if (!b) return;
      const i = +b.dataset.i, set = S[conjunto];
      if (ev.altKey || ev.ctrlKey || ev.metaKey) { set.clear(); set.add(i); }      // só este
      else if (set.has(i)) { if (set.size > 1) set.delete(i); } else set.add(i);
      atualizar();
    });
    chips("f-tipo", "tipos"); chips("f-classe", "classes");
    const semuf = (ev) => { S.semUF = ev.target.checked; atualizar(); };
    document.getElementById("f-semuf").addEventListener("change", semuf);
    document.getElementById("f-semuf2").addEventListener("change", semuf);
    document.getElementById("f-limpar").addEventListener("click", () => { Object.assign(S, PADRAO()); atualizar(); });

    const bt = document.getElementById("f-uf-bt"), painel = document.getElementById("f-uf-painel");
    const abrir = (sim) => { painel.hidden = !sim; bt.setAttribute("aria-expanded", String(sim)); };
    bt.addEventListener("click", () => abrir(painel.hidden));
    document.getElementById("f-uf-fechar").addEventListener("click", () => abrir(false));
    document.addEventListener("click", (ev) => { if (!painel.hidden && !ev.target.closest('[data-f="uf"]')) abrir(false); });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape") abrir(false); });
    painel.addEventListener("change", (ev) => {
      const u = +ev.target.value; ev.target.checked ? S.ufs.add(u) : S.ufs.delete(u); atualizar();
    });
    painel.addEventListener("click", (ev) => {
      const r = ev.target.closest("[data-regiao]"); if (!r) return;
      const daRegiao = UFS.slice(0, SU).map((u, i) => (u[2] === r.dataset.regiao ? i : -1)).filter((i) => i >= 0);
      const todas = daRegiao.every((i) => S.ufs.has(i));
      daRegiao.forEach((i) => (todas ? S.ufs.delete(i) : S.ufs.add(i))); atualizar();
    });
    document.getElementById("f-uf-todas").addEventListener("click", () => { S.ufs.clear(); atualizar(); });
  }
  function sincronizarFiltros() {
    const visiveis = new Set([...FILTROS[S.aba], ...(FILTROS[S.aba].length ? ["limpar"] : [])]);
    barraFiltros.hidden = !FILTROS[S.aba].length;
    barraFiltros.querySelectorAll("[data-f]").forEach((el) => { el.hidden = !visiveis.has(el.dataset.f); el.style.display = el.hidden ? "none" : ""; });
    document.getElementById("f-de").value = S.de; document.getElementById("f-ate").value = S.ate; document.getElementById("f-mes").value = S.ate;
    document.querySelectorAll("#f-tipo .chip").forEach((b) => b.setAttribute("aria-pressed", String(S.tipos.has(+b.dataset.i))));
    document.querySelectorAll("#f-classe .chip").forEach((b) => b.setAttribute("aria-pressed", String(S.classes.has(+b.dataset.i))));
    document.getElementById("f-semuf").checked = S.semUF; document.getElementById("f-semuf2").checked = S.semUF;
    document.querySelectorAll("#f-uf-painel input").forEach((c) => { c.checked = S.ufs.has(+c.value); });
    document.getElementById("f-uf-bt").textContent = rotuloUfs();
  }
  function rotuloUfs() {
    if (!S.ufs.size) return "Todas as UFs";
    if (S.ufs.size === 1) return UFS[[...S.ufs][0]][1];
    const regiao = REGIOES.find((r) => { const lista = UFS.slice(0, SU).map((u, i) => (u[2] === r ? i : -1)).filter((i) => i >= 0); return lista.length === S.ufs.size && lista.every((i) => S.ufs.has(i)); });
    return regiao ? `Região ${regiao}` : `${S.ufs.size} UFs`;
  }
  function descricao({ uf = true, semUf = true } = {}) {
    const partes = [];
    if (uf) partes.push(rotuloUfs() + (semUf && S.semUF && !S.ufs.size ? " + sem UF" : ""));
    partes.push(todosTipos() ? "todos os tipos" : [...S.tipos].sort().map((i) => NOME_TP[TP[i]].toLowerCase()).join(", "));
    const cls = classesOrdenadas();
    const eletr = ELETRIFICADAS.every((c) => S.classes.has(c));
    partes.push(eletr && cls.length === ELETRIFICADAS.length ? "eletrificada (BEV + PHEV + HEV + célula)" : cls.map((c) => CURTO_CL[CL[c]]).join(" + "));
    return partes.join(" · ");
  }

  // ---------- abas ----------
  function irPara(aba) {
    if (!ABAS.includes(aba)) aba = "inicio";
    S.aba = aba;
    document.querySelectorAll(".abas button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.aba === aba)));
    ABAS.forEach((a) => { document.getElementById("aba-" + a).hidden = a !== aba; });
    if (location.hash.slice(1) !== aba) history.replaceState(null, "", "#" + aba);
    atualizar();
  }
  const DESENHOS = {
    inicio: desenharInicio, evolucao: desenharEvolucao, estados: desenharEstados, municipios: desenharMunicipios,
    modelos: desenharModelos, validacao: desenharValidacao, dados: desenharDados,
  };
  function atualizar() { esconderDica(); sincronizarFiltros(); DESENHOS[S.aba](); }

  // ---------- Início ----------
  function desenharInicio() {
    const salvo = { ufs: S.ufs, tipos: S.tipos, classes: S.classes, semUF: S.semUF };
    Object.assign(S, { ufs: new Set(), tipos: new Set(TP.map((_, i) => i)), classes: new Set([...ELETRIFICADAS, IDX_CL.hibrido_leve]), semUF: false });
    const serie = seriePorClasse();
    const tipoXclasse = TP.map(() => new Float64Array(CL.length));
    const s = D.serie;
    for (let i = 0; i < s.v.length; i++) if (s.m[i] === ULTIMO && s.u[i] !== SU) tipoXclasse[s.t[i]][s.c[i]] += s.v[i];
    const { total, pop } = frotaEPop(ULTIMO);
    Object.assign(S, salvo);

    const eletr = (m) => soma(ELETRIFICADAS.map((c) => serie[c][m]));
    const agora = eletr(ULTIMO), ha12 = ULTIMO >= 12 ? eletr(ULTIMO - 12) : null;
    const bev = serie[IDX_CL.eletrico][ULTIMO];
    cartoes(document.getElementById("inicio-cartoes"), [
      { rotulo: `Frota eletrificada, ${rotMes(MESES[ULTIMO])}`, valor: fInt(agora), det: ha12 ? `<span class="sobe">${fVar(agora / ha12 - 1)}</span> em 12 meses` : "" },
      { rotulo: "Participação na frota total", valor: fPct(agora / total), det: `de ${fCurto(total)} veículos registrados` },
      { rotulo: "Elétricos (BEV)", valor: fInt(bev), det: `${fPct(bev / agora)} da frota eletrificada` },
      { rotulo: "Por mil habitantes", valor: pop ? f2((agora / pop) * 1000) : "—", det: "veículos eletrificados" },
      { rotulo: "Híbridos leves (MHEV)", valor: fInt(serie[IDX_CL.hibrido_leve][ULTIMO]), det: "fora da frota eletrificada" },
    ]);
    const ms = d3.range(0, N);
    areaEmpilhada(document.getElementById("inicio-grafico"), ms, serie, ELETRIFICADAS.filter((c) => d3.max(serie[c]) > 0), false);
    document.getElementById("inicio-comp-sub").textContent = `Por tipo de veículo, ${rotMes(MESES[ULTIMO])}, UFs informadas`;
    const linhas = TP.map((t, i) => ({ nome: NOME_TP[t], partes: tipoXclasse[i] }))
      .filter((l) => soma(ORDEM_CL.map((c) => l.partes[c])) > 0)
      .sort((a, b) => soma(ORDEM_CL.map((c) => b.partes[c])) - soma(ORDEM_CL.map((c) => a.partes[c])));
    const el = document.getElementById("inicio-composicao");
    el.innerHTML = '<div class="legenda" id="inicio-leg"></div><div id="inicio-barras"></div>';
    legenda(document.getElementById("inicio-leg"), ORDEM_CL);
    barras(document.getElementById("inicio-barras"), linhas, ORDEM_CL, fCurto);
  }

  // ---------- Evolução ----------
  function desenharEvolucao() {
    const serie = seriePorClasse();
    const classes = classesOrdenadas();
    const ms = d3.range(S.de, S.ate + 1);
    const tot = (m) => soma(classes.map((c) => serie[c][m]));
    const agora = tot(S.ate), base12 = S.ate >= 12 ? tot(S.ate - 12) : null, inicio = tot(S.de);
    const { total } = frotaEPop(S.ate);
    // por habitante só com as UFs informadas: o grupo sem UF não tem população
    const naUf = (u) => u !== SU && ufAtiva(u);
    const popValida = frotaEPop(S.ate, naUf).pop;
    const serieUf = S.semUF ? seriePorClasse(naUf) : serie;
    const agoraUf = soma(classes.map((c) => serieUf[c][S.ate]));
    cartoes(document.getElementById("evo-cartoes"), [
      { rotulo: `Frota em ${rotMes(MESES[S.ate])}`, valor: fInt(agora), det: classes.map((c) => CURTO_CL[CL[c]]).join(" + ") },
      { rotulo: "Variação em 12 meses", valor: base12 ? fVar(agora / base12 - 1) : "—", det: base12 ? `${fInt(agora - base12)} veículos a mais` : "série curta" },
      { rotulo: `Variação desde ${rotMes(MESES[S.de])}`, valor: inicio ? fVar(agora / inicio - 1) : "—", det: `${fInt(agora - inicio)} veículos a mais` },
      todosTipos()
        ? { rotulo: "Participação na frota total", valor: fPct(agora / total), det: `de ${fCurto(total)} veículos registrados` }
        : { rotulo: "Participação na frota total", valor: "—", det: "só com todos os tipos de veículo" },
      { rotulo: "Por mil habitantes", valor: popValida ? f2((agoraUf / popValida) * 1000) : "—", det: "UFs informadas" },
    ]);
    document.getElementById("evo-sub").textContent = descricao();
    document.getElementById("evo-titulo").textContent = S.modoEvo === "pct" ? "Composição por tecnologia" : "Frota por tecnologia";
    legenda(document.getElementById("evo-legenda"), classes);
    areaEmpilhada(document.getElementById("evo-grafico"), ms, serie, classes, S.modoEvo === "pct");

    const linhas = ms.slice().reverse().map((m) => ({ mes: rotMes(MESES[m]), ...Object.fromEntries(classes.map((c) => [CL[c], serie[c][m]])), total: tot(m) }));
    const tab = document.getElementById("evo-tabela");
    tab.hidden = !S.tabelaEvo;
    document.getElementById("evo-tabela-bt").textContent = S.tabelaEvo ? "Esconder tabela" : "Ver tabela";
    if (S.tabelaEvo) tabela(tab, [{ k: "mes", rot: "Mês" }, ...classes.map((c) => ({ k: CL[c], rot: CURTO_CL[CL[c]], n: true, fmt: fInt })), { k: "total", rot: "Total", n: true, fmt: fInt }], linhas);
    document.getElementById("evo-csv").onclick = () => baixarCSV("frota_eletrificada_selecao.csv",
      ["mes", "selecao", ...classes.map((c) => CL[c]), "total"],
      ms.map((m) => [MESES[m], descricao(), ...classes.map((c) => serie[c][m]), tot(m)]));
  }

  // ---------- Estados ----------
  const TILES = { RR: [2, 0], AP: [4, 0], AM: [1, 1], PA: [3, 1], MA: [4, 1], CE: [5, 1], RN: [6, 1], AC: [0, 2], RO: [1, 2],
    MT: [2, 2], TO: [3, 2], PI: [4, 2], PE: [5, 2], PB: [6, 2], MS: [2, 3], GO: [3, 3], DF: [4, 3], BA: [5, 3], AL: [6, 3],
    PR: [2, 4], SP: [3, 4], MG: [4, 4], ES: [5, 4], SE: [6, 4], SC: [2, 5], RJ: [4, 5], RS: [2, 6] };
  function metricaUf(partesUf, u, classes) {
    const v = soma(classes.map((c) => partesUf[u][c]));
    if (S.metricaUF === "abs") return v;
    if (S.metricaUF === "hab") { const p = POP[S.ate][u]; return p ? (v / p) * 1000 : null; }
    return todosTipos() && TOTAL[S.ate][u] ? v / TOTAL[S.ate][u] : null;
  }
  function desenharEstados() {
    const classes = classesOrdenadas();
    const partes = porUf(S.ate);
    const fmt = S.metricaUF === "abs" ? fInt : S.metricaUF === "hab" ? f2 : fPct;
    const nomeMetrica = { abs: "veículos", hab: "veículos por mil habitantes", frota: "% da frota total da UF" }[S.metricaUF];
    const sub = `${rotMes(MESES[S.ate])} · ${descricao({ uf: false })} · ${nomeMetrica}`;
    document.getElementById("uf-sub").textContent = sub;
    document.getElementById("uf-rank-sub").textContent = S.metricaUF === "frota" && !todosTipos() ? "% da frota só com todos os tipos de veículo" : sub;
    legenda(document.getElementById("uf-legenda"), classes);

    const valores = UFS.slice(0, SU).map((u, i) => ({ sigla: u[0], nome: u[1], u: i, v: metricaUf(partes, i, classes) }));
    const max = d3.max(valores, (d) => d.v) || 1;
    const escala = (S.metricaUF === "abs" ? d3.scaleSequentialSqrt() : d3.scaleSequential())
      .domain([0, max]).interpolator(d3.interpolateLab(css("--seq-0"), css("--seq-1")));
    const el = document.getElementById("uf-mapa");
    el.innerHTML = "";
    const lado = 60, alto = 50;
    const svg = d3.select(el).append("svg").attr("viewBox", `0 0 ${7 * lado} ${7 * alto + 4}`).attr("role", "img")
      .attr("aria-label", "Mapa das UFs em grade").style("max-height", "460px");
    const g = svg.selectAll("g").data(valores).join("g")
      .attr("class", (d) => "tile" + (S.ufs.has(d.u) ? " sel" : ""))
      .attr("transform", (d) => `translate(${TILES[d.sigla][0] * lado},${TILES[d.sigla][1] * alto})`)
      .on("pointermove", (ev, d) => mostrarDica(ev, `<b>${d.nome}</b>${linhasDica(classes.map((c) => ({ c, v: partes[d.u][c] })))}<div class="tot"><span>${nomeMetrica}</span><span>${d.v == null ? "—" : fmt(d.v)}</span></div>`))
      .on("pointerleave", esconderDica)
      .on("click", (_, d) => { S.ufs.has(d.u) ? S.ufs.delete(d.u) : S.ufs.add(d.u); atualizar(); });
    g.append("rect").attr("x", 2).attr("y", 2).attr("width", lado - 4).attr("height", alto - 4).attr("rx", 5)
      .style("fill", (d) => (d.v == null ? "var(--grade)" : escala(d.v)));
    const clara = (d) => d.v != null && (S.metricaUF === "abs" ? Math.sqrt(d.v / max) : d.v / max) > 0.55;
    g.append("text").attr("x", lado / 2).attr("y", alto / 2 - 2).attr("text-anchor", "middle")
      .style("fill", (d) => (clara(d) ? "#fff" : "var(--tinta)")).text((d) => d.sigla);
    g.append("text").attr("class", "v").attr("x", lado / 2).attr("y", alto / 2 + 12).attr("text-anchor", "middle")
      .style("fill", (d) => (clara(d) ? "#fff" : "var(--tinta-2)"))
      .text((d) => (d.v == null ? "—" : S.metricaUF === "abs" ? fCurto(d.v) : S.metricaUF === "hab" ? f1(d.v) : L.format(".1%")(d.v)));
    const escalaEl = document.createElement("div");
    escalaEl.className = "escala";
    escalaEl.innerHTML = `<span>0</span><i></i><span>${fmt(max)}</span>`;
    el.appendChild(escalaEl);

    const linhas = valores.filter((d) => d.v != null).sort((a, b) => b.v - a.v).map((d) => {
      const p = new Float64Array(CL.length);
      classes.forEach((c) => {
        const x = partes[d.u][c];
        p[c] = S.metricaUF === "abs" ? x : S.metricaUF === "hab" ? (x / POP[S.ate][d.u]) * 1000 : x / TOTAL[S.ate][d.u];
      });
      return { nome: d.nome, titulo: `${d.nome} (${nomeMetrica})`, partes: p, sel: S.ufs.has(d.u), u: d.u };
    });
    if (S.semUF && S.metricaUF === "abs") {
      linhas.push({ nome: "Sem UF informada", titulo: "Sem UF informada (estoque ainda não emplacado)", partes: partes[SU] });
    }
    barras(document.getElementById("uf-ranking"), linhas, classes, fmt, {
      clique: (l) => { if (l.u == null) return; S.ufs.has(l.u) ? S.ufs.delete(l.u) : S.ufs.add(l.u); atualizar(); } });
  }

  // ---------- Municípios ----------
  function desenharMunicipios() {
    const classes = classesOrdenadas();
    const M = D.municipios, partes = M.cod.map(() => new Float64Array(CL.length));
    for (let k = 0; k < M.v.length; k++) {
      const i = M.i[k];
      if (ufAtiva(M.u[i]) && S.tipos.has(M.t[k]) && S.classes.has(M.c[k])) partes[i][M.c[k]] += M.v[k];
    }
    const busca = S.buscaMun.trim().toLocaleLowerCase("pt-BR").normalize("NFD").replace(/[̀-ͯ]/g, "");
    let linhas = M.cod.map((cod, i) => {
      const v = soma(classes.map((c) => partes[i][c]));
      return { cod, nome: M.nome[i], uf: UFS[M.u[i]][0], u: M.u[i], v, partes: partes[i],
        hab: M.pop[i] ? (v / M.pop[i]) * 1000 : null, frota: todosTipos() && M.total[i] ? v / M.total[i] : null };
    }).filter((l) => l.v > 0 && ufAtiva(l.u));
    const comFrota = linhas.length, totalSel = soma(linhas.map((l) => l.v));
    const topo = linhas.slice().sort((a, b) => b.v - a.v);
    const top10 = soma(topo.slice(0, 10).map((l) => l.v));
    cartoes(document.getElementById("mun-cartoes"), [
      { rotulo: "Municípios com ao menos um veículo", valor: fInt(comFrota), det: `de ${fInt(M.cod.length)} com algum eletrificado ou MHEV` },
      { rotulo: "Frota na seleção", valor: fInt(totalSel), det: rotMes(MESES[ULTIMO]) },
      { rotulo: "Os 10 maiores municípios", valor: fPct(totalSel ? top10 / totalSel : null), det: "da frota da seleção" },
      { rotulo: "Maior frota", valor: topo[0] ? esc(topo[0].nome) : "—", det: topo[0] ? `${topo[0].uf} · ${fInt(topo[0].v)} veículos` : "" },
    ]);
    if (busca) linhas = linhas.filter((l) => l.nome.toLocaleLowerCase("pt-BR").normalize("NFD").replace(/[̀-ͯ]/g, "").includes(busca));
    document.getElementById("mun-sub").textContent = `${rotMes(MESES[ULTIMO])} · ${descricao({ semUf: false })}`;
    const total = tabela(document.getElementById("mun-tabela"), [
      { k: "pos", rot: "#", n: true, ord: false, html: (_, i) => `<span class="etiqueta">${i + 1}</span>` },
      { k: "nome", rot: "Município" }, { k: "uf", rot: "UF" },
      { k: "v", rot: "Veículos", n: true, fmt: fInt },
      { k: "hab", rot: "Por mil hab.", n: true, fmt: (x) => (x == null ? "—" : f2(x)) },
      { k: "frota", rot: "% da frota", n: true, fmt: (x) => (x == null ? "—" : L.format(".2%")(x)) },
      { k: "comp", rot: "Composição", ord: false, html: (l) => miniBarra(l.partes, classes) },
    ], linhas, { ordem: S.ordMun, limite: S.limiteMun, aoOrdenar: (o) => { S.ordMun = o; desenharMunicipios(); } });
    const mais = document.getElementById("mun-mais");
    mais.hidden = total <= S.limiteMun;
    mais.onclick = () => { S.limiteMun += 100; desenharMunicipios(); };
    document.getElementById("mun-csv").onclick = () => baixarCSV("municipios_selecao.csv",
      ["cod_municipio_ibge", "municipio", "uf", ...classes.map((c) => CL[c]), "total", "por_mil_habitantes", "participacao_frota"],
      linhas.sort((a, b) => b.v - a.v).map((l) => [l.cod, l.nome, l.uf, ...classes.map((c) => l.partes[c]), l.v, l.hab ?? "", l.frota ?? ""]));
  }

  // ---------- Marcas e modelos ----------
  function desenharModelos() {
    const classes = classesOrdenadas();
    const Mo = D.modelos, partes = Mo.nome.map(() => new Float64Array(CL.length)), tipos = Mo.nome.map(() => new Float64Array(TP.length));
    for (let k = 0; k < Mo.v.length; k++) {
      if (ufAtiva(Mo.u[k]) && S.tipos.has(Mo.t[k]) && S.classes.has(Mo.c[k])) { partes[Mo.i[k]][Mo.c[k]] += Mo.v[k]; tipos[Mo.i[k]][Mo.t[k]] += Mo.v[k]; }
    }
    const porMarca = new Map();
    Mo.nome.forEach((_, i) => {
      const m = Mo.marca[i];
      if (!porMarca.has(m)) porMarca.set(m, new Float64Array(CL.length));
      const p = porMarca.get(m); classes.forEach((c) => { p[c] += partes[i][c]; });
    });
    const marcas = [...porMarca].map(([nome, p]) => ({ nome, partes: p, v: soma(classes.map((c) => p[c])) })).filter((m) => m.v > 0).sort((a, b) => b.v - a.v);
    const topo = marcas.slice(0, 15);
    if (marcas.length > 15) {
      const resto = new Float64Array(CL.length);
      marcas.slice(15).forEach((m) => classes.forEach((c) => { resto[c] += m.partes[c]; }));
      topo.push({ nome: `Demais ${marcas.length - 15} marcas`, partes: resto });
    }
    document.getElementById("marca-sub").textContent = `${rotMes(MESES[ULTIMO])} · ${descricao()}`;
    legenda(document.getElementById("marca-legenda"), classes);
    barras(document.getElementById("marca-grafico"), topo, classes, fInt, {
      clique: (l) => { if (l.nome.startsWith("Demais")) return; S.buscaMod = l.nome; document.getElementById("modelo-busca").value = l.nome; desenharModelos(); } });

    const busca = S.buscaMod.trim().toLocaleUpperCase("pt-BR");
    let linhas = Mo.nome.map((nome, i) => {
      const v = soma(classes.map((c) => partes[i][c]));
      const dom = classes.reduce((a, c) => (partes[i][c] > partes[i][a] ? c : a), classes[0]);
      const tipo = d3.maxIndex(tipos[i]);
      return { nome, marca: Mo.marca[i], v, tecnologia: CURTO_CL[CL[dom]], tipo: NOME_TP[TP[tipo]], partes: partes[i] };
    }).filter((l) => l.v > 0);
    if (busca) linhas = linhas.filter((l) => l.nome.includes(busca) || l.marca.includes(busca));
    document.getElementById("modelo-sub").textContent = `Texto de marca/modelo do RENAVAM, ${rotMes(MESES[ULTIMO])}`;
    const total = tabela(document.getElementById("modelo-tabela"), [
      { k: "nome", rot: "Modelo" }, { k: "marca", rot: "Marca" },
      { k: "tecnologia", rot: "Tecnologia", html: (l) => `${miniBarra(l.partes, classes).replace('class="mini"', 'class="mini" style="display:inline-flex;min-width:0;width:10px;vertical-align:middle;margin-right:6px"')}${l.tecnologia}` },
      { k: "tipo", rot: "Tipo" }, { k: "v", rot: "Veículos", n: true, fmt: fInt },
    ], linhas, { ordem: S.ordMod, limite: S.limiteMod, aoOrdenar: (o) => { S.ordMod = o; desenharModelos(); } });
    const mais = document.getElementById("modelo-mais");
    mais.hidden = total <= S.limiteMod;
    mais.onclick = () => { S.limiteMod += 100; desenharModelos(); };
    document.getElementById("modelo-csv").onclick = () => baixarCSV("modelos_selecao.csv",
      ["marca_modelo", "marca", ...classes.map((c) => CL[c]), "total"],
      linhas.sort((a, b) => b.v - a.v).map((l) => [l.nome, l.marca, ...classes.map((c) => l.partes[c]), l.v]));
  }

  // ---------- Validação ----------
  function desenharValidacao() {
    const A = D.abve;
    if (!A || !A.tecnologia) { document.getElementById("val-tabela").innerHTML = '<div class="vazio">Sem dados da ABVE.</div>'; return; }
    const desvio = (cresc, vendas) => {
      if (!vendas) return "—";
      const d = cresc / vendas - 1;
      return `<span class="desvio${Math.abs(d) > 0.05 ? " alto" : ""}">${fVar(d)}</span>`;
    };
    const ordemCl = ["eletrificada", "eletrico", "hibrido_plug_in", "hibrido", "hibrido_leve"];
    const acum = A.tecnologia.filter((r) => r[1] === "acumulado");
    const eletr = acum.find((r) => r[2] === "eletrificada");
    if (eletr) cartoes(document.getElementById("val-cartoes"), [
      { rotulo: `Vendas da ABVE, ${A.periodo}`, valor: fInt(eletr[3]), det: "eletrificados leves (BEV + PHEV + HEV)" },
      { rotulo: "Crescimento da frota na base", valor: fInt(eletr[4]), det: "mesmo período, UFs informadas" },
      { rotulo: "Diferença", valor: fVar(eletr[4] / eletr[3] - 1), det: "contra a ABVE publicada" },
      { rotulo: "Diferença no rótulo atual", valor: fVar(eletr[4] / eletr[5] - 1), det: "ABVE com o histórico reclassificado" },
    ]);
    const linhas = A.tecnologia.filter((r) => ordemCl.includes(r[2]))
      .sort((a, b) => (b[1] === "acumulado") - (a[1] === "acumulado") || a[0].localeCompare(b[0])
        || ordemCl.indexOf(a[2]) - ordemCl.indexOf(b[2]))
      .map((r) => ({ periodo: r[1] === "acumulado" ? `${r[0]} (acumulado)` : r[0], classe: NOME_CL[r[2]], vendas: r[3], cresc: r[4], rot: r[5],
        forte: r[2] === "eletrificada" }));
    tabela(document.getElementById("val-tabela"), [
      { k: "periodo", rot: "Período", html: (l) => (l.forte ? `<b>${esc(l.periodo)}</b>` : `<span class="etiqueta">${esc(l.periodo)}</span>`) },
      { k: "classe", rot: "Tecnologia", html: (l) => (l.forte ? `<b>${l.classe}</b>` : l.classe) },
      { k: "vendas", rot: "Vendas ABVE", n: true, fmt: fInt }, { k: "cresc", rot: "Crescimento da frota", n: true, fmt: fInt },
      { k: "d", rot: "Diferença", n: true, html: (l) => desvio(l.cresc, l.vendas) },
      { k: "d2", rot: "No rótulo atual", n: true, html: (l) => desvio(l.cresc, l.rot) },
    ], linhas);
    document.getElementById("val-uf-sub").textContent = `Eletrificados leves, ${A.uf_periodo} (acumulado)`;
    const ufs = A.uf.filter((r) => r[1] === "eletrificada").map((r) => ({ uf: r[0], vendas: r[2], cresc: r[3], rot: r[4], d: r[2] ? r[3] / r[2] - 1 : null }));
    tabela(document.getElementById("val-uf"), [
      { k: "uf", rot: "UF" }, { k: "vendas", rot: "Vendas ABVE", n: true, fmt: fInt }, { k: "cresc", rot: "Crescimento", n: true, fmt: fInt },
      { k: "d", rot: "Diferença", n: true, html: (l) => desvio(l.cresc, l.vendas) },
    ], ufs, { ordem: S.ordValUf || ["vendas", -1], aoOrdenar: (o) => { S.ordValUf = o; desenharValidacao(); } });
  }

  // ---------- Dados ----------
  function desenharDados() {
    const kb = (b) => (b > 1e6 ? f1(b / 1e6) + " MB" : fInt(Math.max(1, b / 1e3)) + " kB");
    tabela(document.getElementById("dados-tratados"), [
      { k: "arquivo", rot: "Arquivo", html: (l) => `<a href="${esc(l.url)}" download>${esc(l.arquivo)}</a>` },
      { k: "descricao", rot: "Conteúdo", html: (l) => `<span class="etiqueta">${esc(l.descricao)}</span>` },
      { k: "bytes", rot: "Tamanho", n: true, fmt: kb },
    ], D.arquivos);
    const link = (f) => {
      if (!f) return "—";
      const texto = `${f.arquivo.split(".").pop()} · ${f.origem || "fonte"}`;
      return f.url ? `<a href="${esc(f.url)}" title="${esc(f.arquivo)}">${esc(texto)}</a>` : `<span title="${esc(f.arquivo)}">${esc(texto)}</span>`;
    };
    const obs = (r) => [r.modelo, r.combustivel].filter((f) => f && (f.ajuste || f.incluido === false))
      .map((f) => esc(f.ajuste || "fora da série")).join("; ");
    const brutos = document.getElementById("dados-brutos");
    if (!D.fontes.length) brutos.innerHTML = '<div class="vazio">Lista de arquivos não gerada (rode com --atualizar-fontes).</div>';
    else tabela(brutos, [
      { k: "mes", rot: "Mês", fmt: rotMes },
      { k: "modelo", rot: "Por marca/modelo", html: (r) => link(r.modelo) },
      { k: "combustivel", rot: "Por combustível", html: (r) => link(r.combustivel) },
      { k: "obs", rot: "Observação", html: (r) => `<span class="etiqueta">${obs(r)}</span>` },
    ], D.fontes.slice().reverse());
    const doc = (nome) => (D.arquivos.find((a) => a.arquivo === nome) || {}).url || D.meta.repositorio;
    document.getElementById("link-leiame").href = doc("LEIAME.md");
    document.getElementById("link-dicionario").href = doc("DICIONARIO.md");
    document.getElementById("link-repo").href = D.meta.repositorio;
  }

  // ---------- início ----------
  document.getElementById("cobertura").textContent = `${rotMes(MESES[0])} a ${rotMes(MESES[ULTIMO])}`;
  document.getElementById("gerado").innerHTML = `Atualizado em ${D.meta.gerado.split("-").reverse().join("/")} · <a href="${D.meta.repositorio}">repositório</a>`;
  montarFiltros();
  segmentado("evo-modo", "modoEvo", desenharEvolucao);
  segmentado("uf-metrica", "metricaUF", desenharEstados);
  document.getElementById("evo-tabela-bt").addEventListener("click", () => { S.tabelaEvo = !S.tabelaEvo; desenharEvolucao(); });
  document.getElementById("mun-busca").addEventListener("input", (ev) => { S.buscaMun = ev.target.value; S.limiteMun = 50; desenharMunicipios(); });
  document.getElementById("modelo-busca").addEventListener("input", (ev) => { S.buscaMod = ev.target.value; S.limiteMod = 50; desenharModelos(); });
  document.querySelector(".abas").addEventListener("click", (ev) => { const b = ev.target.closest("button"); if (b) irPara(b.dataset.aba); });
  document.addEventListener("click", (ev) => { const a = ev.target.closest("[data-ir]"); if (a) { ev.preventDefault(); irPara(a.dataset.ir); } });
  window.addEventListener("hashchange", () => irPara(location.hash.slice(1)));
  let espera;
  window.addEventListener("resize", () => { clearTimeout(espera); espera = setTimeout(() => DESENHOS[S.aba](), 150); });
  irPara(location.hash.slice(1) || "inicio");
})();

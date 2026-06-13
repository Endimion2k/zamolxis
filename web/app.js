"use strict";
let DATA = null;
let tab = "colective";

const $ = (s, r = document) => r.querySelector(s);
const main = () => document.getElementById("main");
const esc = (s) => (s == null ? "" : String(s).replace(/[&<>"]/g, c => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])));
const norm = (s) => (s || "").toLowerCase()
  .normalize("NFKD").replace(/[̀-ͯ]/g, "");

function domLabel(cod) { return (DATA.domenii && DATA.domenii[cod]) || cod || "—"; }
function nivLabel(cod) { return (DATA.niveluri && DATA.niveluri[cod]) || cod; }

// ---- boot ----
fetch("data.json").then(r => r.json()).then(d => {
  DATA = d;
  document.getElementById("generat").textContent = d.generat_la || "—";
  document.querySelectorAll("nav button").forEach(b =>
    b.addEventListener("click", () => { tab = b.dataset.tab; setActive(); render(); }));
  render();
}).catch(e => { main().innerHTML =
  `<div class="card"><p class="muted">Nu am putut încărca datele (${esc(e.message)}).</p></div>`; });

function setActive() {
  document.querySelectorAll("nav button").forEach(b =>
    b.classList.toggle("activ", b.dataset.tab === tab));
}

function render() {
  if (tab === "despre") return renderDespre();
  if (tab === "valuri") return renderValuri();
  return renderColective();
}

// ---- filtre comune (state din DOM) ----
function filtru(items, { q, domeniu, nivel }, campuri) {
  const nq = norm(q);
  return items.filter(it => {
    if (domeniu && it.domeniu !== domeniu) return false;
    if (nivel && it.nivel !== nivel) return false;
    if (nq) {
      const hay = norm(campuri.map(c => it[c]).join(" "));
      if (!hay.includes(nq)) return false;
    }
    return true;
  });
}

function domeniiOptions(items, sel) {
  const set = [...new Set(items.map(i => i.domeniu).filter(Boolean))].sort();
  return `<option value="">Toate domeniile</option>` + set.map(d =>
    `<option value="${d}" ${d === sel ? "selected" : ""}>${esc(domLabel(d))}</option>`).join("");
}

// ---- ACȚIUNI COLECTIVE ----
function renderColective() {
  const s = DATA.stats || {};
  main().innerHTML = `
    <div class="card hero">
      <h2>Ești posibil păgubit? Verifică.</h2>
      <p>Caută o firmă, o instituție sau problema ta (ex: <i>bancă, clauze abuzive, mediu</i>)
        și află dacă există deja un proces colectiv la care te poți raporta.</p>
      <div class="searchbar">
        <input id="q" type="text" placeholder="Caută firma, instituția sau problema ta…">
        <button onclick="render()">Caută</button>
      </div>
    </div>
    <div class="card">
      <span class="stat"><b>${(DATA.cazuri||[]).length}</b><br><span class="muted">acțiuni colective</span></span>
      <span class="stat"><b>${s.confirmate||0}</b><br><span class="muted">confirmate</span></span>
      <span class="stat"><b>${(DATA.grupuri||[]).length}</b><br><span class="muted">valuri de procese</span></span>
    </div>
    <div class="card">
      <div class="filters">
        <div><label>Domeniu</label><select id="fd">${domeniiOptions(DATA.cazuri,"")}</select></div>
        <div><label>Stare</label><select id="fn">
          <option value="">Toate</option><option value="confirmat">Confirmat</option><option value="revizuire">De verificat</option>
        </select></div>
      </div>
    </div>
    <div id="rez"></div>`;
  wire(["q", "fd", "fn"]);
  listColective();
}

function listColective() {
  const f = { q: val("q"), domeniu: val("fd"), nivel: val("fn") };
  const rows = filtru(DATA.cazuri || [], f, ["numar", "obiect", "rezumat", "instanta"])
    .sort((a, b) => b.scor - a.scor);
  $("#rez").innerHTML = rows.length ? `
    <div class="card" style="padding:0;overflow:hidden"><table>
      <thead><tr><th>Dosar</th><th>Domeniu</th><th>Rezumat</th><th>Stare</th></tr></thead>
      <tbody>${rows.slice(0, 200).map((c, i) => `
        <tr class="clickabil" onclick="detaliuCaz(${DATA.cazuri.indexOf(c)})">
          <td><b>${esc(c.numar)}</b><br><span class="num">${esc(c.instanta)}</span></td>
          <td>${c.domeniu ? `<span class="badge b-dom">${esc(domLabel(c.domeniu))}</span>` : "—"}</td>
          <td>${esc(c.rezumat || c.obiect)}</td>
          <td><span class="badge b-${esc(c.nivel)}">${esc(nivLabel(c.nivel))}</span><div class="num">scor ${c.scor}</div></td>
        </tr>`).join("")}</tbody></table></div>
    <p class="muted">${rows.length} rezultate${rows.length > 200 ? " (primele 200)" : ""}.</p>`
    : `<div class="card"><p class="muted">Niciun rezultat. Încearcă alt cuvânt sau vezi valurile de procese.</p></div>`;
}

// ---- VALURI ----
function renderValuri() {
  main().innerHTML = `
    <div class="card hero">
      <h2>Valuri de procese identice</h2>
      <p>Mii de oameni dau în judecată separat aceeași instituție/firmă pentru aceeași
        problemă. Vezi dacă <b>ai și tu același caz</b>.</p>
      <div class="searchbar">
        <input id="q" type="text" placeholder="Caută instituția, firma sau tipul de problemă…">
        <button onclick="render()">Caută</button>
      </div>
    </div>
    <div class="card">
      <div class="filters"><div><label>Domeniu</label>
        <select id="fd">${domeniiOptions(DATA.grupuri,"")}</select></div></div>
    </div>
    <div id="rez"></div>`;
  wire(["q", "fd"]);
  listValuri();
}

function listValuri() {
  const f = { q: val("q"), domeniu: val("fd") };
  const rows = filtru(DATA.grupuri || [], f, ["parat", "obiect_tip"])
    .sort((a, b) => b.nr_dosare - a.nr_dosare);
  $("#rez").innerHTML = rows.length ? `
    <div class="card" style="padding:0;overflow:hidden"><table>
      <thead><tr><th>Problema</th><th>Împotriva</th><th>Domeniu</th><th>Dosare</th></tr></thead>
      <tbody>${rows.slice(0, 200).map(g => `
        <tr class="clickabil" onclick="detaliuGrup(${DATA.grupuri.indexOf(g)})">
          <td><b>${esc(g.obiect_tip)}</b></td>
          <td>${esc(g.parat)}</td>
          <td>${g.domeniu ? `<span class="badge b-dom">${esc(domLabel(g.domeniu))}</span>` : "—"}</td>
          <td><b>${g.aprox ? "≥" : ""}${g.nr_dosare}</b></td>
        </tr>`).join("")}</tbody></table></div>
    <p class="muted">${rows.length} valuri.</p>`
    : `<div class="card"><p class="muted">Niciun val pentru filtrele alese.</p></div>`;
}

// ---- DESPRE ----
function renderDespre() {
  main().innerHTML = `
    <div class="card"><h2 style="margin-top:0">De ce „Zamolxis"</h2>
      <p>Zamolxis era, în tradiția daco-getică, divinitatea legii și a dreptății — cel care aduna
        oamenii și le dădea legile. Platforma face același lucru: <b>strânge laolaltă oamenii
        păgubiți</b> și le arată unde stă dreptatea, în datele publice ale instanțelor.</p></div>
    <div class="card"><h2 style="margin-top:0">Ce găsești aici</h2>
      <p><b>Acțiuni colective</b> — procese pornite de asociații/ONG-uri pentru un grup.</p>
      <p><b>Valuri de procese identice</b> — mii de dosare individuale separate cu aceeași
        problemă vs. aceeași instituție/firmă (pensii, taxe, apartamente nelivrate ca la Nordis).</p></div>
    <div class="card" style="background:#fbf3df;border-color:#e9d6a3"><p style="margin:0;color:#6b521a">
      <b>Important.</b> Informație orientativă, <b>nu</b> consultanță juridică. Clasificarea automată
      poate greși („de verificat"). Consultă un avocat și verifică la
      <a href="https://portal.just.ro" target="_blank" rel="noopener">portal.just.ro</a>.</p></div>`;
}

// ---- detalii (modal) ----
function inchide() { document.getElementById("detaliu").innerHTML = ""; }
function modal(html) {
  document.getElementById("detaliu").innerHTML =
    `<div class="overlay" onclick="if(event.target===this)inchide()"><div class="modal">
      <button class="x" onclick="inchide()">×</button>${html}</div></div>`;
}

function detaliuCaz(i) {
  const c = DATA.cazuri[i]; if (!c) return;
  modal(`
    <h2 style="margin:0 4px 4px 0">Dosar ${esc(c.numar)}</h2>
    <p class="muted">${esc(c.instanta)}${c.stadiu ? " · " + esc(c.stadiu) : ""}
      ${c.domeniu ? ` · <span class="badge b-dom">${esc(domLabel(c.domeniu))}</span>` : ""}
      · <span class="badge b-${esc(c.nivel)}">${esc(nivLabel(c.nivel))} · scor ${c.scor}</span></p>
    ${c.rezumat ? `<p style="font-size:17px"><b>${esc(c.rezumat)}</b></p>` : ""}
    <p><span class="muted">Obiect:</span><br>${esc(c.obiect || "—")}</p>
    ${(c.motive && c.motive.length) ? `<p class="muted">De ce a fost marcat:</p><ul>${c.motive.map(m=>`<li>${esc(m)}</li>`).join("")}</ul>` : ""}
    ${(c.parti && c.parti.length) ? `<h3>Părți</h3><table><tbody>${c.parti.map(p=>`<tr><td>${esc(p.nume)}</td><td class="muted">${esc(p.calitate)}</td></tr>`).join("")}</tbody></table><p class="muted">Persoanele fizice sunt afișate cu inițiale.</p>` : ""}
    <p style="margin-top:14px"><a href="https://portal.just.ro" target="_blank" rel="noopener">🔎 Verifică dosarul ${esc(c.numar)} pe portal.just.ro →</a></p>`);
}

function detaliuGrup(i) {
  const g = DATA.grupuri[i]; if (!g) return;
  const inst = g.instante ? Object.entries(g.instante).sort((a,b)=>b[1]-a[1]) : [];
  modal(`
    <h2 style="margin:0 4px 4px 0">${esc(g.obiect_tip)}</h2>
    <p class="muted">împotriva <b>${esc(g.parat)}</b>${g.domeniu ? ` · <span class="badge b-dom">${esc(domLabel(g.domeniu))}</span>` : ""}</p>
    <p style="font-size:19px"><b>${g.aprox ? "≥ " : ""}${g.nr_dosare} dosare</b> cu aceeași problemă</p>
    ${g.prima_data ? `<p class="muted">Perioadă: ${esc(g.prima_data)} → ${esc(g.ultima_data)}</p>` : ""}
    <div class="card" style="background:#f0f5fb;border-color:#cfe0f2"><p style="margin:0">💡 Dacă ai și tu un astfel de litigiu împotriva <b>${esc(g.parat)}</b>, nu ești singur — sunt cel puțin ${g.nr_dosare} dosare similare.</p></div>
    ${inst.length ? `<h3>Pe instanțe</h3><table><tbody>${inst.slice(0,12).map(([k,v])=>`<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join("")}</tbody></table>` : ""}
    ${(g.exemple&&g.exemple.length) ? `<h3>Exemple de dosare</h3><table><tbody>${g.exemple.map(e=>`<tr><td>${esc(e.numar)}</td><td class="muted">${esc(e.instanta)}</td><td class="num">${esc((e.data||"").slice(0,10))}</td></tr>`).join("")}</tbody></table>` : ""}
    <p style="margin-top:14px"><a href="https://portal.just.ro" target="_blank" rel="noopener">🔎 Caută aceste dosare pe portal.just.ro →</a></p>`);
}

// ---- helpers ----
function val(id) { const e = document.getElementById(id); return e ? e.value.trim() : ""; }
function wire(ids) {
  ids.forEach(id => { const e = document.getElementById(id); if (!e) return;
    e.addEventListener(id === "q" ? "input" : "change", () => tab === "valuri" ? listValuri() : listColective()); });
}
window.render = render; window.detaliuCaz = detaliuCaz; window.detaliuGrup = detaliuGrup; window.inchide = inchide;

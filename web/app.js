"use strict";
let DATA = null, tab = "colective", fdom = "";
let lastFocus = null;

const esc = (s) => (s == null ? "" : String(s).replace(/[&<>"]/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])));
const norm = (s) => (s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");
const main = () => document.getElementById("main");
const qval = () => document.getElementById("q").value.trim();
const domLabel = (c) => (DATA.domenii && DATA.domenii[c]) || c || "—";
const nivLabel = (c) => (DATA.niveluri && DATA.niveluri[c]) || c;

// ---- boot ----
fetch("data.json").then(r => r.json()).then(d => {
  DATA = d;
  document.getElementById("generat").textContent = d.generat_la || "—";
  const q = document.getElementById("q");
  q.addEventListener("input", render);
  document.getElementById("q-btn").addEventListener("click", () => { render(); q.focus(); });
  document.querySelectorAll(".tabs button").forEach(b =>
    b.addEventListener("click", () => { tab = b.dataset.tab; fdom = ""; setTabs(); render(); }));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") inchide(); });
  render();
}).catch(e => { main().innerHTML = `<div class="gol">Nu am putut încărca datele (${esc(e.message)}).</div>`; });

function setTabs() {
  document.querySelectorAll(".tabs button").forEach(b =>
    b.setAttribute("aria-current", String(b.dataset.tab === tab)));
}

function matches(it, q, campuri) {
  const nq = norm(q);
  return !nq || norm(campuri.map(c => it[c]).join(" ")).includes(nq);
}

function render() {
  const q = qval();
  if (q) return renderCautare(q);
  if (tab === "despre") return renderDespre();
  if (tab === "valuri") return renderValuri();
  return renderColective();
}

// ---- căutare globală (peste ambele seturi) ----
function renderCautare(q) {
  const caz = (DATA.cazuri || []).filter(c => matches(c, q, ["numar", "obiect", "rezumat", "instanta"]))
    .sort((a, b) => b.scor - a.scor);
  const grp = (DATA.grupuri || []).filter(g => matches(g, q, ["parat", "obiect_tip"]))
    .sort((a, b) => b.nr_dosare - a.nr_dosare);
  let html = `<p class="muted" style="margin:6px 4px 14px">Rezultate pentru „<b>${esc(q)}</b>" —
    ${caz.length} acțiuni colective, ${grp.length} valuri de procese.
    <button onclick="clearQ()" style="background:none;border:0;color:var(--accent);cursor:pointer;font:inherit;text-decoration:underline">renunță</button></p>`;
  if (!caz.length && !grp.length)
    html += `<div class="gol">Niciun rezultat pentru „${esc(q)}". Încearcă alt cuvânt — o firmă, o instituție sau o problemă.</div>`;
  if (caz.length) html += `<div class="sectiune-titlu">⚖️ Acțiuni colective (${caz.length})</div>` + listaCazuri(caz);
  if (grp.length) html += `<div class="sectiune-titlu">🌊 Valuri de procese identice (${grp.length})</div>` + listaGrupuri(grp);
  main().innerHTML = html;
}
function clearQ() { document.getElementById("q").value = ""; render(); }

// ---- tab: acțiuni colective ----
function renderColective() {
  const total = (DATA.cazuri || []).length;
  main().innerHTML = `
    <div class="lead">
      <h2>Ești posibil păgubit? Verifică.</h2>
      <p>Caută mai sus o firmă, o instituție sau problema ta — vezi dacă există deja un proces la care te poți raporta.</p>
      <div class="chips">
        ${["bancă", "pensii", "asigurări", "Nordis", "mediu", "telefonie"].map(c =>
          `<button onclick="quick('${c}')">${c}</button>`).join("")}
      </div>
    </div>
    <div class="statbar">
      <span><b>${total}</b> acțiuni colective</span>
      <span><b>${(DATA.stats && DATA.stats.confirmate) || 0}</b> confirmate</span>
      <span><b>${(DATA.grupuri || []).length}</b> valuri de procese</span>
    </div>
    ${pastileDomenii()}
    ${filtruDomeniu(DATA.cazuri, "acțiunile colective")}
    <div id="lst"></div>`;
  pictaCazuri();
}

// pastile cu numărul de valuri per domeniu — clic = navighează direct la acel domeniu
function pastileDomenii() {
  const c = {};
  (DATA.grupuri || []).forEach(g => { if (g.domeniu) c[g.domeniu] = (c[g.domeniu] || 0) + 1; });
  const items = Object.entries(c).sort((a, b) => b[1] - a[1]);
  if (!items.length) return "";
  return `<div class="card">
    <div class="sectiune-titlu" style="margin-top:0">🌊 Valuri pe domenii — navighează direct</div>
    <div class="dompastile">${items.map(([d, n]) =>
      `<button onclick="mergiLaDomeniu('${d}')" aria-label="${esc(domLabel(d))}, ${n} valuri">
        <span>${esc(domLabel(d))}</span><b>${n}</b></button>`).join("")}</div></div>`;
}
function mergiLaDomeniu(d) {
  document.getElementById("q").value = "";
  tab = "valuri"; fdom = d; setTabs(); render(); window.scrollTo(0, 0);
}
function pictaCazuri() {
  const rows = (DATA.cazuri || []).filter(c => !fdom || c.domeniu === fdom).sort((a, b) => b.scor - a.scor);
  document.getElementById("lst").innerHTML = rows.length
    ? listaCazuri(rows) + `<p class="muted" style="margin-top:10px">${rows.length} rezultate.</p>`
    : `<div class="gol">Niciun rezultat pentru filtrul ales.</div>`;
}

// ---- tab: valuri ----
function renderValuri() {
  main().innerHTML = `
    <div class="lead">
      <h2>Valuri de procese identice</h2>
      <p>Mii de oameni dau în judecată separat aceeași instituție sau firmă pentru aceeași problemă. Vezi dacă <b>ai și tu același caz</b>.</p>
    </div>
    ${filtruDomeniu(DATA.grupuri, "valurile")}
    <div id="lst"></div>`;
  pictaGrupuri();
}
function pictaGrupuri() {
  const rows = (DATA.grupuri || []).filter(g => !fdom || g.domeniu === fdom).sort((a, b) => b.nr_dosare - a.nr_dosare);
  document.getElementById("lst").innerHTML = rows.length
    ? listaGrupuri(rows) + `<p class="muted" style="margin-top:10px">${rows.length} valuri.</p>`
    : `<div class="gol">Niciun val pentru filtrul ales.</div>`;
}

// ---- liste de carduri ----
function listaCazuri(rows) {
  return `<div class="lista">` + rows.slice(0, 300).map(c => {
    const i = DATA.cazuri.indexOf(c);
    return `<button class="rezultat" onclick="detaliuCaz(${i})" aria-label="Detalii dosar ${esc(c.numar)}">
      <p class="rez-titlu">${esc(c.rezumat || c.obiect)}</p>
      <div class="rez-meta">
        ${c.domeniu ? `<span class="badge b-dom">${esc(domLabel(c.domeniu))}</span>` : ""}
        <span class="badge b-${esc(c.nivel)}">${esc(nivLabel(c.nivel))}</span>
        <span>${esc(c.instanta)}</span><span>· dosar ${esc(c.numar)}</span>
      </div></button>`;
  }).join("") + `</div>`;
}
function listaGrupuri(rows) {
  return `<div class="lista">` + rows.slice(0, 300).map(g => {
    const i = DATA.grupuri.indexOf(g);
    return `<button class="rezultat" onclick="detaliuGrup(${i})" aria-label="Detalii val ${esc(g.obiect_tip)}">
      <div class="rez-top">
        <div>
          <p class="rez-titlu">${esc(g.obiect_tip)}</p>
          <div class="rez-meta">împotriva <b>${esc(g.parat)}</b>
            ${g.domeniu ? `<span class="badge b-dom">${esc(domLabel(g.domeniu))}</span>` : ""}</div>
        </div>
        <span class="count">${g.aprox ? "≥" : ""}${g.nr_dosare}<br><small class="muted">dosare</small></span>
      </div></button>`;
  }).join("") + `</div>`;
}

function filtruDomeniu(items, scop) {
  const set = [...new Set(items.map(i => i.domeniu).filter(Boolean))].sort();
  if (!set.length) return "";
  return `<div class="filtru-domeniu">
    <label for="sel-dom" class="muted">Filtrează ${scop || ""} pe domeniu:</label>
    <select id="sel-dom" onchange="setDom(this.value)">
      <option value="">Toate domeniile (${set.length})</option>
      ${set.map(d => `<option value="${d}" ${d === fdom ? "selected" : ""}>${esc(domLabel(d))}</option>`).join("")}
    </select></div>`;
}
function setDom(v) { fdom = v; tab === "valuri" ? pictaGrupuri() : pictaCazuri(); }
function quick(q) { const e = document.getElementById("q"); e.value = q; render(); e.focus(); }

// ---- despre ----
function renderDespre() {
  main().innerHTML = `
    <div class="card"><h2 style="margin-top:0">De ce „Zamolxis"</h2>
      <p>Zamolxis era, în tradiția daco-getică, divinitatea legii și a dreptății — cel care aduna oamenii
        și le dădea legile. Platforma face același lucru: <b>strânge laolaltă oamenii păgubiți</b> și le arată
        unde stă dreptatea, în datele publice ale instanțelor.</p></div>
    <div class="card"><h2 style="margin-top:0">Ce găsești aici</h2>
      <p><b>Acțiuni colective</b> — procese pornite de asociații/ONG-uri pentru un grup.</p>
      <p><b>Valuri de procese identice</b> — mii de dosare individuale separate cu aceeași problemă împotriva
        aceleiași instituții/firme (pensii, asigurări, taxe, apartamente nelivrate ca la Nordis).</p></div>
    <div class="card" style="background:#fbf3df;border-color:#e9d6a3"><p style="margin:0;color:#6b521a">
      <b>Important.</b> Informație orientativă, <b>nu</b> consultanță juridică. Clasificarea automată poate greși
      („de verificat"). Consultă un avocat și verifică la
      <a href="https://portal.just.ro" target="_blank" rel="noopener">portal.just.ro</a>.</p></div>`;
}

// ---- modal detaliu (focus + Escape) ----
function inchide() {
  const d = document.getElementById("detaliu");
  if (!d.innerHTML) return;
  d.innerHTML = "";
  if (lastFocus) { lastFocus.focus(); lastFocus = null; }
}
function modal(html) {
  lastFocus = document.activeElement;
  const d = document.getElementById("detaliu");
  d.innerHTML = `<div class="overlay" onclick="if(event.target===this)inchide()" role="dialog" aria-modal="true">
    <div class="modal"><button class="x" onclick="inchide()" aria-label="Închide">×</button>${html}</div></div>`;
  const x = d.querySelector(".x"); if (x) x.focus();
}

function detaliuCaz(i) {
  const c = DATA.cazuri[i]; if (!c) return;
  modal(`
    <h2>Dosar ${esc(c.numar)}</h2>
    <p class="muted">${esc(c.instanta)}${c.stadiu ? " · " + esc(c.stadiu) : ""}</p>
    <div class="pills">
      ${c.domeniu ? `<span class="badge b-dom">${esc(domLabel(c.domeniu))}</span>` : ""}
      <span class="badge b-${esc(c.nivel)}">${esc(nivLabel(c.nivel))}</span></div>
    ${c.rezumat ? `<p style="font-size:17px"><b>${esc(c.rezumat)}</b></p>` : ""}
    <p><span class="muted">Obiect:</span><br>${esc(c.obiect || "—")}</p>
    ${(c.motive && c.motive.length) ? `<p class="muted">De ce a fost marcat:</p><ul>${c.motive.map(m => `<li>${esc(m)}</li>`).join("")}</ul>` : ""}
    ${(c.parti && c.parti.length) ? `<h3>Părți</h3><table><tbody>${c.parti.map(p => `<tr><td>${esc(p.nume)}</td><td class="muted">${esc(p.calitate)}</td></tr>`).join("")}</tbody></table><p class="muted">Persoanele fizice sunt afișate cu inițiale.</p>` : ""}
    <div class="cta"><a href="https://portal.just.ro" target="_blank" rel="noopener">🔎 Verifică dosarul ${esc(c.numar)} pe portal.just.ro →</a></div>`);
}
function detaliuGrup(i) {
  const g = DATA.grupuri[i]; if (!g) return;
  const inst = g.instante ? Object.entries(g.instante).sort((a, b) => b[1] - a[1]) : [];
  modal(`
    <h2>${esc(g.obiect_tip)}</h2>
    <p class="muted">împotriva <b>${esc(g.parat)}</b>${g.domeniu ? ` · <span class="badge b-dom">${esc(domLabel(g.domeniu))}</span>` : ""}</p>
    <p style="font-size:20px"><b>${g.aprox ? "≥ " : ""}${g.nr_dosare} dosare</b> cu aceeași problemă</p>
    ${g.prima_data ? `<p class="muted">Perioadă: ${esc(g.prima_data)} → ${esc(g.ultima_data)}</p>` : ""}
    <div class="cta">💡 Dacă ai și tu un astfel de litigiu împotriva <b>${esc(g.parat)}</b>, nu ești singur — sunt cel puțin ${g.nr_dosare} dosare similare.</div>
    ${inst.length ? `<h3>Pe instanțe</h3><table><tbody>${inst.slice(0, 12).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${v}</td></tr>`).join("")}</tbody></table>` : ""}
    ${(g.exemple && g.exemple.length) ? `<h3>Exemple de dosare</h3><table><tbody>${g.exemple.map(e => `<tr><td>${esc(e.numar)}</td><td class="muted">${esc(e.instanta)}</td></tr>`).join("")}</tbody></table>` : ""}
    <div class="cta"><a href="https://portal.just.ro" target="_blank" rel="noopener">🔎 Caută aceste dosare pe portal.just.ro →</a></div>`);
}

window.render = render; window.clearQ = clearQ; window.quick = quick; window.setDom = setDom;
window.mergiLaDomeniu = mergiLaDomeniu;
window.detaliuCaz = detaliuCaz; window.detaliuGrup = detaliuGrup; window.inchide = inchide;

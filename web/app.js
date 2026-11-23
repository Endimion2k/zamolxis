"use strict";
/* Păgubiți.ro — căutare locală peste data.json, liste de valuri și acțiuni colective. */

const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => (s == null ? "" : String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])));
const norm = (s) => (s || "").toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");
const fmt = (n) => Number(n).toLocaleString("ro-RO");
// „21 de dosare”, „5 dosare”, „1 dosar”
const nr = (n, sing, plur) => n === 1 ? `un ${sing}` :
  `${fmt(n)} ${(n % 100 === 0 || n % 100 >= 20) && n >= 20 ? "de " : ""}${plur}`;
const LUNI = ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie", "august",
  "septembrie", "octombrie", "noiembrie", "decembrie"];
const data = (iso) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || "");
  return m ? `${+m[3]} ${LUNI[+m[2] - 1]} ${m[1]}` : "";
};

// Cedila → virgulă (Ş Ţ → Ș Ț) și majuscule → formă de titlu, păstrând SA/SRL/IFN.
const MICI = new Set(["de", "a", "al", "si", "și", "din", "pentru", "la", "in", "în", "pe", "cu"]);
const SIGLE = new Set(["SA", "SRL", "IFN", "SARL", "SCA", "SPRL", "ANAF", "CNAS", "CEC", "BRD", "ING", "OTP", "EOS", "KSI", "UAT", "SPEEH", "CNPP", "AJFP", "DGRFP", "DGAMC", "ANPC", "ONG"]);
const virgula = (s) => (s || "").replace(/ş/g, "ș").replace(/Ş/g, "Ș").replace(/ţ/g, "ț").replace(/Ţ/g, "Ț");
function titlu(s) {
  s = virgula(s).trim();
  return s.split(/(\s+|-)/).map((w, i) => {
    if (/^\s+$|^-$/.test(w) || !w) return w;
    const bare = w.replace(/[^\p{L}]/gu, "");
    if (SIGLE.has(bare) || bare.length < 2 || bare !== bare.toLocaleUpperCase("ro")) return w;
    const lo = w.toLocaleLowerCase("ro");
    if (i > 0 && MICI.has(lo)) return lo;
    return lo.charAt(0).toLocaleUpperCase("ro") + lo.slice(1);
  }).join("");
}
// „CurteadeApelPITESTI” → „Curtea de Apel Pitesti”
function instanta(s) {
  if (!s) return "";
  const m = /^(CurteadeApel|TribunalulSpecializat|TribunalulpentruMinori\w*|Tribunalul|Judecatoria|InaltaCurte\w*)(.*)$/.exec(s);
  if (!m) return titlu(s);
  const pref = { CurteadeApel: "Curtea de Apel", TribunalulSpecializat: "Tribunalul Specializat",
    Tribunalul: "Tribunalul", Judecatoria: "Judecătoria" }[m[1]] || m[1].replace(/([a-z])([A-Z])/g, "$1 $2");
  return `${pref} ${titlu(m[2].replace(/([a-z])([A-Z])/g, "$1 $2"))}`.trim();
}

// Numele scrise integral cu majuscule din rezumate devin formă de titlu.
const rezumat = (t) => virgula(t).replace(/[\p{Lu}][\p{Lu}\d.&]*(?:[\s-]+[\p{Lu}\d.&]+)+|[\p{Lu}]{4,}/gu, (m) => titlu(m));

let D = null;
const stare = { valDom: "", valToate: false, colDom: "", colToate: false };
const domeniu = (c) => (D.domenii && D.domenii[c]) || "Altele";

// ---------- pornire ----------
fetch("data.json", { cache: "no-cache" }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }).then(d => {
  D = d;
  D.grupuri.forEach((g, i) => { g._i = i; g._cauta = norm(`${g.parat} ${g.obiect_tip} ${domeniu(g.domeniu)}`); });
  D.cazuri.forEach((c, i) => {
    c._i = i;
    c._cauta = norm(`${c.numar} ${c.obiect} ${c.rezumat} ${c.instanta} ${(c.parti || []).map(p => p.nume).join(" ")}`);
  });
  cifre();
  reel();
  pictaValuri();
  pictaColective();
  const q = new URLSearchParams(location.search).get("q") || decodeURIComponent((location.hash.match(/^#q=(.+)/) || [])[1] || "");
  if (q) { $("#q").value = q; cauta(q, false); }
}).catch(() => {
  ["#val-lista", "#col-lista"].forEach(s => { $(s).innerHTML = `<li class="empty">Datele nu s-au putut încărca. Reîncarcă pagina.</li>`; });
});

// ---------- cifrele din propoziție ----------
function cifre() {
  const dosare = D.grupuri.reduce((s, g) => s + (g.nr_dosare || 0), 0);
  const conf = (D.stats && D.stats.confirmate) || 0;
  $("#cifre").innerHTML = `Am găsit <b>${nr(D.grupuri.length, "val", "valuri")}</b> de procese identice, cu ` +
    `<b>${nr(dosare, "dosar", "dosare")}</b> deschise separat de oameni cu aceeași problemă. ` +
    `Și <b>${nr(D.cazuri.length, "acțiune colectivă", "acțiuni colective")}</b>${conf ? `, dintre care <b>${fmt(conf)} confirmate</b>` : ""}.`;
  if (D.generat_la) {
    const t = $("#generat"); t.dateTime = D.generat_la; t.textContent = data(D.generat_la);
  }
}

// ---------- filmul de instanțe din primul ecran ----------
function dosareLa(oras) {
  let n = 0;
  D.grupuri.forEach(g => Object.entries(g.instante || {}).forEach(([k, v]) => { if (k.toUpperCase().includes(oras)) n += v; }));
  return n;
}
function reel() {
  const items = [...document.querySelectorAll(".reel-item")];
  const cap = $(".reel-cap");
  const NUME = { VALCEA: "Tribunalul Vâlcea", CLUJ: "Tribunalul Cluj", IASI: "Palatul de Justiție, Iași", BUCURESTI: "Palatul de Justiție, București" };
  const LOC = { VALCEA: "Vâlcea", CLUJ: "Cluj", IASI: "Iași", BUCURESTI: "București" };
  const text = items.map(it => {
    const o = it.dataset.oras, n = dosareLa(o);
    return n ? `${NUME[o]}. ${nr(n, "dosar", "dosare")} din valurile de procese sunt la instanțele din ${LOC[o]}.` : `${NUME[o]}.`;
  });
  let k = 0;
  const arata = (i) => {
    items.forEach((it, j) => it.classList.toggle("on", j === i));
    cap.textContent = text[i];
  };
  arata(0);
  const valcea = dosareLa("VALCEA");
  if (valcea) $("#val-photo-cap").textContent = `Tribunalul Vâlcea. ${nr(valcea, "dosar", "dosare")} din valurile de mai jos trec prin instanțele din Vâlcea.`;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  let pauza = false;
  const fig = $(".reel");
  fig.addEventListener("mouseenter", () => { pauza = true; });
  fig.addEventListener("mouseleave", () => { pauza = false; });
  setInterval(() => { if (!pauza && !document.hidden) { k = (k + 1) % items.length; arata(k); } }, 5000);
}

// ---------- filtre ----------
function filtre(el, items, activ, onPick, scop) {
  const c = {};
  items.forEach(i => { const d = i.domeniu || "alt"; c[d] = (c[d] || 0) + 1; });
  const lista = Object.entries(c).sort((a, b) => b[1] - a[1]);
  el.innerHTML = [["", items.length], ...lista].map(([d, n]) =>
    `<button type="button" data-d="${esc(d)}" aria-pressed="${d === activ}">${d ? esc(domeniu(d)) : `Toate ${scop}`} <span>${fmt(n)}</span></button>`).join("");
  el.onclick = (e) => { const b = e.target.closest("button"); if (b) onPick(b.dataset.d); };
}

// ---------- valuri ----------
function rowVal(g) {
  return `<li class="row">
    <button class="row-btn" type="button" aria-expanded="false" aria-controls="v${g._i}">
      <span class="row-n">${g.aprox ? "≥" : ""}${fmt(g.nr_dosare)}</span>
      <span><span class="row-t">${esc(g.obiect_tip)}</span><span class="row-s">împotriva ${esc(titlu(g.parat))}</span></span>
      <span class="row-d">${esc(domeniu(g.domeniu))}<span class="row-plus" aria-hidden="true"></span></span>
    </button>
    <div class="row-panel" id="v${g._i}" hidden></div>
  </li>`;
}
function panouVal(g) {
  const inst = Object.entries(g.instante || {}).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const per = g.prima_data ? `între ${data(g.prima_data)} și ${data(g.ultima_data)}` : "";
  return `<p>${g.aprox ? "Cel puțin " : ""}${nr(g.nr_dosare, "dosar", "dosare")} de tip „${esc(g.obiect_tip)}” împotriva ${esc(titlu(g.parat))}${per ? `, înregistrate ${per}` : ""}. Dacă ai și tu un astfel de proces, nu ești singur. Numărul de dosare nu arată cine are dreptate; decide instanța.</p>
    <div class="panel-cols">
      ${inst.length ? `<div><h4>Pe instanțe</h4><ul>${inst.map(([k, v]) => `<li><span>${esc(instanta(k))}</span><span>${fmt(v)}</span></li>`).join("")}</ul></div>` : ""}
      ${(g.exemple || []).length ? `<div><h4>Exemple de dosare</h4><ul>${g.exemple.map(e => `<li><span>${esc(e.numar)}</span><span>${esc(instanta(e.instanta))}</span></li>`).join("")}</ul></div>` : ""}
    </div>
    <a class="out" href="https://portal.just.ro">Caută aceste dosare pe portal.just.ro</a>`;
}
function leaga(lista) {
  lista.onclick = (e) => {
    const cm = e.target.closest(".case-more");
    if (cm) {
      const open = cm.getAttribute("aria-expanded") !== "true";
      cm.setAttribute("aria-expanded", String(open));
      document.getElementById(cm.getAttribute("aria-controls")).hidden = !open;
      return;
    }
    const b = e.target.closest(".row-btn"); if (!b) return;
    const p = document.getElementById(b.getAttribute("aria-controls"));
    const open = b.getAttribute("aria-expanded") !== "true";
    if (open && !p.innerHTML) p.innerHTML = panouVal(D.grupuri[+p.id.slice(1)]);
    b.setAttribute("aria-expanded", String(open));
    p.hidden = !open;
  };
}
function pictaValuri() {
  const rows = D.grupuri.filter(g => !stare.valDom || (g.domeniu || "alt") === stare.valDom).sort((a, b) => b.nr_dosare - a.nr_dosare);
  filtre($("#val-filtre"), D.grupuri, stare.valDom, (d) => { stare.valDom = d; stare.valToate = false; pictaValuri(); }, "valurile");
  const arat = stare.valToate ? rows : rows.slice(0, 12);
  const l = $("#val-lista");
  l.innerHTML = arat.map(rowVal).join("") || `<li class="empty">Niciun val în acest domeniu.</li>`;
  leaga(l);
  const m = $("#val-more");
  m.hidden = rows.length <= arat.length;
  m.textContent = `Arată toate cele ${fmt(rows.length)} valuri`;
  m.onclick = () => { stare.valToate = true; pictaValuri(); };
}

// ---------- acțiuni colective ----------
function rowCaz(c) {
  const motive = (c.motive || []).filter(Boolean);
  return `<li class="case">
    <p class="case-t">${esc(rezumat(c.rezumat || c.obiect))}</p>
    <p class="case-m"><span class="lvl${c.nivel === "confirmat" ? "" : " rev"}">${c.nivel === "confirmat" ? "Confirmat" : "De verificat"}</span>
      · ${esc(domeniu(c.domeniu))} · ${esc(instanta(c.instanta))} · dosar ${esc(c.numar)}${c.stadiu ? ` · ${esc(c.stadiu)}` : ""}</p>
    <button class="case-more" type="button" aria-expanded="false" aria-controls="c${c._i}">De ce apare aici</button>
    <div class="case-panel" id="c${c._i}" hidden>
      ${c.obiect ? `<p>Ce se cere în dosar: ${esc(virgula(c.obiect))}.</p>` : ""}
      ${motive.length ? `<ul>${motive.map(m => `<li>${esc(virgula(m))}</li>`).join("")}</ul>` : ""}
      <a class="out" href="https://portal.just.ro">Verifică dosarul ${esc(c.numar)} pe portal.just.ro</a>
    </div>
  </li>`;
}
function pictaColective() {
  const rows = D.cazuri.filter(c => !stare.colDom || (c.domeniu || "alt") === stare.colDom)
    .sort((a, b) => (a.nivel === "confirmat" ? 0 : 1) - (b.nivel === "confirmat" ? 0 : 1) || b.scor - a.scor);
  filtre($("#col-filtre"), D.cazuri, stare.colDom, (d) => { stare.colDom = d; stare.colToate = false; pictaColective(); }, "acțiunile");
  const arat = stare.colToate ? rows : rows.slice(0, 5);
  $("#col-lista").innerHTML = arat.map(rowCaz).join("") || `<li class="empty">Nicio acțiune în acest domeniu.</li>`;
  leaga($("#col-lista"));
  const m = $("#col-more");
  m.hidden = rows.length <= arat.length;
  m.textContent = `Arată toate cele ${fmt(rows.length)} acțiuni`;
  m.onclick = () => { stare.colToate = true; pictaColective(); };
}

// ---------- căutarea ----------
function cauta(q, scroll) {
  const sec = $("#rezultate");
  const nq = norm(q.trim());
  if (!D) return;
  if (!nq) { sec.hidden = true; history.replaceState(null, "", location.pathname); return; }
  const termeni = nq.split(/\s+/);
  const ok = (s) => termeni.every(t => s.includes(t));
  const val = D.grupuri.filter(g => ok(g._cauta)).sort((a, b) => b.nr_dosare - a.nr_dosare);
  const caz = D.cazuri.filter(c => ok(c._cauta)).sort((a, b) => b.scor - a.scor);
  const total = val.reduce((s, g) => s + g.nr_dosare, 0);

  let lead;
  if (val.length) {
    const top = val[0];
    lead = `Nu ești singur. Am găsit <strong>${nr(total, "dosar", "dosare")}</strong> în ${nr(val.length, "val", "valuri")} de procese pentru „${esc(q.trim())}”. Cel mai mare: ${nr(top.nr_dosare, "dosar", "dosare")} de tip „${esc(top.obiect_tip)}” împotriva ${esc(titlu(top.parat))}.`;
  } else if (caz.length) {
    lead = `Am găsit <strong>${nr(caz.length, "acțiune colectivă", "acțiuni colective")}</strong> pentru „${esc(q.trim())}”.`;
  } else {
    lead = `Nu am găsit nimic pentru „${esc(q.trim())}”. Încearcă doar numele firmei (de exemplu „Nordis”), al instituției sau un cuvânt ca „pensie”, „asigurare”, „executare”.`;
  }
  $("#rez-lead").innerHTML = lead;
  $("#rez-h").textContent = "Rezultate";
  $("#rez-body").innerHTML =
    (val.length ? `<h3>Valuri de procese</h3><ul class="rows" id="rez-val">${val.slice(0, 40).map(rowVal).join("")}</ul>` : "") +
    (caz.length ? `<h3>Acțiuni colective</h3><ul class="cases" id="rez-caz">${caz.slice(0, 30).map(rowCaz).join("")}</ul>` : "");
  const rv = $("#rez-val"); if (rv) leaga(rv);
  const rc = $("#rez-caz"); if (rc) leaga(rc);
  sec.hidden = false;
  history.replaceState(null, "", `#q=${encodeURIComponent(q.trim())}`);
  if (scroll) sec.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}
let tmr;
$("#q").addEventListener("input", (e) => { clearTimeout(tmr); tmr = setTimeout(() => cauta(e.target.value, false), 180); });
$("#cauta").addEventListener("submit", (e) => { e.preventDefault(); cauta($("#q").value, true); });
document.querySelectorAll(".try").forEach(b => b.addEventListener("click", () => {
  $("#q").value = b.dataset.q; cauta(b.dataset.q, true);
}));

// ---------- intrări la derulare ----------
(function intrari() {
  const hero = $(".sentence");
  hero.classList.add("pre");
  requestAnimationFrame(() => requestAnimationFrame(() => hero.classList.remove("pre")));
  if (!("IntersectionObserver" in window)) return;
  const grupuri = [
    [".figures", ".figures-text, .figures-note"],
    [".waves", ".section-h, .waves-photo, .waves-intro, .filters"],
    [".collective", ".section-h, .collective-pin p, .pin-photo, .collective-list"],
    [".steps", ".stair li"],
    [".about", ".facts, .section-h, .about-lead"],
    [".footer", ".footer-meta"],
  ];
  const io = new IntersectionObserver((ent) => ent.forEach(en => {
    if (!en.isIntersecting) return;
    en.target.querySelectorAll(".rise").forEach(el => el.classList.add("in"));
    io.unobserve(en.target);
  }), { rootMargin: "0px 0px -6% 0px" });
  grupuri.forEach(([s, kids]) => {
    const sec = $(s); if (!sec) return;
    sec.querySelectorAll(kids).forEach((el, i) => { el.classList.add("rise"); el.style.setProperty("--d", `${i * 80}ms`); });
    io.observe(sec);
  });
})();

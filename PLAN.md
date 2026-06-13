# Portal Acțiuni Colective România — Plan de proiect

> Portal public care scanează dosarele aflate pe rol în România, identifică acțiunile
> colective relevante și le afișează astfel încât orice persoană potențial păgubită
> să le poată găsi.

**Status:** MVP COMPLET livrat (fazele 1–6). Vezi README.md pentru stadiu detaliat.
**Scop ales:** MEDIU — consumatori (L.414/2023) + clauze abuzive bancare + acțiuni de mediu
**Prioritate:** funcțional întâi, design la final
**LLM:** NU — clasificare 100% deterministă (reguli), fără costuri API
**Rulare:** pornim local pe Windows, cod păstrat portabil pentru server ulterior
**Data:** 2026-06-13

---

## 1. Obiectiv

Un cetățean care bănuiește că a fost păgubit (ex: comision bancar abuziv, poluare în
zona lui, practică comercială ilegală) intră pe portal, caută după domeniu/companie și
află dacă **există deja un proces colectiv** la care poate adera sau pe care îl poate urmări.

Valoarea reală: agregăm și *facem inteligibile* dosare care azi sunt îngropate în
portalul oficial, greu de filtrat și scris în limbaj juridic.

---

## 2. Realitatea legală (de ce nu e „class action" clasic)

România **nu** are class action în sens american. Ce identificăm noi (scop mediu):

| Tip | Bază legală | Cum îl recunoaștem |
|-----|-------------|--------------------|
| Acțiune în reprezentare consumatori | Legea 414/2023 (Directiva UE 2020/1828) | Parte = asociație de consumatori autorizată; obiect cu „interese colective" |
| Clauze abuzive bancare | Legea 193/2000, OUG 50/2010 | Obiect „constatare clauze abuzive"; pârât = bancă |
| Acțiuni de mediu colective | OUG 195/2005, L.292/2018 | Parte = ONG mediu; obiect mediu |

**Consecință centrală:** NU există un câmp „class action" în dosare. Le identificăm
**euristic** (vezi secțiunea 4). Asta e miezul tehnic al proiectului.

---

## 3. Sursa de date — portal.just.ro web service

- **Endpoint:** `http://portalquery.just.ro/query.asmx` (SOAP 1.1, **HTTP, nu HTTPS**)
- **Gratuit, public**, fără autentificare.
- **Metode:**
  - `CautareDosare` — caută dosare. Minim un filtru obligatoriu: **număr / obiect / nume parte**. Opțional: instituție, interval de date.
  - `CautareSedinte` — caută ședințe. Obligatoriu: **dată + instanță**.
- **Câmpuri returnate per dosar:** număr unic, număr vechi, dată, instituție, secție,
  categorie caz, stadiu procesual, **listă părți** (nume + calitate), **listă termene/ședințe**
  (dată, oră, soluție, sumar), **căi de atac**.

### Limitări critice (modelează toată arhitectura)
1. **Nu poți „scana tot".** Fiecare query cere un filtru. Nu există „dă-mi toate dosarele pe rol".
2. **Max 1000 rezultate / query.** Query prea larg → trunchiere tăcută.
3. **Fără rate limit documentat** — dar tratăm serviciul cu respect (throttling, retry, cache).
4. **HTTP necriptat** — clientul SOAP trebuie configurat pentru HTTP simplu.

> Bibliotecă de referință (C#): https://github.com/sibies/Just.Net — utilă ca model
> pentru structura SOAP, chiar dacă noi scriem în Python.

---

## 4. Miezul tehnic — clasificatorul „e acțiune colectivă?"

Pentru că nu există flag, fiecare dosar primește un **scor** și un **motiv**. Abordare
în 3 straturi, de la ieftin la scump:

### Strat A — interogări țintite (filtrăm la sursă)
În loc să scanăm orbește, interogăm web service-ul DOAR pe semnale de acțiune colectivă:
- **Pe obiect** (cuvinte-cheie): „acțiune în reprezentare", „interese colective",
  „clauze abuzive", „protecția consumatorilor", „acțiune colectivă".
- **Pe nume parte**: listă albă de asociații (APC, InfoCons, ANPC ca intervenient,
  ONG-uri de mediu cunoscute).
Asta reduce volumul de la „toate dosarele" la „candidați plauzibili".

### Strat B — reguli de scor pe candidați
Fiecare candidat e punctat:
- +obiect conține cuvinte-cheie din taxonomia colectivă
- +o parte e asociație/ONG din lista albă
- +pârâtul e persoană juridică (bancă, companie) iar reclamanții sunt mulți
- +număr de părți peste un prag (ex. >5 reclamanți cu interese similare)
- −semnale de litigiu pur individual (divorț, succesiune, penal individual)
Prag de încredere → „confirmat" / „de revizuit" / „respins".

### (Decis: FĂRĂ LLM)
Clasificarea rămâne 100% deterministă (Strat A + B). Avantaje: gratuit, explicabil,
reproductibil, fără dependențe externe. Cazurile „de revizuit" sunt marcate ca atare
și pot fi validate manual.

Rezumatul public pentru cetățean se generează **prin șabloane** (template), nu prin LLM:
combinăm domeniu + obiect + tip părți într-o frază clară (ex: „Asociația X cere în
instanță anularea unor clauze considerate abuzive în contractele băncii Y").

---

## 5. Arhitectură

```
  ┌────────────────────────────────────────────────────┐
  │  SCANNER  (job zilnic, Python)                     │
  │  1. generează interogări țintite (taxonomie+ONG)   │
  │  2. client SOAP → portalquery.just.ro              │
  │  3. throttle + retry + cache răspunsuri brute      │
  │  4. parse XML → obiecte Dosar                      │
  │  5. clasificator (Strat B) → scor + motiv          │
  │  6. upsert în DB (dedup pe număr unic)             │
  └───────────────────────┬────────────────────────────┘
                          │
                   ┌──────▼──────┐
                   │  DB (SQLite │   → Postgres la scalare
                   │  în MVP)    │
                   └──────┬──────┘
                          │
                ┌─────────▼─────────┐
                │  API  (FastAPI)   │  /cazuri, /cazuri/{id}, /cauta
                └─────────┬─────────┘
                          │
                ┌─────────▼─────────┐
                │  PORTAL WEB       │  listă filtrabilă + pagină caz
                │  (funcțional)     │  „Ești posibil păgubit? verifică"
                └───────────────────┘
```

---

## 6. Model de date (schiță)

```
caz
  id, numar_unic (UNIQUE), numar_vechi, instanta, sectie, categorie,
  obiect, stadiu, data_inregistrare, prima_data_vazut, ultima_actualizare,
  scor_colectiv (0-100), nivel ('confirmat'|'revizuire'|'respins'),
  motiv_clasificare (text), domeniu ('consumatori'|'bancar'|'mediu'),
  rezumat_public (text, generat prin șablon — fără LLM)

parte
  id, caz_id (FK), nume, calitate ('reclamant'|'parat'|'intervenient'),
  este_asociatie (bool)

termen
  id, caz_id (FK), data, ora, solutie_sumar, document_sumar

# raw_cache: răspunsurile SOAP brute, ca să nu re-interogăm și să putem
# re-clasifica fără a lovi serverul.
```

---

## 7. Strategia de scanare (cum ocolim limitele API)

- **Nu** încercăm „toate dosarele". Iterăm produsul cartezian restrâns:
  `taxonomie_obiect × (opțional) instanță × interval_date`.
- Intervale de date împărțite suficient de mic încât niciun query să nu depășească 1000.
- Throttling: pauză între cereri, max N cereri/minut, exponential backoff la erori.
- **Cache brut**: salvăm XML-ul; re-clasificarea nu mai lovește serverul.
- Job **zilnic** (delta): doar dosare noi / cu termen nou de la ultima rulare.
- Logăm explicit dacă un query atinge 1000 (= posibilă trunchiere → împărțim mai fin).

---

## 8. Aspecte legale / etice (de tratat din start)

- **GDPR / date personale.** Portalul oficial afișează adesea inițiale pentru persoane
  fizice. Noi afișăm public — deci: pentru părți **persoane fizice anonimizăm** (inițiale),
  afișăm integral doar **persoane juridice** (bănci, companii, asociații). Acțiunile
  colective oricum opun asociații vs. companii, deci risc PII redus, dar regula stă.
- **Disclaimer** vizibil: „informație orientativă, nu consultanță juridică; verificați
  la sursa oficială". Link către dosarul oficial pe portal.just.ro.
- **Acuratețe**: marcăm clar nivelul de încredere (confirmat / de revizuit). Nu afirmăm
  „ești păgubit", ci „există un proces care ar putea fi relevant".
- **Termenii portalului oficial**: folosim web service-ul public conform scopului; fără
  scraping agresiv, cu throttling.

---

## 9. Roadmap pe faze

| Fază | Livrabil | Verificare |
|------|----------|------------|
| **0. Setup** | structură proiect Python, venv, deps, config | rulează `--help` |
| **1. Client SOAP** | modul care interoghează `CautareDosare` și parsează XML în obiecte Dosar | extragem dosare reale după un obiect cunoscut |
| **2. Clasificator** | taxonomie + reguli de scor (Strat A+B) + teste pe cazuri reale și negative | precizie pe set de validare manuală |
| **3. Stocare** | schema DB + upsert/dedup + cache brut | re-rulare nu duplică |
| **4. Scanner orchestrat** | job care combină 1+2+3 cu throttling și delta zilnic | rulare completă fără a depăși 1000/query |
| **5. API** | FastAPI: listă, filtre (domeniu/instanță/nivel), detaliu caz, căutare | endpoints testate |
| **6. Portal web** | listă + pagină caz + căutare + disclaimer (funcțional, simplu) | un cetățean găsește un caz în <30s |
| **7. (opțional) Polish UX** | design, încredere vizuală, mobil | — |

MVP „demonstrabil" = fazele 1–6. (LLM eliminat din scop.)

---

## 10. Stack tehnic

- **Limbaj:** Python 3.11+
- **SOAP:** `zeep` (sau `requests` + template XML dacă WSDL-ul e capricios pe HTTP)
- **DB:** SQLite + SQLAlchemy în MVP → Postgres la scalare
- **API:** FastAPI + Uvicorn
- **Frontend:** server-side simplu (Jinja2 templates) în MVP — fără SPA, prioritate funcțional
- **Scheduler:** cron / Task Scheduler Windows pentru jobul zilnic
- **Teste:** pytest (clasificator + parser pe fixturi XML salvate)

---

## 11. Riscuri & necunoscute (de validat în Faza 1)

1. **WSDL pe HTTP** poate fi dificil cu `zeep` → plan B: cerere SOAP construită manual.
2. **Acoperirea obiectelor**: nu știm încă exact cum sunt formulate obiectele acțiunilor
   colective în ECRIS → calibrăm taxonomia pe date reale în Faza 2.
3. **Volum real necunoscut**: câte acțiuni colective există de fapt? Posibil zeci-sute,
   nu mii. Asta e ok — portalul rămâne valoros chiar și cu volum mic.
4. **Lista de asociații autorizate** (L.414/2023) — de procurat/menținut.
5. **Stabilitatea serviciului** portal.just.ro (mentenanțe ocazionale) → retry + cache.

---

## 12. Următorul pas propus

Faza 0 + 1: setăm structura și scriem clientul SOAP, apoi tragem **dosare reale** ca să
calibrăm taxonomia clasificatorului pe date adevărate (nu presupuneri). Restul fazelor
se sprijină pe ce învățăm aici.

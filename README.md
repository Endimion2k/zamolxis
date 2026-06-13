# ⚖️ Zamolxis — Legea celor mulți

> Zamolxis era, în tradiția daco-getică, divinitatea legii și a dreptății — cel care
> aduna oamenii și le dădea legile. Platforma face același lucru: **strânge laolaltă
> oamenii păgubiți** și le arată unde stă dreptatea, în datele publice ale instanțelor.

Zamolxis scanează dosarele aflate pe rol în România (via web service-ul public
portal.just.ro) și scoate la lumină:
- **Acțiuni colective** — procese pornite de asociații/ONG-uri pentru un grup
  (consumatori, clauze abuzive bancare, mediu);
- **Valuri de procese identice** — mii de dosare individuale separate cu aceeași
  problemă împotriva aceleiași instituții/firme (pensii, taxe, apartamente nelivrate…),
  cu **descoperire automată** a pârâților de masă (următorul „Nordis" apare singur).

Vezi [PLAN.md](PLAN.md) pentru arhitectură completă, scop și roadmap.

> ⚠️ Informație orientativă, **nu** consultanță juridică. Sursa oficială rămâne
> [portal.just.ro](https://portal.just.ro). Persoanele fizice sunt anonimizate.

## Stadiu

- [x] **Faza 0** — setup proiect
- [x] **Faza 1** — client SOAP `CautareDosare` (validat pe date reale)
- [x] **Faza 2** — clasificator determinist „e acțiune colectivă?" (fără LLM, 9 teste)
- [x] **Faza 3** — stocare SQLite (upsert+dedup, 6 teste; ~130 dosare reale în DB)
- [x] **Faza 4** — scanner orchestrat (registru 38 actori, împărțire adaptivă pe date, delta; 5 teste)
- [x] **Faza 5** — API FastAPI (JSON: `/api/cazuri`, `/api/cazuri/{nr}`, `/api/statistici`)
- [x] **Faza 6** — portal web (listă + filtre + detaliu, anonimizare GDPR; 5 teste)

- [x] **Faza 7** — „valuri de procese identice": clustering de dosare individuale după
      (pârât + tip obiect), pentru litigiul de masă (pensii, fiscal, muncă etc.)
- [x] **Faza 8** — DESCOPERIRE AUTOMATĂ: caută pe tip de problemă (obiect) și descoperă
      firme/instituții noi acționate în masă, fără listă prealabilă (10 teste cluster)

**MVP complet (toate fazele livrate).**

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Folosire (Faza 1 — explorare date)

```powershell
# după obiect, restrâns la o instanță
.\.venv\Scripts\python.exe scripts\fetch_sample.py --obiect "clauze abuzive" --institutie TribunalulBUCURESTI --max 10

# după numele unei părți (ex. asociație)
.\.venv\Scripts\python.exe scripts\fetch_sample.py --parte "Asociatia Pro Consumatori"

# preview clasificare (client + clasificator, mini-scanner Faza 2+4)
.\.venv\Scripts\python.exe scripts\scan_preview.py --parte "Asociatia Pro Consumatori"

# scanează + clasifică + salvează în SQLite (data/portal.db) — o singură interogare
.\.venv\Scripts\python.exe scripts\scan_to_db.py --parte "Agent Green"
```

## Scanner complet (Faza 4)

Parcurge automat tot registrul de actori colectivi (vezi [app/registry.py](app/registry.py)
— consumatori, bancar, mediu, muncă, sănătate) + markeri de obiect, clasifică și
actualizează baza. Robust la limita de 1000/cerere prin **împărțire adaptivă pe date**.

```powershell
.\.venv\Scripts\python.exe scripts\run_scanner.py              # scanare completă
.\.venv\Scripts\python.exe scripts\run_scanner.py --since 2024-01-01   # delta
.\.venv\Scripts\python.exe scripts\run_scanner.py --no-obiecte         # doar actori
```

## Valuri de procese identice (Faza 7)

Detectează „valurile" de litigii: mii de dosare individuale separate cu aceeași problemă
împotriva aceleiași instituții (ex. contestații pensii vs. Casa de Pensii). Grupează după
(pârât + tip de obiect) și afișează la `/valuri`. Util pentru cetățeanul care vrea să afle
că „nu e singur" — chiar dacă procedural fiecare are dosar separat.

```powershell
# toate domeniile (lung — zeci de instituții mari)
.\.venv\Scripts\python.exe scripts\run_cluster_scan.py
# focusat + rapid
.\.venv\Scripts\python.exe scripts\run_cluster_scan.py --domenii pensii,fiscal --since 2024-01-01
```

Registrul de pârâți de masă (≈80 instituții/firme pe 16 domenii: Case de Pensii,
ANAF/Finanțe, inspectorate, spitale, primării, CNAS, ANRP, APIA, bănci CHF, Nordis și alți
dezvoltatori, **asigurători în faliment — City Insurance, Euroins, Astra, FGA**, **recuperatori
de creanțe — KRUK, EOS, Kredyt Inkaso**, telecom, retail/eMAG, agenții de turism, fitness și
universități private...) e în [app/registry.py](app/registry.py). Utilitățile de energie sunt
excluse intenționat (acolo furnizorul e reclamant, nu pârât).

## Descoperire automată de pârâți noi (Faza 8)

Nu depinde de registru: caută pe **tipul de problemă** (obiect) și descoperă ce
persoane juridice sunt acționate în masă, grupând după pârâtul-firmă canonicalizat
(robust la forme juridice SRL/SA și învelișuri de insolvență). Așa apar automat
dezvoltatori/firme noi (următorul Nordis), nu doar cele cunoscute.

```powershell
# descoperă dezvoltatori imobiliari cu valuri de procese (din 2022)
.\.venv\Scripts\python.exe scripts\discover_waves.py --domenii imobiliare --since 2022-01-01 --prag 20
# un anumit tip de problemă
.\.venv\Scripts\python.exe scripts\discover_waves.py --obiect "rezolutiune" --prag 25
```

Persoanele fizice ca pârât sunt ignorate (descoperim doar firme/instituții).

## Automatizare zilnică pe Windows (Task Scheduler):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_task_windows.ps1 -Time 03:00
# eliminare: ...install_task_windows.ps1 -Uninstall
```

## Pornirea portalului (Faza 5+6)

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

Apoi deschide http://127.0.0.1:8000 — listă filtrabilă de acțiuni colective + pagină
de detaliu per dosar. API JSON: `/api/cazuri`, `/api/cazuri/{numar}`, `/api/statistici`.

Persoanele fizice sunt afișate cu inițiale (GDPR); persoanele juridice/instituțiile,
integral. Calea bazei se poate schimba cu variabila `PORTAL_DB`.

## Teste

```powershell
.\.venv\Scripts\python.exe -m pytest -q   # 20 teste (client/clasificator/stocare/API)
```

## Clasificator (Faza 2)

Determinist, fără LLM. Scor 0–100 → nivel `confirmat` (≥70) / `revizuire` (40–69) /
`respins` (<40). Semnale (vezi [app/classifier/](app/classifier/)):
- **asociație pe latura reclamantă** (semnalul central) — listă albă + indicii generice
- **număr de reclamanți** (acțiune de masă)
- **marker explicit** în obiect („în reprezentare", „interese colective")
- **domeniu** relevant (bancar / consumatori / mediu) — pre-filtru slab
- **excludere directă** pentru obiecte individuale/administrative (divorț, partaj, acte
  constitutive asociație etc.)

Validat pe date reale: cele 232 dosare „clauze abuzive" (individuale) → toate respinse;
cazurile cu APC ca reclamant → ridicate la revizuire.

## Note tehnice

- Web service: `http://portalquery.just.ro/query.asmx` (SOAP 1.1, **HTTP**, public, gratuit).
- Fiecare căutare cere minim un filtru (numar / obiect / parte) și întoarce **max 1000** dosare.
- Client scris „de mână" (requests + ElementTree din stdlib) — fără `zeep`/`lxml`, ca să
  rămână portabil pe Python 3.14.

## Structură

```
app/client/      # client SOAP + modele de date (Dosar, Parte, Sedinta)
scripts/         # utilitare CLI (fetch_sample.py)
tests/           # teste (de la Faza 2)
PLAN.md          # planul complet
```

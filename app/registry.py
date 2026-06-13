"""Sursă unică de adevăr: registrul de actori colectivi + taxonomia de obiecte.

DATE PURE (fără importuri din `app`), consumate fără cicluri de `classifier.taxonomy`
și de `scanner.orchestrator`.

Conținut consolidat prin cercetare web (workflow `cercetare-actori-colectivi-ro`).
- `query`   = substring scurt/distinctiv pentru căutarea `numeParte` (ECRIS face match de
              substring exact, FĂRĂ diacritice; siglele apar direct în nume).
- `variante`= scrieri cum apar în ECRIS (folosite la potrivirea părților în clasificator).

Insight confirmat: câmpul `obiect` e generic și NU separă colectivul de individual —
semnalul vine din PĂRȚI (ONG/sindicat/autoritate ca reclamant). Cheile de obiect de mai
jos sunt fie distinctive de domeniu (pentru etichetare), fie markeri expliciți de colectiv.
Toate cheile de obiect se compară pe text normalizat (taxonomy le normalizează la load).
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class Asociatie(TypedDict):
    nume_oficial: str
    query: str
    variante: list[str]
    domeniu: str  # consumatori | bancar | mediu | munca | sanatate | alt
    # opțional: îngustează căutarea numeParte cu un filtru de obiect, pentru actori
    # foarte „zgomotoși" (ex. ANPC = autoritate, parte la zeci de mii de dosare).
    obiect: NotRequired[str]


# --- Registrul de actori colectivi ------------------------------------------
ASOCIATII: list[Asociatie] = [
    # --- consumatori ---
    {"nume_oficial": "Asociația Pro Consumatori (APC România)", "query": "Pro Consumatori",
     "variante": ["asociatia pro consumatori", "pro consumatori", "apc romania",
                  "asociatia pentru protectia consumatorilor din romania"],
     "domeniu": "consumatori"},
    {"nume_oficial": "InfoCons", "query": "InfoCons",
     "variante": ["infocons", "asociatia infocons"], "domeniu": "consumatori"},
    {"nume_oficial": "ANPCPPS (Asoc. Naț. Protecția Consumatorilor și Promovarea Programelor)",
     "query": "Promovarea Programelor si Strategiilor",
     "variante": ["anpcpps", "asociatia nationala pentru protectia consumatorilor si promovarea programelor si strategiilor"],
     "domeniu": "consumatori"},
    {"nume_oficial": "Autoritatea Națională pentru Protecția Consumatorilor (ANPC)",
     "query": "Autoritatea Nationala pentru Protectia Consumatorilor",
     "variante": ["autoritatea nationala pentru protectia consumatorilor", "anpc",
                  "comisariatul pentru protectia consumatorilor", "ojpc", "cjpc"],
     "domeniu": "consumatori",
     # ANPC e parte la zeci de mii de dosare contravenționale individuale; îngustăm la
     # cazurile colective emblematice (ANPC vs. comerciant pe clauze abuzive).
     "obiect": "clauze abuzive"},
    # --- bancar / financiar ---
    {"nume_oficial": "Asoc. Utilizatorilor Români de Servicii Financiare (AURSF)",
     "query": "Utilizatorilor Romani de Servicii Financiare",
     "variante": ["aursf", "asociatia utilizatorilor romani de servicii financiare"],
     "domeniu": "bancar"},
    {"nume_oficial": "Asociația pentru Protecția Consumatorilor PARAKLETOS", "query": "Parakletos",
     "variante": ["parakletos", "asociatia parakletos"], "domeniu": "bancar"},
    {"nume_oficial": "Grupul Clienților cu Credite în CHF (GCCC)", "query": "Credite in CHF",
     "variante": ["grupul clientilor cu credite in chf", "credite in chf", "gccc",
                  "grupul clientilor cu credite in franci elvetieni"], "domeniu": "bancar"},
    {"nume_oficial": "Asociația Investitorilor pe Piața de Capital (AIPC)",
     "query": "Investitorilor pe Piata de Capital",
     "variante": ["asociatia investitorilor pe piata de capital", "aipc"], "domeniu": "bancar"},
    # --- mediu ---
    {"nume_oficial": "Asociația Agent Green", "query": "Agent Green",
     "variante": ["agent green", "asociatia agent green"], "domeniu": "mediu"},
    {"nume_oficial": "Greenpeace România (Fundația Greenpeace CEE)", "query": "Greenpeace",
     "variante": ["greenpeace", "fundatia greenpeace cee", "greenpeace romania"], "domeniu": "mediu"},
    {"nume_oficial": "Asociația Declic", "query": "Declic",
     "variante": ["declic", "asociatia declic", "comunitatea declic"], "domeniu": "mediu"},
    {"nume_oficial": "Bankwatch România (Filiala Cluj)", "query": "Bankwatch",
     "variante": ["bankwatch", "asociatia bankwatch romania", "cee bankwatch"], "domeniu": "mediu"},
    {"nume_oficial": "Asociația 2Celsius", "query": "2Celsius",
     "variante": ["2celsius", "asociatia 2celsius"], "domeniu": "mediu"},
    {"nume_oficial": "WWF Programul Dunăre Carpați România", "query": "WWF",
     "variante": ["wwf", "wwf romania", "asociatia wwf programul dunare carpati"], "domeniu": "mediu"},
    {"nume_oficial": "Asociația Ecopolis", "query": "Ecopolis",
     "variante": ["ecopolis", "asociatia ecopolis"], "domeniu": "mediu"},
    {"nume_oficial": "Asociația ECOLEGAL", "query": "Ecolegal",
     "variante": ["ecolegal", "asociatia ecolegal"], "domeniu": "mediu"},
    {"nume_oficial": "Centrul Independent pentru Dezvoltarea Resurselor de Mediu (CIDRM)",
     "query": "Resurselor de Mediu",
     "variante": ["centrul independent pentru dezvoltarea resurselor de mediu", "cidrm"], "domeniu": "mediu"},
    {"nume_oficial": "Asociația Alburnus Maior", "query": "Alburnus Maior",
     "variante": ["alburnus maior", "alburnus major", "asociatia alburnus maior"], "domeniu": "mediu"},
    {"nume_oficial": "Mining Watch România", "query": "Mining Watch",
     "variante": ["mining watch", "miningwatch", "asociatia mining watch"], "domeniu": "mediu"},
    {"nume_oficial": "Fundația TERRA Mileniul III", "query": "TERRA Mileniul III",
     "variante": ["terra mileniul iii", "terra mileniul 3", "fundatia terra mileniul"], "domeniu": "mediu"},
    # --- muncă (sindicate / federații) ---
    {"nume_oficial": "Blocul Național Sindical (BNS)", "query": "Blocul National Sindical",
     "variante": ["blocul national sindical", "bns"], "domeniu": "munca"},
    {"nume_oficial": "CNS Cartel ALFA", "query": "Cartel ALFA",
     "variante": ["cartel alfa", "confederatia nationala sindicala cartel alfa"], "domeniu": "munca"},
    {"nume_oficial": "CNSLR-Frăția", "query": "CNSLR Fratia",
     "variante": ["cnslr fratia", "confederatia nationala a sindicatelor libere din romania fratia"],
     "domeniu": "munca"},
    {"nume_oficial": "Confederația Sindicatelor Democratice din România (CSDR)",
     "query": "Sindicatelor Democratice din Romania",
     "variante": ["confederatia sindicatelor democratice din romania", "csdr"], "domeniu": "munca"},
    {"nume_oficial": "CSN Meridian", "query": "CSN Meridian",
     "variante": ["confederatia sindicala nationala meridian", "csn meridian"], "domeniu": "munca"},
    {"nume_oficial": "Federația Sindicatelor Libere din Învățământ (FSLI)",
     "query": "Sindicatelor Libere din Invatamant",
     "variante": ["federatia sindicatelor libere din invatamant", "fsli"], "domeniu": "munca"},
    {"nume_oficial": "Federația Sindicatelor din Educație „Spiru Haret\"", "query": "Spiru Haret",
     "variante": ["spiru haret", "federatia sindicatelor din educatie spiru haret"], "domeniu": "munca"},
    {"nume_oficial": "Federația SANITAS", "query": "SANITAS",
     "variante": ["sanitas", "federatia sanitas"], "domeniu": "munca"},
    {"nume_oficial": "Federația „Solidaritatea Sanitară\"", "query": "Solidaritatea Sanitara",
     "variante": ["solidaritatea sanitara", "federatia solidaritatea sanitara"], "domeniu": "munca"},
    # --- sănătate / pacienți ---
    {"nume_oficial": "Federația Asociațiilor Bolnavilor de Cancer (FABC)", "query": "Bolnavilor de Cancer",
     "variante": ["federatia asociatiilor bolnavilor de cancer", "fabc"], "domeniu": "sanatate"},
    {"nume_oficial": "Coaliția Organizațiilor Pacienților cu Afecțiuni Cronice (COPAC)", "query": "COPAC",
     "variante": ["copac", "coalitia organizatiilor pacientilor"], "domeniu": "sanatate"},
    {"nume_oficial": "Asociația Națională pentru Protecția Pacienților (ANPP)", "query": "Protectia Pacientilor",
     "variante": ["asociatia nationala pentru protectia pacientilor", "anpp"], "domeniu": "sanatate"},
    # --- alte interese colective ---
    {"nume_oficial": "Asociația ACCEPT", "query": "Asociatia ACCEPT",
     "variante": ["asociatia accept"], "domeniu": "alt"},
    {"nume_oficial": "Romani CRISS", "query": "Romani CRISS",
     "variante": ["romani criss", "centrul romilor pentru interventie sociala si studii"], "domeniu": "alt"},
    {"nume_oficial": "Centrul de Resurse Juridice (CRJ)", "query": "Centrul de Resurse Juridice",
     "variante": ["centrul de resurse juridice", "crj"], "domeniu": "alt"},
    {"nume_oficial": "APADOR-CH (Comitetul Helsinki)", "query": "APADOR",
     "variante": ["apador", "apador ch", "comitetul helsinki"], "domeniu": "alt"},
    {"nume_oficial": "Federația Asociațiilor de Proprietari din România (FAPR)",
     "query": "Federatia Asociatiilor de Proprietari",
     "variante": ["federatia asociatiilor de proprietari din romania", "fapr"], "domeniu": "alt"},
]


# --- Markeri EXPLICIȚI de acțiune colectivă / în reprezentare (semnal de scor) -
MARKERI_COLECTIV: tuple[str, ...] = (
    "actiune in reprezentare",
    "in reprezentare",
    "interese colective",
    "interesele colective",
    "protectia intereselor colective ale consumatorilor",
    "actiune in interes colectiv",
    "actiune colectiva",
    "drepturi colective",
    "incetare clauze abuzive",
    "incetare a practicilor comerciale incorecte",
)

# --- Frază(e) de obiect pentru SCANARE (interogare numeObiect) — păstrăm și forma
#     cu diacritice, fiindcă ECRIS pare să facă match exact pe textul stocat.
OBIECTE_QUERY: tuple[str, ...] = (
    "acţiune în reprezentare",
    "actiune in reprezentare",
    "interese colective",
    "interesele colective ale consumatorilor",
    "acţiune colectivă",
    "actiune colectiva",
)

# --- Cuvinte-cheie DISTINCTIVE de domeniu (doar pentru etichetare/scor +15) ---
# Intenționat fără frazări generice ("pretentii", "obligatie de a face", "anulare act
# administrativ") care ar eticheta greșit aproape orice dosar.
DOMENII_OBIECTE: dict[str, tuple[str, ...]] = {
    "bancar": (
        "clauze abuzive", "contract de credit", "comision", "dobanda",
        "recalculare credit", "inghetare curs", "franci elvetieni", "chf",
        "credite chf", "robor", "ifn",
    ),
    "consumatori": (
        "consumator", "practici comerciale incorecte", "practici comerciale inselatoare",
        "produs cu defect",
    ),
    "mediu": (
        "poluare", "deseuri", "emisii", "defrisare", "arie protejata",
        "protectia mediului", "acord de mediu", "aviz de mediu", "autorizatie de mediu",
        "amenajament silvic", "plan urbanistic", "calitatea aerului", "zgomot",
        "gospodarire a apelor",
    ),
    "munca": (
        "litigiu de munca", "litigii de munca", "drepturi salariale",
        "concediere colectiva", "drepturi banesti",
    ),
}

# --- Markeri de EXCLUDERE (litigiu pur individual/familial/administrativ → respins) -
MARKERI_EXCLUDERE: tuple[str, ...] = (
    # familial / personal
    "divort", "partaj", "succesiune", "mostenire", "pensie de intretinere",
    "ordin de protectie", "tagada paternitate", "stabilire paternitate",
    "incredintare minor", "stabilire domiciliu minor", "exercitarea autoritatii parintesti",
    "punere sub interdictie", "tutela", "curatela", "uzucapiune", "granituire",
    "iesire din indiviziune", "exequatur", "evacuare", "inregistrare tardiva nastere",
    "rectificare act de stare civila",
    # executare individuală
    "validare poprire", "contestatie la executare", "recuperare cote intretinere",
    # viața corporativă a unei asociații (nu acțiune în reprezentare)
    "acte constitutive", "modificare acte constitutive", "og 26 2000", "dizolvare",
    "lichidare", "inscriere persoana juridica",
    "inregistrare in registrul asociatiilor si fundatiilor",
)


# ============================================================================
#  VALURI DE LITIGII (clustering): pârâți de masă + bucket-uri de obiect
#  (date îmbogățite prin workflow `cercetare-parati-de-masa-ro`)
# ============================================================================

class ParatMasa(TypedDict):
    nume_oficial: str
    query: str
    variante: list[str]
    domeniu: str


# Instituții acționate în mii de dosare individuale identice. `query` = substring
# generic care prinde toate filialele (ex. toate cele 41 de case județene).
# Sursă: workflow `cercetare-parati-de-masa-ro`. Utilitățile de energie sunt EXCLUSE
# intenționat: acolo valul mare e furnizorul ca RECLAMANT (recuperare debite), nu pârât.
PARATI_MASA: list[ParatMasa] = [
    # --- pensii ---
    {"nume_oficial": "Casa Județeană de Pensii", "query": "Casa Judeteana de Pensii",
     "variante": ["casa judeteana de pensii", "cjp"], "domeniu": "pensii"},
    {"nume_oficial": "Casa Teritorială de Pensii", "query": "Casa Teritoriala de Pensii",
     "variante": ["casa teritoriala de pensii", "ctp"], "domeniu": "pensii"},
    {"nume_oficial": "Casa de Pensii a Municipiului București", "query": "Casa de Pensii a Municipiului Bucuresti",
     "variante": ["casa de pensii a municipiului bucuresti", "cpmb"], "domeniu": "pensii"},
    {"nume_oficial": "Casa Locală de Pensii", "query": "Casa Locala de Pensii",
     "variante": ["casa locala de pensii", "clp"], "domeniu": "pensii"},
    {"nume_oficial": "Casa Națională de Pensii Publice (CNPP)", "query": "Casa Nationala de Pensii",
     "variante": ["casa nationala de pensii", "cnpp"], "domeniu": "pensii"},
    # --- fiscal ---
    {"nume_oficial": "ANAF", "query": "Agentia Nationala de Administrare Fiscala",
     "variante": ["agentia nationala de administrare fiscala", "anaf"], "domeniu": "fiscal"},
    {"nume_oficial": "DGRFP (Finanțe regionale)", "query": "Directia Generala Regionala a Finantelor Publice",
     "variante": ["directia generala regionala a finantelor publice", "dgrfp", "dgfp"], "domeniu": "fiscal"},
    {"nume_oficial": "AJFP (Finanțe județene)", "query": "Administratia Judeteana a Finantelor Publice",
     "variante": ["administratia judeteana a finantelor publice", "ajfp",
                  "administratia finantelor publice", "afp"], "domeniu": "fiscal"},
    {"nume_oficial": "Marii Contribuabili (DGAMC)", "query": "Directia Generala de Administrare a Marilor Contribuabili",
     "variante": ["directia generala de administrare a marilor contribuabili", "dgamc"], "domeniu": "fiscal"},
    {"nume_oficial": "Ministerul Finanțelor", "query": "Ministerul Finantelor",
     "variante": ["ministerul finantelor", "mfp"], "domeniu": "fiscal"},
    # --- muncă (angajatori publici) ---
    {"nume_oficial": "Inspectoratul Școlar", "query": "Inspectoratul Scolar",
     "variante": ["inspectoratul scolar", "isj", "ismb"], "domeniu": "munca"},
    {"nume_oficial": "Ministerul Educației", "query": "Ministerul Educatiei",
     "variante": ["ministerul educatiei", "men", "mects"], "domeniu": "munca"},
    {"nume_oficial": "Unitate de învățământ (școală/liceu/colegiu)", "query": "Scoala Gimnaziala",
     "variante": ["scoala gimnaziala", "liceul", "colegiul national", "gradinita"], "domeniu": "munca"},
    {"nume_oficial": "Spital public", "query": "Spitalul",
     "variante": ["spitalul judetean", "spitalul municipal", "spitalul clinic", "spitalul orasenesc"],
     "domeniu": "munca"},
    {"nume_oficial": "Primărie / UAT (angajator + restituiri)", "query": "Primaria",
     "variante": ["primaria", "consiliul local", "comuna", "municipiul"], "domeniu": "munca"},
    {"nume_oficial": "Poliția Locală", "query": "Politia Locala",
     "variante": ["politia locala"], "domeniu": "munca"},
    {"nume_oficial": "DGASPC (Asistență socială)", "query": "Directia Generala de Asistenta Sociala",
     "variante": ["directia generala de asistenta sociala", "dgaspc"], "domeniu": "munca"},
    # --- sănătate ---
    {"nume_oficial": "CNAS", "query": "Casa Nationala de Asigurari de Sanatate",
     "variante": ["casa nationala de asigurari de sanatate", "cnas"], "domeniu": "sanatate"},
    {"nume_oficial": "Casa de Asigurări de Sănătate (CJAS/CASMB)", "query": "Casa de Asigurari de Sanatate",
     "variante": ["casa de asigurari de sanatate", "cjas", "casmb"], "domeniu": "sanatate"},
    {"nume_oficial": "Ministerul Sănătății", "query": "Ministerul Sanatatii",
     "variante": ["ministerul sanatatii"], "domeniu": "sanatate"},
    {"nume_oficial": "Agenția Medicamentului (ANMDMR)", "query": "Agentia Nationala a Medicamentului",
     "variante": ["agentia nationala a medicamentului", "anmdmr", "anmdm"], "domeniu": "sanatate"},
    # --- proprietăți (restituiri / despăgubiri) ---
    {"nume_oficial": "ANRP", "query": "Autoritatea Nationala pentru Restituirea Proprietatilor",
     "variante": ["autoritatea nationala pentru restituirea proprietatilor", "anrp"], "domeniu": "proprietati"},
    {"nume_oficial": "Comisia Națională pentru Compensarea Imobilelor (CNCI)",
     "query": "Comisia Nationala pentru Compensarea Imobilelor",
     "variante": ["comisia nationala pentru compensarea imobilelor", "cnci"], "domeniu": "proprietati"},
    {"nume_oficial": "Comisia Județeană de Fond Funciar", "query": "Comisia Judeteana pentru Stabilirea Dreptului de Proprietate",
     "variante": ["comisia judeteana pentru stabilirea dreptului de proprietate", "comisia judeteana de fond funciar"],
     "domeniu": "proprietati"},
    {"nume_oficial": "Comisia Locală de Fond Funciar", "query": "Comisia Locala de Fond Funciar",
     "variante": ["comisia locala de fond funciar"], "domeniu": "proprietati"},
    # --- agricultură ---
    {"nume_oficial": "APIA", "query": "Agentia de Plati si Interventie pentru Agricultura",
     "variante": ["agentia de plati si interventie pentru agricultura", "apia"], "domeniu": "agricultura"},
    {"nume_oficial": "AFIR (fosta APDRP)", "query": "Agentia pentru Finantarea Investitiilor Rurale",
     "variante": ["agentia pentru finantarea investitiilor rurale", "afir", "apdrp"], "domeniu": "agricultura"},
    # --- bancar (valuri CHF / clauze abuzive, banca = pârât) ---
    {"nume_oficial": "OTP Bank România", "query": "OTP Bank", "variante": ["otp bank"], "domeniu": "bancar"},
    {"nume_oficial": "Volksbank (preluată de Banca Transilvania)", "query": "Volksbank",
     "variante": ["volksbank"], "domeniu": "bancar"},
    {"nume_oficial": "Bancpost (preluată de Banca Transilvania)", "query": "Bancpost",
     "variante": ["bancpost"], "domeniu": "bancar"},
    {"nume_oficial": "Piraeus Bank / First Bank", "query": "Piraeus Bank",
     "variante": ["piraeus bank", "first bank"], "domeniu": "bancar"},
    {"nume_oficial": "Raiffeisen Bank", "query": "Raiffeisen Bank", "variante": ["raiffeisen bank"], "domeniu": "bancar"},
    {"nume_oficial": "Credit Europe Bank", "query": "Credit Europe Bank", "variante": ["credit europe bank"], "domeniu": "bancar"},
    {"nume_oficial": "Banca Românească", "query": "Banca Romaneasca", "variante": ["banca romaneasca"], "domeniu": "bancar"},
    {"nume_oficial": "Banca Transilvania", "query": "Banca Transilvania", "variante": ["banca transilvania"], "domeniu": "bancar"},
    # --- imobiliare (dezvoltatori cu mii de cumpărători păgubiți) ---
    {"nume_oficial": "Nordis (Management / Mamaia / Group)", "query": "Nordis",
     "variante": ["nordis management", "nordis mamaia", "nordis group", "nordis"],
     "domeniu": "imobiliare"},
    # --- alt (compensații pasageri aerieni) ---
    {"nume_oficial": "Wizz Air", "query": "Wizz Air", "variante": ["wizz air", "wizzair"], "domeniu": "alt"},
    {"nume_oficial": "TAROM", "query": "TAROM", "variante": ["tarom"], "domeniu": "alt"},
    {"nume_oficial": "Blue Air", "query": "Blue Air", "variante": ["blue air"], "domeniu": "alt"},
    {"nume_oficial": "Ryanair", "query": "Ryanair", "variante": ["ryanair"], "domeniu": "alt"},
    # --- asigurări (falimente RCA + asigurători activi + FGA) ---
    {"nume_oficial": "City Insurance (în faliment)", "query": "city insurance",
     "variante": ["city insurance", "asigurare reasigurare city insurance"], "domeniu": "asigurari"},
    {"nume_oficial": "Euroins România (în faliment)", "query": "euroins",
     "variante": ["euroins"], "domeniu": "asigurari"},
    {"nume_oficial": "Astra Asigurări (în faliment)", "query": "astra asigurari",
     "variante": ["astra asigurari", "asigurare reasigurare astra"], "domeniu": "asigurari"},
    {"nume_oficial": "Fondul de Garantare a Asiguraților (FGA)", "query": "fondul de garantare a asigurat",
     "variante": ["fondul de garantare a asiguratilor", "fga"], "domeniu": "asigurari"},
    {"nume_oficial": "Allianz-Țiriac Asigurări", "query": "allianz", "variante": ["allianz tiriac", "allianz"], "domeniu": "asigurari"},
    {"nume_oficial": "Omniasig VIG", "query": "omniasig", "variante": ["omniasig"], "domeniu": "asigurari"},
    {"nume_oficial": "Groupama Asigurări", "query": "groupama", "variante": ["groupama"], "domeniu": "asigurari"},
    {"nume_oficial": "Generali România", "query": "generali", "variante": ["generali"], "domeniu": "asigurari"},
    {"nume_oficial": "Asirom VIG", "query": "asirom", "variante": ["asirom"], "domeniu": "asigurari"},
    # --- recuperare creanțe / IFN ---
    {"nume_oficial": "KRUK România", "query": "kruk", "variante": ["kruk romania", "kruk"], "domeniu": "recuperare"},
    {"nume_oficial": "Investcapital (grup KRUK)", "query": "investcapital", "variante": ["investcapital"], "domeniu": "recuperare"},
    {"nume_oficial": "Secapital (grup KRUK)", "query": "secapital", "variante": ["secapital"], "domeniu": "recuperare"},
    {"nume_oficial": "Prosperocapital (grup KRUK)", "query": "prosperocapital", "variante": ["prospero capital", "prosperocapital"], "domeniu": "recuperare"},
    {"nume_oficial": "EOS KSI România", "query": "eos ksi", "variante": ["eos ksi"], "domeniu": "recuperare"},
    {"nume_oficial": "Kredyt Inkaso / Best Capital", "query": "kredyt inkaso", "variante": ["kredyt inkaso", "best capital"], "domeniu": "recuperare"},
    {"nume_oficial": "APS (Asset Portfolio Servicing)", "query": "asset portfolio servicing", "variante": ["asset portfolio servicing", "aps recovery"], "domeniu": "recuperare"},
    {"nume_oficial": "Coface România", "query": "coface", "variante": ["coface"], "domeniu": "recuperare"},
    {"nume_oficial": "Provident Financial România IFN", "query": "provident", "variante": ["provident financial"], "domeniu": "recuperare"},
    {"nume_oficial": "Credius IFN", "query": "credius", "variante": ["credius"], "domeniu": "recuperare"},
    {"nume_oficial": "Viva Credit IFN", "query": "viva credit", "variante": ["viva credit"], "domeniu": "recuperare"},
    {"nume_oficial": "Hora Credit IFN", "query": "hora credit", "variante": ["hora credit"], "domeniu": "recuperare"},
    # --- telecom (semnal colectiv doar când e PÂRÂT) ---
    {"nume_oficial": "Orange România", "query": "orange romania", "variante": ["orange romania"], "domeniu": "telecom"},
    {"nume_oficial": "Vodafone România", "query": "vodafone romania", "variante": ["vodafone romania"], "domeniu": "telecom"},
    {"nume_oficial": "Digi / RCS & RDS", "query": "rcs", "variante": ["rcs rds", "digi romania"], "domeniu": "telecom"},
    {"nume_oficial": "Telekom România Mobile", "query": "telekom romania mobile", "variante": ["telekom romania mobile", "cosmote"], "domeniu": "telecom"},
    # --- retail / garanții produse ---
    {"nume_oficial": "eMAG (Dante International)", "query": "dante international", "variante": ["dante international"], "domeniu": "retail"},
    {"nume_oficial": "Altex România", "query": "altex", "variante": ["altex"], "domeniu": "retail"},
    {"nume_oficial": "Flanco Retail", "query": "flanco", "variante": ["flanco"], "domeniu": "retail"},
    {"nume_oficial": "Dedeman", "query": "dedeman", "variante": ["dedeman"], "domeniu": "retail"},
    # --- turism / transport ---
    {"nume_oficial": "Omnia Turism", "query": "omnia turism", "variante": ["omnia turism"], "domeniu": "turism"},
    {"nume_oficial": "Genius Travel", "query": "genius travel", "variante": ["genius travel"], "domeniu": "turism"},
    {"nume_oficial": "Christian Tour", "query": "christian tour", "variante": ["christian tour"], "domeniu": "turism"},
    {"nume_oficial": "Paralela 45", "query": "paralela 45", "variante": ["paralela 45"], "domeniu": "turism"},
    {"nume_oficial": "CFR Călători", "query": "cfr calatori", "variante": ["cfr calatori"], "domeniu": "turism"},
    # --- investiții / fraude ---
    {"nume_oficial": "AAAS (fosta AVAS) — investitori FNI", "query": "autoritatea pentru administrarea activelor statului",
     "variante": ["autoritatea pentru administrarea activelor statului", "aaas", "avas"], "domeniu": "investitii"},
    {"nume_oficial": "SOV Invest / FNI", "query": "sov invest", "variante": ["sov invest", "fondul national de investitii"], "domeniu": "investitii"},
    # --- servicii cu abonament (fitness / educație privată / clinici) ---
    {"nume_oficial": "World Class România", "query": "world class", "variante": ["world class", "vectr fitness"], "domeniu": "servicii"},
    {"nume_oficial": "Univ. Spiru Haret (Fundația România de Mâine)", "query": "spiru haret", "variante": ["spiru haret", "fundatia romania de maine"], "domeniu": "servicii"},
    {"nume_oficial": "Univ. Dimitrie Cantemir", "query": "dimitrie cantemir", "variante": ["dimitrie cantemir"], "domeniu": "servicii"},
    {"nume_oficial": "Univ. Vasile Goldiș Arad", "query": "vasile goldis", "variante": ["vasile goldis"], "domeniu": "servicii"},
    {"nume_oficial": "MedLife", "query": "medlife", "variante": ["medlife"], "domeniu": "servicii"},
    {"nume_oficial": "Regina Maria (Centrul Medical Unirea)", "query": "centrul medical unirea", "variante": ["centrul medical unirea", "regina maria"], "domeniu": "servicii"},
    {"nume_oficial": "Medicover", "query": "medicover", "variante": ["medicover"], "domeniu": "servicii"},
]


class Bucket(TypedDict):
    label: str
    domeniu: str
    chei: list[str]


# Tipuri canonice de obiect — variantele care conțin una dintre `chei` (normalizate)
# se grupează sub aceeași etichetă. Altfel se folosește un fallback (primele cuvinte).
# Ordinea contează: bucket-urile mai specifice înaintea celor generice.
BUCKETE_OBIECT: list[Bucket] = [
    # pensii
    {"label": "Contestație decizie de pensionare", "domeniu": "pensii",
     "chei": ["contestatie decizie de pensionare", "contestatie decizie pensionare",
              "anulare decizie de pensie", "contestatie decizie de pensie"]},
    {"label": "Recalculare pensie", "domeniu": "pensii",
     "chei": ["recalculare pensi", "recalculare drepturi de pensie", "recalculare drepturi pensie"]},
    {"label": "Drepturi de asigurări sociale", "domeniu": "pensii",
     "chei": ["drepturi de asigurari sociale", "asigurari sociale"]},
    # fiscal
    {"label": "Restituire taxă auto / timbru de mediu", "domeniu": "fiscal",
     "chei": ["restituire taxa", "timbru de mediu", "taxa de poluare", "taxa auto", "taxa speciala"]},
    {"label": "Contestație decizie de impunere / act fiscal", "domeniu": "fiscal",
     "chei": ["contestatie act administrativ fiscal", "anulare decizie de impunere",
              "contestatie decizie de impunere", "anulare act administrativ fiscal"]},
    {"label": "Contestație la executare fiscală", "domeniu": "fiscal",
     "chei": ["anulare poprire", "suspendare executare silita", "contestatie la executare"]},
    # muncă
    {"label": "Sporuri / spor condiții de muncă", "domeniu": "munca",
     "chei": ["spor conditii", "sporuri", "transe de vechime", "supliment post", "prima de vacanta"]},
    {"label": "Drepturi salariale", "domeniu": "munca",
     "chei": ["drepturi salariale", "diferente salariale", "recalculare drepturi salariale",
              "recalculare salarii", "actualizare drepturi salariale", "drepturi banesti",
              "obligare la plata"]},
    # sănătate
    {"label": "Acces tratament/medicamente (ordonanță președințială)", "domeniu": "sanatate",
     "chei": ["ordonanta presedintiala", "includere medicament", "decontare", "medicament"]},
    # proprietăți
    {"label": "Fond funciar", "domeniu": "proprietati",
     "chei": ["fond funciar", "lege 18 1991", "titlu de proprietate", "reconstituirea dreptului",
              "punere in posesie"]},
    {"label": "Despăgubiri / compensare imobile (L.10/2001, L.165/2013)", "domeniu": "proprietati",
     "chei": ["lege 10 2001", "lege 165", "lege 247 2005", "despagubir", "decizie de compensare",
              "masuri reparatorii", "restituire imobil", "titlu de despagubire", "dispozitie de restituire"]},
    # agricultură
    {"label": "Anulare decizie/debit subvenții (APIA/AFIR)", "domeniu": "agricultura",
     "chei": ["anulare decizie de plata", "nota de debit", "decizie de reziliere",
              "proces verbal de constatare", "proces verbal de receptie"]},
    # insolvență (cross-domeniu: domeniul vine de la pârât) — ex. creditori-victime
    # care contestă tabelul de creanțe în falimentul unui dezvoltator
    {"label": "Contestație creanțe (insolvență)", "domeniu": "",
     "chei": ["contestatie creante", "tabel preliminar", "tabelul preliminar",
              "creante impotriva tabelului", "contestatie tabel", "tabel de creante",
              "tabelul de creante", "tabelul definitiv"]},
    # imobiliare (dezvoltatori — ex. Nordis: apartamente vândute multiplu / nelivrate)
    {"label": "Rezoluțiune / desființare contract", "domeniu": "imobiliare",
     "chei": ["rezolutiune", "desfiintare contract", "reziliere contract", "rezilierea contractului"]},
    {"label": "Hotărâre care ține loc de act (predare imobil)", "domeniu": "imobiliare",
     "chei": ["hotarare care sa tina loc", "hotarare care tina loc", "sa tina loc de act"]},
    {"label": "Restituire avans / preț apartament", "domeniu": "imobiliare",
     "chei": ["restituire avans", "restituire pret", "restituire arvuna"]},
    {"label": "Plângere carte funciară", "domeniu": "imobiliare",
     "chei": ["carte funciara", "plangere impotriva incheierii"]},
    # bancar
    {"label": "Clauze abuzive bancare / CHF", "domeniu": "bancar",
     "chei": ["clauze abuzive", "nulitate absoluta clauze", "inghetare curs", "chf",
              "franci elvetieni", "constatare nulitate act"]},
    # aerian (obiect generic → discriminantul e pârâtul)
    {"label": "Compensații pasageri aerieni", "domeniu": "alt",
     "chei": ["despagubir", "raspundere contractuala"]},
]


# Domeniile AGREATE cu userul (scop „mediu"): consumatori + bancar + mediu.
# munca/sanatate/alt rămân în registru pentru extindere viitoare (opt-in), dar nu
# sunt scanate implicit — sindicatele/autoritățile generează volume uriașe de litigii
# individuale care ar dilua portalul.
DOMENII_IN_SCOP: tuple[str, ...] = ("consumatori", "bancar", "mediu")


def query_names(domenii: tuple[str, ...] | None = None) -> list[str]:
    """Substring-urile de căutare pentru asociațiile din domeniile date (sau toate)."""
    return [a["query"] for a in ASOCIATII if domenii is None or a["domeniu"] in domenii]


# Catalog EXTINS de tipuri de obiect pentru descoperire, pe domenii suplimentare
# (asigurări, telecom, recuperare creanțe, retail, turism, investiții, servicii...).
# Completat din workflow `extindere-domenii-zamolxis`. {query, label, domeniu}.
OBIECTE_DESCOPERIRE: list[dict] = [
    # asigurări (falimente RCA: City Insurance, Euroins, Astra + FGA)
    {"query": "contestatie decizie respingere cerere de plata fond garantare", "label": "Contestație decizie FGA de respingere a plății", "domeniu": "asigurari"},
    {"query": "contestatie decizie fond de garantare a asiguratilor", "label": "Contestație decizie FGA (L.213/2015)", "domeniu": "asigurari"},
    {"query": "contestatie tabel creante asigurator faliment", "label": "Contestație tabel creanțe (faliment asigurător)", "domeniu": "asigurari"},
    {"query": "pretentii despagubiri rca asigurator faliment", "label": "Despăgubiri RCA de la asigurător în faliment", "domeniu": "asigurari"},
    {"query": "pretentii asigurare casco daune", "label": "Despăgubire CASCO / daune", "domeniu": "asigurari"},
    {"query": "restituire prima de asigurare reziduala faliment asigurator", "label": "Restituire primă reziduală (poliță încetată la faliment)", "domeniu": "asigurari"},
    # recuperare creanțe / IFN
    {"query": "constatare nulitate clauze abuzive", "label": "Clauze abuzive credit de consum", "domeniu": "recuperare"},
    {"query": "contestatie la poprire", "label": "Contestație la poprire (recuperator)", "domeniu": "recuperare"},
    # telecom
    {"query": "rezolutiune contract", "label": "Reziliere/rezoluțiune abonament telecom", "domeniu": "telecom"},
    {"query": "drepturi consumatori", "label": "Litigiu protecția consumatorilor vs. operator", "domeniu": "telecom"},
    # retail / garanții
    {"query": "rezolutiune contract vanzare cumparare bun mobil", "label": "Rezoluțiune vânzare bun cu defect", "domeniu": "retail"},
    {"query": "obligatia de a face inlocuire produs neconform garantie", "label": "Înlocuire/reparare produs în garanție (OUG 140/2021)", "domeniu": "retail"},
    {"query": "actiune in raspundere pentru vicii ascunse bun vandut", "label": "Vicii ascunse ale bunului vândut", "domeniu": "retail"},
    {"query": "rezolutiune contract restituire pret produs defect", "label": "Rezoluțiune + restituire preț produs defect", "domeniu": "retail"},
    # turism / transport pasageri
    {"query": "pretentii pachet turistic", "label": "Preț pachet turistic neonorat", "domeniu": "turism"},
    {"query": "restituire pret pachet servicii turistice", "label": "Restituire preț pachet turistic", "domeniu": "turism"},
    {"query": "rezolutiune contract servicii turistice", "label": "Rezoluțiune contract servicii turistice", "domeniu": "turism"},
    {"query": "despagubiri pachet turistic neexecutat", "label": "Despăgubiri pachet turistic neexecutat", "domeniu": "turism"},
    {"query": "compensatie pasageri zbor intarziat anulat", "label": "Compensație pasageri aerieni (Reg. 261/2004)", "domeniu": "turism"},
    {"query": "restituire contravaloare bilet avion", "label": "Restituire contravaloare bilet avion", "domeniu": "turism"},
    {"query": "despagubiri intarziere tren restituire bilet", "label": "Despăgubiri întârziere tren / bilet feroviar", "domeniu": "turism"},
    # imobiliare extins
    {"query": "rezolutiune antecontract de vanzare cumparare", "label": "Rezoluțiune antecontract + restituire avans", "domeniu": "imobiliare"},
    {"query": "obligatia de a incheia contractul de vanzare in forma autentica", "label": "Obligare la actul autentic (refuz dezvoltator)", "domeniu": "imobiliare"},
    {"query": "penalitati de intarziere predare imobil", "label": "Penalități întârziere predare apartament", "domeniu": "imobiliare"},
    {"query": "restituire avans antecontract", "label": "Restituire avans antecontract apartament", "domeniu": "imobiliare"},
    # investiții / fraude
    {"query": "imbogatire fara justa cauza", "label": "Îmbogățire fără justă cauză (restituire sume)", "domeniu": "investitii"},
    {"query": "despagubiri investitori fni", "label": "Despăgubiri investitori FNI (vs. stat/AAAS)", "domeniu": "investitii"},
    # servicii cu abonament (fitness, educație privată, clinici)
    {"query": "actiune in constatare clauze abuzive abonament", "label": "Clauze abuzive în contract de abonament", "domeniu": "servicii"},
    {"query": "reziliere contract prestari servicii restituire taxa", "label": "Reziliere abonament + restituire taxă", "domeniu": "servicii"},
    {"query": "restituire taxa de scolarizare", "label": "Restituire taxă școlarizare (educație privată)", "domeniu": "servicii"},
    {"query": "pretentii penalitati reziliere anticipata abonament", "label": "Penalități reziliere anticipată abonament", "domeniu": "servicii"},
]


def obiecte_descoperire(domenii: tuple[str, ...] | None = None) -> list[dict]:
    """Tipurile de obiect folosite pentru DESCOPERIREA automată de pârâți de masă:
    cele derivate din BUCKETE_OBIECT + catalogul extins OBIECTE_DESCOPERIRE.
    Dedup pe (query, domeniu); filtru opțional pe domenii."""
    out, vazute = [], set()
    surse = [
        {"query": b["chei"][0], "label": b["label"], "domeniu": b["domeniu"]}
        for b in BUCKETE_OBIECT if b["domeniu"] and b["chei"]
    ] + OBIECTE_DESCOPERIRE
    for o in surse:
        if domenii is not None and o["domeniu"] not in domenii:
            continue
        cheie = (o["query"], o["domeniu"])
        if cheie in vazute:
            continue
        vazute.add(cheie)
        out.append(o)
    return out

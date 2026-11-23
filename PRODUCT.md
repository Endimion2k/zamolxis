# Păgubiți.ro

## Ce este
Un site static, gratuit, care arată acțiunile colective și „valurile" de procese identice din instanțele din România. Datele vin din web service-ul public portal.just.ro, scanat automat săptămânal. Persoanele fizice sunt anonimizate.

## Pentru cine
Omul păgubit: un pensionar căruia Casa de Pensii i-a calculat greșit pensia, un client Nordis care nu și-a primit apartamentul, un asigurat City Insurance sau Euroins, un datornic executat de un recuperator. Caută numele firmei sau al instituției, de pe telefon, adesea emoționat, și vrea un singur răspuns: mai sunt și alții ca mine? Câți? Unde?

Secundar: jurnaliști și avocați care explorează valurile.

## Ce trebuie să facă vizitatorul
1. Să caute firma, instituția sau problema lui.
2. Să vadă câte dosare identice există, împotriva cui, la ce instanțe, în ce perioadă.
3. Să meargă pe portal.just.ro să verifice.

## Adevăruri de produs (nu se inventează)
- Cifrele vin doar din data.json: număr de acțiuni colective, confirmate, valuri, dosare per val.
- Informație orientativă, nu consultanță juridică. Clasificarea automată poate greși („De verificat").
- Fără mărturii, fără parteneri, fără statistici de business.

## Angajamente de brand
- Nume: Păgubiți.ro. Promisiune: „Nu ești singur."
- Ton: editorial, sobru, ca o publicație de date sau un registru public. Direct, fără patos.
- Limbă: română, cu diacritice corecte.

## Constrângeri tehnice
- HTML + CSS + JS vanilla, fără build, servit de GitHub Pages din `web/`.
- `data.json` (~370 KB) e încărcat client-side; căutarea e locală.
- Trebuie să meargă bine pe telefon și fără animații.

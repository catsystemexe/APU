# PRIORITA CASE INFO — APU NOTEPAD
## Kritické pravidlo
Informace o případu (Case Info) musí být strukturovány podle priority, ne podle pohodlí implementace.
APU nesmí dělat silnou inference bez splnění minimálních podmínek.
Minimální podmínky jsou:
1. Pozorovaný jev (observable)
2. Potřeba učitele (need)
Teprve poté:
3. Kontext
4. Intenzita / trend
Bez bodu 1 a 2 je inference výrazně oslabená nebo se musí zastavit.
---
# Pořadí a priorita
## 1. Pozorovaný jev (observable) — POVINNÉ
Nejdůležitější vrstva.
Observable znamená:
něco, co lze přímo vidět nebo slyšet.
Například:
- bere dětem hračky
- rozpláče se při příchodu
- zakrývá si uši při hluku
- přestane mluvit po upozornění
- odbíhá od stolu
Bez validního observable:
APU nesmí inferovat bloky, profily ani zóny.
### Důležité
Interpretation label není observable.
Například:
- dítě zlobí
- manipuluje
- je líné
- je protivné
- dělá to schválně
Tyto výroky se zapisují jako:
⚠ teacher_interpretation_labels
a vyžadují upřesnění.
Nejsou validní observable.
---
## 2. Potřeba učitele (need) — POVINNÉ
Druhá povinná vrstva.
Need znamená:
co chce pedagog skutečně řešit.
Ne:
co si myslí APU.
Například:
- potřebuji rychle zklidnit situaci
- potřebuji udržet skupinu
- chci porozumět příčině
- potřebuji komunikaci s rodiči
- potřebuji dlouhodobý plán
Bez need:
APU sice může popsat situaci,
ale neví, jaký typ výstupu má být prioritní.
Proto je inference bez need neúplná.
### Důležité
APU nesmí need domýšlet.
Pokud není známý:
→ zapisuje se open question
Například:
„Co je teď hlavní cíl podpory?“
---
## 3. Kontext — DOPLŇUJÍCÍ
Kontext odpovídá na:
kdy / kde / s kým / při čem
Například:
- při volné hře
- při obědě
- při přechodu z venku
- hlavně u jedné učitelky
- odpoledne při únavě
Kontext zvyšuje kvalitu inference,
ale sám nestačí.
Bez observable není kontext dostatečný.
---
## 4. Intenzita / trend — DOPLŇUJÍCÍ
Trend odpovídá na:
jak často / jak dlouho / zda se to mění
Například:
- poprvé
- občas
- každý den
- poslední dva týdny
- zhoršuje se
- jen ve školce
Trend upravuje confidence,
ale není náhradou observable.
„Zhoršuje se to“
bez informace co přesně,
není použitelný vstup.
---
# Praktické pravidlo pipeline
## Validní minimum pro kvalitní inference
```text
observable + need

Toto je minimální bezpečný základ.

⸻

Silnější inference

observable + need + context

Výrazně lepší.

⸻

Nejlepší pracovní stav

observable + need + context + trend

Plná pracovní kvalita.

⸻

Nevalidní stav

label only

Například:

„Dítě zlobí.“

→ LOW_DATA
→ bez inference
→ pouze clarification workflow

⸻

Notepad zápis

Case Info musí být řazen přesně takto:

{
  "case_info": {
    "observable_anchor": [],
    "pedagogical_need": [],
    "context": [],
    "trend_intensity": []
  }
}

Toto pořadí není kosmetické.

Je to logika systému.

⸻

Hlavní chyba, které se musíme vyhnout

Nesmí vzniknout situace:

silná hypotéza
bez validního observable
nebo bez známé potřeby učitele

To je hlavní zdroj falešné jistoty.

⸻

Jednoduché pravidlo

Nejdřív:

Co dítě skutečně dělá?

Potom:

Co přesně potřebujete řešit?

Až potom:

Proč se to možná děje?
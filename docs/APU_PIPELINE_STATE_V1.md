# APU_PIPELINE_STATE_V1.md

# APU — PIPELINE STATE V1

## Stav projektu

Tento dokument popisuje aktuální architekturu inference systému APU MŠ.

Nejde o UX popis.  
Jde o technický stav pipeline, inference logiky a validační vrstvy.

APU není diagnostický systém.

APU je:
pedagogický inference systém pro práci s funkčními hypotézami nad chováním dítěte.

Cíl:

ne „co dítě má“

ale

## kde je aktuální pedagogická zátěž  
## co je potřeba upravit v prostředí  
## jak minimalizovat falešné závěry

---

# HLAVNÍ PRINCIP

APU nikdy nesmí dělat:

projev → diagnóza

Vždy:

## observable  
→ více hypotéz  
→ validace  
→ pracovní pedagogický návrh

To je základ celého systému.

---

# ARCHITEKTURA PIPELINE

## INPUT

uživatel zadává:

- pozorovaný projev dítěte
- kontext situace
- pedagogickou potřebu
- případně věk
- případně rodič × škola mismatch

např.

„5 let, při ranním kruhu běhá po třídě a skáče do řeči, potřebuji udržet skupinu“

---

# SIGNAL LAYER

---

## S1 — Observable Map

soubor:

kb/signals/S1_observable_map.json

### Účel

mapování konkrétních pozorovatelných projevů

např.

- běhá po třídě
- utíká ze třídy
- nemluví ve třídě
- lpí na rodiči

Každý observable obsahuje:

- candidate_blocks
- candidate_profiles
- candidate_zones
- confidence
- disambiguation questions

S1 je hlavní anchor systému.

Bez S1 inference nesmí být silná.

---

## S2 — Context Map

soubor:

kb/signals/S2_context_map.json

### Účel

mapování kontextových situací

např.

- ranní kruh
- přechod mezi činnostmi
- šatna
- oběd
- odpočinek
- separace

S2 samo neurčuje problém.

Pouze pomáhá interpretovat S1.

Kontext ≠ observable.

---

## S3 — Label Map

soubor:

kb/signals/S3_label_map.json

### Účel

detekce interpretačního, morálního a zkresleného jazyka

např.

- manipulativní
- zlobivý
- líný
- dělá to schválně
- rozmazlený
- nevychovaný

S3:

nesmí mapovat na block/profile/zone

S3 pouze:

- snižuje inference confidence
- aktivuje validační flags
- vrací replacement questions

tedy:

„co přesně dítě udělalo?“

S3 chrání systém před halucinací.

---

## S4 — Trend / Intensity Map

soubor:

kb/signals/S4_trend_intensity_map.json

### Účel

váhová a validační vrstva

S4 neříká:

co dítěti je

ale:

## jak silně brát již rozpoznaný signál

Rozlišuje:

- jednorázová epizoda
- opakovaný vzorec
- frekvenci
- eskalaci
- zlepšování
- bezpečnostní riziko
- generalizaci
- intenzitu
- situační omezení

např.

- pořád
- každý den
- dnes poprvé
- utíká ze třídy
- nejde zastavit

S4 modifikuje:

- specificity
- confidence
- validation flags
- zone priority

---

# INFERENCE LAYER

---

# BLOCKS

Vývojové oblasti A–E

## A — Emoce a regulace

## B — Sociální chování

## C — Kognice a učení

## D — Řeč a komunikace

## E — Tělo a aktivace

Blocks nejsou diagnóza.

Jsou funkční oblasti.

---

# PROFILES

8 profilů jinakosti

P1–P8

Profiles jsou vyšší interpretační vrstva.

Používají se opatrněji než blocks.

Nikdy nesmí být první závěr.

---

# ZONES

4 zóny pedagogické zátěže

## Z1 — Výkon a nárok

## Z2 — Regulace

## Z3 — Bezpečí

## Z4 — Očekávání a porozumění

Zóny nejsou vlastnost dítěte.

Jsou:

## aktuální stav pedagogické priority

např.

„teď je primární bezpečí“

ne

„dítě patří do Z3“

To je zásadní rozdíl.

---

# ZONE ENGINE V1

soubor:

backend/inference/zone_engine.py

### Účel

výpočet dominantní zóny

### vstupy

- S1 observable anchors
- S4 modifiers
- validation dampening
- specificity confidence cap

### výstup

např.

Z3 dominant  
Z2 secondary

s:

- score
- role
- state
- reasons
- dampening

např.

utíká ze třídy  
→ Z3 dominant  
→ bezpečí má prioritu

Zone Engine je klíčová část systému.

---

# VALIDATION LAYER

složka:

kb/validation/

Obsah:

V1–V8

řeší:

- kolizní mapování
- weak inference
- false positives
- false negatives
- hraniční případy
- kdy APU nemá odpověď
- legislativní limity
- MKF mapping

Validační flags:

např.

- MISSING_OBSERVABLE_BEHAVIOR
- LABEL_WITHOUT_OBSERVATION
- FALSE_POSITIVE_RISK
- WEAK_INFERENCE
- MULTIPLE_HYPOTHESES

Validation chrání inference.

Nejde o kosmetiku.  
Jde o bezpečnost systému.

---

# SPECIFICITY SCORING

Výpočet kvality vstupu.

Vrací:

- LOW
- MEDIUM
- HIGH

a numeric score.

Ovlivňuje:

- output mode
- confidence cap
- zone confidence

např.

LOW specificity:

→ systém se ptá

HIGH specificity:

→ systém navrhuje

---

# OUTPUT MODES

---

## LOW_DATA

chybí observable

→ systém odmítá inference

---

## PARTIAL

observable existuje  
ale chybí důležité části

→ systém doplňuje otázky

---

## FULL

dost dat pro pracovní návrh

→ pedagogický návrh

---

## FAST

rychlý zásah

→ krátká okamžitá pomoc

---

## PERSONAL

explain mode

→ jak APU funguje

---

# DEV MODE

Frontend DEV zobrazuje:

- mode
- intent
- confidence
- specificity
- blocks
- profiles
- zones
- primary zone
- validation flags
- token cost

DEV musí být transparentní.

Inference bez auditability je nepoužitelná.

---

# AKTUÁLNÍ STAV

Hotové:

## signal architecture S1–S4

## validation layer

## specificity scoring

## output mode routing

## zone engine v1

## DEV transparent reasoning

## frontend DEV inspector

To je první skutečně funkční inference systém.

Ne jen prompt wrapper.

---

# DALŠÍ PRIORITA

## TEST MATRIX

Nutné:

systematické testování

bez test harnessu bude systém driftovat.

Plán:

kb/tests/

- T1 clean observable
- T2 label traps
- T3 collision cases
- T4 false positives
- T5 safety priority
- T6 parent/school mismatch
- T7 low-data refusal

Další rozvoj bez test matrix je chyba.

---

# KRITICKÁ POZNÁMKA

APU nesmí být:

diagnostický chatbot

To by byl špatný produkt.

APU musí zůstat:

## inference + pedagogická navigace

To je jeho skutečná síla.
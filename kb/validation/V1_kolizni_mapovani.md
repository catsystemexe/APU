# V1_kolizni_mapovani.md

# HUMAN POPIS

# V1 – KOLIZNÍ MAPOVÁNÍ

## Účel

Tento soubor řeší:

## kdy stejný projev může znamenat více různých příčin

To je největší riziko inference systému.

APU nesmí dělat:

rychlé závěry z povrchu

protože:

## stejný projev ≠ stejná příčina

Např.

„dítě nemluví“

může znamenat:

- jazykový problém
- úzkost
- adaptaci
- senzorické přetížení
- sociální stažení
- selektivní mutismus
- normální vývojovou fázi

Bez kolizního mapování začne APU:

halucinovat závěry

To je nepřijatelné.

---

# KLÍČOVÁ VĚTA

## Projev není diagnóza.

## Projev je vstup do hypotéz.

To je základ validační vrstvy.

---

# PRAVIDLO APU

Nikdy:

projev → závěr

Vždy:

projev → více hypotéz → doplňující otázky → pracovní hypotéza

To je povinné.

---

# HLAVNÍ KOLIZNÍ OBLASTI

---

# 1. DÍTĚ NEMLUVÍ

## možné příčiny

### P1 komunikace & jazyk

- jazyková bariéra
- opožděná řeč
- porozumění

### P3 emoční regulace

- úzkost
- strach
- zamrznutí

### P5 adaptace

- nové prostředí
- separační nejistota

### P6 sociální porozumění

- stažení
- sociální nejistota

### P4 senzorika

- hluk
- sociální overload

## APU se ptá

- mluví doma?
- mluví s vrstevníky?
- jde o všechny situace?
- je problém jen ve školce?
- reaguje neverbálně?
- zlepšuje se v bezpečné dvojici?

Teprve potom inference.

---

# 2. AGRESE

## možné příčiny

### P3 emoční regulace

- frustrace

### P2 aktivace

- impulzivita

### P4 senzorika

- obranná reakce

### P6 sociální fungování

- dominance
- neporozumění hře

### P5 změna

- přechodový kolaps

## APU se ptá

- co tomu předchází?
- je agrese obranná?
- je při přechodech?
- je impulzivní nebo cílená?
- je sociální nebo senzorická?

---

# 3. DÍTĚ JE SAMO

## možné příčiny

### P6 sociální fungování

- stažení

### P3 úzkost

- ochrana před selháním

### P4 senzorika

- skupina je přetěžující

### P1 komunikace

- jazyková bariéra

### vývojová norma

- temperament
- preference samostatné hry

## APU se ptá

- trápí ho to?
- odmítá kontakt nebo neumí vstoupit?
- funguje v malé skupině?
- je to stabilní nebo nové?
- je klid nebo stažení?

---

# 4. ODMÍTÁ KRUH

## možné příčiny

### P2 aktivace

- neudrží se

### P4 senzorika

- hluk
- skupina

### P6 sociální tlak

- expozice

### P5 změna

- přechod

### P3 frustrace

- přetížení

## APU se ptá

- je problém v sezení nebo ve skupině?
- pomáhá aktivní role?
- je horší ráno?
- jde o výkon nebo bezpečí?

---

# 5. MELTDOWN

## možné příčiny

### P3 regulace

- emoční kolaps

### P4 senzorika

- overload

### P5 změna

- přechod

### P2 aktivace

- vyčerpání kapacity

## APU se ptá

- co bylo těsně předtím?
- je to předvídatelné?
- jde o změnu?
- jde o hluk?
- jde o frustraci?

---

# POVINNÁ PRAVIDLA VALIDACE

## 1. minimálně 3 hypotézy

nikdy ne jedna

---

## 2. nejdřív bezpečnější vysvětlení

ne patologizace

---

## 3. vždy hledat vývojovou normu

ne všechno je problém

---

## 4. explicitně označit nejistotu

APU musí říct:

## „může jít o více příčin“

---

## 5. vyžádat doplnění

ne falešná jistota

---

# FORMULACE APU

Správně:

- „To může mít několik příčin“
- „Potřebuji vědět ještě…“
- „Zatím je nejpravděpodobnější…“
- „Pokud platí X, spíše jde o Y“

Špatně:

- „Vaše dítě je…“

---

# KLÍČOVÁ META-OTÁZKA

## Je to problém dítěte

nebo

## problém situace?

To musí APU kontrolovat vždy.

---

# TVRDÉ STOP PRAVIDLO

Pokud chybí:

- kontext
- trend
- spouštěč

APU:

## NESMÍ dělat silnou inferenci

pouze:

pracovní hypotézu

To je zásadní.

---

# KLÍČOVÁ VĚTA

## Největší chyba není nevědět.

## Největší chyba je být si jistý příliš brzo.

To je jádro validace.

---

# JSON STRUKTURA

{
  "id": "V1_kolizni_mapovani",

  "hlavni_princip": "projev_neni_diagnoza",

  "pravidlo_inference": [
    "projev",
    "vice_hypotez",
    "doplnujici_otazky",
    "pracovni_hypoteza"
  ],

  "povinna_pravidla": [
    "minimalne_3_hypotezy",
    "nejdriv_bezpecnejsi_vysvetleni",
    "hledat_vyvojovou_normu",
    "explicitne_oznacit_nejistotu",
    "vyzadat_doplneni"
  ],

  "stop_pravidlo": [
    "bez_kontextu",
    "bez_trendu",
    "bez_spoustece"
  ],

  "kolizni_oblasti": [
    "dite_nemluvi",
    "agrese",
    "dite_je_samo",
    "odmita_kruh",
    "meltdown"
  ]
}
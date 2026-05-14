# V5_hranicni_pripady.md

# HUMAN POPIS

# V5 – HRANIČNÍ PŘÍPADY

## Účel

Tento soubor řeší:

## kde není jasné, zda jde ještě o běžný vývoj,
nebo už o situaci vyžadující zvýšenou podporu

To je nejtěžší oblast celé APU inference.

Protože:

největší chyba není jen:

přehlédnout problém

nebo

vytvořit problém z ničeho

ale:

## špatně odhadnout hranici mezi normou a intervencí

Tady musí být APU velmi přesné a současně pokorné.

---

# KLÍČOVÁ VĚTA

## Nejdůležitější otázka není:

„Je to problém?“

ale:

## „Je to ještě vývojově únosné bez další podpory?“

To je správná optika.

---

# TYPOVÉ HRANIČNÍ PŘÍPADY

---

# 1. SEPARAČNÍ ÚZKOST

Otázka:

je to ještě adaptace,
nebo už významná separační obtíž?

Sledujeme:

- trend zlepšení
- délku návratu do klidu
- funkčnost během dne
- rozsah mimo MŠ

Rozhodující není pláč.

Rozhodující je:

## vývoj v čase

---

# 2. TICHÉ DÍTĚ

Otázka:

introverze,
nebo sociální stažení?

Sledujeme:

- spontánní kontakt
- bezpečný vztah
- aktivní vyhledávání vrstevníků
- subjektivní nepohodu

Rozhodující není ticho.

Rozhodující je:

## možnost vztahu

---

# 3. HYPERAKTIVITA

Otázka:

vývojová potřeba pohybu,
nebo dysregulace?

Sledujeme:

- funkčnost v různých situacích
- míru impulsivity
- možnost návratu do regulace
- dopad na skupinové fungování

Rozhodující není pohyb.

Rozhodující je:

## regulační kapacita

---

# 4. MELTDOWN

Otázka:

běžná frustrace,
nebo výrazný regulační kolaps?

Sledujeme:

- intenzitu
- frekvenci
- předvídatelnost
- délku návratu

Rozhodující není samotný výbuch.

Rozhodující je:

## systémový vzorec

---

# 5. ODMÍTÁNÍ KOMUNIKACE

Otázka:

stydlivost,
nebo selektivní mutismus / silná úzkost?

Sledujeme:

- mluvení doma
- mluvení s vrstevníky
- bezpečné mikrosituace
- rigiditu vzorce

Rozhodující není mlčení.

Rozhodující je:

## nemožnost komunikace

---

# 6. AGRESE

Otázka:

vývojově běžná impulzivita,
nebo významný problém regulace?

Sledujeme:

- spouštěče
- obrannost vs dominance
- frekvenci
- schopnost opravy vztahu

Rozhodující není úder.

Rozhodující je:

## funkční vzorec

---

# 7. SAMOSTATNÁ HRA

Otázka:

temperament,
nebo sociální izolace?

Sledujeme:

- možnost vstupu do vztahu
- flexibilitu
- reakci na nabídku kontaktu

Rozhodující není samota.

Rozhodující je:

## možnost volby

---

# ROZHODOVACÍ KRITÉRIA

APU musí vždy ověřit:

---

# 1. TREND

lepší × stejné × horší

---

# 2. GENERALIZACE

jen ve školce  
nebo všude?

---

# 3. INTENZITA

mírné × výrazné × systémově limitující

---

# 4. FUNKČNÍ DOPAD

omezuje to dítě reálně?

---

# 5. NÁVRAT DO REGULACE

jak rychle se vrací?

---

# 6. SOCIÁLNÍ DOPAD

ničí to vztahy?

---

# 7. POTŘEBA EXTERNÍ PODPORY

stačí pedagogika?

nebo už ne?

---

# APU NESMÍ

říct:

## „to je určitě problém“

ani:

## „to přejde“

bez těchto kritérií.

To je zakázané.

---

# SPRÁVNÁ FORMULACE

„Zatím to může být v rámci vývoje, ale je potřeba sledovat trend.“

„Pokud se nezlepší během…, budeme uvažovat jinak.“

„Rozhodující bude, zda…“

„Teď ještě neuzavírejme závěr.“

---

# ŠPATNÁ FORMULACE

„To je normální.“

„To je určitě porucha.“

„Tohle se samo spraví.“

„Tohle dítě potřebuje odborníka.“

bez dat

→ chyba

---

# TVRDÉ STOP PRAVIDLO

Pokud:

## není jasný trend

APU:

## NESMÍ uzavírat hraniční případ definitivně

pouze:

pracovní sledovací hypotézu

---

# KLÍČOVÁ VĚTA

## Hraniční případ se neřeší jistotou.

## Řeší se kvalitním sledováním.

To je jádro.

---

# JSON STRUKTURA

{
  "id": "V5_hranicni_pripady",

  "hlavni_princip": "dulezita_je_hranice_mezi_normou_a_intervenci",

  "typove_pripady": [
    "separacni_uzkost",
    "tiche_dite",
    "hyperaktivita",
    "meltdown",
    "odmitani_komunikace",
    "agrese",
    "samostatna_hra"
  ],

  "rozhodovaci_kriteria": [
    "trend",
    "generalizace",
    "intenzita",
    "funkcni_dopad",
    "navrat_do_regulace",
    "socialni_dopad",
    "potreba_externi_podpory"
  ],

  "apu_nesmi": [
    "urcite_problem",
    "to_prejde"
  ],

  "stop_pravidlo": [
    "bez_jasneho_trendu_nelze_pripad_uzavrit"
  ]
}
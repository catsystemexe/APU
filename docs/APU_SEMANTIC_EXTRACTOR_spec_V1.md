# APU Semantic Extractor Spec v1
## Cíl
Extrahovat strukturované informace z přirozeného vstupu uživatele:
- bez diagnostiky
- bez interpretace osobnosti dítěte
- bez inferování bloků / profilů / zón
Extractor neříká:
„dítě má problém s regulací“
ale pouze:
„při přechodu do třídy se rozpláče“
---
## Důležitá poznámka: práce s labely
Pokud LLM vrstva zachytí ve vstupu interpretační nebo hodnotící label, například:
- dítě zlobí
- dítě je manipulativní
- dítě je líné
- dítě je hloupé
- dítě provokuje
- dítě to dělá schválně
nesmí tento label přijmout jako fakt.
Místo toho má:
1. označit jej jako interpretační rámec
2. uložit jej do `interpretation_labels`
3. aktivně směřovat doplňující otázku zpět na uživatele
Například:
„Když říkáte, že dítě manipuluje — co přesně dělá nebo říká?“
nebo:
„Podle čeho usuzujete, že to dělá schválně?“
Cíl:
vrátit komunikaci od interpretace zpět ke konkrétnímu pozorovatelnému projevu.
To je zásadní bezpečnostní princip APU.
---
## INPUT
```json
{
  "message": "Dítě při přechodu z venku do třídy pláče a nechce se převlékat."
}

Volitelně:

{
  "message": "...",
  "existing_case_state": {}
}

kvůli kontinuitě notepadu.

⸻

OUTPUT SCHEMA

{
  "observable": [
    {
      "text": "",
      "confidence": "high|medium|low",
      "source": "llm_fallback",
      "requires_confirmation": true
    }
  ],
  "pedagogical_need": [
    {
      "text": ""
    }
  ],
  "context": [
    {
      "text": ""
    }
  ],
  "trend_intensity": [
    {
      "text": ""
    }
  ],
  "interpretation_labels": [
    {
      "text": "",
      "risk": "high",
      "replacement_question": ""
    }
  ],
  "uncertain_points": [
    {
      "text": ""
    }
  ]
}

⸻

POVOLENÉ OPERACE

1. Observable extraction

ANO

* bere dětem hračky
* zakrývá si uši
* přestane mluvit
* odchází stranou

NE

* je agresivní
* je manipulativní
* má poruchu attachmentu
* je rozmazlené

⸻

2. Pedagogical need extraction

ANO

* potřebuji rychle zklidnit situaci
* nevím jak reagovat
* potřebuji to vysvětlit rodičům

NE

* musíme dítě diagnostikovat

⸻

3. Context extraction

ANO

* při ranním kruhu
* u oběda
* při příchodu
* u jedné učitelky
* jen ve školce

⸻

4. Trend extraction

ANO

* každý den
* poprvé
* zhoršuje se
* po chvíli se uklidní
* jen někdy

⸻

5. Label detection

ANO

* je líné
* manipuluje
* dělá to schválně
* provokuje

a převod na:

{
  "text": "dítě je líné",
  "replacement_question": "Co konkrétně dítě dělá nebo nedělá?"
}

⸻

ZAKÁZANÉ OPERACE

Extractor NESMÍ:

* přiřazovat bloky A–E
* přiřazovat profily P1–P8
* přiřazovat zóny Z1–Z4
* diagnostikovat
* doporučovat intervence
* hodnotit rodiče
* hodnotit učitele
* vyvozovat úmysl dítěte
* přepisovat uživatelské tvrzení jako fakt

To patří až do další vrstvy.

⸻

CONFIDENCE RULES

HIGH

Přímá explicitní věta:

„zakrývá si uši při hluku“

⸻

MEDIUM

Silně pravděpodobná formulace:

„nechce pustit maminku“

→ separační situace

⸻

LOW

Nejasné / více možností:

„je protivné“

→ spíše label než observable

⸻

REFUSAL CONDITIONS

Pokud není observable:

→ LOW_DATA

a otázka:

„Co přesně dítě dělá nebo říká?“

ne halucinace.

⸻

VALIDATION LAYER

Extractor vrací také:

{
  "requires_confirmation": true
}

pokud:

* inference není jistá
* existuje více možných interpretací
* jde o label místo observable
* existuje konflikt MŠ vs domov
* jde o jednorázovou epizodu

⸻

ZÁSADNÍ PRINCIP

Extractor nesmí být chytrý.

Musí být auditovatelný.

Chytrost patří až do inference layer.

Tohle je nejdůležitější architektonické rozhodnutí v celém APU.
# ESVE – Core Spec (Evidence & Source Validation Engine)

Tento soubor shrnuje základní principy validačního modulu ESVE, který se stará o práci se zdroji.

Hlavní funkce ESVE:
- rozlišování kvality zdrojů (GOLD / SILVER / BRONZE),
- výpočet míry jistoty (certainty_score) na základě kvality, shody a aktuálnosti zdrojů,
- detekce rozporů mezi zdroji (konflikty v doporučeních),
- nucená práce s nejistotou: žádné domýšlení studií nebo faktů,
- generování citací a odkazů na zdroje tam, kde je to relevantní,
- upozornění uživateli, když jsou data slabá, stará nebo rozporná.

Detailní specifikace ESVE je v `modules/esve/esve_full_spec.md`.

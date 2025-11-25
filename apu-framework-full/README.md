# APU Framework – AI Asistent Pedagoga

Tento repozitář obsahuje modulární architekturu pro AI framework zaměřený na podporu pedagogů.
Konkrétní profil **APU (Asistent Pedagoga Umění)** je specializovaná varianta pro ZUŠ.

Repo je strukturován tak, aby:
- byl přehledný pro člověka (pedagog, vývojář, metodik),
- umožňoval "kompilaci" více souborů do jednoho knowledge promptu pro GPT agenta,
- byl snadno rozšiřitelný o další typy škol a profily.

Základní složky:
- `core/` – základní charakter agenta, bezpečnost, obecná pedagogika, styl komunikace
- `domains/` – profily typů škol, věkových skupin a výukových kontextů
- `modules/` – tematické moduly (didaktika, komunikace, krize, rodiče, wellbeing…)
- `builds/` – výsledné "kompilované" knowledge prompty (např. APU ZUŠ v1)
- `scripts/` – pomocné skripty pro automatické skládání a validaci
- `tests/` – scénáře a checklisty pro testování kvality odpovědí
- `docs/` – dokumentace pro lidi (grant, vedení školy, spolupracovníky)

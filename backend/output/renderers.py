def render_fast_response(interventions: list[dict]) -> str:
    """
    Deterministic FAST mode renderer.
    Uses first 3 interventions only.
    """

    selected = (interventions or [])[:3]

    if not selected:
        return (
            "⚡ RYCHLÝ ZÁSAH\n"
            "Krok 1: Zpomalte situaci a snižte množství podnětů.\n"
            "Krok 2: Použijte krátký a konkrétní pokyn.\n"
            "Krok 3: Ověřte, že dítě ví, co má udělat teď.\n"
            "🤔 Co přesně je právě teď nejtěžší?"
        )

    lines = ["⚡ RYCHLÝ ZÁSAH"]

    for idx, item in enumerate(selected, start=1):
        action = item.get("action", "").strip()

        if not action:
            action = "Použijte jeden konkrétní a bezpečný krok."

        lines.append(f"Krok {idx}: {action}")

    lines.append("🤔 V jaké situaci se to objevuje nejčastěji?")

    return "\n".join(lines)


def render_partial_response(
    blocks: list[dict],
    interventions: list[dict],
    signals: list[dict] | None = None,
    input_quality: dict | None = None,
) -> str:
    """
    Deterministic PARTIAL renderer.

    If observable + usable interventions exist, provide actionable partial:
    safe working steps + explicit uncertainty + clarifying questions.
    """

    signal = (signals or [{}])[0]
    context_candidates = signal.get("context_candidates") or []

    if context_candidates:
        ctx = context_candidates[0]
        meaning = ctx.get("meaning") or "nesoulad v popisu situace"
        candidate_contexts = ctx.get("candidate_contexts") or []
        focus = ctx.get("recommended_focus") or []

        possibilities = (
            "Možnosti: " + ", ".join(candidate_contexts[:3]) + "."
            if candidate_contexts
            else "Možnosti: Může jít o rozdíl mezi domácím a školním prostředím, obrannou reakci rodiče nebo chybějící společný konkrétní popis situace."
        )

        missing = (
            "Doporučené zaměření: " + focus[0] + "."
            if focus
            else "Chybí upřesnit: jaké konkrétní projevy školka pozoruje a v jakých situacích se objevují."
        )

        return "\n".join([
            f"Shrnutí: Popisujete kontextový signál – {meaning}.",
            possibilities,
            missing,
            "🤔 Jaký konkrétní projev dítěte školka opakovaně pozoruje?",
            "🤔 V jakých situacích se tento projev objevuje ve školce a kdy naopak ne?",
        ])

    block_names = []
    for b in (blocks or [])[:3]:
        name = b.get("name")
        if name:
            block_names.append(name.lower())

    selected = (interventions or [])[:3]
    iq = input_quality or {}
    need_known = bool(iq.get("pedagogical_need_known"))

    if selected and not need_known:
        joined = ", ".join(block_names) if block_names else "pozornost, regulaci nebo nárok situace"

        options = ["Obecně může pomoci:"]
        for idx, item in enumerate(selected, start=1):
            action = (item.get("action") or "").strip()
            if not action:
                continue
            options.append(f"Možnost {idx}: {action}")

        return "\n".join([
            "Shrnutí: Máme popsaný projev, ale zatím nevíme, co přesně potřebujete řešit.",
            f"Pracovní hypotézy: Projev může souviset s oblastí {joined}.",
            "Nejde o závěr o dítěti; je to pracovní vodítko pro další zpřesnění.",
            *options,
            "Chybí upřesnit: zda chcete situaci rychle zklidnit, porozumět příčině, nastavit dlouhodobý plán, nebo řešit komunikaci s rodiči.",
            "🤔 Co je teď hlavní cíl podpory?",
            "🤔 Potřebujete spíš rychlý zásah do aktuální situace, nebo dlouhodobější postup?",
        ])

    if selected:
        hypotheses = []

        joined = ", ".join(block_names) if block_names else "regulace, pozornost nebo nárok situace"
        hypotheses.append(
            f"Pracovní hypotézy: Projev může souviset s oblastí {joined}."
        )

        hypotheses.append(
            "Nejde o závěr o dítěti; je to pracovní vodítko pro bezpečný pedagogický postup."
        )

        steps = ["Doporučený postup:"]
        for idx, item in enumerate(selected, start=1):
            action = (item.get("action") or "").strip()
            if not action:
                action = "Použijte jeden krátký, konkrétní a bezpečný krok."
            steps.append(f"Krok {idx}: {action}")

        missing = (
            "Pro zpřesnění chybí: kdy přesně se to děje, co tomu předchází, "
            "jak dlouho projev trvá a co už pomáhá alespoň částečně."
        )

        return "\n".join([
            "Shrnutí: Máme popsaný projev a cíl podpory, takže lze zkusit bezpečný pracovní postup.",
            *hypotheses,
            *steps,
            missing,
            "🤔 Při jaké činnosti se to děje nejčastěji?",
            "🤔 Co dítěti pomůže vrátit se zpět do činnosti: krátký pohyb, jasnější pokyn, nebo menší úsek práce?",
        ])

    summary = "Shrnutí: Vidíme konkrétní obtíž, ale zatím chybí část důležitých informací."

    if not block_names:
        possibilities = (
            "Možnosti: Může jít o potíž v regulaci, porozumění situaci "
            "nebo zátěž v konkrétní činnosti."
        )
    else:
        joined = ", ".join(block_names)
        possibilities = (
            f"Možnosti: Nejčastěji se nabízí oblast {joined}, "
            "ale bez dalších dat nelze dělat silný závěr."
        )

    missing = (
        "Chybí upřesnit: co je cílem podpory, kdy přesně se to děje "
        "a kdy naopak dítě funguje lépe."
    )

    return "\n".join([
        summary,
        possibilities,
        missing,
        "🤔 Co potřebujete v této situaci hlavně změnit nebo podpořit?",
        "🤔 Kdy naopak dítě funguje klidněji nebo lépe?",
    ])

def render_full_response(
    interventions: list[dict]
) -> str:
    """
    Deterministic FULL mode renderer.
    Concrete pedagogical output.
    """

    summary = (
        "Shrnutí: Máme dost informací pro pracovní pedagogický návrh."
    )

    interpretation = (
        "Pracovní interpretace: Nejvíce to ukazuje na funkční obtíž, "
        "kterou lze řešit úpravou struktury, očekávání a vedení situace."
    )

    selected = (interventions or [])[:3]

    steps = []
    for idx, item in enumerate(selected, start=1):
        action = item.get("action", "").strip()

        if not action:
            action = "Použijte jeden konkrétní a bezpečný krok."

        steps.append(f"Krok {idx}: {action}")

    while len(steps) < 3:
        idx = len(steps) + 1
        steps.append(
            f"Krok {idx}: Udržte jasné, krátké a předvídatelné vedení situace."
        )

    verification = (
        "Ověření: Sledujte, zda dítě reaguje rychleji, "
        "potřebuje méně korekcí a lépe se vrací do činnosti."
    )

    return "\n".join([
        summary,
        interpretation,
        "Doporučený postup:",
        *steps,
        verification,
    ])

def render_low_data_response() -> str:
    """
    Deterministic LOW_DATA mode renderer.
    Used when there is no observable anchor.
    """

    return "\n".join([
        "Shrnutí: Zatím chybí konkrétní pozorovatelný projev.",
        "Nelze bezpečně vyhodnotit situaci jen z označení nebo dojmu.",
        "🤔 Co přesně dítě dělá nebo říká, co je vidět nebo slyšet?",
    ])

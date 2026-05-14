def apply_didactic_filter(interventions, context=None):
    """
    Didactic selector v1.

    context očekává:
    {
      "blocks": [...],
      "profiles": [...],
      "zones": [...],
      "input_quality": {...}
    }

    Zatím nefiltruje hotové intervence.
    Vrací kandidátní didaktické oblasti T0–T10.
    """

    context = context or {}

    blocks = context.get("blocks") or []
    profiles = context.get("profiles") or []
    zones = context.get("zones") or []

    block_codes = {b.get("code") for b in blocks}
    profile_codes = {p.get("code") for p in profiles}
    zone_codes = {z.get("code") for z in zones}

    selected = {}

    def add(code, reason, confidence="LOW"):
        if code not in selected:
            selected[code] = {
                "code": code,
                "confidence": confidence,
                "reasons": [],
            }
        selected[code]["reasons"].append(reason)

    # T0 — obecné didaktické principy vždy jako background
    add("T0", "obecný didaktický rámec APU", "MEDIUM")

    # P2 regulace/aktivace + Z1/Z2
    if "P2" in profile_codes:
        add("T1", "P2: potřeba struktury a předvídatelnosti", "MEDIUM")
        add("T2", "P2: úprava prostředí a podnětů", "MEDIUM")
        add("T5", "P2: individualizace nároků a tempa", "MEDIUM")
        add("T7", "P2: motivace a zapojení pozornosti", "MEDIUM")

    # P6 sociální porozumění
    if "P6" in profile_codes:
        add("T3", "P6: pravidla a hranice", "MEDIUM")
        add("T4", "P6: skupina a sociální dynamika", "MEDIUM")
        add("T8", "P6: spolupráce s rodiči / sjednocení očekávání", "LOW")

    # Z1 výkon / činnost
    if "Z1" in zone_codes:
        add("T1", "Z1: strukturování činnosti", "MEDIUM")
        add("T5", "Z1: diferenciace nároku", "MEDIUM")
        add("T7", "Z1: udržení zapojení", "MEDIUM")
        add("T9", "Z1: reflexe výkonu a průběhu", "LOW")

    # Z4 očekávání / porozumění / vztah
    if "Z4" in zone_codes:
        add("T3", "Z4: zpřesnění pravidel a očekávání", "MEDIUM")
        add("T4", "Z4: vztahový a skupinový rámec", "LOW")
        add("T8", "Z4: sdílení očekávání s rodiči", "LOW")

    # blok B sociální chování
    if "B" in block_codes:
        add("T3", "B: práce s hranicemi", "MEDIUM")
        add("T4", "B: sociální dynamika skupiny", "MEDIUM")

    # blok C kognice / pozornost
    if "C" in block_codes:
        add("T1", "C: jasná struktura a sekvence", "MEDIUM")
        add("T5", "C: individualizace úkolu", "MEDIUM")
        add("T7", "C: aktivní zapojení pozornosti", "MEDIUM")

    # blok E tělo / aktivace
    if "E" in block_codes:
        add("T2", "E: úprava podnětové zátěže", "MEDIUM")
        add("T6", "E: přechody, změny a adaptace", "LOW")

    return {
        "selected": list(selected.values()),
        "allowed": interventions or [],
        "removed": [],
        "notes": [],
    }

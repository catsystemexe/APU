from backend.validation.rule_registry import registry_summary


def _unique_add(items: list, value: str):
    if value and value not in items:
        items.append(value)


def _codes(items):
    return {x.get("code") for x in (items or []) if x.get("code")}


def detect_contradictions(signals, blocks, profiles, zones):
    flags = []
    warnings = []
    items = []
    score = 0

    text = " ".join((s.get("normalized_text") or s.get("raw_text") or "") for s in (signals or []))
    all_flags = []
    for s in signals or []:
        for f in s.get("flags", []):
            if f not in all_flags:
                all_flags.append(f)

    def add(code, severity, evidence, warning, points=1):
        nonlocal score
        if code not in flags:
            flags.append(code)
            warnings.append(warning)
            items.append({
                "code": code,
                "severity": severity,
                "evidence": evidence,
                "hypothesis_only": True,
            })
            score += points

    # doma vs školka mismatch
    if (
        ("doma" in text and ("skolce" in text or "skolka" in text or "tride" in text))
        or "SETTING_DIFFERENCE" in all_flags
    ):
        add(
            "CONTRADICTION_HOME_SCHOOL_MISMATCH",
            "MEDIUM",
            "Popis rozlišuje fungování doma a ve školce/třídě.",
            "Rozdíl doma vs. školka může znamenat situační nebo environmentální faktor, ne vlastnost dítěte.",
            2,
        )

    # absolutní tvrzení vs situační omezení
    if (
        ("ABSOLUTIZING_LANGUAGE" in all_flags or "TIME_ABSOLUTIZATION" in all_flags)
        and (
            "SITUATIONAL_LIMITED" in all_flags
            or "SETTING_DIFFERENCE" in all_flags
            or "ADULT_SPECIFIC_CONTEXT" in all_flags
            or "LOW_LOAD_FUNCTIONING_BETTER" in all_flags
        )
    ):
        add(
            "CONTRADICTION_ABSOLUTE_VS_SITUATIONAL",
            "HIGH",
            "Současně se objevuje absolutizující jazyk a situační omezení.",
            "Absolutní závěr je oslabený, protože popis zároveň ukazuje závislost na situaci.",
            3,
        )

    # label/intent bias vs observable evidence
    if "HAS_INTERPRETATION_LABEL" in all_flags:
        observable_count = sum(len(s.get("observable_candidates") or []) for s in (signals or []))
        if observable_count > 0:
            add(
                "CONTRADICTION_LABEL_VS_OBSERVABLE",
                "MEDIUM",
                "Vstup obsahuje hodnotící label i konkrétní pozorovatelný projev.",
                "Label nesmí převážit nad popisem toho, co je skutečně vidět nebo slyšet.",
                1,
            )

    # zlepšení / funguje lépe vs silný globální problém
    if (
        ("IMPROVING_TREND" in all_flags or "RECOVERY_PRESENT" in all_flags or "LOW_LOAD_FUNCTIONING_BETTER" in all_flags)
        and (
            "HAS_INTERPRETATION_LABEL" in all_flags
            or "ABSOLUTIZING_LANGUAGE" in all_flags
            or "TIME_ABSOLUTIZATION" in all_flags
        )
    ):
        add(
            "CONTRADICTION_GLOBAL_PROBLEM_VS_RECOVERY",
            "MEDIUM",
            "Popis obsahuje známku zlepšení/regulace a zároveň silný globalizující rámec.",
            "Přítomnost zlepšení nebo návratu do klidu oslabuje globální negativní závěr.",
            2,
        )

    level = "NONE"
    if score >= 4:
        level = "HIGH"
    elif score >= 2:
        level = "MEDIUM"
    elif score > 0:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "flags": flags,
        "warnings": warnings,
        "items": items,
    }


def validate_pipeline(signals, blocks, profiles, zones):
    flags = []
    warnings = []
    downgrades = []
    severity = "LOW"

    for s in signals or []:
        for f in s.get("flags", []):
            _unique_add(flags, f)

    if not signals:
        _unique_add(flags, "LOW_DATA")

    block_codes = _codes(blocks)
    profile_codes = _codes(profiles)
    zone_codes = _codes(zones)

    observable_count = 0
    specificity_score = 0

    for s in signals or []:
        observable_count += len(s.get("observable_candidates") or [])
        spec = s.get("specificity") or {}
        specificity_score = max(specificity_score, int(spec.get("score") or 0))

    # -----------------------------
    # V1 collision / multiple hypothesis
    # -----------------------------
    if len(blocks or []) > 1 or len(profiles or []) > 1 or len(zones or []) > 1:
        _unique_add(flags, "MULTIPLE_HYPOTHESES")
        _unique_add(flags, "DO_NOT_COLLAPSE_TO_SINGLE_CAUSE")
        _unique_add(warnings, "Stejný projev může mít více legitimních vysvětlení.")
        severity = "MEDIUM"

    # -----------------------------
    # V2 weak inference
    # -----------------------------
    if observable_count == 1 and specificity_score < 4:
        _unique_add(flags, "WEAK_INFERENCE")
        _unique_add(warnings, "Inference stojí jen na jednom pozorovatelném projevu nebo nízké specificitě.")
        _unique_add(downgrades, "avoid_strong_conclusion")
        severity = "MEDIUM"

    # -----------------------------
    # V3 false positive risk
    # -----------------------------
    if "E" in block_codes and "P2" in profile_codes and specificity_score < 5:
        _unique_add(flags, "FALSE_POSITIVE_RISK")
        _unique_add(warnings, "Potřeba pohybu nemusí sama o sobě znamenat závažný problém dítěte.")
        _unique_add(downgrades, "frame_as_regulation_need_not_disorder")

    # -----------------------------
    # Context-only branch
    # -----------------------------
    if "CONTEXT_WITHOUT_CHILD_OBSERVABLE" in flags:
        _unique_add(warnings, "Jde o kontextový nebo vztahový signál, nikoli přímý popis chování dítěte.")
        _unique_add(downgrades, "do_not_infer_child_profile")
        severity = "MEDIUM"

    # -----------------------------
    # Label-only branch
    # -----------------------------
    if "LABEL_WITHOUT_OBSERVATION" in flags:
        _unique_add(warnings, "Uživatel používá interpretační nebo hodnotící label bez konkrétního pozorování.")
        _unique_add(downgrades, "ask_for_observable_before_mapping")
        severity = "HIGH"

    contradictions = detect_contradictions(signals, blocks, profiles, zones)

    for f in contradictions.get("flags", []):
        _unique_add(flags, f)

    for w in contradictions.get("warnings", []):
        _unique_add(warnings, w)

    if contradictions.get("level") == "HIGH":
        _unique_add(downgrades, "resolve_contradiction_before_strong_conclusion")
        severity = "HIGH"
    elif contradictions.get("level") == "MEDIUM" and severity == "LOW":
        severity = "MEDIUM"

    needs_more_input = (
        "LOW_DATA" in flags
        or "MISSING_OBSERVABLE_BEHAVIOR" in flags
        or "LABEL_WITHOUT_OBSERVATION" in flags
    )

    return {
        "flags": flags,
        "warnings": warnings,
        "downgrades": downgrades,
        "severity": severity,
        "contradictions": contradictions,
        "rule_registry": {
            "validation_rules": registry_summary(),
        },
        "diagnostic_guard": True,
        "label_hiding_required": True,
        "needs_more_input": needs_more_input,
    }

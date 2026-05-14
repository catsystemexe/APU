# backend/inference/zone_engine.py

from backend.zones.registry import (
    ZONE_REGISTRY,
    confidence_from_score,
    apply_confidence_cap,
    detect_zone_state,
    zone_name,
)


BASE_OBSERVABLE_WEIGHT = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}


S4_ZONE_MODIFIERS = {
    # Z1 – výkon / činnost
    "HARD_TO_COMPLETE_TASK": {"Z1": 2},
    "TASK_DEMAND_HIGH": {"Z1": 2},

    # Z2 – regulace
    "HARD_TO_INTERRUPT": {"Z2": 2},
    "ADULT_SUPPORT_NEEDED": {"Z2": 1},
    "ESCALATION_PATTERN": {"Z2": 2},
    "FREQUENCY_HIGH": {"Z2": 1},
    "REPEATED_PATTERN": {"Z2": 1},

    # Z3 – bezpečí
    "LEAVES_SAFE_AREA": {"Z3": 3},
    "SAFETY_CONTEXT": {"Z3": 2},

    # Z4 – očekávání / porozumění
    "HIGH_SUPPORT_DEPENDENCY": {"Z4": 2},
    "ESCALATION_WITH_CHANGE": {"Z4": 2},
}


S4_DAMPENING_FLAGS = {
    "SINGLE_EPISODE": 0,
    "SUBJECTIVE_IMPRESSION": -1,
}


VALIDATION_DAMPENING_FLAGS = {
    "LABEL_WITHOUT_OBSERVATION": -3,
    "MISSING_OBSERVABLE_BEHAVIOR": -3,
    "FALSE_POSITIVE_RISK": -1,
    "WEAK_INFERENCE": -1,
}


def _init_zone_scores():
    return {
        code: {
            "code": code,
            "name": data["name"],
            "score": 0,
            "reasons": [],
            "dampening": [],
        }
        for code, data in ZONE_REGISTRY.items()
    }


def _add(zone_scores, code, points, reason):
    if code not in zone_scores:
        return

    zone_scores[code]["score"] += points

    if points >= 0:
        zone_scores[code]["reasons"].append(reason)
    else:
        zone_scores[code]["dampening"].append(reason)


def _collect_flags(signals, validation=None):
    flags = []

    for s in signals or []:
        for f in s.get("flags", []):
            if f not in flags:
                flags.append(f)

    for f in (validation or {}).get("flags", []):
        if f not in flags:
            flags.append(f)

    return flags


def _specificity_cap(input_quality=None):
    specificity = (input_quality or {}).get("specificity") or {}
    level = specificity.get("level", "LOW")

    if level == "LOW":
        return "MEDIUM"

    return "HIGH"


def infer_zone_states(
    signals: list[dict],
    validation: dict | None = None,
    input_quality: dict | None = None,
) -> list[dict]:
    """
    Zone Engine v1.

    Zones are transient pedagogical load states,
    not child traits and not diagnoses.
    """

    zone_scores = _init_zone_scores()
    flags = _collect_flags(signals, validation)

    # -----------------------------
    # 1. S1 observable candidate zones
    # -----------------------------
    for signal in signals or []:
        for obs in signal.get("observable_candidates", []) or []:
            conf = obs.get("confidence", "MEDIUM")
            base = BASE_OBSERVABLE_WEIGHT.get(conf, 2)

            for z in obs.get("candidate_zones", []) or []:
                _add(
                    zone_scores,
                    z,
                    base,
                    f"{obs.get('id') or 'observable'} → {z} (+{base})",
                )

    # -----------------------------
    # 2. S4 validation flags as modifiers
    # -----------------------------
    for flag in flags:
        modifiers = S4_ZONE_MODIFIERS.get(flag) or {}
        for zone_code, points in modifiers.items():
            _add(
                zone_scores,
                zone_code,
                points,
                f"{flag} → {zone_code} (+{points})",
            )

    # -----------------------------
    # 3. Global dampening
    # -----------------------------
    for flag in flags:
        if flag in S4_DAMPENING_FLAGS:
            points = S4_DAMPENING_FLAGS[flag]
            for code in zone_scores:
                if zone_scores[code]["score"] > 0:
                    _add(zone_scores, code, points, f"{flag} ({points})")

        if flag in VALIDATION_DAMPENING_FLAGS:
            points = VALIDATION_DAMPENING_FLAGS[flag]
            for code in zone_scores:
                if zone_scores[code]["score"] > 0:
                    _add(zone_scores, code, points, f"{flag} ({points})")

    # -----------------------------
    # 4. Build active zone list
    # -----------------------------
    active = [
        z for z in zone_scores.values()
        if z["score"] > 0
    ]

    if not active:
        return []

    active.sort(key=lambda z: z["score"], reverse=True)

    top_score = active[0]["score"]
    second_score = active[1]["score"] if len(active) > 1 else 0
    diff = top_score - second_score

    state = detect_zone_state(flags)
    cap = _specificity_cap(input_quality)

    out = []

    for idx, z in enumerate(active):
        raw_conf = confidence_from_score(z["score"])
        conf = apply_confidence_cap(raw_conf, cap)

        if idx == 0:
            top_flags = set(flags)
            z3_safety_override = (
                z["code"] == "Z3"
                and "LEAVES_SAFE_AREA" in top_flags
                and "SAFETY_CONTEXT" in top_flags
            )

            if z3_safety_override:
                role = "dominant"
            elif diff >= 3:
                role = "dominant"
            elif diff >= 1:
                role = "dominant_mixed"
            else:
                role = "unresolved"
        else:
            role = "secondary"

        out.append({
            "code": z["code"],
            "name": zone_name(z["code"]),
            "score": z["score"],
            "confidence": conf,
            "raw_confidence": raw_conf,
            "confidence_cap": cap,
            "state": state,
            "role": role,
            "hypothesis_only": True,
            "reasons": z["reasons"],
            "dampening": z["dampening"],
            "missing_disambiguation": [
                "co situaci spouští",
                "jak často se opakuje",
                "co pomáhá snížit zátěž",
            ],
        })

    return out
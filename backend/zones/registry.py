# backend/zones/registry.py

ZONE_REGISTRY = {
    "Z1": {
        "code": "Z1",
        "name": "Výkon a nárok",
        "priority": 1,
        "default_confidence_cap": "HIGH",
        "dominant_output_focus": [
            "task_splitting",
            "scaffold",
            "reduced_demand",
            "completion_support",
        ],
    },

    "Z2": {
        "code": "Z2",
        "name": "Regulace",
        "priority": 2,
        "default_confidence_cap": "HIGH",
        "dominant_output_focus": [
            "regulation",
            "stabilization",
            "tempo_control",
            "transition_support",
        ],
    },

    "Z3": {
        "code": "Z3",
        "name": "Bezpečí",
        "priority": 3,
        "default_confidence_cap": "HIGH",
        "dominant_output_focus": [
            "safety",
            "predictability",
            "relationship_anchor",
            "stabilization",
        ],
    },

    "Z4": {
        "code": "Z4",
        "name": "Očekávání a porozumění",
        "priority": 4,
        "default_confidence_cap": "HIGH",
        "dominant_output_focus": [
            "clarity",
            "visual_structure",
            "modelling",
            "rule_visibility",
        ],
    },
}


ZONE_STATE_RULES = {
    "transient": [
        "SINGLE_EPISODE",
    ],

    "persistent_candidate": [
        "REPEATED_PATTERN",
        "LONG_DURATION",
    ],

    "escalating": [
        "ESCALATION_PATTERN",
    ],

    "improving": [
        "IMPROVING_PATTERN",
    ],
}


ZONE_CONFIDENCE_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def confidence_from_score(score: int) -> str:
    """
    Raw score → confidence
    """

    if score >= 7:
        return "HIGH"

    if score >= 4:
        return "MEDIUM"

    return "LOW"


def apply_confidence_cap(confidence: str, cap: str) -> str:
    """
    Example:
    confidence=HIGH
    cap=MEDIUM
    → MEDIUM
    """

    if ZONE_CONFIDENCE_ORDER[confidence] <= ZONE_CONFIDENCE_ORDER[cap]:
        return confidence

    return cap


def detect_zone_state(flags: list[str]) -> str:
    """
    Priority:
    escalating
    persistent_candidate
    improving
    transient
    default
    """

    flags = flags or []

    if any(x in flags for x in ZONE_STATE_RULES["escalating"]):
        return "escalating"

    persistent_hits = sum(
        1 for x in ZONE_STATE_RULES["persistent_candidate"]
        if x in flags
    )
    if persistent_hits >= 2:
        return "persistent_candidate"

    if any(x in flags for x in ZONE_STATE_RULES["improving"]):
        return "improving"

    if any(x in flags for x in ZONE_STATE_RULES["transient"]):
        return "transient"

    return "standard"


def zone_name(code: str) -> str:
    return ZONE_REGISTRY.get(code, {}).get("name", code)
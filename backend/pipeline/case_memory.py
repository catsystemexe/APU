from backend.rag.signal_registry import load_observable_map
from backend.inference.blocks import infer_blocks
from backend.inference.profiles import infer_profiles
from backend.inference.zones import infer_zones
from backend.interventions.selector import select_interventions


def _fallback_observable_from_text(text: str):
    t = (text or "").lower()

    if "nedává pozor" in t or "nedava pozor" in t or "neudrží pozornost" in t or "neudrzi pozornost" in t:
        return {
            "type": "observable_candidate",
            "id": "CASE_OBS_ATTENTION_001",
            "meaning": "nedává pozor / neudrží pozornost",
            "source": "case_state_text_fallback",
            "confidence": "MEDIUM",
            "matched_patterns": [],
            "candidate_blocks": ["C"],
            "candidate_zones": ["Z1"],
            "disambiguation_questions": [
                "Při jaké činnosti se to děje?",
                "Jak dlouho pozornost udrží?",
                "Co dělá místo očekávané činnosti?"
            ],
        }

    if "běhá" in t or "beha" in t or "pohybu" in t:
        return {
            "type": "observable_candidate",
            "id": "CASE_OBS_ACTIVITY_001",
            "meaning": "výrazně zvýšená potřeba pohybu a aktivace těla",
            "source": "case_state_text_fallback",
            "confidence": "MEDIUM",
            "matched_patterns": [],
            "candidate_blocks": ["E", "A"],
            "candidate_zones": ["Z2"],
            "disambiguation_questions": [
                "Děje se to při klidové činnosti, přechodu nebo ve volné hře?",
                "Pomáhá krátký řízený pohybový úkol?"
            ],
        }

    return None


def hydrate_signals_from_case_state(case_state=None):
    case_state = case_state or {}
    refs = []
    observable_candidates = []

    observation_source = ((case_state.get("case_info") or {}).get("observable_anchor") or [])

    for item in observation_source:
        if not isinstance(item, dict):
            continue

        # Preferred path: explicit mapping stored in notepad item.
        if item.get("candidate_blocks") or item.get("candidate_zones"):
            observable_candidates.append({
                "type": "observable_candidate",
                "id": item.get("id") or "CASE_OBS_METADATA",
                "meaning": item.get("observable_meaning") or item.get("text"),
                "source": "case_state_metadata",
                "confidence": "MEDIUM",
                "matched_patterns": [],
                "candidate_blocks": item.get("candidate_blocks", []),
                "candidate_zones": item.get("candidate_zones", []),
                "disambiguation_questions": [],
            })
            continue

        for ref in item.get("evidence_refs") or []:
            if ref and ref not in refs:
                refs.append(ref)

        fallback = _fallback_observable_from_text(item.get("text") or "")
        if fallback:
            observable_candidates.append(fallback)

    by_id = {x.get("id"): x for x in load_observable_map() if x.get("id")}

    for ref in refs:
        src = by_id.get(ref)
        if not src:
            continue

        observable_candidates.append({
            "type": "observable_candidate",
            "id": src.get("id"),
            "meaning": src.get("observable"),
            "source": "case_state_ref",
            "confidence": src.get("confidence", "MEDIUM"),
            "matched_patterns": [],
            "candidate_blocks": src.get("candidate_blocks", []),
            "candidate_zones": src.get("candidate_zones", []),
            "disambiguation_questions": src.get("disambiguation_questions", []),
        })

    if not observable_candidates:
        return []

    return [{
        "type": "case_state_signal_v1",
        "raw_text": "",
        "normalized_text": "",
        "observable_candidates": observable_candidates,
        "context_candidates": [],
        "context": [],
        "age": [],
        "pedagogical_need": [],
        "trend_intensity": [],
        "interpretation_labels": [],
        "slang_or_jargon": [],
        "flags": ["CASE_STATE_OBSERVABLE_ANCHOR"],
        "confidence": "LOW",
        "specificity": {
            "score": 2,
            "level": "LOW",
            "reasons": ["case_state_observable_anchor"],
        },
    }]


def hydrate_inference_from_case_state(case_state=None, validation=None, input_quality=None):
    signals = hydrate_signals_from_case_state(case_state)

    if not signals:
        return {
            "signals": [],
            "blocks": [],
            "profiles": [],
            "zones": [],
            "interventions": [],
        }

    blocks = infer_blocks(signals)
    profiles = infer_profiles(signals, blocks)
    zones = infer_zones(
        signals,
        blocks,
        profiles,
        validation=validation,
        input_quality=input_quality,
    )
    interventions = select_interventions(blocks, profiles, zones, signals)

    return {
        "signals": signals,
        "blocks": blocks,
        "profiles": profiles,
        "zones": zones,
        "interventions": interventions,
    }

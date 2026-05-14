from backend.rag.intervention_registry import load_micro_interventions


def _overlap(a, b) -> bool:
    return bool(set(a or []) & set(b or []))


def select_interventions(
    blocks: list[dict],
    profiles: list[dict],
    zones: list[dict],
    signals: list[dict] | None = None,
) -> list[dict]:
    block_codes = [b.get("code") for b in (blocks or [])]
    profile_codes = [p.get("code") for p in (profiles or [])]
    zone_codes = [z.get("code") for z in (zones or [])]

    signal = (signals or [{}])[0]
    flags = signal.get("flags") or []
    contexts = [
        c.get("meaning")
        for c in (signal.get("context") or [])
        if c.get("meaning")
    ]
    context_candidate_ids = [
        c.get("id")
        for c in (signal.get("context_candidates") or [])
        if c.get("id")
    ]

    out = []

    for item in load_micro_interventions():
        score = 0

        if _overlap(item.get("match_blocks"), block_codes):
            score += 2

        if _overlap(item.get("match_profiles"), profile_codes):
            score += 2

        if _overlap(item.get("match_zones"), zone_codes):
            score += 2

        if _overlap(item.get("match_context"), contexts):
            score += 2

        if _overlap(item.get("match_context_flags"), flags):
            score += 3

        if _overlap(item.get("match_context_candidates"), context_candidate_ids):
            score += 3

        if score <= 0:
            continue

        out.append({
            "code": item.get("id"),
            "title": item.get("title"),
            "action": item.get("action"),
            "reason": "KB intervention match",
            "confidence": item.get("confidence", "MEDIUM"),
            "timing": item.get("timing", "now"),
            "hypothesis_only": True,
            "score": score,
        })

    out.sort(key=lambda x: (-x.get("score", 0), x.get("code") or ""))

    return out[:5]

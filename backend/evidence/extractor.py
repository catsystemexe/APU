def _list(x):
    return x if isinstance(x, list) else []


def build_evidence(signals, blocks=None, profiles=None, zones=None, validation=None):
    items = []

    for s in signals or []:
        raw_text = s.get("raw_text")
        normalized_text = s.get("normalized_text")

        for obs in _list(s.get("observable_candidates")):
            items.append({
                "type": "observable",
                "source": obs.get("source") or "direct_pattern",
                "id": obs.get("id"),
                "text": raw_text,
                "normalized_text": normalized_text,
                "meaning": obs.get("meaning"),
                "matched_patterns": _list(obs.get("matched_patterns")),
                "matched_stems": _list(obs.get("matched_stems")),
                "candidate_blocks": _list(obs.get("candidate_blocks")),
                "candidate_zones": _list(obs.get("candidate_zones")),
                "confidence": obs.get("confidence"),
            })

        for label in _list(s.get("interpretation_labels")):
            items.append({
                "type": "interpretation_label",
                "source": label.get("source") or "label_pattern",
                "id": label.get("id"),
                "text": raw_text,
                "normalized_text": normalized_text,
                "label": label.get("label") or label.get("meaning"),
                "label_type": label.get("label_type"),
                "risk": label.get("risk"),
                "matched_patterns": _list(label.get("matched_patterns")),
                "matched_stems": _list(label.get("matched_stems")),
                "replacement_question": label.get("replacement_question"),
            })

        for ti in _list(s.get("trend_intensity")):
            effect = ti.get("effect") or {}
            items.append({
                "type": "trend_intensity",
                "source": ti.get("source"),
                "id": ti.get("id"),
                "text": raw_text,
                "normalized_text": normalized_text,
                "category": ti.get("category"),
                "signal": ti.get("signal"),
                "matched_patterns": _list(ti.get("matched_patterns")),
                "matched_stems": _list(ti.get("matched_stems")),
                "validation_flags": _list(effect.get("validation_flags")),
                "confidence_modifier": effect.get("confidence_modifier"),
            })

        for ctx in _list(s.get("context_candidates")):
            items.append({
                "type": "context_candidate",
                "source": ctx.get("source"),
                "id": ctx.get("id"),
                "text": raw_text,
                "normalized_text": normalized_text,
                "meaning": ctx.get("meaning"),
                "matched_patterns": _list(ctx.get("matched_patterns")),
                "candidate_contexts": _list(ctx.get("candidate_contexts")),
            })

    zone_evidence = []
    for z in zones or []:
        zone_evidence.append({
            "type": "zone",
            "code": z.get("code"),
            "role": z.get("role"),
            "score": z.get("score"),
            "confidence": z.get("confidence"),
            "raw_confidence": z.get("raw_confidence"),
            "reasons": _list(z.get("reasons")),
            "dampening": _list(z.get("dampening")),
        })

    validation_evidence = {
        "flags": _list((validation or {}).get("flags")),
        "warnings": _list((validation or {}).get("warnings")),
        "downgrades": _list((validation or {}).get("downgrades")),
        "contradictions": (validation or {}).get("contradictions") or {},
    }

    return {
        "items": items,
        "zones": zone_evidence,
        "validation": validation_evidence,
        "summary": {
            "observable_count": sum(1 for x in items if x["type"] == "observable"),
            "label_count": sum(1 for x in items if x["type"] == "interpretation_label"),
            "trend_intensity_count": sum(1 for x in items if x["type"] == "trend_intensity"),
            "context_candidate_count": sum(1 for x in items if x["type"] == "context_candidate"),
            "zone_count": len(zone_evidence),
        }
    }

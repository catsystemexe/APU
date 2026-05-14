from backend.rag.didactic_registry import load_didactic_text


PRIORITY_ORDER = {
    "T1": 100,  # struktura dne
    "T3": 95,   # pravidla a hranice
    "T5": 90,   # individualizace
    "T7": 85,   # motivace
    "T2": 80,   # prostředí
    "T4": 70,   # skupina
    "T6": 60,   # přechody
    "T8": 50,   # rodiče
    "T9": 40,   # reflexe
    "T0": 30,   # obecný background
    "T10": 20,
}


def _score(code, confidence):
    base = PRIORITY_ORDER.get(code, 10)

    bonus = {
        "HIGH": 30,
        "MEDIUM": 15,
        "LOW": 0,
    }.get((confidence or "").upper(), 0)

    return base + bonus


def load_targeted_didactic(
    didactic_filter,
    max_chars_per_item: int = 2500,
    max_items: int = 5,
):
    selected = (didactic_filter or {}).get("selected") or []

    ranked = []

    for item in selected:
        code = (item.get("code") or "").strip().upper()
        confidence = item.get("confidence", "LOW")

        if not code:
            continue

        ranked.append({
            "code": code,
            "confidence": confidence,
            "score": _score(code, confidence),
            "reasons": item.get("reasons", []),
        })

    ranked.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    ranked = ranked[:max_items]

    loaded = []
    missing = []
    selected_codes = []

    for item in ranked:
        code = item["code"]
        selected_codes.append(code)

        loaded_item = load_didactic_text(
            code,
            max_chars=max_chars_per_item
        )

        if loaded_item:
            loaded.append({
                "code": loaded_item["code"],
                "slug": loaded_item["slug"],
                "filename": loaded_item["filename"],
                "chars": loaded_item["chars"],
                "text": loaded_item["text"],
                "score": item["score"],
                "confidence": item["confidence"],
            })
        else:
            missing.append(code)

    return {
        "selected_codes": selected_codes,
        "loaded": loaded,
        "missing": missing,
        "ranked_preview": ranked,
    }


def format_didactic_for_prompt(bundle: dict) -> str:
    chunks = []

    for item in bundle.get("loaded", []):
        chunks.append(
            f"### {item['code']} – {item['filename']}\n{item['text']}"
        )

    return "\n\n".join(chunks).strip()

from backend.validation.rule_registry import load_validation_rule


def select_validation_rule_codes(validation: dict) -> list[str]:
    flags = validation.get("flags", []) if validation else []

    codes = []

    if (
        "MULTIPLE_HYPOTHESES" in flags
        or "DO_NOT_COLLAPSE_TO_SINGLE_CAUSE" in flags
    ):
        codes.append("V1")

    if (
        "MISSING_OBSERVABLE_BEHAVIOR" in flags
        or "LABEL_WITHOUT_OBSERVATION" in flags
    ):
        codes.append("V2")

    if "FALSE_POSITIVE_RISK" in flags:
        codes.append("V3")

    if "FALSE_NEGATIVE_RISK" in flags:
        codes.append("V4")

    if "EDGE_CASE" in flags:
        codes.append("V5")

    if "NO_SAFE_OUTPUT" in flags:
        codes.append("V6")

    if "LEGAL_BOUNDARY" in flags:
        codes.append("V7")

    return list(dict.fromkeys(codes))


def load_targeted_validation_rules(validation: dict, max_chars_per_rule: int = 4000):
    codes = select_validation_rule_codes(validation)

    loaded = []
    missing = []

    for code in codes:
        item = load_validation_rule(code, max_chars=max_chars_per_rule)

        if item:
            loaded.append({
                "code": item["code"],
                "slug": item["slug"],
                "filename": item["filename"],
                "chars": item["chars"],
                "text": item["text"],
            })
        else:
            missing.append(code)

    return {
        "selected_codes": codes,
        "loaded": loaded,
        "missing": missing,
    }


def format_validation_rules_for_prompt(bundle: dict) -> str:
    chunks = []

    for item in bundle.get("loaded", []):
        chunks.append(
            f"### {item['code']} – {item['filename']}\n{item['text']}"
        )

    return "\n\n".join(chunks).strip()

from backend.inference.rule_registry import load_inference_rule


def select_inference_rule_codes(intent: str, validation: dict) -> list[str]:
    flags = validation.get("flags", []) if validation else []

    codes = ["I1"]  # default orchestration source

    if (
        "LOW_DATA" in flags
        or "MISSING_OBSERVABLE_BEHAVIOR" in flags
        or "LABEL_WITHOUT_OBSERVATION" in flags
    ):
        codes.append("I3")

    if intent == "FAST_REQUEST":
        codes.append("I2")

    if "RED_FLAG" in flags or "SAFETY_RISK" in flags:
        codes.append("I5")

    # I4 zatím special branch, později pro komunikaci s rodiči / konflikt
    # držíme mimo default, ať nezvětšujeme prompt zbytečně

    return list(dict.fromkeys(codes))


def load_targeted_inference_rules(intent: str, validation: dict, max_chars_per_rule: int = 4000) -> dict:
    codes = select_inference_rule_codes(intent, validation)

    loaded = []
    missing = []

    for code in codes:
        rule = load_inference_rule(code, max_chars=max_chars_per_rule)
        if rule:
            loaded.append({
                "code": rule["code"],
                "slug": rule["slug"],
                "filename": rule["filename"],
                "chars": rule["chars"],
                "text": rule["text"],
            })
        else:
            missing.append(code)

    return {
        "selected_codes": codes,
        "loaded": loaded,
        "missing": missing,
    }


def format_inference_rules_for_prompt(bundle: dict) -> str:
    chunks = []

    for rule in bundle.get("loaded", []):
        chunks.append(
            f"### {rule['code']} – {rule['filename']}\n{rule['text']}"
        )

    return "\n\n".join(chunks).strip()

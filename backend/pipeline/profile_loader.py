from backend.rag.profile_registry import load_profile_text


def load_targeted_profiles(profiles, max_chars_per_profile: int = 5000):
    loaded = []
    missing = []

    for p in profiles or []:
        code = p.get("code")
        if not code:
            continue

        item = load_profile_text(code, max_chars=max_chars_per_profile)

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
        "selected_codes": [p.get("code") for p in (profiles or []) if p.get("code")],
        "loaded": loaded,
        "missing": missing,
    }


def format_profiles_for_prompt(bundle: dict) -> str:
    chunks = []

    for item in bundle.get("loaded", []):
        chunks.append(
            f"### {item['code']} – {item['filename']}\n{item['text']}"
        )

    return "\n\n".join(chunks).strip()

from backend.rag.output_registry import load_output_text


MODE_MAP = {
    "STANDARD": ["O1", "O2", "O3"],
    "FAST_REQUEST": ["O1", "O3", "O5"],
    "PARENT_OUTPUT": ["O1", "O3", "O4"],
    "PROFESSIONAL_REPORT": ["O1", "O3", "O6"],
}


def load_targeted_output(output_mode, max_chars_per_item: int = 3000):
    selected_codes = MODE_MAP.get(output_mode, ["O1", "O3"])

    loaded = []
    missing = []

    for code in selected_codes:
        item = load_output_text(
            code,
            max_chars=max_chars_per_item
        )

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
        "selected_codes": selected_codes,
        "loaded": loaded,
        "missing": missing,
    }


def format_output_for_prompt(bundle: dict) -> str:
    chunks = []

    for item in bundle.get("loaded", []):
        chunks.append(
            f"### {item['code']} – {item['filename']}\n{item['text']}"
        )

    return "\n\n".join(chunks).strip()

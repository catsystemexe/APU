from backend.rag.block_registry import load_block_text


def load_targeted_blocks(blocks, max_chars_per_block: int = 5000):
    selected_codes = []
    loaded = []
    missing = []

    seen = set()

    for block in (blocks or []):
        for code in block.get("candidate_subblocks", []):
            code = (code or "").strip().upper()

            if not code or code in seen:
                continue

            seen.add(code)
            selected_codes.append(code)

            item = load_block_text(code, max_chars=max_chars_per_block)

            if item:
                loaded.append({
                    "code": item["code"],
                    "family": item["family"],
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


def format_blocks_for_prompt(bundle: dict) -> str:
    chunks = []

    for item in bundle.get("loaded", []):
        chunks.append(
            f"### {item['code']} – {item['filename']}\n{item['text']}"
        )

    return "\n\n".join(chunks).strip()

from pathlib import Path
import re

BASE_PATH = Path("kb/output")


def registry_summary():
    files = []

    if not BASE_PATH.exists():
        return {
            "count": 0,
            "codes": [],
            "files": [],
        }

    for path in sorted(BASE_PATH.glob("O*.md")):
        name = path.name
        match = re.match(r"^(O\d+)_([^.]+)\.md$", name)

        if not match:
            continue

        code = match.group(1)
        slug = match.group(2)

        files.append({
            "code": code,
            "slug": slug,
            "filename": name,
            "path": str(path),
        })

    return {
        "count": len(files),
        "codes": [f["code"] for f in files],
        "files": files,
    }


def load_output_text(code: str, max_chars: int = 4000):
    summary = registry_summary()

    for item in summary["files"]:
        if item["code"] != code:
            continue

        path = Path(item["path"])

        if not path.exists():
            return None

        text = path.read_text(encoding="utf-8").strip()

        return {
            **item,
            "chars": min(len(text), max_chars),
            "text": text[:max_chars],
        }

    return None

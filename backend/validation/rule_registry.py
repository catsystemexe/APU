from pathlib import Path
import re
from typing import Dict, List


VALIDATION_DIR = Path("kb/validation")

RULE_FILE_RE = re.compile(
    r"^(?P<code>V[0-9]+)_(?P<slug>[a-zA-Z0-9_\-]+)\.md$"
)


def parse_rule_filename(path: Path) -> dict | None:
    m = RULE_FILE_RE.match(path.name)
    if not m:
        return None

    return {
        "code": m.group("code"),
        "slug": m.group("slug"),
        "filename": path.name,
        "path": str(path),
    }


def list_validation_rules() -> List[Dict]:
    if not VALIDATION_DIR.exists():
        return []

    out = []
    for p in sorted(VALIDATION_DIR.glob("V*.md")):
        item = parse_rule_filename(p)
        if item:
            out.append(item)

    return out


def load_validation_rule(code: str, max_chars: int = 6000) -> dict | None:
    code = (code or "").strip().upper()

    for item in list_validation_rules():
        if item["code"].upper() == code:
            path = Path(item["path"])
            txt = path.read_text(encoding="utf-8", errors="ignore").strip()
            if max_chars and len(txt) > max_chars:
                txt = txt[:max_chars]
            return {
                **item,
                "text": txt,
                "chars": len(txt),
            }

    return None


def registry_summary() -> dict:
    files = list_validation_rules()
    return {
        "count": len(files),
        "codes": [f["code"] for f in files],
        "files": files,
    }

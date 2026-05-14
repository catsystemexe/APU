from pathlib import Path
import re
from typing import Dict, List


BLOCKS_DIR = Path("kb/blocks")

BLOCK_FILE_RE = re.compile(
    r"^(?P<code>[A-E][0-9]+)_(?P<slug>[a-zA-Z0-9_\-]+)\.md$"
)


def parse_block_filename(path: Path) -> dict | None:
    m = BLOCK_FILE_RE.match(path.name)
    if not m:
        return None

    code = m.group("code")
    slug = m.group("slug")

    return {
        "code": code,
        "family": code[0],
        "slug": slug,
        "filename": path.name,
        "path": str(path),
    }


def list_block_files() -> List[Dict]:
    if not BLOCKS_DIR.exists():
        return []

    out = []
    for p in sorted(BLOCKS_DIR.glob("*.md")):
        item = parse_block_filename(p)
        if item:
            out.append(item)

    return out


def load_block_text(code: str, max_chars: int = 6000) -> dict | None:
    code = (code or "").strip().upper()

    for item in list_block_files():
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
    files = list_block_files()
    by_family = {}

    for item in files:
        by_family.setdefault(item["family"], 0)
        by_family[item["family"]] += 1

    return {
        "count": len(files),
        "by_family": by_family,
        "files": files,
    }

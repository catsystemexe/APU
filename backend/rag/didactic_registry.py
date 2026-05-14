from pathlib import Path
import re


DIDACTIC_DIR = Path("kb/didactic")

FILE_RE = re.compile(
    r"^(?P<code>T[0-9]+)_(?P<slug>[a-zA-Z0-9_\-]+)\.md$"
)


def parse_filename(path):
    m = FILE_RE.match(path.name)
    if not m:
        return None

    code = m.group("code")
    slug = m.group("slug")

    return {
        "code": code,
        "slug": slug,
        "filename": path.name,
        "path": str(path),
    }


def list_didactic_files():
    if not DIDACTIC_DIR.exists():
        return []

    out = []

    for p in sorted(DIDACTIC_DIR.glob("*.md")):
        item = parse_filename(p)
        if item:
            out.append(item)

    return out


def load_didactic_text(code, max_chars=6000):
    code = (code or "").strip().upper()

    for item in list_didactic_files():
        if item["code"].upper() == code:
            p = Path(item["path"])
            txt = p.read_text(
                encoding="utf-8",
                errors="ignore"
            ).strip()

            if max_chars and len(txt) > max_chars:
                txt = txt[:max_chars]

            return {
                **item,
                "text": txt,
                "chars": len(txt),
            }

    return None


def registry_summary():
    files = list_didactic_files()

    return {
        "count": len(files),
        "codes": [f["code"] for f in files],
        "files": files,
    }

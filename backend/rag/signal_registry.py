from pathlib import Path
import json
import re
import unicodedata


BASE = Path("kb/signals")

# legacy fallback files
S1_PATH = BASE / "S1_observable_map.json"
S1_CANDIDATES_PATH = BASE / "S1_observable_candidates_from_profiles.json"
S2_PATH = BASE / "S2_need_map.json"  # legacy fallback if ever added
S3_CONTEXT_PATH = BASE / "S3_context_map.json"
S3_LABEL_PATH = BASE / "S3_label_map.json"
S4_PATH = BASE / "S4_trend_intensity_map.json"

# new folder-based db
S1_DIR = BASE / "S1-observables"
S2_DIR = BASE / "S2-needs"
S3_DIR = BASE / "S3-context"
S4_DIR = BASE / "S4-intensity-trend"


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_items(data):
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        items = data.get("items")
        if isinstance(items, list):
            return items

    return []


def _load_json_file(path: Path) -> list[dict]:
    data = _read_json(path)
    return _extract_items(data)


def _load_json_folder(
    folder: Path,
    exclude_files: set[str] | None = None,
) -> list[dict]:
    exclude_files = exclude_files or set()

    if not folder.exists():
        return []

    out = []

    for path in sorted(folder.glob("*.json")):
        if path.name in exclude_files:
            continue

        data = _read_json(path)
        items = _extract_items(data)

        if items:
            out.extend(items)

    return out


def _dedupe_by_id(items: list[dict]) -> list[dict]:
    out = []
    seen = set()

    for item in items or []:
        if not isinstance(item, dict):
            continue

        key = item.get("id") or (
            item.get("observable")
            or item.get("label")
            or item.get("meaning")
            or item.get("notepad")
            or str(item)
        )

        if key in seen:
            continue

        out.append(item)
        seen.add(key)

    return out


def _folder_plus_legacy(
    folder: Path,
    legacy_files: list[Path] | None = None,
    exclude_files: set[str] | None = None,
) -> list[dict]:
    items = _load_json_folder(
        folder=folder,
        exclude_files=exclude_files,
    )

    for fallback_file in legacy_files or []:
        items.extend(_load_json_file(fallback_file))

    return _dedupe_by_id(items)


def _folder_first(
    folder: Path,
    fallback_file: Path | None = None,
    exclude_files: set[str] | None = None,
) -> list[dict]:
    items = _load_json_folder(
        folder=folder,
        exclude_files=exclude_files,
    )

    if items:
        return _dedupe_by_id(items)

    if fallback_file:
        return _load_json_file(fallback_file)

    return []


def load_observable_map() -> list[dict]:
    # S1_N is label/guard style, not normal observable runtime.
    # Runtime observables merge new DB + legacy maps to preserve old behavior.
    return _folder_plus_legacy(
        folder=S1_DIR,
        legacy_files=[S1_PATH, S1_CANDIDATES_PATH],
        exclude_files={"S1_N.json"},
    )


def load_need_map() -> list[dict]:
    return _folder_first(
        folder=S2_DIR,
        fallback_file=S2_PATH,
    )


def load_context_map() -> list[dict]:
    return _folder_plus_legacy(
        folder=S3_DIR,
        legacy_files=[S3_CONTEXT_PATH],
    )


def load_label_map() -> list[dict]:
    items = _load_json_file(S3_LABEL_PATH)

    # Add S1_N* false-positive guard items as interpretation labels.
    for guard_file in sorted(S1_DIR.glob("S1_N*.json")):
        for item in _load_json_file(guard_file):
            if not isinstance(item, dict):
                continue
            x = dict(item)
            x.setdefault("label_type", "false_positive_guard")
            x.setdefault("risk", x.get("false_positive_risk") or "HIGH")
            items.append(x)

    return _dedupe_by_id(items)


def load_trend_intensity_map() -> list[dict]:
    # S4_F is QA/checklist, not runtime matching.
    return _folder_plus_legacy(
        folder=S4_DIR,
        legacy_files=[S4_PATH],
        exclude_files={"S4_F.json"},
    )


def _get_patterns(entry: dict) -> list[str]:
    return (
        entry.get("patterns")
        or entry.get("trigger_patterns")
        or entry.get("teacher_phrases")
        or entry.get("typical_signals")
        or []
    )


TOO_GENERIC_PATTERNS = {
    "ceka",
    "cekani",
    "nechce",
    "problem",
    "nevydrzi cekat",
    "nevydrží čekat",
}


def _usable_pattern(pattern: str) -> bool:
    p = normalize_text(pattern)
    if not p:
        return False

    # Avoid single broad stems that cause false matches.
    if p in TOO_GENERIC_PATTERNS:
        return False

    # Very short one-word patterns are dangerous unless intentionally specific.
    if len(p.split()) == 1 and len(p) < 6:
        return False

    return True


def match_signal_map(text: str, entries: list[dict]) -> list[dict]:
    norm = normalize_text(text)
    hits = []

    for entry in entries or []:
        patterns = _get_patterns(entry)
        matched_patterns = []

        for pat in patterns:
            if not _usable_pattern(pat):
                continue

            p = normalize_text(pat)
            if p and p in norm:
                matched_patterns.append(pat)

        if matched_patterns:
            item = dict(entry)
            item["matched_patterns"] = matched_patterns
            hits.append(item)

    return hits


def match_observables(text: str) -> list[dict]:
    return match_signal_map(text, load_observable_map())


def match_needs(text: str) -> list[dict]:
    return match_signal_map(text, load_need_map())


def match_contexts(text: str) -> list[dict]:
    return match_signal_map(text, load_context_map())


def match_labels(text: str) -> list[dict]:
    return match_signal_map(text, load_label_map())


def match_trend_intensity(text: str) -> list[dict]:
    return match_signal_map(text, load_trend_intensity_map())


def registry_summary() -> dict:
    return {
        "observables": len(load_observable_map()),
        "needs": len(load_need_map()),
        "contexts": len(load_context_map()),
        "labels": len(load_label_map()),
        "trend_intensity": len(load_trend_intensity_map()),
    }

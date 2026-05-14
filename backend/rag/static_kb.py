from pathlib import Path
from typing import List, Tuple

KB_DIR = Path("kb/source")

# Priorita: nejdřív pravidla a techniky, pak profily.
KB_FILES: List[str] = [
    "SafetyCore_ZUS.md",
    "AgentRulesCore.md",
    "Techniky_ZUS.md",
    "SpecPedCore_ZUS.md",
    "DidacticCore_ZUS.md",
    "PsychCore_ZUS.md",
    "QuestionCore_ZUS.md",
    "Profil_01_ZUS.md",
    "Profil_02_ZUS.md",
    "Profil_03_ZUS.md",
    "Profil_04_ZUS.md",
    "Profil_05_ZUS.md",
    "Profil_06_ZUS.md",
    "Profil_07_ZUS.md",
    "Profil_08_ZUS.md",
]

# Hrubé limity per-file (znaky). Udržíme “jádro” i při menším budgetu.
PER_FILE_LIMITS = {
    "SafetyCore_ZUS.md": 4000,
    "AgentRulesCore.md": 6000,
    "Techniky_ZUS.md": 12000,
    "SpecPedCore_ZUS.md": 8000,
    "DidacticCore_ZUS.md": 6000,
    "PsychCore_ZUS.md": 5000,
    "QuestionCore_ZUS.md": 5000,
    # Profily menší, ať se vejdou aspoň výtah
    "Profil_01_ZUS.md": 2500,
    "Profil_02_ZUS.md": 2500,
    "Profil_03_ZUS.md": 2500,
    "Profil_04_ZUS.md": 2500,
    "Profil_05_ZUS.md": 2500,
    "Profil_06_ZUS.md": 2500,
    "Profil_07_ZUS.md": 2500,
    "Profil_08_ZUS.md": 2500,
}

def _read_file(path: Path, limit: int) -> str:
    txt = path.read_text(encoding="utf-8", errors="ignore").strip()
    if not txt:
        return ""
    return txt[:limit] if limit and len(txt) > limit else txt

def load_static_kb(max_chars: int = 26000) -> Tuple[str, List[Tuple[str, int]]]:
    """
    Načte KB soubory v prioritním pořadí.
    Vrací: (kb_text, used_files[(name, chars)])
    max_chars = globální budget, aby systém prompt nevybouchl.
    """
    chunks = []
    used: List[Tuple[str, int]] = []
    total = 0

    for fname in KB_FILES:
        p = KB_DIR / fname
        if not p.exists():
            continue

        per_lim = PER_FILE_LIMITS.get(fname, 2000)
        txt = _read_file(p, per_lim)
        if not txt:
            continue

        remaining = max_chars - total
        if remaining <= 0:
            break

        # Když už nemáme budget, vezmeme jen zbytek bez hlavičky
        if len(txt) > remaining:
            txt = txt[:remaining]

        block = f"\n\n### {fname}\n{txt}"
        chunks.append(block)
        used.append((fname, len(txt)))
        total += len(txt)

        if total >= max_chars:
            break

    return ("\n".join(chunks).strip(), used)
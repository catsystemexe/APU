import re
from typing import Dict, Tuple

# -----------------------------
# Text normalization
# -----------------------------
def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("ě", "e").replace("š", "s").replace("č", "c").replace("ř", "r").replace("ž", "z")
    s = s.replace("ý", "y").replace("á", "a").replace("í", "i").replace("é", "e").replace("ú", "u").replace("ů", "u")
    s = s.replace("ť", "t").replace("ď", "d").replace("ň", "n")
    return s

# -----------------------------
# Keyword families (tolerant stems)
# -----------------------------
URG_STEMS = [
    r"\bakutn", r"\burgent", r"\bhned\b", r"\bted\b", r"\bted hned\b",
    r"\bokamz", r"\brychl", r"\brychly zasah\b", r"\bzasah\b",
    r"\bfofr", r"\bfofrem\b", r"\brychle\b",
]

AUTH_STEMS = [
    r"\bano\b", r"\bjasne\b", r"\bnavrhni\b", r"\bchci navrh\b", r"\bchci reseni\b",
    r"\bpoj[dď] do reseni\b", r"\bfaze 2\b", r"\bmuze[sš] navrhnout\b", r"\bnavrhni postup\b",
]

# ACTOR/CONTEXT words (NOT enough for WHAT)
ACTOR_STEMS = [
    r"\bzak\b", r"\bzakyn", r"\bdite\b", r"\bdeti\b", r"\btrida\b", r"\bskupin\b",
]

# Observable behavior / symptoms (THIS defines WHAT)
BEHAVIOR_STEMS = [
    # disruption / class behaviors
    r"\bvyru[sš]", r"\bskace\b", r"\bskace do reci\b", r"\bprekric", r"\bkric",
    r"\bsm(e|ej|ich|eji)", r"\bplac", r"\bodmita", r"\bute(k|c)", r"\bprovok",
    r"\burazi", r"\bbitk", r"\bstrka", r"\bhluk\b", r"\bchaos\b",

    # performance anxiety / stage fright – observable
    r"\btres", r"\btrase", r"\btresou", r"\btr(e|a)s(ou|e)\b",
    r"\bztuhn", r"\bzmrzn", r"\bzamrzn",
    r"\bvynecha\b", r"\bvynech", r"\bvypadek\b", r"\bvypadky\b",
    r"\bzapom(e|ne)", r"\bzadrh", r"\bsekne\b", r"\bsekne se\b",
    r"\brychle dycha\b", r"\bpot(i|í)\b", r"\bzbled", r"\bhlas se\b", r"\bchve",
]

# Attention / focus – these are already usable WHAT signals (not "fog")
ATTENTION_STEMS = [
    r"\bnedava pozor\b",
    r"\bne dava pozor\b",
    r"\broztekan",
    r"\bneudrzi pozornost\b",
    r"\bneudrzi\b.*\bpozornost\b",
    r"\bnesoustred",
    r"\bnepozorn",
    r"\bodbih",
]


WHERE_STEMS = [
    r"\bve tride\b", r"\bv tride\b", r"\bv hodine\b", r"\bna hodine\b", r"\bna uceni\b",
    r"\bv hudeb", r"\bve vytvar", r"\bna chodbe\b", r"\bve sborov", r"\bve studiu\b",
]

INTENSITY_STEMS = [
    r"\bted\b", r"\bhned\b", r"\bakutn", r"\bprave\b", r"\bneustale\b", r"\bporad\b",
    r"\bhodne\b", r"\bcasto\b", r"\bvelmi\b", r"\beskaluje\b", r"\bnebezpec",
]

AGE_STEMS = [
    r"\b(\d{1,2})\s*(let|roku|rocni)\b",          # "10 let", "8 roku"
    r"\bvek\b",                                   # "věk"
    r"\bmladsi\b|\bstarsi\b",                     # hrubé, když někdo napíše "mladší/starší"
    r"\b(1|2|3|4|5|6|7|8|9)\.\s*trida\b",          # "3. třída"
    r"\b(prvni|druha|treti|ctvrta|pata)\s*trida\b" # "první třída" (bez diakritiky po _norm)
]

NEED_HINTS = [
    r"\bpotrebu", r"\bchci\b", r"\bpomo[cs]", r"\bjak\b", r"\bco mam delat\b",
    r"\bvyresit\b", r"\bztlumit\b", r"\bnastavit hranice\b", r"\bmotivovat\b", r"\bkomunikovat s rodic",
]

# If teacher describes a problem category, it's usually also their need (must be verified later)
NEED_IMPLICIT_STEMS = [
    r"\bnedava pozor\b",
    r"\broztekan",
    r"\bneudrzi pozornost\b",
    r"\btr(e|a)ma\b",   # "trema" after _norm => "trema"
]

def _has_any(text_norm: str, stems) -> bool:
    for pat in stems:
        if re.search(pat, text_norm):
            return True
    return False

# -----------------------------
# Slot extraction (heuristic)
# -----------------------------
def extract_slots(message: str) -> Dict[str, bool]:
    t = _norm(message)

    need_explicit = _has_any(t, NEED_HINTS)
    need_implicit = _has_any(t, NEED_IMPLICIT_STEMS)

    what_behavior = _has_any(t, BEHAVIOR_STEMS)
    what_attention = _has_any(t, ATTENTION_STEMS)
    what = bool(what_behavior or what_attention)

    need = bool(need_explicit or need_implicit)
    age = _has_any(t, AGE_STEMS)
    where = _has_any(t, WHERE_STEMS)
    intensity = _has_any(t, INTENSITY_STEMS)

    return {
        "need": bool(need),
        "what": bool(what),
        "age": bool(age),
        "where": bool(where),
        "intensity": bool(intensity),
    }

def merge_slots(old: Dict[str, bool], new: Dict[str, bool]) -> Dict[str, bool]:
    out = dict(old or {})
    for k, v in (new or {}).items():
        out[k] = bool(out.get(k)) or bool(v)
    # ensure keys
    for k in ["need", "what", "age", "where", "intensity"]:
        out.setdefault(k, False)
    return out

def slot_completeness(slots: Dict[str, bool]) -> Tuple[bool, str]:
    # “complete” for standard F1→F2 readiness
    required = ["need", "what", "age", "where", "intensity"]
    missing = [k for k in required if not slots.get(k)]
    if not missing:
        return True, "GOLD"
    # if at least anchor exists, we can do SILVER quick actions (for urgency)
    if slots.get("what"):
        return False, "SILVER"
    return False, "DENY"

# -----------------------------
# Routing FSM
# -----------------------------
def route_message(message: str, state: dict) -> dict:
    """
    state:
      {
        "slots": {need,what,where,intensity},
        "auth_pending": bool,   # user must confirm transition to F2
      }
    """
    msg = message or ""
    t = _norm(msg)

    # --------------------------------
    # PERSONAL MODE BYPASS (priority)
    # --------------------------------
    if any(x in t for x in [
        "personal",
        "jak to funguje",
        "co umis",
        "co umíš"
    ]):
        return {
            "mode": "PERSONAL",
            "urgency": False,
            "has_anchor": False,
            "tier": "INFO",
            "auth_pending": False,
            "f1_complete": False,
            "reason": "personal_mode_trigger",
            "slots": state.get("slots", {}),
            "state": state,
        }

    # init state
    slots = merge_slots(state.get("slots") or {}, extract_slots(msg))
    state["slots"] = slots
    state.setdefault("auth_pending", False)

    urgency = _has_any(t, URG_STEMS)
    has_anchor = bool(slots.get("what"))

    # if we are waiting for explicit authorization to enter F2
    if state.get("auth_pending"):
        # explicit authorize now?
        if _has_any(t, AUTH_STEMS):
            complete, tier = slot_completeness(slots)
            if not complete:
                # still not enough to do F2 (deny with minimal instruction)
                return {
                    "mode": "F2_DENY",
                    "urgency": False,
                    "has_anchor": has_anchor,
                    "tier": "DENY",
                    "auth_pending": True,
                    "f1_complete": False,
                    "reason": "auth_confirmed_but_f1_incomplete",
                    "slots": slots,
                    "state": state,
                }
            return {
                "mode": "F2",
                "urgency": False,
                "has_anchor": has_anchor,
                "tier": "GOLD",
                "auth_pending": False,
                "f1_complete": True,
                "reason": "auth_confirmed_enter_f2",
                "slots": slots,
                "state": state,
            }

        # user did not authorize; keep them here (one short reminder)
        return {
            "mode": "F1",
            "urgency": False,
            "has_anchor": has_anchor,
            "tier": "SILVER" if has_anchor else "DENY",
            "auth_pending": True,
            "f1_complete": False,
            "reason": "waiting_for_auth_yes_no",
            "slots": slots,
            "state": state,
        }

    # -----------------------------
    # URGENCY path
    # -----------------------------
    if urgency:
        # No anchor → ask ONE question (F1_URG_ASK1)
        if not has_anchor:
            # Important: we DO NOT produce quick steps without anchor
            return {
                "mode": "F1_URG_ASK1",
                "urgency": True,
                "has_anchor": False,
                "tier": "SILVER",
                "auth_pending": False,
                "f1_complete": False,
                "reason": "urgency_no_anchor_ask1",
                "slots": slots,
                "state": state,
            }

        # We have an anchor. Decide SILVER vs GOLD based on completeness.
        complete, tier = slot_completeness(slots)

        if tier == "DENY":
            return {
                "mode": "FAST_DENY",
                "urgency": True,
                "has_anchor": False,
                "tier": "DENY",
                "auth_pending": False,
                "f1_complete": False,
                "reason": "urgency_but_no_anchor_deny",
                "slots": slots,
                "state": state,
            }

        if complete:
            return {
                "mode": "FAST_GOLD",
                "urgency": True,
                "has_anchor": True,
                "tier": "GOLD",
                "auth_pending": False,
                "f1_complete": True,
                "reason": "urgency_anchor_complete_fast_gold",
                "slots": slots,
                "state": state,
            }

        # anchor present but missing other slots → safe generic quick steps
        return {
            "mode": "FAST_SILVER",
            "urgency": True,
            "has_anchor": True,
            "tier": "SILVER",
            "auth_pending": False,
            "f1_complete": False,
            "reason": "urgency_anchor_partial_fast_silver",
            "slots": slots,
            "state": state,
        }

    # -----------------------------
    # STANDARD path (no urgency)
    # -----------------------------
    complete, tier = slot_completeness(slots)
    if complete:
        # we do NOT auto-enter F2; we ask for confirmation and set auth_pending
        state["auth_pending"] = True
        return {
            "mode": "F1",
            "urgency": False,
            "has_anchor": has_anchor,
            "tier": "GOLD",
            "auth_pending": True,
            "f1_complete": True,
            "reason": "f1_complete_offer_f2",
            "slots": slots,
            "state": state,
        }

    # default: keep F1 loop
    return {
        "mode": "F1",
        "urgency": False,
        "has_anchor": has_anchor,
        "tier": tier,
        "auth_pending": False,
        "f1_complete": False,
        "reason": "f1_incomplete_continue",
        "slots": slots,
        "state": state,
    }
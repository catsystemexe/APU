from copy import deepcopy
from datetime import datetime, timezone


NOTEPAD_VERSION = "3.0"


DEFAULT_CASE_STATE = {
    "case_id": None,
    "version": NOTEPAD_VERSION,
    "created_at": None,
    "updated_at": None,
    "case_summary": "",
    "confirmed_observations": [],
    "uncertain_observations": [],
    "environmental_triggers": [],
    "effective_supports": [],
    "ineffective_supports": [],
    "uncertain_hypotheses": [],
    "contradictions": [],
    "open_questions": [],
    "parent_notes": [],
    "teacher_notes": [],
    "timeline_markers": [],
    "safety_notes": [],
    "next_steps": [],

    "case_core": {
        "observable_anchor": [],
        "pedagogical_need": [],
        "context": [],
        "age": [],
        "trend_intensity": [],
        "parent_school_mismatch": [],
    },

    "case_understanding": {
        "plain_language_hypotheses": [],
        "working_interpretation": "",
    },

    "case_gaps": {
        "missing_information": [],
        "clarifying_questions": [],
        "recommended_next_step": [],
    },

    "case_info": {
        "observable_anchor": [],
        "pedagogical_need": [],
        "context": [],
        "parent_school_difference": [],
        "trend_intensity": [],
    },

    "working_hypotheses": [],

    "certainty_and_gaps": {
        "most_supported": [],
        "missing_for_disambiguation": [],
    },

    "what_to_try": [],
    "general_support_options": [],
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_case_state(case_id=None):
    state = deepcopy(DEFAULT_CASE_STATE)
    state["case_id"] = case_id
    now = now_iso()
    state["created_at"] = now
    state["updated_at"] = now
    return state


def normalize_case_state(state=None):
    base = new_case_state()
    if not isinstance(state, dict):
        return base

    out = deepcopy(base)
    for key in out:
        if key in state:
            out[key] = state[key]

    out["version"] = NOTEPAD_VERSION
    if not out.get("created_at"):
        out["created_at"] = state.get("updated_at") or now_iso()
    out["updated_at"] = now_iso()
    return out


def add_item(state, section, item):
    state = normalize_case_state(state)
    if section not in state or not isinstance(state[section], list):
        raise ValueError(f"invalid notepad section: {section}")

    if not isinstance(item, dict):
        raise ValueError("notepad item must be dict")

    existing = state[section]
    text = (item.get("text") or item.get("question") or "").strip()

    if text:
        for old in existing:
            old_text = (old.get("text") or old.get("question") or "").strip()
            if old_text == text:
                return state

    existing.append(item)
    state["updated_at"] = now_iso()
    return state

from backend.notepad.state import normalize_case_state, add_item


LIST_SECTIONS = [
    "uncertain_observations",
    "environmental_triggers",
    "teacher_interpretation_labels",
    "effective_supports",
    "ineffective_supports",
    "uncertain_hypotheses",
    "contradictions",
    "open_questions",
    "parent_notes",
    "teacher_notes",
    "timeline_markers",
    "safety_notes",
    "next_steps",
]


def _merge_list_unique(existing, incoming):
    existing = existing if isinstance(existing, list) else []
    incoming = incoming if isinstance(incoming, list) else []

    out = list(existing)
    seen = {
        (x.get("text") or x.get("question") or str(x)).strip()
        for x in out
        if isinstance(x, dict)
    }

    for item in incoming:
        if not isinstance(item, dict):
            continue
        key = (item.get("text") or item.get("question") or str(item)).strip()
        if key and key not in seen:
            out.append(item)
            seen.add(key)

    return out


CONTEXT_COVERS = {
    "při skupinové práci v kruhu": [
        "skupinový kruh",
    ],
    "při ranním kruhu": [
        "ranní kruh",
        "skupinový kruh",
        "při společné klidové činnosti ve skupině",
    ],
    "v souvislosti s jídlem / stolováním": [
        "jídlo / oběd",
    ],
}


def _dedupe_context_items(items):
    items = items if isinstance(items, list) else []
    texts = {
        (x.get("text") or "").strip()
        for x in items
        if isinstance(x, dict)
    }

    covered = set()
    for specific, parents in CONTEXT_COVERS.items():
        if specific in texts:
            covered.update(parents)

    out = []
    seen = set()

    for item in items:
        if not isinstance(item, dict):
            continue

        text = (item.get("text") or "").strip()
        if not text:
            continue

        if text in covered:
            continue

        if text in seen:
            continue

        out.append(item)
        seen.add(text)

    return out


def _merge_case_dict_section(state, proposal, section):
    src = proposal.get(section) or {}
    dst = state.get(section) or {}

    if not isinstance(src, dict) or not isinstance(dst, dict):
        return

    for key, value in src.items():
        if isinstance(value, list):
            dst[key] = _merge_list_unique(dst.get(key), value)
        elif isinstance(value, str) and value and not dst.get(key):
            dst[key] = value

    if section == "case_info":
        dst["context"] = _dedupe_context_items(dst.get("context") or [])

    state[section] = dst


def apply_notepad_proposal(case_state, proposal):
    state = normalize_case_state(case_state)

    if proposal.get("case_summary"):
        state["case_summary"] = proposal["case_summary"]

    for section in LIST_SECTIONS:
        for item in proposal.get(section) or []:
            state = add_item(state, section, item)

    for section in ["case_core", "case_understanding", "case_gaps", "case_info", "certainty_and_gaps"]:
        _merge_case_dict_section(state, proposal, section)

    state["working_hypotheses"] = _merge_list_unique(
        state.get("working_hypotheses"),
        proposal.get("working_hypotheses"),
    )

    state["what_to_try"] = _merge_list_unique(
        state.get("what_to_try"),
        proposal.get("what_to_try"),
    )

    state["general_support_options"] = _merge_list_unique(
        state.get("general_support_options"),
        proposal.get("general_support_options"),
    )

    return state

from backend.notepad.state import normalize_case_state, now_iso


VALID_ACTIONS = {
    "confirm",
    "reject",
    "mark_uncertain",
    "add_manual_note",
}


def _find_item(items, target_id):
    if not isinstance(items, list):
        return None

    for item in items:
        if item.get("id") == target_id:
            return item

    return None


def _ensure_id(item, fallback_prefix="item"):
    if not item.get("id"):
        item["id"] = f"{fallback_prefix}_{abs(hash(str(item))) % 10_000_000}"
    return item


def apply_notepad_action(case_state, action_payload):
    """
    Supported actions:

    confirm
    reject
    mark_uncertain
    add_manual_note
    """

    state = normalize_case_state(case_state)

    action = (action_payload.get("action") or "").strip()
    section = (action_payload.get("section") or "").strip()
    target_id = (action_payload.get("target_id") or "").strip()
    payload = action_payload.get("payload") or {}

    if action not in VALID_ACTIONS:
        raise ValueError(f"invalid action: {action}")

    if action == "add_manual_note":
        note = {
            "id": None,
            "text": payload.get("text", ""),
            "status": "reported",
            "source": "manual_user_note",
            "created_at": now_iso(),
        }
        note = _ensure_id(note, "manual")

        if section not in state or not isinstance(state.get(section), list):
            raise ValueError(f"invalid section: {section}")

        state[section].append(note)
        state["updated_at"] = now_iso()
        return state

    if section not in state or not isinstance(state.get(section), list):
        raise ValueError(f"invalid section: {section}")

    item = _find_item(state[section], target_id)

    if not item:
        raise ValueError(f"target item not found: {target_id}")

    if action == "confirm":
        item["status"] = "confirmed"

    elif action == "reject":
        item["status"] = "rejected"

    elif action == "mark_uncertain":
        item["status"] = "to_verify"

    item["updated_at"] = now_iso()
    state["updated_at"] = now_iso()

    return state

from copy import deepcopy
from uuid import uuid4

from backend.notepad.state import new_case_state, normalize_case_state


_CASE_STORE = {}


def generate_case_id():
    return f"case_{uuid4().hex[:12]}"


def load_case_state(case_id=None):
    """
    In-memory MVP persistence.

    Later:
    DB / redis / real persistence layer.
    """

    if not case_id:
        case_id = generate_case_id()

    if case_id not in _CASE_STORE:
        _CASE_STORE[case_id] = new_case_state(case_id=case_id)

    return deepcopy(_CASE_STORE[case_id])


def save_case_state(case_state):
    state = normalize_case_state(case_state)
    case_id = state.get("case_id")

    if not case_id:
        case_id = generate_case_id()
        state["case_id"] = case_id

    _CASE_STORE[case_id] = deepcopy(state)
    return deepcopy(state)


def list_cases():
    return sorted(list(_CASE_STORE.keys()))

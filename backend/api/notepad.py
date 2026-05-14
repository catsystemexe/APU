from fastapi import APIRouter, HTTPException

from backend.session.case_store import load_case_state, save_case_state
from backend.notepad.actions import apply_notepad_action


router = APIRouter()


@router.post("/api/notepad/action")
def notepad_action(payload: dict):
    case_id = payload.get("case_id")

    if not case_id:
        raise HTTPException(status_code=400, detail="missing case_id")

    try:
        case_state = load_case_state(case_id)
        updated = apply_notepad_action(case_state, payload)
        saved = save_case_state(updated)

        return {
            "ok": True,
            "case_id": saved.get("case_id"),
            "case_state": saved,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

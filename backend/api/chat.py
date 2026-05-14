from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.core.model import call_model
from backend.output.renderers import (
    render_fast_response,
    render_partial_response,
    render_full_response,
)
from backend.rag.static_kb import load_static_kb
from backend.pipeline.orchestrator import run_pipeline_async
from backend.session.case_store import load_case_state, save_case_state
from backend.pipeline.schemas import APURequest

from config.settings import SYSTEM_INSTRUCTIONS

import os
import uuid
import time

router = APIRouter()

# --------------------------------------------------
# In-memory sessions
# --------------------------------------------------

_SESSIONS = {}
_SESSION_TTL_SEC = 6 * 60 * 60


def _now():
    return time.time()


def _gc_sessions():
    t = _now()
    dead = [
        sid for sid, s in _SESSIONS.items()
        if (t - float(s.get("updated_at", t))) > _SESSION_TTL_SEC
    ]
    for sid in dead:
        _SESSIONS.pop(sid, None)


def _get_sid(request: Request):
    sid = request.cookies.get("apu_session")
    if not sid:
        sid = uuid.uuid4().hex
    return sid


def _get_state(sid: str):
    st = _SESSIONS.get(sid) or {}
    st["updated_at"] = _now()
    _SESSIONS[sid] = st
    return st


def _set_state(sid: str, st: dict):
    st = dict(st or {})
    st["updated_at"] = _now()
    _SESSIONS[sid] = st


# --------------------------------------------------
# Token estimates
# --------------------------------------------------

def est_tokens_from_chars(chars: int):
    return max(0, int(chars / 4))


def get_pricing():
    pin = os.getenv("OPENAI_PRICE_IN_PER_1M")
    pout = os.getenv("OPENAI_PRICE_OUT_PER_1M")

    if not pin or not pout:
        return None

    try:
        return float(pin), float(pout)
    except ValueError:
        return None


# --------------------------------------------------
# Output mode wrappers
# --------------------------------------------------

def build_mode_prefix(mode: str):
    return f"""
ROUTING JE ROZHODNUT PIPELINE.

AKTUÁLNÍ OUTPUT MODE: {mode}

Neprováděj vlastní routing.
Nezobrazuj interní bloky, profily, zóny ani interní kódy.
Dodrž přesně pouze pravidla tohoto režimu.
"""


def build_mode_instructions(mode: str):
    if mode == "FAST":
        return """
MODE C – FAST / QUICK SAFE RESPONSE

Použij pouze interventions z PIPELINE CONTEXT.

Nevymýšlej vlastní kroky.

Formát:
⚡ RYCHLÝ ZÁSAH
Krok 1: ...
Krok 2: ...
Krok 3: ...
🤔 jedna krátká ověřovací otázka

Pravidla:
- max 3 kroky
- pouze 1 otázka
- bez diagnóz
- bez hluboké analýzy
- bez dalších nabídek
- vykání
"""

    if mode == "PARTIAL":
        return """
MODE B – PARTIAL / OMEZENÁ ODPOVĚĎ

Formát:
Shrnutí: <1 věta>
Možnosti: <2–3 pracovní možnosti>
Chybí upřesnit: <1 věta>
🤔 <otázka 1>
🤔 <otázka 2>

Pravidla:
- žádný definitivní závěr
- bez diagnóz
- bez interních kódů
- vykání
"""

    if mode == "FULL":
        return """
MODE A – FULL / PLNÁ ODPOVĚĎ

Formát:
Shrnutí: <1 věta>
Pracovní interpretace: <stručně>
Doporučený postup:
Krok 1: ...
Krok 2: ...
Krok 3: ...
Ověření: <jak poznat zlepšení>

Pravidla:
- použij interventions + didactic context
- bez diagnóz
- bez interních kódů
- vykání
"""

    if mode == "LOW_DATA":
        return """
MODE D – LOW DATA

Formát:
Shrnutí: <1 věta>
Nelze zatím bezpečně vyhodnotit, protože chybí konkrétní pozorovatelný projev.
🤔 Co přesně dítě dělá nebo říká, co je vidět nebo slyšet?

Pravidla:
- žádné hypotézy
- žádné rady
- žádná diagnóza
- pouze 1 otázka
- vykání
"""

    if mode == "PERSONAL":
        return """
PERSONAL MODE

Stručně:
- kdo jsi
- co umíš
- jak s tebou pracovat

Bez interní pipeline.
Bez diagnostiky.
"""

    return """
FALLBACK MODE

Použij LOW_DATA bezpečný režim.
"""


# --------------------------------------------------
# API
# --------------------------------------------------


@router.post("/session/reset")
async def reset_session(request: Request):
    sid = request.cookies.get("apu_session")

    if sid:
        _SESSIONS.pop(sid, None)

    resp = JSONResponse({
        "ok": True,
        "reset": True,
    })

    resp.delete_cookie(
        "apu_session",
        httponly=True,
        samesite="lax",
    )

    return resp


@router.post("/chat")
async def chat(request: Request):
    _gc_sessions()

    body = await request.json()
    message = body.get("message", "")
    llm_extraction = bool(body.get("llm_extraction", False))

    sid = _get_sid(request)
    state = _get_state(sid)

    new_state = state
    _set_state(sid, new_state)

    incoming_case_id = body.get("case_id")
    loaded_case_state = load_case_state(incoming_case_id)
    new_state["case_id"] = loaded_case_state.get("case_id")
    new_state["case_state"] = loaded_case_state
    _set_state(sid, new_state)

    kb_context, used = load_static_kb()

    pipeline_result = await run_pipeline_async(
        APURequest(
            message=message,
            state={
                **new_state,
                "case_state": loaded_case_state,
            },
        ),
        kb_context=kb_context,
        llm_extraction=llm_extraction,
    )

    effective_mode = pipeline_result.meta.output_mode or "LOW_DATA"

    mode_prefix = build_mode_prefix(effective_mode)
    mode_instructions = build_mode_instructions(effective_mode)

    system = f"""{SYSTEM_INSTRUCTIONS}

{mode_prefix}

{mode_instructions}

--------------------------------
PIPELINE CONTEXT
--------------------------------

{pipeline_result.system_context}

--------------------------------
KB CONTEXT
--------------------------------

{kb_context}
"""

    if effective_mode == "FAST":
        response = render_fast_response(
            pipeline_result.meta.interventions or []
        )
    elif effective_mode == "PARTIAL":
        response = render_partial_response(
            pipeline_result.meta.blocks or [],
            pipeline_result.meta.interventions or [],
            pipeline_result.meta.signals or [],
            pipeline_result.meta.input_quality or {},
        )
    elif effective_mode == "FULL":
        response = render_full_response(
            pipeline_result.meta.interventions or []
        )
    else:
        response = await call_model(system, message)

    est_in = est_tokens_from_chars(len(system) + len(message))
    est_out = est_tokens_from_chars(len(response))
    est_total = est_in + est_out

    pricing = get_pricing()

    est_cost = None
    price_in = None
    price_out = None

    if pricing:
        price_in, price_out = pricing
        est_cost = (
            (est_in / 1_000_000) * price_in
            + (est_out / 1_000_000) * price_out
        )

    updated_case_state = (
        ((pipeline_result.meta.input_quality or {}).get("notepad") or {}).get("case_state")
        or loaded_case_state
    )
    saved_case_state = save_case_state(updated_case_state)
    new_state["case_id"] = saved_case_state.get("case_id")
    new_state["case_state"] = saved_case_state
    _set_state(sid, new_state)

    meta = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "pricing": {
            "in_per_1m": price_in,
            "out_per_1m": price_out,
        },
        "kb_chars": len(kb_context),
        "kb_files": [
            {"name": n, "chars": c}
            for (n, c) in used
        ],
        "tokens": {
            "est_input_tokens": est_in,
            "est_output_tokens": est_out,
            "est_total_tokens": est_total,
            "est_cost_usd": est_cost,
        },
        "pipeline": pipeline_result.meta.to_dict(),
        "routing": {
            "output_mode": effective_mode,
            "source": "pipeline",
            "input_quality": pipeline_result.meta.input_quality,
            "sid": sid,
        },
    }

    resp = JSONResponse({
        "response": response,
        "case_id": saved_case_state.get("case_id"),
        "case_state": saved_case_state,
        "meta": meta,
    })

    if request.cookies.get("apu_session") != sid:
        resp.set_cookie(
            "apu_session",
            sid,
            httponly=True,
            samesite="lax",
        )

    return resp

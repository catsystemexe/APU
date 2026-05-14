import json
from pathlib import Path

from openai import AsyncOpenAI

from config.settings import (
    OPENAI_MODEL,
    ENABLE_LLM_SEMANTIC_EXTRACTION,
    SEMANTIC_EXTRACTOR_PROMPT_PATH,
)

import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


EMPTY_SEMANTIC_RESULT = {
    "observable": [],
    "pedagogical_need": [],
    "context": [],
    "trend_intensity": [],
    "interpretation_labels": [],
    "uncertain_points": [],
}


def _load_prompt() -> str:
    path = Path(SEMANTIC_EXTRACTOR_PROMPT_PATH)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _safe_list(value):
    return value if isinstance(value, list) else []


def _normalize_result(data: dict) -> dict:
    if not isinstance(data, dict):
        return dict(EMPTY_SEMANTIC_RESULT)

    out = dict(EMPTY_SEMANTIC_RESULT)
    for key in out:
        out[key] = _safe_list(data.get(key))

    return out


def should_run_semantic_fallback(signals: list[dict], validation: dict | None = None) -> bool:
    if not ENABLE_LLM_SEMANTIC_EXTRACTION:
        return False

    s = (signals or [{}])[0]
    flags = set(s.get("flags") or [])

    has_observable = bool(s.get("observable_candidates"))
    has_label = bool(s.get("interpretation_labels"))
    has_context_without_observable = "CONTEXT_WITHOUT_CHILD_OBSERVABLE" in flags
    missing_observable = "MISSING_OBSERVABLE_BEHAVIOR" in flags

    return (
        not has_observable
        or has_label
        or has_context_without_observable
        or missing_observable
    )


async def run_semantic_extractor(message: str) -> dict:
    prompt = _load_prompt()

    if not prompt:
        result = dict(EMPTY_SEMANTIC_RESULT)
        result["_error"] = "missing_semantic_extractor_prompt"
        return result

    try:
        resp = await client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message or ""},
            ],
        )

        text = getattr(resp, "output_text", None) or ""

        if not text:
            parts = []
            for item in (resp.output or []):
                for c in getattr(item, "content", []) or []:
                    t = getattr(c, "text", None)
                    if t:
                        parts.append(t)
            text = "\n".join(parts).strip()

        data = json.loads(text)
        result = _normalize_result(data)
        result["_raw_text"] = text
        result["_error"] = None
        return result

    except Exception as e:
        result = dict(EMPTY_SEMANTIC_RESULT)
        result["_error"] = f"{type(e).__name__}: {e}"
        return result


def semantic_result_to_signal(message: str, semantic: dict) -> dict:
    observable_candidates = []
    for item in semantic.get("observable") or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if not text:
            continue
        observable_candidates.append({
            "type": "observable_candidate",
            "meaning": text,
            "source": "llm_fallback",
            "confidence": (item.get("confidence") or "low").upper(),
            "requires_confirmation": item.get("requires_confirmation", True),
            "candidate_blocks": [],
            "candidate_zones": [],
        })

    pedagogical_need = []
    for item in semantic.get("pedagogical_need") or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if text:
            pedagogical_need.append({
                "type": "pedagogical_need_signal",
                "meaning": text,
                "source": "llm_fallback",
                "confidence": "LOW",
                "requires_confirmation": True,
            })

    context = []
    for item in semantic.get("context") or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if text:
            context.append({
                "type": "context_signal",
                "meaning": text,
                "source": "llm_fallback",
                "confidence": "LOW",
                "requires_confirmation": True,
            })

    trend_intensity = []
    for item in semantic.get("trend_intensity") or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if text:
            trend_intensity.append({
                "type": "trend_intensity_signal",
                "signal": text,
                "source": "llm_fallback",
                "effect": {"validation_flags": []},
                "confidence": "LOW",
                "requires_confirmation": True,
            })

    labels = []
    for item in semantic.get("interpretation_labels") or []:
        if not isinstance(item, dict):
            continue
        text = (item.get("text") or "").strip()
        if text:
            labels.append({
                "type": "interpretation_label",
                "label": text,
                "meaning": text,
                "risk": item.get("risk") or "high",
                "replacement_question": item.get("replacement_question"),
                "source": "llm_fallback",
                "confidence": "LOW",
                "requires_confirmation": True,
            })

    flags = ["LLM_FALLBACK_USED"]
    if labels:
        flags.append("HAS_INTERPRETATION_LABEL")
    if labels and not observable_candidates:
        flags.append("LABEL_WITHOUT_OBSERVATION")
    if not observable_candidates:
        flags.append("MISSING_OBSERVABLE_BEHAVIOR")

    return {
        "type": "signal_extraction_llm_fallback_v1",
        "raw_text": message or "",
        "normalized_text": message or "",
        "observable_candidates": observable_candidates,
        "context_candidates": [],
        "context": context,
        "age": [],
        "pedagogical_need": pedagogical_need,
        "trend_intensity": trend_intensity,
        "interpretation_labels": labels,
        "slang_or_jargon": [],
        "flags": flags,
        "confidence": "LOW",
        "specificity": {
            "score": 2 if observable_candidates else 0,
            "level": "LOW",
            "reasons": ["llm_fallback_candidate"] if observable_candidates else ["llm_fallback_no_observable"],
        },
        "semantic_extractor": {
            "source": "llm_fallback",
            "prompt_version": "semantic_extractor_prompt_v1",
            "requires_confirmation": True,
            "error": semantic.get("_error"),
        },
    }

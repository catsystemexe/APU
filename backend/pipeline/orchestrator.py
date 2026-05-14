import json
from backend.pipeline.schemas import APURequest, APUPipelineResult, APUPipelineMeta
from backend.input.intent import detect_intent, detect_pedagogical_need
from backend.inference.signals import extract_signals
from backend.inference.blocks import infer_blocks
from backend.inference.profiles import infer_profiles
from backend.inference.zones import infer_zones
from backend.interventions.selector import select_interventions
from backend.didactics.filter import apply_didactic_filter
from backend.validation.validator import validate_pipeline
from backend.output.transformer import select_output_mode
from backend.rag.block_registry import registry_summary
from backend.rag.profile_registry import registry_summary as profile_registry_summary
from backend.inference.rule_registry import registry_summary as inference_registry_summary
from backend.pipeline.inference_loader import load_targeted_inference_rules, format_inference_rules_for_prompt
from backend.pipeline.profile_loader import load_targeted_profiles, format_profiles_for_prompt
from backend.pipeline.validation_loader import load_targeted_validation_rules, format_validation_rules_for_prompt
from backend.pipeline.block_loader import load_targeted_blocks, format_blocks_for_prompt
from backend.pipeline.didactic_loader import load_targeted_didactic, format_didactic_for_prompt
from backend.pipeline.output_loader import load_targeted_output, format_output_for_prompt
from backend.pipeline.case_memory import hydrate_inference_from_case_state
from backend.evidence.extractor import build_evidence
from backend.notepad.extractor import build_notepad_update_proposal
from backend.notepad.updater import apply_notepad_proposal
from config.settings import ENABLE_LLM_SEMANTIC_EXTRACTION
from backend.llm.semantic_extractor import (
    should_run_semantic_fallback,
    run_semantic_extractor,
    semantic_result_to_signal,
)


CONFIDENCE_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}


def _cap_confidence(confidence: str, cap: str) -> str:
    confidence = confidence or "LOW"
    cap = cap or "LOW"
    if CONFIDENCE_ORDER.get(confidence, 1) <= CONFIDENCE_ORDER.get(cap, 1):
        return confidence
    return cap


def calibrate_overall_confidence(has_observable, specificity, validation):
    flags = set((validation or {}).get("flags", []))
    downgrades = set((validation or {}).get("downgrades", []))
    contradictions = (validation or {}).get("contradictions") or {}
    contradiction_level = contradictions.get("level", "NONE")

    score = int((specificity or {}).get("score") or 0)

    if not has_observable:
        return {
            "level": "LOW",
            "score": score,
            "cap": "LOW",
            "reasons": ["no_observable_anchor"],
        }

    level = "LOW"
    reasons = ["observable_anchor_present"]

    if score >= 5:
        level = "HIGH"
        reasons.append("high_specificity")
    elif score >= 3:
        level = "MEDIUM"
        reasons.append("medium_specificity")
    else:
        level = "LOW"
        reasons.append("low_specificity")

    cap = "HIGH"

    if "WEAK_INFERENCE" in flags:
        cap = "LOW"
        reasons.append("weak_inference_cap_low")

    if "FALSE_POSITIVE_RISK" in flags:
        cap = _cap_confidence(cap, "MEDIUM")
        reasons.append("false_positive_cap_medium")

    if "LABEL_WITHOUT_OBSERVATION" in flags or "MISSING_OBSERVABLE_BEHAVIOR" in flags:
        cap = "LOW"
        reasons.append("missing_observable_cap_low")

    if "HAS_INTERPRETATION_LABEL" in flags:
        cap = _cap_confidence(cap, "MEDIUM")
        reasons.append("interpretation_label_cap_medium")

    if contradiction_level == "HIGH":
        cap = "LOW"
        reasons.append("high_contradiction_cap_low")
    elif contradiction_level == "MEDIUM":
        cap = _cap_confidence(cap, "MEDIUM")
        reasons.append("medium_contradiction_cap_medium")

    if "resolve_contradiction_before_strong_conclusion" in downgrades:
        cap = _cap_confidence(cap, "LOW")
        reasons.append("contradiction_downgrade_cap_low")

    final = _cap_confidence(level, cap)

    return {
        "level": final,
        "raw_level": level,
        "score": score,
        "cap": cap,
        "reasons": reasons,
    }


def case_state_has_observable_anchor(case_state=None) -> bool:
    case_state = case_state or {}

    # v4 source of truth
    observations = ((case_state.get("case_info") or {}).get("observable_anchor") or [])

    return any(
        (x.get("status") in ["reported", "confirmed", "to_verify", None])
        and (x.get("text") or "").strip()
        for x in observations
        if isinstance(x, dict)
    )


def apply_case_memory_to_validation(validation, case_state=None, pedagogical_need_known=False):
    """
    If current turn only adds pedagogical need but prior case_state already
    contains observable anchor, do not force LOW_DATA.
    """
    validation = dict(validation or {})
    flags = list(validation.get("flags") or [])
    warnings = list(validation.get("warnings") or [])
    downgrades = list(validation.get("downgrades") or [])

    if pedagogical_need_known and case_state_has_observable_anchor(case_state):
        if "MISSING_OBSERVABLE_BEHAVIOR" in flags:
            flags.remove("MISSING_OBSERVABLE_BEHAVIOR")

        if "CASE_STATE_OBSERVABLE_ANCHOR" not in flags:
            flags.append("CASE_STATE_OBSERVABLE_ANCHOR")

        validation["needs_more_input"] = (
            "LOW_DATA" in flags
            or "LABEL_WITHOUT_OBSERVATION" in flags
        )

        validation["flags"] = flags
        validation["warnings"] = warnings
        validation["downgrades"] = downgrades

    return validation


def build_input_quality(intent, signals, validation, message="", case_state=None):
    signal = (signals or [{}])[0]

    observables = signal.get("observable_candidates", [])
    context_candidates = signal.get("context_candidates", [])
    labels = signal.get("interpretation_labels", [])
    context = signal.get("context", [])
    age = signal.get("age", [])
    pedagogical_need_signals = signal.get("pedagogical_need", [])

    has_current_observable = bool(observables)
    has_case_observable = case_state_has_observable_anchor(case_state)
    has_observable = has_current_observable or has_case_observable

    has_label = bool(labels)
    specificity = signal.get("specificity") or {"score": 0, "level": "LOW", "reasons": []}

    if has_case_observable and not has_current_observable:
        specificity = dict(specificity)
        reasons = list(specificity.get("reasons") or [])
        if "case_state_observable_anchor" not in reasons:
            reasons.append("case_state_observable_anchor")
        specificity["reasons"] = reasons
        specificity["score"] = max(int(specificity.get("score") or 0), 2)
        specificity["level"] = "MEDIUM" if specificity["score"] >= 3 else "LOW"

    needs_observation = (
        not has_observable
        or "LABEL_WITHOUT_OBSERVATION" in validation.get("flags", [])
        or (
            "MISSING_OBSERVABLE_BEHAVIOR" in validation.get("flags", [])
            and not has_case_observable
        )
    )

    pedagogical_need_known = (
        intent in ["FAST_REQUEST", "FULL_REQUEST"]
        or detect_pedagogical_need(message)
        or bool(pedagogical_need_signals)
    )

    calibrated_confidence = calibrate_overall_confidence(
        has_observable=has_observable,
        specificity=specificity,
        validation=validation,
    )

    confidence = calibrated_confidence["level"]

    missing_for_next_step = []

    if not has_observable:
        missing_for_next_step.append("observable_anchor")

    if not pedagogical_need_known:
        missing_for_next_step.append("pedagogical_need")

    return {
        "has_observable_anchor": has_observable,
        "has_current_observable_anchor": has_current_observable,
        "has_case_observable_anchor": has_case_observable,
        "has_context_signal": bool(context_candidates),
        "has_interpretation_label": has_label,
        "pedagogical_need_known": pedagogical_need_known,
        "context_known": bool(context),
        "age_known": bool(age),
        "needs_observation": needs_observation,
        "confidence": confidence,
        "overall_confidence": calibrated_confidence,
        "specificity": specificity,
        "missing_for_next_step": missing_for_next_step,
    }


def _run_pipeline_core(req: APURequest, kb_context: str, precomputed_signals=None) -> APUPipelineResult:
    message = req.message or ""

    intent = detect_intent(message)

    signals = precomputed_signals if precomputed_signals is not None else extract_signals(message)
    blocks = infer_blocks(signals)
    loaded_blocks = load_targeted_blocks(blocks)

    profiles = infer_profiles(signals, blocks)
    loaded_profiles = load_targeted_profiles(profiles)

    # preliminary input quality before zone scoring
    preliminary_validation = {"flags": []}
    input_quality = build_input_quality(
        intent,
        signals,
        preliminary_validation,
        message,
        case_state=req.state.get("case_state"),
    )

    zones = infer_zones(
        signals,
        blocks,
        profiles,
        validation=preliminary_validation,
        input_quality=input_quality,
    )

    interventions = select_interventions(blocks, profiles, zones, signals)
    didactic_filter = apply_didactic_filter(
        interventions,
        {
            "blocks": blocks,
            "profiles": profiles,
            "zones": zones,
            "state": req.state,
        }
    )
    loaded_didactic = load_targeted_didactic(didactic_filter)

    validation = validate_pipeline(signals, blocks, profiles, zones)

    preliminary_need_known = (
        intent in ["FAST_REQUEST", "FULL_REQUEST"]
        or detect_pedagogical_need(message)
        or bool(((signals or [{}])[0]).get("pedagogical_need", []))
    )
    validation = apply_case_memory_to_validation(
        validation,
        case_state=req.state.get("case_state"),
        pedagogical_need_known=preliminary_need_known,
    )

    loaded_validation_rules = load_targeted_validation_rules(validation)

    block_registry = registry_summary()
    profile_registry = profile_registry_summary()
    inference_registry = inference_registry_summary()
    inference_rules = load_targeted_inference_rules(intent, validation)

    input_quality = build_input_quality(
        intent,
        signals,
        validation,
        message,
        case_state=req.state.get("case_state"),
    )

    # re-score zones after validation dampening
    zones = infer_zones(
        signals,
        blocks,
        profiles,
        validation=validation,
        input_quality=input_quality,
    )

    meta_signals = signals
    case_memory_inference = {
        "signals": [],
        "blocks": [],
        "profiles": [],
        "zones": [],
        "interventions": [],
    }

    if (
        input_quality.get("has_case_observable_anchor")
        and not input_quality.get("has_current_observable_anchor")
    ):
        case_memory_inference = hydrate_inference_from_case_state(
            req.state.get("case_state"),
            validation=validation,
            input_quality=input_quality,
        )

        if case_memory_inference.get("signals"):
            meta_signals = signals + case_memory_inference["signals"]

        if case_memory_inference.get("blocks"):
            blocks = case_memory_inference["blocks"]

        if case_memory_inference.get("profiles"):
            profiles = case_memory_inference["profiles"]

        if case_memory_inference.get("zones"):
            zones = case_memory_inference["zones"]

        if case_memory_inference.get("interventions"):
            interventions = case_memory_inference["interventions"]

    output_mode = select_output_mode(intent, validation, input_quality)
    targeted_output = load_targeted_output(output_mode)
    output_context = format_output_for_prompt(targeted_output)

    evidence = build_evidence(
        signals=meta_signals,
        blocks=blocks,
        profiles=profiles,
        zones=zones,
        validation=validation,
    )
    input_quality["evidence"] = evidence

    meta = APUPipelineMeta(
        intent=intent,
        signals=meta_signals,
        input_quality=input_quality,
        blocks=blocks,
        profiles=profiles,
        zones=zones,
        interventions=interventions,
        didactic_filter=didactic_filter,
        validation=validation,
        output_mode=output_mode,
        confidence=input_quality["confidence"],
    )

    notepad_proposal = build_notepad_update_proposal(meta)
    case_state = apply_notepad_proposal(req.state.get("case_state"), notepad_proposal)
    meta.input_quality["notepad"] = {
        "proposal": notepad_proposal,
        "case_state": case_state,
    }

    meta.input_quality["semantic_extractor"] = {
        "enabled": ENABLE_LLM_SEMANTIC_EXTRACTION,
        "status": "wrapper_ready_not_invoked_sync_pipeline",
    }

    meta.input_quality["block_registry"] = {
        "count": block_registry["count"],
        "by_family": block_registry["by_family"],
    }

    meta.input_quality["profile_registry"] = {
        "count": profile_registry["count"],
        "codes": profile_registry["codes"],
    }

    meta.input_quality["loaded_blocks"] = {
        "selected_codes": loaded_blocks["selected_codes"],
        "loaded": [
            {
                "code": r["code"],
                "filename": r["filename"],
                "chars": r["chars"],
            }
            for r in loaded_blocks["loaded"]
        ],
        "missing": loaded_blocks["missing"],
    }

    meta.input_quality["inference_registry"] = {
        "count": inference_registry["count"],
        "codes": inference_registry["codes"],
    }

    meta.input_quality["loaded_inference_rules"] = {
        "selected_codes": inference_rules["selected_codes"],
        "loaded": [
            {
                "code": r["code"],
                "filename": r["filename"],
                "chars": r["chars"],
            }
            for r in inference_rules["loaded"]
        ],
        "missing": inference_rules["missing"],
    }

    meta.input_quality["loaded_profiles"] = {
        "selected_codes": loaded_profiles["selected_codes"],
        "loaded": [
            {
                "code": r["code"],
                "filename": r["filename"],
                "chars": r["chars"],
            }
            for r in loaded_profiles["loaded"]
        ],
        "missing": loaded_profiles["missing"],
    }

    meta.input_quality["loaded_validation_rules"] = {
        "selected_codes": loaded_validation_rules["selected_codes"],
        "loaded": [
            {
                "code": r["code"],
                "filename": r["filename"],
                "chars": r["chars"],
            }
            for r in loaded_validation_rules["loaded"]
        ],
        "missing": loaded_validation_rules["missing"],
    }

    meta.input_quality["loaded_didactic"] = {
        "selected_codes": loaded_didactic["selected_codes"],
        "loaded": [
            {
                "code": r["code"],
                "filename": r["filename"],
                "chars": r["chars"],
            }
            for r in loaded_didactic["loaded"]
        ],
        "missing": loaded_didactic["missing"],
    }

    meta.input_quality["loaded_output"] = {
        "selected_codes": targeted_output["selected_codes"],
        "loaded": [
            {
                "code": x["code"],
                "filename": x["filename"],
                "chars": x["chars"],
            }
            for x in targeted_output["loaded"]
        ],
        "missing": targeted_output["missing"],
    }
    
    case_state_for_context = req.state.get("case_state") or {}
    active_case_state = meta.input_quality.get("notepad", {}).get("case_state") or case_state_for_context

    case_state_context = json.dumps({
        "case_id": active_case_state.get("case_id"),
        "case_summary": active_case_state.get("case_summary"),
        "observable_anchor": ((active_case_state.get("case_info") or {}).get("observable_anchor") or [])[-6:],
        "uncertain_observations": active_case_state.get("uncertain_observations", [])[-6:],
        "environmental_triggers": active_case_state.get("environmental_triggers", [])[-6:],
        "effective_supports": active_case_state.get("effective_supports", [])[-6:],
        "ineffective_supports": active_case_state.get("ineffective_supports", [])[-6:],
        "uncertain_hypotheses": active_case_state.get("uncertain_hypotheses", [])[-6:],
        "contradictions": active_case_state.get("contradictions", [])[-6:],
        "open_questions": active_case_state.get("open_questions", [])[-6:],
        "timeline_markers": active_case_state.get("timeline_markers", [])[-6:],
        "safety_notes": active_case_state.get("safety_notes", [])[-6:],
        "next_steps": active_case_state.get("next_steps", [])[-6:],
    }, ensure_ascii=False, indent=2)

    system_context = f"""
APU CASE STATE / NOTEPAD:
{case_state_context}

PRAVIDLO NAVAZOVÁNÍ:
- Při další odpovědi ber CASE STATE jako pracovní paměť případu.
- Nenavrhuj, že informace chybí, pokud už je uvedena v CASE STATE.
- Novou zprávu vyhodnoť ve vztahu k dosavadnímu případu.
- Pokud nová zpráva odporuje CASE STATE, označ to jako rozpor nebo upřesnění, ne jako nový izolovaný případ.
- Nezobrazuj interní kódy uživateli.

APU PIPELINE META:
intent: {intent}
output_mode: {output_mode}
input_quality: {input_quality}
validation: {validation}

TARGETED INFERENCE RULES:
{format_inference_rules_for_prompt(inference_rules)}

TARGETED BLOCK RULES:
{format_blocks_for_prompt(loaded_blocks)}

TARGETED PROFILE RULES:
{format_profiles_for_prompt(loaded_profiles)}

TARGETED VALIDATION RULES:
{format_validation_rules_for_prompt(loaded_validation_rules)}

TARGETED DIDACTIC RULES:
{format_didactic_for_prompt(loaded_didactic)}

TARGETED OUTPUT RULES:
{format_output_for_prompt(targeted_output)}

KB CONTEXT:
{kb_context}
"""

    return APUPipelineResult(
        system_context=system_context,
        user_message=message,
        meta=meta,
    )

def run_pipeline(req: APURequest, kb_context: str) -> APUPipelineResult:
    """
    Backward-compatible sync pipeline.
    Does not invoke async LLM fallback.
    Used by tests and deterministic shell checks.
    """
    return _run_pipeline_core(req, kb_context)


async def run_pipeline_async(req: APURequest, kb_context: str, llm_extraction: bool | None = None) -> APUPipelineResult:
    """
    Async pipeline with optional LLM semantic fallback.

    Rule layer remains primary.
    LLM fallback is append-only and low-confidence.
    """
    message = req.message or ""

    signals = extract_signals(message)
    semantic_enabled = ENABLE_LLM_SEMANTIC_EXTRACTION if llm_extraction is None else bool(llm_extraction)

    semantic_audit = {
        "enabled": semantic_enabled,
        "invoked": False,
        "status": "disabled_or_not_needed",
        "error": None,
    }

    if semantic_enabled and (
        should_run_semantic_fallback(signals)
        or llm_extraction is True
    ):
        semantic_audit["invoked"] = True
        semantic = await run_semantic_extractor(message)
        semantic_signal = semantic_result_to_signal(message, semantic)
        semantic_audit["error"] = semantic.get("_error")
        semantic_audit["status"] = "ok" if not semantic.get("_error") else "error"

        # Append-only: deterministic signal stays first.
        signals = signals + [semantic_signal]

    result = _run_pipeline_core(req, kb_context, precomputed_signals=signals)
    result.meta.input_quality["semantic_extractor"] = semantic_audit
    return result


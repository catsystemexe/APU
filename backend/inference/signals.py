import re
from typing import Dict, List

from backend.rag.signal_registry import (
    match_observables,
    match_contexts,
    match_labels,
    match_trend_intensity,
    match_needs,
)

CZ_TRANS = str.maketrans({
    "ě": "e", "š": "s", "č": "c", "ř": "r", "ž": "z",
    "ý": "y", "á": "a", "í": "i", "é": "e", "ú": "u", "ů": "u",
    "ť": "t", "ď": "d", "ň": "n",
})


SLANG_MAP = {
    "nedava bacha": {
        "meaning": "nedava pozor",
        "observable": "nedává pozor / neudrží pozornost",
    },
    "nedava majzla": {
        "meaning": "nedava pozor",
        "observable": "nedává pozor / neudrží pozornost",
    },
    "dela bordel": {
        "meaning": "vyrusuje / narusuje vyuku",
        "observable": "vyrušuje / narušuje průběh",
    },
    "robi bordel": {
        "meaning": "vyrusuje / narusuje vyuku",
        "observable": "vyrušuje / narušuje průběh",
    },
    "jede si svoje": {
        "meaning": "ignoruje instrukce",
        "observable": "nereaguje na instrukce",
    },
    "vypne": {
        "meaning": "prestane reagovat",
        "observable": "nereaguje na instrukce",
    },
    "furt mimo": {
        "meaning": "opakovana odpojena pozornost",
        "observable": None,
    },
    "je mimo": {
        "meaning": "neurcity stav / odpojena pozornost",
        "observable": None,
    },
    "zasekne se": {
        "meaning": "nepokračuje / zamrzne",
        "observable": "zamrzne / nepokračuje",
    },
    "sekne se": {
        "meaning": "nepokračuje / zamrzne",
        "observable": "zamrzne / nepokračuje",
    },
    "meltdown": {
        "meaning": "silna dysregulace",
        "observable": None,
    },
}


LABEL_PATTERNS = [
    (r"\bliny\b|\blina\b|\blenoch\b", "líný / lenivý"),
    (r"\bzlob[ií]\b|\bzlobivy\b|\bzlobiva\b", "dítě zlobí"),
    (r"\bnic ho nezajima\b|\bnic ho nezajímá\b", "nic ho nezajímá"),
    (r"\bnedokaze se soustredit\b|\bnedokáže se soustředit\b", "nedokáže se soustředit"),
    (r"\bproblemovy\b|\bproblemova\b", "problémový"),
    (r"\bdivny\b|\bdivna\b", "divný / neurčitý label"),
]


OBSERVABLE_PATTERNS = [
    (r"\bnedava pozor\b|\bneudrzi pozornost\b|\bkouka jinam\b", "nedává pozor / neudrží pozornost"),
    (r"\bvyrusuje\b|\bnarusuje\b|\bkrici\b|\bvykrikuje\b|\bvykřikuje\b", "vyrušuje / narušuje průběh"),
    (r"\bnepracuje\b|\bnechce pracovat\b|\bodmita pracovat\b|\bodmítá pracovat\b", "odmítá práci / nezapojuje se"),
    (r"\bzakryva usi\b|\bzakrývá uši\b|\bzakryva si usi\b|\bzakrývá si uši\b", "zakrývá si uši při hluku / sluchová citlivost"),
    (r"\bodchazi stranou\b|\bodchází stranou\b", "odchází stranou při zátěži"),
]


AGE_PATTERNS = [
    (r"\b(\d{1,2})\s*let\b", "věk dítěte"),
    (r"\b(\d{1,2})\s*roku\b", "věk dítěte"),
    (r"\bpetilety\b|\bpetileta\b", "5 let"),
    (r"\bpredskolak\b|\bpredskolni\b", "předškolní věk"),
]

CONTEXT_PATTERNS = [
    (r"\branni kruh\b|\brannim kruhu\b", "ranní kruh"),
    (r"\bpri kruhu\b|\bv kruhu\b", "skupinový kruh"),
    (r"\bpri uklidu\b|\buklid\b", "úklid / ukončení činnosti"),
    (r"\bpri prechodu\b|\bprechod\b", "přechod mezi činnostmi"),
    (r"\bsatna\b|\bv satne\b", "šatna / předávání"),
    (r"\bobed\b|\bu obeda\b", "jídlo / oběd"),
    (r"\bodpocinek\b|\bspanek\b", "odpočinek"),
    (r"\bve skolce\b|\bve tride\b", "prostředí školky / třídy"),
    (r"\bhluk\b|\bhluku\b|\bhlasity\b|\bhlasit[eé]\b", "hlukové zatížení"),
    (r"\bu jedne ucitelky\b|\bu jedné učitelky\b|\bjedne ucitelky\b|\bjedné učitelky\b", "obtíž se objevuje hlavně u jedné učitelky"),
]

NEED_PATTERNS = [
    # generic request markers — useful for routing, filtered out of notepad if no concrete need follows
    (r"\bpotrebuju\b|\bpotrebuji\b|\bchci\b|\bnev[ií]m si rady\b", "uživatel žádá pomoc nebo změnu"),
    (r"\bco mam delat\b|\bco mám dělat\b", "uživatel žádá postup"),
    (r"\bjak to resit\b|\bjak to řešit\b", "uživatel žádá řešení"),

    # concrete pedagogical need classes
    (r"\bzklidnit\b|\bzklidneni\b|\bzklidnění\b|\buklidnit\b", "aktuálně zklidnit situaci"),
    (r"\budrzet skupinu\b|\budržet skupinu\b|\budrzet tridu\b|\budržet třídu\b", "udržet skupinu v klidu / činnosti"),
    (r"\bnastavit hranice\b|\bhranice\b", "nastavit hranice"),
    (r"\bdlouhodoby plan\b|\bdlouhodobý plán\b|\bdlouhodobe reseni\b|\bdlouhodobé řešení\b", "nastavit dlouhodobý plán podpory"),
    (r"\bkomunikovat s rodici\b|\bkomunikace s rodici\b|\bkomunikovat s rodiči\b|\bkomunikace s rodiči\b", "připravit komunikaci s rodiči"),
    (r"\bzjistit pricinu\b|\bzjistit příčinu\b|\bporozumet pricine\b|\bporozumět příčině\b", "porozumět možné příčině projevu"),
]


def normalize_text(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.translate(CZ_TRANS)
    t = re.sub(r"\s+", " ", t)
    return t


def extract_from_slang(text_norm: str):
    slang_hits = []
    observable_from_slang = []

    for slang, data in SLANG_MAP.items():
        s = normalize_text(slang)
        if s in text_norm:
            slang_hits.append({
                "raw": slang,
                "normalized_meaning": data["meaning"],
                "type": "slang_or_jargon",
                "confidence": "MEDIUM",
            })

            if data.get("observable"):
                observable_from_slang.append({
                    "type": "observable_candidate",
                    "meaning": data["observable"],
                    "source": "slang_map",
                    "confidence": "MEDIUM",
                })

    return slang_hits, observable_from_slang


def match_patterns(text_norm: str, patterns: list, signal_type: str):
    hits = []
    for pattern, meaning in patterns:
        if re.search(pattern, text_norm):
            hits.append({
                "type": signal_type,
                "meaning": meaning,
                "pattern": pattern,
                "confidence": "MEDIUM",
            })
    return hits



def extract_age(text_norm: str):
    hits = []
    for pattern, meaning in AGE_PATTERNS:
        m = re.search(pattern, text_norm)
        if m:
            value = m.group(1) if m.groups() else meaning
            hits.append({
                "type": "age_signal",
                "meaning": meaning,
                "value": value,
                "pattern": pattern,
                "confidence": "MEDIUM",
            })
    return hits


def extract_context(text_norm: str):
    return match_patterns(text_norm, CONTEXT_PATTERNS, "context_signal")


def extract_pedagogical_need(text_norm: str):
    return match_patterns(text_norm, NEED_PATTERNS, "pedagogical_need_signal")



def compute_specificity_score(
    observable_candidates: list,
    age_signals: list,
    context_signals: list,
    pedagogical_need_signals: list,
) -> dict:
    score = 0
    reasons = []

    obs_count = len(observable_candidates or [])
    if obs_count >= 1:
        score += 2
        reasons.append("observable_present")
    if obs_count >= 2:
        score += 1
        reasons.append("multiple_observables")

    if context_signals:
        score += 2
        reasons.append("context_present")

    if pedagogical_need_signals:
        score += 1
        reasons.append("pedagogical_need_present")

    if age_signals:
        score += 1
        reasons.append("age_present")

    score = min(score, 5)

    if score >= 5:
        level = "HIGH"
    elif score >= 3:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "reasons": reasons,
    }


def extract_signals(message: str) -> list[dict]:
    raw = (message or "").strip()
    text_norm = normalize_text(raw)

    slang_hits, slang_observables = extract_from_slang(text_norm)
    legacy_labels = match_patterns(text_norm, LABEL_PATTERNS, "interpretation_label")
    for item in legacy_labels:
        item["label"] = item.get("meaning")
        item["label_type"] = "legacy_interpretation_label"
        item["risk"] = "MEDIUM"

    registry_labels = []
    for hit in match_labels(raw):
        registry_labels.append({
            "type": "interpretation_label",
            "id": hit.get("id"),
            "meaning": hit.get("label"),
            "label": hit.get("label"),
            "label_type": hit.get("label_type"),
            "risk": hit.get("risk"),
            "replacement_question": hit.get("replacement_question"),
            "do_not_infer": hit.get("do_not_infer", []),
            "matched_patterns": hit.get("matched_patterns", []),
            "matched_stems": hit.get("matched_stems", []),
            "source": "V9_label_guard",
            "confidence": "HIGH" if hit.get("risk") == "HIGH" else "MEDIUM",
        })

    labels = registry_labels + legacy_labels
    direct_observables = match_patterns(text_norm, OBSERVABLE_PATTERNS, "observable_candidate")

    for obs in direct_observables:
        meaning = obs.get("meaning") or ""

        if "vyrušuje" in meaning or "narušuje" in meaning:
            obs["candidate_blocks"] = ["B", "E", "A"]
            obs["candidate_zones"] = ["Z2"]

        elif "odmítá práci" in meaning:
            obs["candidate_blocks"] = ["A", "C"]
            obs["candidate_zones"] = ["Z1", "Z4"]

        elif (
            "nedává pozor" in meaning
            or "nedava pozor" in meaning
            or "kouká jinam" in meaning
            or "kouka jinam" in meaning
        ):
            obs["candidate_blocks"] = ["C"]
            obs["candidate_zones"] = ["Z1"]
    age_signals = extract_age(text_norm)
    context_signals = extract_context(text_norm)
    pedagogical_need_signals = extract_pedagogical_need(text_norm)
    for hit in match_needs(raw):
        pedagogical_need_signals.append({
            "type": "pedagogical_need_signal",
            "id": hit.get("id"),
            "meaning": hit.get("notepad_label") or hit.get("label"),
            "label": hit.get("label"),
            "source": "S2_needs",
            "matched_patterns": hit.get("matched_patterns", []),
            "confidence": "HIGH",
        })

    
    registry_hits = []
    for hit in match_observables(raw):
        observable = hit.get("observable")

        # False-positive guard / label records must never become observable candidates.
        if not observable:
            continue

        registry_hits.append({
            "type": "observable_candidate",
            "id": hit.get("id"),
            "meaning": observable,
            "source": "S1_observable_map",
            "confidence": hit.get("confidence", "MEDIUM"),
            "matched_patterns": hit.get("matched_patterns", []),
            "candidate_blocks": hit.get("candidate_blocks", []),
            "candidate_zones": hit.get("candidate_zones", []),
            "disambiguation_questions": hit.get("disambiguation_questions", []),
        })

    observable_candidates = registry_hits + direct_observables + slang_observables

    trend_intensity_signals = []
    for hit in match_trend_intensity(raw):
        trend_intensity_signals.append({
            "type": "trend_intensity_signal",
            "id": hit.get("id"),
            "category": hit.get("category"),
            "signal": hit.get("signal") or hit.get("meaning") or hit.get("label"),
            "effect": hit.get("effect") or {
                "validation_flags": hit.get("validation_flags", []),
                "confidence_modifier": hit.get("confidence_effect"),
            },
            "risk": hit.get("risk") or hit.get("false_positive_risk"),
            "replacement_question": hit.get("replacement_question"),
            "matched_patterns": hit.get("matched_patterns", []),
            "matched_stems": hit.get("matched_stems", []),
            "source": "S4_trend_intensity_map",
        })

    context_candidates = []
    for hit in match_contexts(raw):
        context_candidates.append({
            "type": "context_candidate",
            "id": hit.get("id"),
            "meaning": hit.get("notepad") or hit.get("meaning") or hit.get("observable") or hit.get("label"),
            "source": "S3_context_map",
            "priority": hit.get("priority", "MEDIUM"),
            "matched_patterns": hit.get("matched_patterns", []),
            "candidate_contexts": hit.get("candidate_contexts", []),
            "recommended_focus": hit.get("recommended_focus", []),
        })

    specificity = compute_specificity_score(
        observable_candidates,
        age_signals,
        context_signals,
        pedagogical_need_signals,
    )

    flags = []

    for ti in trend_intensity_signals:
        effect = ti.get("effect") or {}
        for f in effect.get("validation_flags") or []:
            if f not in flags:
                flags.append(f)

    if labels:
        flags.append("HAS_INTERPRETATION_LABEL")

    if labels and not observable_candidates:
        flags.append("LABEL_WITHOUT_OBSERVATION")

    if not observable_candidates and not context_candidates:
        flags.append("MISSING_OBSERVABLE_BEHAVIOR")

    if context_candidates and not observable_candidates:
        flags.append("CONTEXT_WITHOUT_CHILD_OBSERVABLE")

    if slang_hits:
        flags.append("SLANG_OR_JARGON_DETECTED")

    confidence = "MEDIUM" if observable_candidates else "LOW"

    return [{
        "type": "signal_extraction_v1",
        "raw_text": raw,
        "normalized_text": text_norm,
        "observable_candidates": observable_candidates,
        "context_candidates": context_candidates,
        "context": context_signals,
        "age": age_signals,
        "pedagogical_need": pedagogical_need_signals,
        "trend_intensity": trend_intensity_signals,
        "interpretation_labels": labels,
        "slang_or_jargon": slang_hits,
        "flags": flags,
        "confidence": confidence,
        "specificity": specificity,
    }]

import unicodedata

def _list(x):
    return x if isinstance(x, list) else []


def _first_text(evidence_item):
    return evidence_item.get("text") or ""


def _incomplete_observable_fragment(text: str) -> str:
    t = (text or "").strip().lower()
    t = t.strip(" .,!?:;„“\"'()[]{}")
    if ("nechce do školky" in t or "nechce do skolky" in t) and ("pláče" in t or "place" in t):
        return "nechce do školky a pláče"

    fragments = {
        "pláče": "pláče",
        "place": "pláče",
        "zapomíná": "zapomíná",
        "zapomina": "zapomíná",
        "běhá": "běhá",
        "beha": "běhá",
        "zamlklé": "je zamlklé",
        "zamlkle": "je zamlklé",
        "mlčí": "mlčí",
        "mlci": "mlčí",
    }
    return fragments.get(t, "")



def _teacher_observable_phrase(item):
    observable_id = item.get("id")

    preferred = {
        "OBS_TASK_002": "dítě nezvládá tempo s ostatními",
        "OBS_ACT_005": "dítě sahá na věci kolem sebe během činnosti",
        "OBS_ACT_004": "dítě odbíhá od stolu nebo od činnosti",
        "OBS_SAFE_002": "dítě hází sešitem nebo jiným předmětem",
        "OBS_ACT_002": "dítě je hlučné, vykřikuje a ruší ostatní",
        "OBS_TASK_001": "dítě dokončí úkol jen s blízkou podporou dospělého",
    }

    if observable_id in preferred:
        return preferred[observable_id]

    meaning_map = {
        "nedává pozor / neudrží pozornost": "dítě nedává pozor / kouká jinam",
        "vyrušuje / narušuje průběh": "dítě vyrušuje / narušuje průběh",
        "odchází od činnosti nebo pracovního místa": "dítě odchází od činnosti",
        "dokončí úkol pouze s blízkou podporou dospělého": "dítě dokončí úkol jen s podporou dospělého",
    }

    meaning = (item.get("meaning") or "").strip()
    if meaning in meaning_map:
        return meaning_map[meaning]

    matched = item.get("matched_patterns") or []
    if matched:
        return matched[0]

    raw = (item.get("text") or "").strip()
    if raw and len(raw.split()) <= 4:
        return raw

    if matched:
        return matched[0]

    return ""



def _dedupe_observable_items(items):
    items = items if isinstance(items, list) else []

    has_evidence_backed = any(bool(x.get("evidence_refs")) for x in items)

    filtered = []
    for x in items:
        raw = ((x.get("text") or "") + " " + (x.get("teacher_phrase") or "")).lower()
        weak_generic = (
            not x.get("evidence_refs")
            and (
                "vyrušuje" in raw
                or "vyrušuje" in raw
                or "narusuje prubeh" in raw
                or "narušuje průběh" in raw
            )
        )
        if has_evidence_backed and weak_generic:
            continue
        filtered.append(x)

    def norm(x):
        import unicodedata
        text = (x.get("teacher_phrase") or x.get("text") or "").strip().lower()
        text = "".join(
            c for c in unicodedata.normalize("NFKD", text)
            if not unicodedata.combining(c)
        )
        text = (
            text.replace("dite", "")
                .replace("/", " ")
                .replace("  ", " ")
                .strip()
        )
        return text

    preferred = {}
    order = []

    for item in filtered:
        key = norm(item)
        if not key:
            continue

        score = 0
        if item.get("evidence_refs"):
            score += 10
        score += len(item.get("teacher_phrase") or "")

        if key not in preferred:
            preferred[key] = (score, item)
            order.append(key)
        else:
            old_score, _ = preferred[key]
            if score > old_score:
                preferred[key] = (score, item)

    return [preferred[k][1] for k in order[:3]]



def _observable_notepad_text(item, meaning):
    """
    User-facing notepad text.
    Keep it short and pedagogically readable.
    Store inference/generalization separately in observable_meaning.
    """
    phrase = _teacher_observable_phrase(item)
    return phrase or meaning


def _context_notepad_text(signal, item):
    norm = item.get("normalized_text") or ""
    signal_norm = (signal or "").strip().lower()

    context_map = {
        "vazba na skupinovou statickou aktivitu": "při společné klidové činnosti ve skupině",
        "vazba na jidlo nebo stolovani": "v souvislosti s jídlem / stolováním",
        "vazba na jídlo nebo stolování": "v souvislosti s jídlem / stolováním",
        "ranní kruh": "při ranním kruhu",
        "skupinový kruh": "při skupinové práci v kruhu",
    }

    if signal_norm in context_map:
        return context_map[signal_norm]

    if signal == "rozdil mezi domovem a MS":
        if "skolce" in norm and "doma" in norm:
            return "Rozdíl mezi MŠ a domovem – projev je popisován ve školce, doma rodiče obtíže nepozorují."
        return "Rozdíl mezi MŠ a domovem."

    return signal


def _has_block(pipeline_meta, code):
    return any(b.get("code") == code for b in (pipeline_meta.blocks or []))


def _has_zone(pipeline_meta, code):
    return any(z.get("code") == code for z in (pipeline_meta.zones or []))


def _add_case_understanding_and_gaps(proposal, pipeline_meta):
    """
    User-facing translation of internal mapping.
    No internal codes in text.
    """

    iq = pipeline_meta.input_quality or {}
    need_known = bool(iq.get("pedagogical_need_known"))

    hypotheses = []
    missing = []
    questions = []

    if not need_known:
        missing.append({
            "text": "Chybí potřeba učitele: zatím není jasné, zda jde o okamžité zklidnění, dlouhodobý plán, porozumění příčině, práci se skupinou nebo komunikaci s rodiči.",
            "priority": "high",
        })

    if _has_block(pipeline_meta, "C"):
        hypotheses.append({
            "text": "Obtíž může souviset s udržením pozornosti, délkou činnosti nebo porozuměním zadání.",
            "status": "hypothesis",
            "source": "plain_language_mapping",
        })
        proposal["working_hypotheses"].append({
            "id": "H1",
            "priority": 1,
            "title": "Udržení pozornosti / nárok činnosti",
            "summary": "Obtíž může souviset s délkou činnosti, nejasným zadáním nebo tím, že úkol není rozdělený na zvládnutelné části.",
            "status": "active",
            "source": "plain_language_mapping",
        })
        missing.append({
            "text": "Není jasné, při jaké konkrétní činnosti pozornost klesá a jak dlouho dítě vydrží.",
            "priority": "medium",
        })
        questions.append({
            "question": "Při jaké činnosti se to děje nejčastěji a jak dlouho dítě pozornost obvykle udrží?",
            "priority": "high",
        })

    if _has_block(pipeline_meta, "E") or _has_zone(pipeline_meta, "Z2"):
        hypotheses.append({
            "text": "Může jít také o regulační přebuzení nebo potřebu krátce vybít aktivaci bezpečným způsobem.",
            "status": "hypothesis",
            "source": "plain_language_mapping",
        })
        proposal["working_hypotheses"].append({
            "id": "H2",
            "priority": 2,
            "title": "Regulační přebuzení / aktivace",
            "summary": "Projev může souviset s tím, že dítě potřebuje krátký bezpečný regulační krok před návratem k činnosti.",
            "status": "active",
            "source": "plain_language_mapping",
        })
        missing.append({
            "text": "Není jasné, zda dítě potřebuje spíše zklidnění, pohybový reset nebo jasnější strukturu.",
            "priority": "medium",
        })
        questions.append({
            "question": "Pomáhá mu spíš krátký řízený pohyb, nebo klidné zjednodušení pokynu?",
            "priority": "medium",
        })

    if _has_block(pipeline_meta, "B"):
        hypotheses.append({
            "text": "Vykřikování nebo vstupování do řeči může souviset i se sociální situací ve skupině.",
            "status": "hypothesis",
            "source": "plain_language_mapping",
        })
        proposal["working_hypotheses"].append({
            "id": "H3",
            "priority": 3,
            "title": "Skupinová / sociální dynamika",
            "summary": "Vykřikování nebo rušení může být výraznější při práci celé skupiny než v individuální situaci.",
            "status": "active",
            "source": "plain_language_mapping",
        })
        questions.append({
            "question": "Děje se to hlavně při práci celé skupiny, nebo i při individuální činnosti?",
            "priority": "medium",
        })

    if _has_zone(pipeline_meta, "Z1"):
        hypotheses.append({
            "text": "Část obtíží může souviset s nárokem činnosti: úkol může být příliš dlouhý, málo jasný nebo málo ukončený.",
            "status": "hypothesis",
            "source": "plain_language_mapping",
        })

    interventions = pipeline_meta.interventions or []

    if not need_known:
        for item in interventions[:3]:
            action = item.get("action")
            if action:
                proposal["general_support_options"].append({
                    "text": action,
                    "type": "general_option",
                    "priority": "medium",
                    "note": "Obecná možnost podpory při tomto typu projevu; konkrétní postup závisí na cíli učitele.",
                })

    def infer_linked_hypothesis(action: str):
        a = (action or "").lower()

        if any(x in a for x in [
            "zkraťte činnost",
            "kratší úsek",
            "označte konec úkolu",
            "jednou krátkou větou",
            "pokyn"
        ]):
            return "H1"

        if any(x in a for x in [
            "pohybový úkol",
            "řízený pohyb",
            "regulovaný pohyb",
            "vráťte k jednomu kroku"
        ]):
            return "H2"

        if any(x in a for x in [
            "role v kruhu",
            "vrátit dítě do skupiny",
            "skupiny",
            "podržet obrázek",
            "podat pomůcku"
        ]):
            return "H3"

        return "H1"

    for item in interventions[:3]:
        if not need_known:
            continue

        action = item.get("action")
        if action:
            linked = infer_linked_hypothesis(action)

            step = {
                "text": action,
                "type": "test_hypothesis",
                "priority": "medium",
                "linked_hypothesis": linked,
                "observe": "Sledujte, zda se sníží rušení, zkrátí návrat do činnosti nebo dítě potřebuje méně opakovaných korekcí.",
                "success_signal": "rychlejší návrat do činnosti / méně korekcí",
                "failure_signal": "bez změny nebo další eskalace projevu",
            }

            proposal["case_gaps"]["recommended_next_step"].append({
                "text": action,
                "type": "working_step",
                "priority": "medium",
            })

            proposal["what_to_try"].append(step)

    if hypotheses:
        proposal["case_understanding"]["plain_language_hypotheses"].extend(hypotheses[:4])
        proposal["case_understanding"]["working_interpretation"] = (
            "Zatím jde o pracovní porozumění situaci: projev je konkrétně popsaný, "
            "ale přesnější příčinu je potřeba ověřit podle kontextu, spouštěče a reakce na podporu."
        )

    proposal["case_gaps"]["missing_information"].extend(missing[:4])
    proposal["case_gaps"]["clarifying_questions"].extend(questions[:4])

    proposal["certainty_and_gaps"]["missing_for_disambiguation"].extend(missing[:4])



def _renumber_working_hypotheses(proposal):
    hypotheses = proposal.get("working_hypotheses") or []
    if not hypotheses:
        return proposal

    hypotheses.sort(key=lambda x: int(x.get("priority") or 999))

    remap = {}
    for idx, h in enumerate(hypotheses, start=1):
        old_id = h.get("id")
        new_id = f"H{idx}"
        if old_id:
            remap[old_id] = new_id
        h["id"] = new_id
        h["priority"] = idx

    for section in ["what_to_try", "general_support_options"]:
        for item in proposal.get(section) or []:
            old = item.get("linked_hypothesis")
            if old in remap:
                item["linked_hypothesis"] = remap[old]

    return proposal


def build_notepad_update_proposal(pipeline_meta):
    """
    Convert pipeline meta + evidence into human-readable notepad update proposal.

    This is not persistent state yet.
    It proposes safe, user-facing case notes.
    """

    iq = pipeline_meta.input_quality or {}
    evidence = iq.get("evidence") or {}
    evidence_items = _list(evidence.get("items"))
    validation = pipeline_meta.validation or {}
    output_mode = pipeline_meta.output_mode

    proposal = {
        "case_summary": "",
        "uncertain_observations": [],
        "teacher_interpretation_labels": [],
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
            "teacher_interpretation_labels": [],
            "pedagogical_need": [],
            "context": [],
            "parent_school_difference": [],
            "trend_intensity": [],
            "uncertain_observations": [],
        },

        "working_hypotheses": [],

        "certainty_and_gaps": {
            "most_supported": [],
            "missing_for_disambiguation": [],
        },

        "what_to_try": [],
        "general_support_options": [],
    }

    flags = set(validation.get("flags") or [])

    if "CONTRADICTION_HOME_SCHOOL_MISMATCH" in flags:
        proposal["case_info"]["parent_school_difference"].append({
            "text": "Rozdíl mezi MŠ a domovem – ve školce je obtíž popisována, doma ji rodiče nepozorují.",
            "status": "reported",
            "source": "validation_layer",
        })

    # Pedagogical need can be captured even when observable behavior is missing.
    for sig in _list(getattr(pipeline_meta, "signals", []) or []):
        for need in _list(sig.get("pedagogical_need")):
            meaning = (need.get("meaning") or "").strip()

            skip_generic = {
                "uživatel žádá pomoc nebo změnu",
                "uživatel potřebuje řešení situace",
                "potřeba řešit situaci",
            }

            if not meaning or meaning.lower() in skip_generic:
                continue

            item = {
                "text": meaning,
                "status": "reported",
                "source": "user",
            }

            proposal["case_core"]["pedagogical_need"].append(item)
            proposal["case_info"]["pedagogical_need"].append(item)

    # Context from current input should be preserved even in LOW_DATA.
    for sig in _list(getattr(pipeline_meta, "signals", []) or []):
        sig_norm = sig.get("normalized_text") or ""

        for ctx in _list(sig.get("context")):
            meaning = (ctx.get("meaning") or "").strip()

            if (
                meaning == "prostředí školky / třídy"
                and "doma" in sig_norm
            ):
                continue

            if not meaning:
                continue

            item = {
                "text": meaning,
                "status": "reported",
                "source": "user",
            }

            proposal["case_core"]["context"].append(item)
            proposal["case_info"]["context"].append(item)

        for age in _list(sig.get("age")):
            value = age.get("value") or age.get("meaning")
            if value:
                proposal["case_core"]["age"].append({
                    "text": str(value),
                    "status": "reported",
                    "source": "user",
                })

    # Context candidates from evidence layer (S3 matcher)
    for item in evidence_items:
        if item.get("type") != "context_candidate":
            continue

        matched_patterns = [
            (x or "").strip().lower()
            for x in (item.get("matched_patterns") or [])
        ]

        weak_only_patterns = {
            "konflikt",
            "konflikty",
        }

        if matched_patterns and set(matched_patterns).issubset(weak_only_patterns):
            continue

        meaning = (
            item.get("meaning")
            or (item.get("candidate_contexts") or [None])[0]
            or ""
        ).strip()

        if not meaning:
            continue

        ctx_item = {
            "text": _context_notepad_text(
                meaning,
                {"normalized_text": item.get("normalized_text") or ""}
            ),
            "status": "reported",
            "source": "signal_registry",
            "evidence_refs": [item.get("id")] if item.get("id") else [],
        }

        proposal["case_core"]["context"].append(ctx_item)
        proposal["case_info"]["context"].append(ctx_item)


    # Trends / context triggers.
    for item in evidence_items:
        if item.get("type") != "trend_intensity":
            continue

        signal = item.get("signal")
        flags_i = set(item.get("validation_flags") or [])

        if not signal:
            continue

        if flags_i & {
            "TRANSITION_TRIGGER",
            "SITUATIONAL_LIMITED",
            "SETTING_DIFFERENCE",
            "ENVIRONMENTAL_INFLUENCE_POSSIBLE",
            "GROUP_STATIC_ACTIVITY",
            "MORNING_TRANSITION",
        }:
            env_item = {
                "text": _context_notepad_text(signal, item),
                "confidence": "working",
                "status": "reported",
                "evidence_refs": [item.get("id")] if item.get("id") else [],
            }
            proposal["environmental_triggers"].append(env_item)
            proposal["case_info"]["context"].append(env_item)

            if flags_i & {"SETTING_DIFFERENCE", "ENVIRONMENTAL_INFLUENCE_POSSIBLE"}:
                proposal["case_info"]["parent_school_difference"].append(env_item)

        if flags_i & {
            "SINGLE_EPISODE",
            "OCCASIONAL_PATTERN",
            "REPEATED_PATTERN",
            "FREQUENCY_HIGH",
            "ESCALATION",
            "RECOVERY_PRESENT",
        }:
            item = {
                "text": signal,
                "status": "reported",
                "time_anchor": "low_frequency_or_single_episode",
            }
            proposal["timeline_markers"].append(item)
            proposal["case_info"]["trend_intensity"].append(item)

    # Labels are noted as uncertain framing, not child fact.
    for item in evidence_items:
        if item.get("type") != "interpretation_label":
            continue

        label_text = (
                item.get("label")
                or item.get("meaning")
                or item.get("text")
                or ""
            ).strip()

        if not label_text:
            continue

        label_item = {
                "text": label_text,
                "status": "needs_clarification",
                "source": item.get("source") or "signal_registry",
                "valid_as_observable": False,
                "warning": True,
                "replacement_question": item.get("replacement_question") or f"Co přesně dítě dělá nebo říká, když popisujete situaci jako: {label_text}?",
                "evidence_refs": [item.get("id")] if item.get("id") else [],
            }

        proposal["case_info"]["teacher_interpretation_labels"].append(label_item)

        # user-facing audit trace
        proposal["case_info"]["uncertain_observations"].append({
                "text": f"Učitel popisuje situaci jako: {label_text}",
                "status": "reported",
                "source": "interpretation_label",
            })

        replacement_question = label_item.get("replacement_question")
        if replacement_question:
            proposal["open_questions"].append({
                    "question": replacement_question,
                    "priority": "high",
                    "source": "label_clarification",
                    "purpose": "převést interpretační label na konkrétní pozorovatelný projev",
                })


    # Incomplete observable fragment: behavior-like word, but too little context for inference.
    fragment = _incomplete_observable_fragment(getattr(pipeline_meta, "signals", [{}])[0].get("raw_text", ""))
    if fragment:
        frag_item = {
            "text": fragment,
            "status": "needs_context",
            "source": "user",
            "valid_as_observable": False,
            "warning": True,
            "type": "incomplete_observable_fragment",
            "replacement_question": f"Kdy, kde a v jaké situaci dítě {fragment}? Co se děje předtím a potom?",
        }
        proposal["case_info"]["teacher_interpretation_labels"].append(frag_item)
        proposal["case_info"]["uncertain_observations"].append({
            "text": f"Uživatel uvedl neúplný pozorovaný projev: {fragment}",
            "status": "needs_context",
            "source": "incomplete_observable_fragment",
        })
        proposal["open_questions"].append({
            "question": frag_item["replacement_question"],
            "priority": "high",
            "source": "incomplete_observable_fragment",
            "purpose": "doplnit kontext neúplného pozorovaného projevu",
        })

    # LOW DATA: do not create child hypotheses.
    if output_mode == "LOW_DATA" or "MISSING_OBSERVABLE_BEHAVIOR" in flags:
        proposal["uncertain_observations"].append({
            "text": "Uživatel zatím neuvedl konkrétní pozorovatelný projev dítěte.",
            "status": "to_verify",
            "source": "notepad_extractor",
        })

        has_specific_lowdata_question = bool(
            proposal["case_info"].get("teacher_interpretation_labels")
        )

        if not has_specific_lowdata_question:
            proposal["open_questions"].append({
                "question": "Co přesně dítě dělá nebo říká, co je vidět nebo slyšet?",
                "priority": "high",
                "purpose": "získat pozorovatelný projev před pracovní interpretací",
            })

        step = {
            "text": "Doplnit konkrétní popis situace bez hodnotícího labelu.",
            "type": "information_needed",
            "priority": "high",
        }

        proposal["next_steps"].append(step)
        proposal["case_gaps"]["missing_information"].append({
            "text": "Chybí konkrétní pozorovatelný projev dítěte.",
            "priority": "high",
        })

        if not has_specific_lowdata_question:
            proposal["case_gaps"]["clarifying_questions"].append({
                "question": "Co přesně dítě dělá nebo říká, co je vidět nebo slyšet?",
                "priority": "high",
            })

        proposal["case_gaps"]["recommended_next_step"].append(step)
        return proposal

    # Observables.
    for item in evidence_items:
        if item.get("type") != "observable":
            continue

        meaning = item.get("meaning")
        if not meaning:
            continue

        display_text = _observable_notepad_text(item, meaning)

        v3_obs = {
            "text": display_text,
            "status": "reported",
            "source": "user",
            "evidence_refs": [item.get("id")] if item.get("id") else [],
            "candidate_blocks": item.get("candidate_blocks", []),
            "candidate_zones": item.get("candidate_zones", []),
            "observable_meaning": meaning,
            "teacher_phrase": _teacher_observable_phrase(item),
        }
        proposal["case_core"]["observable_anchor"].append(v3_obs)
        proposal["case_info"]["observable_anchor"].append(v3_obs)

    proposal["case_core"]["observable_anchor"] = _dedupe_observable_items(
        proposal["case_core"]["observable_anchor"]
    )
    proposal["case_info"]["observable_anchor"] = _dedupe_observable_items(
        proposal["case_info"]["observable_anchor"]
    )

    proposal["case_core"]["observable_anchor"] = _dedupe_observable_items(
        proposal["case_core"]["observable_anchor"]
    )
    proposal["case_info"]["observable_anchor"] = _dedupe_observable_items(
        proposal["case_info"]["observable_anchor"]
    )

    # Context from current input.
    for sig in _list(getattr(pipeline_meta, "signals", []) or []):
        sig_norm = sig.get("normalized_text") or ""

        for ctx in _list(sig.get("context")):
            meaning = ctx.get("meaning")

            if (
                meaning == "prostředí školky / třídy"
                and "doma" in sig_norm
            ):
                continue

            if meaning:
                item = {
                    "text": _context_notepad_text(meaning, {"normalized_text": sig_norm}),
                    "status": "reported",
                    "source": "user",
                }
                proposal["case_core"]["context"].append(item)
                proposal["case_info"]["context"].append(item)

        for age in _list(sig.get("age")):
            value = age.get("value") or age.get("meaning")
            if value:
                proposal["case_core"]["age"].append({
                    "text": str(value),
                    "status": "reported",
                    "source": "user",
                })

    # Contradictions.
    contradictions = (validation.get("contradictions") or {}).get("items") or []
    for c in contradictions:
        proposal["contradictions"].append({
            "text": c.get("evidence") or c.get("code"),
            "meaning": c.get("severity"),
            "status": "needs_clarification",
        })

    # Safety notes.
    if {"LEAVES_SAFE_AREA", "SAFETY_CONTEXT"} & flags:
        proposal["safety_notes"].append({
            "text": "Bylo popsáno možné opuštění bezpečného prostoru nebo bezpečnostní kontext.",
            "priority": "high",
            "required_action": "ověřit frekvenci, kontext a aktuální bezpečnostní opatření",
        })

    # Open questions from pipeline quality.
    for missing in iq.get("missing_for_next_step") or []:
        if missing == "pedagogical_need":
            proposal["open_questions"].append({
                "question": "Co má být hlavní cíl podpory: zklidnit situaci, udržet skupinu, nebo porozumět spouštěči?",
                "priority": "medium",
                "purpose": "upřesnit pedagogickou potřebu",
            })

    _add_case_understanding_and_gaps(proposal, pipeline_meta)
    return _renumber_working_hypotheses(proposal)

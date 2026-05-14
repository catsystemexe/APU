def select_output_mode(intent: str, validation: dict, input_quality: dict | None = None) -> str:
    """
    Output mode v3:

    FAST:
      rychlý zásah / akutní větev + pozorovaný projev

    FULL:
      pozorovaný projev + potřeba učitele + konkrétní situační kontext

    PARTIAL:
      pozorovaný projev existuje, ale chybí potřeba nebo situační kontext
      NEBO existuje context signal bez child observable

    LOW_DATA:
      chybí pozorovaný projev i context signal
    """

    if intent == "PERSONAL":
        return "PERSONAL"

    iq = input_quality or {}

    has_observable = bool(iq.get("has_observable_anchor"))
    has_context_signal = bool(iq.get("has_context_signal"))
    need_known = bool(iq.get("pedagogical_need_known"))
    context_known = bool(iq.get("context_known"))
    specificity_score = int((iq.get("specificity") or {}).get("score", 0))

    if intent == "FAST_REQUEST" and has_observable:
        return "FAST"

    if not has_observable and has_context_signal:
        return "PARTIAL"

    if not has_observable:
        return "LOW_DATA"

    if has_observable and need_known and context_known and specificity_score >= 4:
        return "FULL"

    return "PARTIAL"

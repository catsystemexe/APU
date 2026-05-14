# backend/inference/zones.py

from backend.inference.zone_engine import infer_zone_states


def infer_zones(
    signals,
    blocks=None,
    profiles=None,
    validation=None,
    input_quality=None,
):
    """
    Zone inference v2.

    Uses Zone Engine v1:
    - observable anchors
    - S4 modifiers
    - validation dampening
    - specificity confidence caps

    Zones are transient pedagogical load states,
    not child traits.
    """

    return infer_zone_states(
        signals=signals,
        validation=validation,
        input_quality=input_quality,
    )
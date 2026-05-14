def infer_profiles(signals, blocks):
    profiles = []
    block_codes = {b.get("code") for b in (blocks or [])}

    def add(code, name, reason, confidence="LOW"):
        if any(p["code"] == code for p in profiles):
            return
        profiles.append({
            "code": code,
            "name": name,
            "confidence": confidence,
            "hypothesis_only": True,
            "reasons": [reason],
        })

    if "E" in block_codes or "A" in block_codes:
        add(
            "P2",
            "regulace / aktivace",
            "signály tělesné aktivace, regulace nebo pohybové potřeby",
            "MEDIUM",
        )

    if "B" in block_codes:
        add(
            "P6",
            "sociální porozumění",
            "signály vztahového nebo skupinového zatížení",
            "LOW",
        )

    if "D" in block_codes:
        add(
            "P1",
            "komunikace",
            "signály komunikační nejistoty nebo omezené komunikace",
            "MEDIUM",
        )

    if "C" in block_codes:
        add(
            "P2",
            "regulace / aktivace",
            "signály pozornosti nebo obtíže udržet činnost",
            "MEDIUM",
        )

    return profiles

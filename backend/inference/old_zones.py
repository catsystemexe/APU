ZONE_NAMES = {
    "Z1": "Výkon / činnost",
    "Z2": "Regulace",
    "Z3": "Bezpečí",
    "Z4": "Očekávání / porozumění / vztah",
}

ZONE_DEFAULT_MISSING = {
    "Z1": ["jaká činnost právě probíhá?", "co má dítě udělat?", "kdy se z činnosti odpojí?"],
    "Z2": ["jak rychle se stav rozjede?", "jak dlouho trvá návrat do klidu?", "co pomáhá regulaci?"],
    "Z3": ["co dítě vnímá jako ohrožující nebo zahlcující?", "je přítomné bezpečnostní riziko?", "kde se cítí bezpečněji?"],
    "Z4": ["rozumí dítě očekávání?", "jak byla instrukce podaná?", "jak reaguje na zjednodušení pravidla?"],
}


def infer_zones(signals, blocks, profiles):
    zones = {}

    for s in (signals or []):
        for o in s.get("observable_candidates", []):
            meaning = o.get("meaning") or "pozorovaný projev"
            confidence = o.get("confidence", "MEDIUM")
            candidate_zones = o.get("candidate_zones") or []

            for code in candidate_zones:
                if code not in ZONE_NAMES:
                    continue

                if code not in zones:
                    zones[code] = {
                        "code": code,
                        "name": ZONE_NAMES[code],
                        "confidence": confidence,
                        "hypothesis_only": True,
                        "reasons": [],
                        "missing_disambiguation": ZONE_DEFAULT_MISSING.get(code, []),
                    }

                reason = f"observable candidate: {meaning}"
                if reason not in zones[code]["reasons"]:
                    zones[code]["reasons"].append(reason)

                if confidence == "HIGH":
                    zones[code]["confidence"] = "HIGH"

    if not zones and signals:
        has_observable = any(
            s.get("observable_candidates")
            for s in (signals or [])
        )
        if has_observable:
            zones["ZX"] = {
                "code": "ZX",
                "name": "zóna zatím neurčena",
                "confidence": "LOW",
                "hypothesis_only": True,
                "reasons": ["existují pozorovatelné projevy, ale nestačí pro mapování na Z1–Z4"],
                "missing_disambiguation": ["potřeba učitele", "kontext", "intenzita", "spouštěče"],
            }

    return list(zones.values())

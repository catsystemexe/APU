BLOCK_NAMES = {
    "A": "Emoce a regulace",
    "B": "Sociální chování",
    "C": "Kognice a pozornost",
    "D": "Řeč a komunikace",
    "E": "Tělo a aktivace",
}

BLOCK_DEFAULT_MISSING = {
    "A": ["co spouští reakci?", "jak dlouho trvá zklidnění?", "co pomáhá návratu do klidu?"],
    "B": ["jde o skupinu nebo jednotlivce?", "jak reagují ostatní děti?", "mění se to s konkrétní osobou?"],
    "C": ["rozumí zadání?", "udrží činnost krátce nebo vůbec?", "je problém stálý nebo situační?"],
    "D": ["komunikuje více v bezpečnějším prostředí?", "pomáhá gesto nebo vizuální opora?", "jde o porozumění nebo vyjádření?"],
    "E": ["jde o přebuzení nebo útlum?", "pomáhá pohyb nebo klid?", "mění se stav během dne?"],
}


def infer_blocks(signals):
    found = {}

    for signal in signals or []:
        for obs in signal.get("observable_candidates", []) or []:
            meaning = obs.get("meaning") or "pozorovaný projev"
            confidence = obs.get("confidence") or "MEDIUM"
            candidate_blocks = obs.get("candidate_blocks") or []

            for code in candidate_blocks:
                code = str(code).strip().upper()

                if code not in BLOCK_NAMES:
                    continue

                if code not in found:
                    found[code] = {
                        "code": code,
                        "name": BLOCK_NAMES[code],
                        "confidence": confidence,
                        "hypothesis_only": True,
                        "reasons": [],
                        "candidate_subblocks": [],
                        "missing_disambiguation": BLOCK_DEFAULT_MISSING.get(code, []),
                    }

                reason = f"observable candidate: {meaning}"
                if reason not in found[code]["reasons"]:
                    found[code]["reasons"].append(reason)

                if confidence == "HIGH":
                    found[code]["confidence"] = "HIGH"

    return list(found.values())

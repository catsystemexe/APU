def detect_intent(message: str) -> str:
    t = (message or "").lower()

    if any(x in t for x in [
        "personal",
        "jak to funguje",
        "co umíš",
        "co umis",
    ]):
        return "PERSONAL"

    if any(x in t for x in [
        "rychlý zásah",
        "rychly zasah",
        "akutně",
        "akutne",
        "hned",
        "teď hned",
        "ted hned",
    ]):
        return "FAST_REQUEST"

    if any(x in t for x in [
        "navrhni",
        "řešení",
        "reseni",
        "postup",
        "chci návrh",
        "chci navrh",
        "jak to řešit",
        "jak to resit",
        "co mam delat",
        "co mám dělat",
        "potrebuju poradit",
        "potřebuji poradit",
        "potrebuju pomoct",
        "potřebuji pomoct",
    ]):
        return "FULL_REQUEST"

    return "STANDARD"


def detect_pedagogical_need(message: str) -> bool:
    t = (message or "").lower()

    return any(x in t for x in [
        "potrebuju",
        "potřebuji",
        "chci",
        "jak",
        "co mam delat",
        "co mám dělat",
        "resit",
        "řešit",
        "pomoc",
        "poradit",
        "udrzet",
        "udržet",
        "zklidnit",
        "nastavit hranice",
        "komunikovat s rodicem",
        "komunikovat s rodičem",
    ])

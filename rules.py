"""RULE ENGINE (not ML): Life-Saving Rules + barrier failures with word-boundary phrase matching and evidence."""
import re
def _c(p): return re.compile(p, re.I)
LSR = {
 "Energy Isolation / LOTO": [r"\bloto\b", r"\block(?:ed)?[- ]?out\b", r"\btag(?:ged)?[- ]?out\b", r"\bisolation\b", r"\bnot isolated\b", r"\blive (?:electrical|wire|wiring|cable|panel|equipment)\b", r"\benergi[sz]ed\b", r"\bstored energy\b"],
 "Working at Height": [r"\bat height\b", r"\bharness\b", r"\bscaffold\w*", r"\bladder\b", r"\bfall protection\b", r"\bfell from\b", r"\bunprotected edge\b", r"\bfall arrest\b"],
 "Confined Space": [r"\bconfined space\b", r"\bentered (?:the )?(?:tank|vessel|sump|pit|manhole)\b", r"\btank entry\b", r"\bvessel entry\b", r"\bmanhole\b"],
 "Line of Fire": [r"\bline of fire\b", r"\bunder (?:a )?(?:suspended|swinging) load\b", r"\bswung\b.*\bworker\b", r"\bstruck by\b", r"\bpinch point\b", r"\bwhipcheck\b|\bhose whip\w*"],
 "Lifting": [r"\bcrane\b", r"\bsling\w*", r"\bsuspended load\b", r"\blifting (?:operation|plan)\b", r"\bhoist\b", r"\brigging\b"],
 "Driving / Vehicle Safety": [r"\bseat ?belt\b", r"\bovers?peed\w*", r"\bforklift\b", r"\breversing\b", r"\bmobile phone while driving\b", r"\bvehicle\b"],
 "Hot Work": [r"\bhot work\b", r"\bwelding\b", r"\bgrinding\b", r"\bgas cutting\b", r"\bspark\w*", r"\bfire watch\b"],
 "Permit to Work": [r"\bpermit\b", r"\bptw\b", r"\bwithout (?:a )?permit\b", r"\bexpired permit\b"],
 "H2S / Toxic Gas": [r"\bh2s\b", r"\bhydrogen sulph?ide\b", r"\btoxic gas\b", r"\bgas detector\b", r"\bbreathing apparatus\b|\bscba\b"],
 "Gas Leak": [r"\bgas leak\w*", r"\bhydrocarbon leak\w*", r"\bleak(?:ing)? (?:gas|flange|valve)\b", r"\bflange leak\w*"],
 "Electrical Safety": [r"\belectric(?:al|ity)?\b", r"\bshock\b", r"\bearthing\b", r"\bexposed (?:wire|wiring|cable)s?\b", r"\bdistribution board\b"],
 "Excavation": [r"\bexcavat\w*", r"\btrench\w*", r"\bshoring\b"],
 "PPE": [r"\bppe\b", r"\bhelmet\b", r"\bsafety (?:shoes|glasses|goggles)\b", r"\bwithout (?:a )?(?:hard hat|gloves)\b"],
 "Dropped Objects": [r"\bdropped (?:object|tool|item)s?\b", r"\bfalling (?:object|tool)s?\b", r"\btool fell\b"],
}
NEG = r"(?:no|not|without|missing|absent|never|didn'?t|did not|skipped|bypass\w*|failed|unavailable|lack of|nahi)"
BARRIERS = {
 "Gas testing": [rf"\b{NEG}\b[^.]{{0,25}}\bgas (?:test\w*|detector|check\w*)\b", r"\bwithout gas test\w*"],
 "Permit to Work": [rf"\b{NEG}\b[^.]{{0,20}}\b(?:permit|ptw)\b", r"\bexpired permit\b"],
 "Energy isolation": [rf"\b{NEG}\b[^.]{{0,20}}\b(?:isolation|loto|lock(?:ed)?[- ]?out)\b", r"\bnot isolated\b"],
 "PPE": [rf"\b{NEG}\b[^.]{{0,20}}\b(?:ppe|helmet|gloves|goggles|safety shoes)\b"],
 "Barricade": [rf"\b{NEG}\b[^.]{{0,20}}\b(?:barricad\w*|cordon\w*)\b"],
 "Interlock / safety system": [r"\binterlock\b[^.]{0,20}\b(?:bypass\w*|failed|defeated)\b", r"\bbypass\w*[^.]{0,20}\b(?:interlock|alarm|trip|safety system)\b"],
 "Machine guarding": [rf"\b{NEG}\b[^.]{{0,20}}\bguard\w*\b"],
 "Standby person": [rf"\b{NEG}\b[^.]{{0,20}}\b(?:standby|stand-by|watchman|attendant)\b"],
 "Fall protection": [rf"\b{NEG}\b[^.]{{0,20}}\b(?:harness|fall protection|lifeline|fall arrest)\b"],
 "Supervision": [rf"\b(?:no|inadequate|lack of)\b[^.]{{0,15}}\bsupervis\w*\b"],
}
_L = {k: [_c(p) for p in v] for k, v in LSR.items()}
_B = {k: [_c(p) for p in v] for k, v in BARRIERS.items()}
def _snip(text, m):
    s, e = max(0, m.start()-15), min(len(text), m.end()+25)
    return text[s:e].strip()
def detect_rules(text):
    """Returns [{'rule':..., 'evidence':...}] — first matching evidence per rule."""
    out = []
    for rule, pats in _L.items():
        for p in pats:
            m = p.search(text or "")
            if m: out.append({"rule": rule, "evidence": _snip(text, m)}); break
    return out
def detect_barriers(text):
    """Returns [{'barrier':..., 'status':'Missing/Failed', 'evidence':...}]."""
    out = []
    for b, pats in _B.items():
        for p in pats:
            m = p.search(text or "")
            if m: out.append({"barrier": b, "status": "Missing/Failed", "evidence": _snip(text, m)}); break
    return out

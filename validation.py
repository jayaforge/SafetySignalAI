import re
from config import MIN_TEXT_CHARS
SAFETY_TERMS = r"""\b(ppe|helmet|harness|gas|h2s|tank|vessel|confined|permit|ptw|loto|lockout|isolat\w*|valve|pipeline|crane|lift\w*|sling|scaffold\w*|height|fall\w*|spill|leak\w*|fire|flame|spark|weld\w*|hot work|electric\w*|cable|energi[sz]ed|excavat\w*|trench|barricade|guard|interlock|rig|drill\w*|wellhead|pressure|chemical|unsafe|hazard\w*|near miss|injur\w*|accident|incident|forklift|truck|vehicle|seatbelt|worker|operator|contractor|slip\w*|trip\w*|dropped|falling|unprotected|bypass\w*|detector|alarm|explosi\w*|toxic|fumes?)\b"""
_RX = re.compile(SAFETY_TERMS, re.I)
def validate_text(text):
    """Returns (ok, message). Never raises."""
    if text is None or not isinstance(text, str) or not text.strip():
        return False, "Report text is empty."
    t = re.sub(r"\s+", " ", text).strip()
    if len(t) < MIN_TEXT_CHARS:
        return False, f"Report text is too short (minimum {MIN_TEXT_CHARS} characters)."
    if not re.search(r"[A-Za-z]{3,}", t):
        return False, "Report text contains no readable words."
    return True, t
def is_safety_relevant(text):
    """RULE-ENGINE keyword gate (not ML). Returns (bool, matched_terms)."""
    hits = sorted({m.group(0).lower() for m in _RX.finditer(text or "")})
    return len(hits) >= 1, hits
NOT_SAFETY_MSG = "This input does not appear to be an industrial safety report."

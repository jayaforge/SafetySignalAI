import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rules import detect_rules, detect_barriers
from validation import validate_text, is_safety_relevant
from risk import compute_risk
names = lambda t: [r["rule"] for r in detect_rules(t)]
def test_delivery_not_live_electrical():
    assert "Energy Isolation / LOTO" not in names("Delivery truck arrived late at the store yard")
def test_live_cable_triggers():
    assert "Energy Isolation / LOTO" in names("Worked on live cable without isolation")
def test_confined_space_evidence():
    r = detect_rules("Worker entered tank without gas testing")
    assert any(x["rule"] == "Confined Space" and "entered tank" in x["evidence"] for x in r)
def test_barrier_gas_test():
    assert any(b["barrier"] == "Gas testing" for b in detect_barriers("No gas detector test was completed before entry."))
def test_validation():
    assert not validate_text("")[0] and not validate_text(None)[0] and not validate_text("hi")[0]
def test_non_safety():
    assert not is_safety_relevant("The canteen food was good today.")[0]
def test_risk_breakdown_and_cap():
    r = compute_risk(0.8, "High", "Near Miss", 1, 1, 3, True)
    assert r["score"] == 92 and r["level"] == "CRITICAL"
    assert compute_risk(0, "Low", "Unsafe Act", 0, 0, safety_relevant=False)["level"] == "N/A"

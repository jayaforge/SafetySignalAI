import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline import Engine
_e = Engine()
def test_empty_and_short_input_never_crash():
    for t in (None, "", "   ", "hi", 12345): assert "error" in _e.analyze(t)
def test_non_safety_gets_no_risk_level():
    a = _e.analyze("The canteen food was good today."); assert a["relevant"] is False and a["risk"]["level"] == "N/A"
def test_confined_space_report_full_analysis():
    a = _e.analyze("Worker entered the tank without gas testing and no standby person at the manhole.", site="Duliajan", severity="Low")
    assert a["relevant"] and any(r["rule"] == "Confined Space" for r in a["rules"]) and any(b["barrier"] == "Gas testing" for b in a["barriers"])
    assert a["risk"]["level"] in ("HIGH", "CRITICAL") and a["actions"] and "model confidence estimate" in " ".join(a["explanations"])
def test_prediction_fields_present():
    a = _e.analyze("Suspended load swung unexpectedly during crane lift and narrowly missed a worker.")
    assert a["ml"]["report_type"]["label"] in ("Unsafe Act", "Unsafe Condition", "Near Miss") and a["ml"]["sif"]["sif_level"] in ("High", "Medium", "Low")
def test_delivery_text_does_not_trigger_electrical():
    a = _e.analyze("Delivery truck arrived late with spare parts"); assert not a.get("rules")
def test_malformed_csv_values_rejected_not_crashed():
    import tempfile, database as db
    from pipeline import ingest
    c = db.connect(os.path.join(tempfile.mkdtemp(), "x.db"))
    saved, rej = ingest(c, _e, [{"text": "Fitter on scaffold at height without harness", "severity": "Extreme"}, {"text": "gas leak at flange", "reported_at": "garbage"}, {"text": ""}])
    assert saved == 0 and len(rej) == 3

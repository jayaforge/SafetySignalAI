import sys, os, tempfile, datetime as dt; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
from repeats import SimilarityIndex, repeat_count, with_rules
from early_warning import detect_emerging, cross_site_clusters
import database as db, actions as A
def _d(rows): return pd.DataFrame(rows, columns=["id", "reported_at", "site", "text"]).pipe(with_rules)
def test_duplicate_vs_similar():
    h = _d([(1, "2026-09-01", "Duliajan", "Worker entered the tank without gas testing and no standby person"), (2, "2026-09-02", "Digboi", "Oil spill on walkway near pump house")])
    r = SimilarityIndex(h).query("Worker entered the tank without gas testing and no standby person.")
    assert r[0]["id"] == 1 and r[0]["kind"].startswith("Duplicate")
    r2 = SimilarityIndex(h).query("Contractor went inside the tank, gas testing not done")
    assert r2 and r2[0]["id"] == 1 and not r2[0]["kind"].startswith("Duplicate")
def test_repeat_window():
    h = _d([(i, f"2026-09-{d:02d}", "Duliajan", "entered tank without gas test") for i, d in enumerate([1, 10, 20], 1)] + [(9, "2026-06-01", "Duliajan", "entered tank without gas test")])
    assert repeat_count(h, "Duliajan", "Confined Space", "2026-09-25") == 3 and repeat_count(h, "Digboi", "Confined Space", "2026-09-25") == 0
def _ew(prev, cur, now="2026-09-30"):
    n = pd.Timestamp(now); rows = [(i, str(n - pd.Timedelta(days=8 + i % 5)), "Duliajan", "entered tank without gas test") for i in range(prev)]
    rows += [(100 + i, str(n - pd.Timedelta(days=i % 6)), "Duliajan", "entered tank without gas test") for i in range(cur)]; return _d(rows), n
def test_early_warning_triggers_3_to_9():
    d, n = _ew(3, 9); a = detect_emerging(d, n)
    assert len(a) == 1 and a[0]["growth_percent"] == 200.0 and a[0]["level"] == "CRITICAL" and "not guaranteed prediction" in a[0]["note"]
def test_early_warning_no_false_alarm():
    assert detect_emerging(*_ew(1, 2)) == [] and detect_emerging(*_ew(2, 3)) == []   # <3 current, or <2x previous
def test_cross_site():
    n = pd.Timestamp("2026-09-30"); d = _d([(i, str(n - pd.Timedelta(days=1)), s, "worked on live cable without isolation") for i, s in enumerate(["A", "B", "C"])])
    assert cross_site_clusters(d, n)[0]["hazard"] == "Energy Isolation / LOTO"
def test_db_actions_workflow_and_safety():
    p = os.path.join(tempfile.mkdtemp(), "t.db"); c = db.connect(p)
    rid = db.add_report(c, {"text": "x'); DROP TABLE reports;--", "site": "Duliajan", "reported_at": "2026-09-01 10:00"})
    assert c.execute("SELECT COUNT(*) FROM reports").fetchone()[0] == 1       # injection text stored as data
    acts = A.recommend(["Confined Space"], "CRITICAL", dt.datetime(2026, 9, 1)); assert len(acts) == 6 and A.recommend(["Confined Space"], "LOW") == []
    db.add_actions(c, rid, acts); aid = c.execute("SELECT id FROM actions").fetchone()[0]
    for bad in [("Resolved", "Ravi", "done"), ("Verified", "Sam", None)]:
        try: A.advance(c, aid, *bad); assert False
        except ValueError: pass
    A.advance(c, aid, "In Progress", "Ravi"); A.advance(c, aid, "Resolved", "Ravi", "Entry suspended")
    try: A.advance(c, aid, "Verified", "ravi"); assert False
    except ValueError: pass
    A.advance(c, aid, "Verified", "Meera"); assert c.execute("SELECT status FROM actions WHERE id=?", (aid,)).fetchone()[0] == "Verified"
def test_overdue_and_escalation():
    a = {"status": "Open", "priority": "CRITICAL", "due_date": "2026-09-01T10:00"}
    assert A.escalation_stage(a, dt.datetime(2026, 9, 1, 9)) is None
    assert A.escalation_stage(a, dt.datetime(2026, 9, 1, 12)) == "Site HSE" and A.escalation_stage(a, dt.datetime(2026, 9, 2, 12)) == "Area Manager" and A.escalation_stage(a, dt.datetime(2026, 9, 4)) == "GM-HSE"
def test_review_stores_original():
    c = db.connect(os.path.join(tempfile.mkdtemp(), "r.db")); rid = db.add_report(c, {"text": "abc def ghi jkl mno", "report_type": "Near Miss", "risk_level": "HIGH"})
    db.review_report(c, rid, "Overridden", "Asha", "Actually UA", new_type="Unsafe Act"); r = c.execute("SELECT * FROM reports").fetchone()
    assert r["report_type"] == "Unsafe Act" and "Near Miss" in r["original_prediction"] and r["reviewer"] == "Asha"
